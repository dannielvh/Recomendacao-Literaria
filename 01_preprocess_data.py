import pandas as pd
import numpy as np
import re
from collections import Counter
import os

INPUT_FILE = 'goodreads_books.csv'
OUTPUT_FILE = 'goodreads_graph_base_clean.csv'

MIN_RATING_COUNT = 1000 
MIN_VOTES_FOR_CONFIDENCE = 1000 

try:
    df = pd.read_csv(INPUT_FILE, low_memory=False)
except FileNotFoundError:
    print(f"\nERRO: Arquivo '{INPUT_FILE}' não encontrado.")
    exit()

COLUMNS_TO_KEEP = ['title', 'genre', 'rating', 'totalratings', 'author']
df = df[COLUMNS_TO_KEEP].copy()

df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
df['totalratings'] = pd.to_numeric(df['totalratings'], errors='coerce')

# Remove linhas onde falta o ID, título, notas, ou autor
df.dropna(subset=['title', 'rating', 'totalratings', 'author'], inplace=True)


#UNIFICAÇÃO DE MÚLTIPLAS EDIÇÕEs
df['title_clean'] = df['title'].str.strip().str.lower()
df['author_clean'] = df['author'].str.strip().str.lower() 

df_grouped = df.groupby(['title_clean', 'author_clean']).agg(
    # Soma a contagem total de avaliações
    totalratings=('totalratings', 'sum'),
    rating_sum_product=('totalratings', lambda x: (df.loc[x.index, 'rating'] * x).sum()),
    
    title=('title', 'first'),
    genre=('genre', 'first'),
    author=('author', 'first') 
).reset_index()

df_grouped['rating'] = np.where(
    df_grouped['totalratings'] == 0,
    0.0,
    df_grouped['rating_sum_product'] / df_grouped['totalratings']
)

df_grouped.drop(columns=['rating_sum_product'], inplace=True)
df = df_grouped.copy() 

# TRATAMENTO DE GÊNEROS E SUBGÊNEROS

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

df['cleaned_genres'] = df['genre'].apply(clean_and_standardize_genres)
df = df[df['cleaned_genres'].apply(len) > 0].copy()


# CÁLCULO DA MÉDIA PONDERADA FINAL (Weighted Rating)
C = df['rating'].mean()  
m = MIN_VOTES_FOR_CONFIDENCE 
R = df['rating']
v = df['totalratings']
df['weighted_rating'] = ((R * v) + (C * m)) / (v + m)

#GERAÇÃO DA BASE FINAL PARA O GRAFO

df_filtered = df[df['totalratings'] >= MIN_RATING_COUNT].copy()

# 'Explode' o DataFrame para que cada linha seja um relacionamento (Obra <-> Subgênero)
graph_base = df_filtered.explode('cleaned_genres').rename(columns={'cleaned_genres': 'subgenre_node'})
COLUMNS_TO_EXPORT = ['title', 'author', 'subgenre_node', 'weighted_rating', 'totalratings']
graph_base_final = graph_base[COLUMNS_TO_EXPORT].copy()

graph_base_final.dropna(subset=['subgenre_node'], inplace=True)
graph_base_final = graph_base_final[graph_base_final['subgenre_node'] != '']


print(f"Total de Subgêneros Únicos (Vértices de Subgênero): {graph_base_final['subgenre_node'].nunique()}")
print(f"Total de Arestas (Relações Obra-Subgênero): {len(graph_base_final)}")
print(f"Base Final salva em: {OUTPUT_FILE}")

graph_base_final.to_csv(OUTPUT_FILE, index=False)