import pandas as pd
import sys
import os
import numpy as np
from collections import deque, Counter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import vertice
    import arestas
except ImportError as e:
    print(f"ERRO CRÍTICO: Não foi possível importar 'vertice.py' ou 'arestas.py'.")
    print(f"Detalhe: {e}")
    sys.exit(1)

INPUT_FILE = 'csv/goodreads_graph_base_clean.csv'
EDGES_FILE = 'csv/goodreads_graph_edges.csv'
SUBGRAPH_FILE = 'csv/usuario_subgrafo.csv' 

def write_tree_structure(node, file_obj, level=0, prefix="Raiz: ", is_word_tree=False):
     if node is not None:
        indent = "    " * level
        #folha
        if node.item is not None:
            if is_word_tree:
                file_obj.write(f"{indent}├── 🔤 '{node.item}' [Freq: {node.frequency}]\n")
            else:
                # Item é um dicionário de livro
                item_info = node.item
                if isinstance(item_info, dict):
                    title = str(item_info.get('title', 'N/A'))[:40] # Trunca titulo longo
                    author = item_info.get('author', 'N/A')
                    file_obj.write(f"{indent}├── 📖 {title}.. ({author}) [Nota: {node.frequency:.2f}]\n")
        
        # no interno
        else:
            file_obj.write(f"{indent}{prefix} (Soma: {node.frequency:.2f})\n")
            if node.left: write_tree_structure(node.left, file_obj, level + 1, "├── Esq:", is_word_tree)
            if node.right: write_tree_structure(node.right, file_obj, level + 1, "└── Dir:", is_word_tree)

