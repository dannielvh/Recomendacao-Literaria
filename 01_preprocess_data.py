import pandas as pd
import numpy as np
import re
from collections import Counter
import os
import heapq

INPUT_FILE = 'goodreads_books.csv'
OUTPUT_FILE = 'goodreads_graph_base_clean.csv'

MIN_RATING_COUNT = 1000 
MIN_VOTES_FOR_CONFIDENCE = 1000 
GENRE_ALVO = 'Gothic'

try:
    df = pd.read_csv(INPUT_FILE, low_memory=False)
except FileNotFoundError:
    print(f"\nERRO: Arquivo '{INPUT_FILE}' não encontrado.")
    exit()

COLUMNS_TO_KEEP = ['isbn', 'title', 'desc', 'genre', 'rating', 'totalratings', 'author']
df = df[COLUMNS_TO_KEEP].copy()

df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
df['totalratings'] = pd.to_numeric(df['totalratings'], errors='coerce')

# Remove linhas onde falta o ID, título, notas...
df.dropna(subset=['isbn', 'title', 'rating', 'totalratings', 'author', 'desc'], inplace=True)


#UNIFICAÇÃO DE MÚLTIPLAS EDIÇÕEs
df['title_clean'] = df['title'].str.strip().str.lower()
df['author_clean'] = df['author'].str.strip().str.lower() 

df_grouped = df.groupby(['title_clean', 'author_clean']).agg(
    # Soma a contagem total de avaliações
    totalratings=('totalratings', 'sum'),
    rating_sum_product=('totalratings', lambda x: (df.loc[x.index, 'rating'] * x).sum()),
    
    title=('title', 'first'),
    genre=('genre', 'first'),
    author=('author', 'first'),
    desc=('desc', 'first') 
).reset_index()

df_grouped['book_id'] = np.arange(len(df_grouped)) + 1

df_grouped['rating'] = np.where(
    df_grouped['totalratings'] == 0,
    0.0,
    df_grouped['rating_sum_product'] / df_grouped['totalratings']
)

df_grouped.drop(columns=['rating_sum_product'], inplace=True)
df = df_grouped.copy() 

# Filtragem de Livros que pertencem ao Gênero-Alvo
df_target = df[df['genre'].str.contains(GENRE_ALVO, case=False, na=False)].copy()

print(f"Total de Obras no Gênero '{GENRE_ALVO}': {len(df_target)}")

if len(df_target) < 100:
    print("Aviso: Poucas obras no gênero-alvo. Considere um gênero mais amplo.")

