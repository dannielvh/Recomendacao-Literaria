import pandas as pd
import heapq
from collections import defaultdict
import os

# Definição do Arquivo de Entrada
INPUT_FILE = 'goodreads_graph_base_clean.csv'

# Classe para representar um Nó na Árvore de Huffman
# Um nó pode ser uma folha (um livro) ou um nó interno (junção de dois nós)
class HuffmanNode:
    """
    Representa um nó na Árvore de Huffman.
    O 'item' pode ser o ID do livro (para nós folha) ou None (para nós internos).
    A 'frequency' é o weighted_rating do livro.
    """
    def __init__(self, item, frequency, left=None, right=None):
        self.item = item            # book_id (se for folha) ou None (se for interno)
        self.frequency = frequency  # weighted_rating (peso)
        self.left = left
        self.right = right

    # É necessário definir como o objeto será comparado pelo 'heapq'.
    # O heapq sempre trata o menor elemento como prioridade.
    # Aqui, a comparação é baseada na frequência (weighted_rating).
    def __lt__(self, other):
        return self.frequency < other.frequency

def build_huffman_tree(book_list_with_weights):
    """
    Constrói a Árvore de Huffman a partir de uma lista de itens e seus pesos.
    No seu caso, o item é o book_id e o peso é o weighted_rating.

    Args:
        book_list_with_weights (list): Lista de tuplas (book_id, weighted_rating).

    Returns:
        HuffmanNode: A raiz da Árvore de Huffman construída.
    """
    if not book_list_with_weights:
        return None

    # Cria uma lista de Nodes e a transforma em um min-heap
    # (Fila de prioridade onde o nó com menor frequência está no topo)
    priority_queue = []
    for book_id, weight in book_list_with_weights:
        # Nota: O algoritmo de Huffman padrão comprime melhor itens de menor frequência.
        # Se você quer **priorizar a busca** pelos livros com MAIOR NOTA (weighted_rating),
        # você deve inverter o peso (ex: 1/weight) ou usar (max_rating - weight).
        # Vamos manter o padrão para a compressão, mas lembre-se dessa consideração para otimização da busca.
        # Por simplicidade, usaremos o weighted_rating como frequência, focando na **estrutura** da árvore.
        
        # Cria um nó folha para cada livro e adiciona ao heap
        heapq.heappush(priority_queue, HuffmanNode(book_id, weight))
        
    #     
    # Continua até que reste apenas um nó na fila (a raiz da árvore)
    while len(priority_queue) > 1:
        # Extrai os dois nós com a menor frequência
        left_node = heapq.heappop(priority_queue)
        right_node = heapq.heappop(priority_queue)

        # Cria um novo nó interno, cuja frequência é a soma dos seus filhos
        merged_frequency = left_node.frequency + right_node.frequency
        new_internal_node = HuffmanNode(
            item=None, 
            frequency=merged_frequency, 
            left=left_node, 
            right=right_node
        )

        # Adiciona o novo nó interno de volta ao heap
        heapq.heappush(priority_queue, new_internal_node)

    # O último nó restante é a raiz da Árvore de Huffman
    return priority_queue[0] if priority_queue else None

    # Lógica Principal para Construção do Grafo
def generate_graph_vertices_with_huffman():
    """
    Lê o dataset, agrupa por subgênero e constrói a Árvore de Huffman para cada um.
    """
    if not os.path.exists(INPUT_FILE):
        print(f"\nERRO: Arquivo '{INPUT_FILE}' não encontrado. Certifique-se de que ele está no diretório correto.")
        return None

    # 1. Carregamento e Agrupamento dos Dados
    print("Iniciando o carregamento e agrupamento dos dados...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except pd.errors.ParserError as e:
        print(f"Erro ao ler o CSV: {e}. Verifique o formato do arquivo.")
        return None

    # Agrupa por subgênero e extrai a lista de (book_id, weighted_rating)
    # A coluna 'subgenre_node' é o seu identificador de vértice.
    grouped_data = df.groupby('subgenre_node').apply(
        lambda x: list(zip(x['book_id'], x['weighted_rating']))
    ).to_dict()

    print(f"Processando {len(grouped_data)} subgêneros únicos...")

    # 2. Construção dos Vértices do Grafo (Subgênero + Árvore de Huffman)
    graph_vertices = {}

    for subgenre, book_list_with_weights in grouped_data.items():
        if subgenre: # Garante que o subgênero não é vazio
            # Constrói a Árvore de Huffman para todos os livros desse subgênero
            huffman_root = build_huffman_tree(book_list_with_weights)
            
            # Armazena o resultado no dicionário de vértices
            graph_vertices[subgenre] = {
                'subgenre_node': subgenre,
                'total_books': len(book_list_with_weights),
                'huffman_tree_root': huffman_root
            }
            
    print("\nEstrutura de Vértices do Grafo criada com sucesso!")
    return graph_vertices

# --- Execução do Script ---

# Gerar a estrutura
graph_vertices = generate_graph_vertices_with_huffman()

# Demonstração do Resultado
if graph_vertices:
    
    print("\n----------------- DEMONSTRAÇÃO DOS VÉRTICES (TOP 3) -----------------")
    # Para fins de demonstração, vamos pegar os primeiros 3 subgêneros
    for i, (subgenre, vertex_data) in enumerate(list(graph_vertices.items())[:3]):
        
        root = vertex_data['huffman_tree_root']
        root_freq = root.frequency if root else 0
        
        print(f"\nSubgênero (Vértice): **{subgenre}**")
        print(f"  > Total de Livros Associados: {vertex_data['total_books']}")
        print(f"  > Raiz da Árvore de Huffman (Objeto): {root}")
        print(f"  > Frequência Total da Raiz: {root_freq:.4f} (Soma de todos os weighted_ratings)")
        
        if root and root.left and root.right:
            # Exibe os pesos dos dois primeiros nós (a primeira junção)
            print(f"  > Peso do Ramo Esquerdo: {root.left.frequency:.4f}")
            print(f"  > Peso do Ramo Direito: {root.right.frequency:.4f}")