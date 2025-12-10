import pandas as pd
import heapq
from collections import Counter
import os

INPUT_FILE = 'csv/goodreads_graph_base_clean.csv'

class HuffmanNode:
    def __init__(self, item, frequency, left=None, right=None):
        self.item = item            
        self.frequency = frequency  
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.frequency < other.frequency

def build_huffman_tree(data_list):
    if not data_list: return None
    priority_queue = []
    for item, weight in data_list:
        heapq.heappush(priority_queue, HuffmanNode(item, weight))
    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)
        merged = HuffmanNode(None, left.frequency + right.frequency, left, right)
        heapq.heappush(priority_queue, merged)
    return priority_queue[0] if priority_queue else None

def generate_graph_vertices_with_huffman():
    if not os.path.exists(INPUT_FILE):
        print(f"ERRO: Arquivo '{INPUT_FILE}' não encontrado.")
        return None

    try:
        df = pd.read_csv(INPUT_FILE)
        df['cleaned_desc'] = df['cleaned_desc'].astype(str)
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        return None

    graph_vertices = {}
    grouped = df.groupby('subgenre_node')
    
    for subgenre, group in grouped:
        # Rating Tree
        rating_data = []
        for _, row in group.iterrows():
            meta = {'title': row['title'], 'author': row['author'] if 'author' in row else 'N/A'}
            rating_data.append((meta, row['weighted_rating']))
        rating_root = build_huffman_tree(rating_data)
        
        # Word Tree
        full_text = " ".join(group['cleaned_desc'])
        word_counts = Counter(full_text.split())
        word_list = word_counts.most_common(1000)
        word_root = build_huffman_tree(word_list)

        if rating_root and word_root:
            graph_vertices[subgenre] = {
                'subgenre_node': subgenre,
                'rating_tree_root': rating_root,
                'word_tree_root': word_root
            }
            
    return graph_vertices