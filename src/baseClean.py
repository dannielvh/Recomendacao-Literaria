import pandas as pd
import numpy as np
import re
import os

INPUT_FILE = 'goodreads_books.csv'
OUTPUT_FILE = 'csv/goodreads_graph_base_clean.csv'

MIN_RATING_COUNT = 1000       
MIN_VOTES_FOR_CONFIDENCE = 1000 

STOPWORDS = set([
    #portugues
    "a", "o", "e", "de", "da", "do", "em", "um", "uma", "os", "as", "para", 
    "com", "por", "sem", "nas", "nos", "ele", "ela", "eles", "elas", "isso", 
    "este", "esta", "aquele", "aquela", "sao", "foi", "nao", "sim", "que", "se",
    "seu", "sua", "pelo", "pela", "como", "mais", "mas", "foi", "era", "ser",
    #ingles
    "the", "and", "of", "to", "a", "in", "is", "that", "it", "was", "for", "on", 
    "with", "as", "by", "he", "she", "at", "be", "this", "an", "his", "her", 
    "from", "are", "but", "not", "or", "have", "had", "which", "one", "you", 
    "story", "book", "novel", "life", "about", "all", "so", "my", "me"
])

def load_and_basic_clean():
    if not os.path.exists(INPUT_FILE):
        print(f"ERRO: Arquivo '{INPUT_FILE}' não encontrado na raiz do projeto.")
        return None
    try:
        df = pd.read_csv(INPUT_FILE, low_memory=False)
        cols = ['isbn', 'title', 'desc', 'genre', 'rating', 'totalratings', 'author']
        available_cols = [c for c in cols if c in df.columns]
        df = df[available_cols].copy()
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        df['totalratings'] = pd.to_numeric(df['totalratings'], errors='coerce')
        df.dropna(subset=['title', 'rating', 'totalratings', 'desc', 'genre'], inplace=True)
        return df
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        return None

def clean_text_for_huffman(text):
    if pd.isna(text): return ""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text) 
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = text.split()
    clean_tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    return " ".join(clean_tokens)

def clean_and_standardize_genres(genres_str):
    if pd.isna(genres_str): return []
    genres_list = [g.strip().lower() for g in genres_str.split(',')]
    mapping = {
        'sci-fi': 'science fiction', 'ya': 'young adult', 'sf': 'science fiction',
        'hist': 'history', 'non-fiction': 'nonfiction'
    }
    cleaned = []
    for g in genres_list:
        g_clean = mapping.get(g, g)
        if len(g_clean) > 2 and g_clean != 'books': 
            cleaned.append(g_clean)
    return list(set(cleaned))

def process_data(target_genre=None):
    df = load_and_basic_clean()
    if df is None: return False

    # Unificação de Edições
    df['title_clean'] = df['title'].str.strip().str.lower()
    df['author_clean'] = df['author'].str.strip().str.lower() 
    df['temp_score'] = df['rating'] * df['totalratings']

    df_grouped = df.groupby(['title_clean', 'author_clean']).agg(
        totalratings=('totalratings', 'sum'),
        total_score=('temp_score', 'sum'),
        title=('title', 'first'),
        genre=('genre', 'first'),
        author=('author', 'first'),
        desc=('desc', 'first')
    ).reset_index()

    df_grouped['rating'] = np.where(
        df_grouped['totalratings'] == 0, 0.0,
        df_grouped['total_score'] / df_grouped['totalratings']
    )
    df_grouped['book_id'] = np.arange(len(df_grouped)) + 1
    df = df_grouped.copy()

    if target_genre:
        df = df[df['genre'].str.contains(target_genre, case=False, na=False)].copy()
        if len(df) == 0:
            print(f"AVISO: Nenhum livro encontrado para '{target_genre}'.")
            return False
    
    print(f"Livros encontrados: {len(df)}")
    
    df['cleaned_desc'] = df['desc'].apply(clean_text_for_huffman)
    df = df[df['cleaned_desc'].str.len() > 0].copy()

    #Estimativa da Média Bayesiana
    C = df['rating'].mean()
    m = MIN_VOTES_FOR_CONFIDENCE
    df['weighted_rating'] = ((df['rating'] * df['totalratings']) + (C * m)) / (df['totalratings'] + m)

    df = df[df['totalratings'] >= MIN_RATING_COUNT].copy()

    df['cleaned_genres'] = df['genre'].apply(clean_and_standardize_genres)
    graph_base = df.explode('cleaned_genres').rename(columns={'cleaned_genres': 'subgenre_node'})
    
    graph_base.dropna(subset=['subgenre_node', 'cleaned_desc'], inplace=True)
    graph_base = graph_base[graph_base['subgenre_node'] != '']

    cols = ['book_id', 'title', 'subgenre_node', 'weighted_rating', 'cleaned_desc', 'title', 'author']
    # Remove duplicatas de colunas se houver
    cols = list(dict.fromkeys(cols))
    graph_base_final = graph_base[cols].copy()
    
    print(f"Salvando em {OUTPUT_FILE}.")
    graph_base_final.to_csv(OUTPUT_FILE, index=False)
    return True

if __name__ == "__main__":
    process_data('Gothic')