# Função para Limpeza e Pré-processamento Textual (Sinopse)
def clean_text_for_huffman(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    stopwords = set(["a", "o", "e", "de", "da", "do", "em", "um", "uma", "o", "as", "os", "para"])
    tokens = text.split()
    return " ".join(t for t in tokens if t not in stopwords)

df_target['cleaned_desc'] = df_target['desc'].apply(clean_text_for_huffman)
df_target = df_target[df_target['cleaned_desc'].str.len() > 0].copy()


def clean_and_standardize_genres(genres_str):
    #Limpa e padroniza os subgêneros de uma string
    if pd.isna(genres_str):
        return []
    genres_list = [g.strip().lower() for g in genres_str.split(',')]
    mapping = {
        'sci-fi': 'science fiction', 'ya': 'young adult', 'sf': 'science fiction',
        'hist': 'history', 'non-fiction': 'nonfiction'
    }
    cleaned_genres = []
    for g in genres_list:
        g_clean = mapping.get(g, g)
        if len(g_clean) > 2 and g_clean != 'books': 
            cleaned_genres.append(g_clean)
    return list(set(cleaned_genres))

# 🚨 APLICAÇÃO NO DATAFRAME FILTRADO: df_target
df_target['cleaned_genres'] = df_target['genre'].apply(clean_and_standardize_genres)
df_target = df_target[df_target['cleaned_genres'].apply(len) > 0].copy()

C = df_target['rating'].mean()  
m = MIN_VOTES_FOR_CONFIDENCE 
R = df_target['rating']
v = df_target['totalratings']
df_target['weighted_rating'] = ((R * v) + (C * m)) / (v + m)

class Node:
    #Nó na Árvore de Huffman.
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanTree:
    """Construção e codificação da Árvore de Huffman."""
    def __init__(self, text):
        self.text = text
        self.heap = []
        self.codes = {}
        self.root = None
        if text:
            self._build_tree(text)

    def _make_frequency_dict(self):
        return Counter(self.text)

    def _build_heap(self, frequency):
        for char, freq in frequency.items():
            heapq.heappush(self.heap, Node(char, freq))

    def _build_tree(self, text):
        frequency = self._make_frequency_dict()
        if not frequency:
            return
        self._build_heap(frequency)

        while len(self.heap) > 1:
            node1 = heapq.heappop(self.heap)
            node2 = heapq.heappop(self.heap)
            merged = Node(None, node1.freq + node2.freq)
            merged.left = node1
            merged.right = node2
            heapq.heappush(self.heap, merged)

        self.root = self.heap[0]
        self._make_codes_helper(self.root, "")

    def _make_codes_helper(self, root, current_code):
        if root is None:
            return
        if root.char is not None:
            self.codes[root.char] = current_code
            return
        self._make_codes_helper(root.left, current_code + "0")
        self._make_codes_helper(root.right, current_code + "1")
        
    def get_avg_code_length(self):
        """Calcula o tamanho médio do código em bits por caractere (Métrica de Similaridade)."""
        if not self.codes: return 0
        total_bits = 0
        total_chars = 0
        frequency = Counter(self.text)
        
        for char, freq in frequency.items():
            code = self.codes.get(char)
            if code is not None:
                total_bits += freq * len(code)
                total_chars += freq
            
        return total_bits / total_chars if total_chars > 0 else 0


def build_huffman_trees(df_target):
    """
    Agrupa o texto por subgênero e constrói uma Árvore de Huffman (Vértice) para cada um.
    """
    print("\n--- 3.1 GERAÇÃO DE VÉRTICES (ÁRVORES DE HUFFMAN) ---")
    
    # Explode o DataFrame para ter uma linha por Obra-Subgênero
    df_huffman = df_target.explode('cleaned_genres')
    
    # 1. Agrega todo o texto limpo para cada subgênero
    subgenre_texts = df_huffman.groupby('cleaned_genres')['cleaned_desc'].apply(lambda x: ' '.join(x)).reset_index()
    
    # 2. Constrói a Árvore de Huffman para cada texto consolidado
    huffman_trees = {}
    
    for index, row in subgenre_texts.iterrows():
        subgenre = row['cleaned_genres']
        consolidated_text = row['cleaned_desc']
        
        tree = HuffmanTree(consolidated_text)
        
        if tree.root is not None:
            huffman_trees[subgenre] = tree
        
    print(f"Total de Vértices/Árvores geradas: {len(huffman_trees)}")
    return huffman_trees

# CHAMADA FINAL DAS FUNÇÕES
# 1. GERAÇÃO DAS ÁRVORES (Output principal da sua tarefa)
huffman_subgenre_vertices = build_huffman_trees(df_target)

# 2. PREPARAÇÃO DA BASE DE DADOS PARA O GRAFO (Output para o Dan)

# Aplica o filtro final de relevância (MIN_RATING_COUNT)
df_filtered = df_target[df_target['totalratings'] >= MIN_RATING_COUNT].copy()

# 'Explode' o DataFrame para que cada linha seja uma relação Obra <-> Subgênero
graph_base = df_filtered.explode('cleaned_genres').rename(columns={'cleaned_genres': 'subgenre_node'})

# Seleciona as colunas essenciais para o Grafo
COLUMNS_TO_EXPORT = ['book_id', 'title', 'author', 'subgenre_node', 'weighted_rating', 'totalratings']
graph_base_final = graph_base[COLUMNS_TO_EXPORT].copy()

# Limpeza final de linhas que podem ter subgêneros vazios
graph_base_final.dropna(subset=['subgenre_node'], inplace=True)
graph_base_final = graph_base_final[graph_base_final['subgenre_node'] != '']


print(f"Total de Obras Únicas no Grafo (após filtro): {graph_base_final['book_id'].nunique()}")
print(f"Total de Arestas (Relações Obra-Subgênero): {len(graph_base_final)}")
print(f"Base Final salva em: {OUTPUT_FILE}")

# Exportar o arquivo final limpo
graph_base_final.to_csv(OUTPUT_FILE, index=False)