def generate_report(target_genre):
    print(f"\nRELATÓRIO COMPLETO para: '{target_genre}'")
    
    if not os.path.exists(INPUT_FILE):
        print(f"ERRO: Base de dados '{INPUT_FILE}' não encontrada.")
        return

    # Carrega e Filtra Dados
    try:
        df = pd.read_csv(INPUT_FILE)
        # Garante que cleaned_desc é string
        df['cleaned_desc'] = df['cleaned_desc'].astype(str)
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        return
    
    df_genre = df[df['subgenre_node'] == target_genre].copy()
    
    if df_genre.empty:
        print(f"ERRO: Gênero '{target_genre}' não encontrado.")
        return
    
    # CONSTRUÇÃO DA ÁRVORE 1: POPULARIDADE (Bayesiana)
    rating_data = []
    for _, row in df_genre.iterrows():
        meta = {'title': row['title'], 'author': row['author'] if 'author' in row else 'N/A'}
        rating_data.append((meta, row['weighted_rating']))
    
    rating_root = vertice.build_huffman_tree(rating_data)
    rating_metric = arestas.bfs_get_avg_depth(rating_root)

    # CONSTRUÇÃO DA ÁRVORE 2: CONTEÚDO (Sinopse) 
    print("   -> A construir Árvore de Sinopses...")
    full_text = " ".join(df_genre['cleaned_desc'])
    word_counts = Counter(full_text.split())
    # Limitamos a visualização às top 100 palavras para o relatório não ficar infinito
    word_list = word_counts.most_common(100) 
    word_root = vertice.build_huffman_tree(word_list)
    word_metric = arestas.bfs_get_avg_depth(word_root)

    # RANKING DE SIMILARIDADE
    similar_genres = []
    if os.path.exists(EDGES_FILE):
        try:
            df_edges = pd.read_csv(EDGES_FILE)
            mask = (df_edges['Source'] == target_genre) | (df_edges['Target'] == target_genre)
            df_neighbors = df_edges[mask].copy()
            for _, row in df_neighbors.iterrows():
                neighbor = row['Target'] if row['Source'] == target_genre else row['Source']
                similar_genres.append((neighbor, row['Weight']))
            similar_genres.sort(key=lambda x: x[1], reverse=True)
        except: pass

    # EXPORTAÇÃO DO RELATÓRIO
    safe_name = "".join([c if c.isalnum() else "_" for c in target_genre])
    filename = f"relatorio_{safe_name}.dat"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"RELATÓRIO DE ANÁLISE: {target_genre.upper()}\n")
            f.write(f"Total de Obras: {len(df_genre)}\n")
            f.write("="*80 + "\n\n")
            
            # SEÇÃO 1: MÉTRICAS BFS (Topo do Relatório)
            f.write(f"MÉTRICAS ESTRUTURAIS (Calculadas via BFS)\n")
            f.write(f"Estas métricas definem a posição do gênero no grafo.\n")
            f.write(f" - Profundidade Média (Popularidade): {rating_metric:.4f}\n")
            f.write(f" - Profundidade Média (Vocabulário):  {word_metric:.4f}\n")
            f.write("-" * 80 + "\n\n")

            # SEÇÃO 2: RANKING DE SIMILARIDADE
            f.write(f"RANKING DE SIMILARIDADE (Gêneros Vizinhos no Grafo)\n")
            f.write("-" * 80 + "\n")
            if not similar_genres:
                f.write("   (Sem conexões fortes)\n")
            else:
                for i, (genre, weight) in enumerate(similar_genres[:15], 1): 
                    f.write(f"{i:<3} | {weight*100:.1f}% | {genre}\n")
            f.write("\n" + "="*80 + "\n\n")

            # SEÇÃO 3: RANKING DE LIVROS
            f.write(" RANKING DE LIVROS (Melhores Avaliados - Bayesiano)\n")
            f.write(f"{'RANK':<5} | {'NOTA':<6} | {'TÍTULO'}\n")
            f.write("-" * 80 + "\n")
            
            df_rank = df_genre.sort_values(by='weighted_rating', ascending=False)
            for i, (_, row) in enumerate(df_rank.iterrows(), 1):
                title = str(row['title'])
                f.write(f"{i:<5} | {row['weighted_rating']:.2f}   | {title} ({row.get('author','N/A')})\n")
            f.write("\n" + "="*80 + "\n\n")

            # SEÇÃO 4: ÁRVORES VISUAIS
            f.write(f"ESTRUTURA DAS ÁRVORES DE HUFFMAN\n")
            f.write("-" * 80 + "\n")
            f.write(">>> ÁRVORE DE POPULARIDADE:\n")
            write_tree_structure(rating_root, f, is_word_tree=False)
            f.write("\n>>> ÁRVORE SEMÂNTICA (SINOPSES):\n")
            write_tree_structure(word_root, f, is_word_tree=True)
                
        print(f" RELATÓRIO SALVO: {filename}")
        
    except Exception as e:
        print(f"Erro ao salvar: {e}")

def interactive_menu():
    print("\nGerar relatorio")
    
    if os.path.exists(SUBGRAPH_FILE):
        try:
            df_sub = pd.read_csv(SUBGRAPH_FILE)
            if not df_sub.empty:
                sources = df_sub['Source'].unique()
                targets = df_sub['Target'].unique()
                nodes = sorted(np.unique(np.concatenate((sources, targets))))
                
                print(f"Gêneros no grafo recente ({SUBGRAPH_FILE}):")
                for i, node in enumerate(nodes):
                    print(f"[{i+1}] {node}")
                
                print("\nEscolha um número ou digite o nome:")
                choice = input(">> ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(nodes):
                        generate_report(nodes[idx])
                        return
                
                if choice:
                    if choice in nodes:
                        generate_report(choice)
                    else:
                        print(f"Aviso: '{choice}' não está no subgrafo atual, mas vou tentar buscar na base completa.")
                        generate_report(choice)
                    return
        except Exception as e:
            print(f"Aviso ao ler subgrafo: {e}")

    print("\n Digite o nome do gênero:")
    g = input(">> ").strip()
    if g: generate_report(g)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_report(" ".join(sys.argv[1:]))
    else:
        interactive_menu()