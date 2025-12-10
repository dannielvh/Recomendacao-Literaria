import pandas as pd
from collections import deque
import itertools
import sys

try:
    from vertice import generate_graph_vertices_with_huffman as generate_vertices
except ImportError as e:
    print(f"ERRO: Não foi possível importar 'vertice.py'. Detalhe: {e}")
    sys.exit(1)

OUTPUT_EDGES_FILE = 'csv/goodreads_graph_edges.csv'
MIN_SIMILARITY_THRESHOLD = 0.5 

def bfs_get_avg_depth(root_node):
    if not root_node: return 0.0
    queue = deque([(root_node, 0)])
    total_depth, leaf_count = 0, 0
    while queue:
        node, depth = queue.popleft()
        if node.item is not None:
            leaf_count += 1
            total_depth += depth
        if node.left: queue.append((node.left, depth + 1))
        if node.right: queue.append((node.right, depth + 1))
    return (total_depth / leaf_count) if leaf_count > 0 else 0.0

def precompute_metrics(vertices_dict):
    #Pré-calculando métricas 
    cache = {}
    for subgenre, data in vertices_dict.items():
        cache[subgenre] = {
            'rating_depth': bfs_get_avg_depth(data['rating_tree_root']),
            'word_depth': bfs_get_avg_depth(data['word_tree_root'])
        }
    return cache

def calculate_similarity_fast(metrics_a, metrics_b):
    diff_rating = abs(metrics_a['rating_depth'] - metrics_b['rating_depth'])
    sim_rating = 1.0 / (1.0 + diff_rating)
    diff_word = abs(metrics_a['word_depth'] - metrics_b['word_depth'])
    sim_word = 1.0 / (1.0 + diff_word)
    return (sim_rating + sim_word) / 2

def main():
    print("\nGerando Grafo Híbrido")
    vertices = generate_vertices()
    if not vertices: return

    subgenres = list(vertices.keys())
    metrics_cache = precompute_metrics(vertices)
    edge_list = []
    combinations = list(itertools.combinations(subgenres, 2))
    
    for i, (sub_a, sub_b) in enumerate(combinations):
        final_sim = calculate_similarity_fast(metrics_cache[sub_a], metrics_cache[sub_b])
        if final_sim >= MIN_SIMILARITY_THRESHOLD:
            edge_list.append({
                'Source': sub_a, 'Target': sub_b,
                'Weight': round(final_sim, 4), 'Type': 'Undirected'
            })

    if edge_list:
        df = pd.DataFrame(edge_list)
        df.sort_values(by='Weight', ascending=False, inplace=True)
        df.to_csv(OUTPUT_EDGES_FILE, index=False)
        print(f"{len(df)} arestas salvas em {OUTPUT_EDGES_FILE}")
    else:
        print("Nenhuma aresta encontrada.")

if __name__ == "__main__":
    main()