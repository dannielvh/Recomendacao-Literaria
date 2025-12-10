import pandas as pd
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import baseClean 
    import arestas
    import visualizador
except ImportError as e:
    print(f"ERRO CRÍTICO DE IMPORTAÇÃO: {e}")
    sys.exit(1)

EDGES_FILE = 'csv/goodreads_graph_edges.csv'
USER_EXPORT_FILE = 'csv/usuario_subgrafo.csv'

def run_full_pipeline(target_genre):
    
    # Pré-processamento
    print(f"Limpando dados para: {target_genre}...")
    if not baseClean.process_data(target_genre): return False

    # Grafo
    try:
        print(f"Gerando Grafo Híbrido...")
        arestas.main() 
    except Exception as e:
        print(f"Erro no grafo: {e}")
        return False
    return True

def offer_menu_from_subgraph():
    if not os.path.exists(USER_EXPORT_FILE): return

    try:
        df_sub = pd.read_csv(USER_EXPORT_FILE)
        if df_sub.empty: return

        sources = df_sub['Source'].unique()
        targets = df_sub['Target'].unique()
        unique_genres = sorted(np.unique(np.concatenate((sources, targets))))
        
        while True:
            print("\n" + "="*60)
            print(f"   MENU DE INSPEÇÃO (Vértices no Subgrafo)")
            print("="*60)
            for i, genre in enumerate(unique_genres):
                print(f"[{i+1}] {genre}")
                
            print("\nEscolha um número para ver o relatório ou 'voltar':")
            choice = input("Opção: ").strip().lower()
            
            if choice in ['voltar', 'sair']: break
                
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(unique_genres):
                    target = unique_genres[idx]
                    visualizador.generate_report(target)
                    input("\n(ENTER para continuar...)")
                else: print("Número inválido.")
            except ValueError: print("Entrada inválida.")
                
    except Exception as e:
        print(f"Erro no menu: {e}")

def export_for_gephi(selected_subgenres, df_edges):
    mask = (df_edges['Source'].isin(selected_subgenres)) | (df_edges['Target'].isin(selected_subgenres))
    subgraph = df_edges[mask].copy()
    
    if subgraph.empty:
        print("Aviso: Vértices isolados (sem arestas no subgrafo).")
        print("Gerando relatórios individuais...")
        for g in selected_subgenres: visualizador.generate_report(g)
    else:
        subgraph.to_csv(USER_EXPORT_FILE, index=False)
        print(f"Arquivo '{USER_EXPORT_FILE}' gerado.")
        offer_menu_from_subgraph()

def main():
    print("Analisador de Grafos Literários")
    target = input("Gênero Principal (ex: Fantasy, Romance, Gothic): ").strip() or 'Gothic'
    
    if not run_full_pipeline(target): return

    if not os.path.exists(EDGES_FILE):
        print("Arquivo de arestas não gerado.")
        return
        
    df_edges = pd.read_csv(EDGES_FILE)
    all_nodes = sorted(list(set(df_edges['Source']).union(set(df_edges['Target']))))
    
    if not all_nodes:
        print("Grafo vazio.")
        return

    while True:
        print("\nSubgêneros disponíveis:")
        for i, node in enumerate(all_nodes):
            print(f"[{i+1}] {node}")
            
        sel = input("\nEscolha números (ex: 1, 3), 'tudo' ou 'sair': ").strip().lower()
        if sel == 'sair': break
        
        selected = []
        if sel == 'tudo': selected = all_nodes
        else:
            try:
                idx_list = [int(x)-1 for x in sel.split(',') if x.strip().isdigit()]
                selected = [all_nodes[i] for i in idx_list if 0 <= i < len(all_nodes)]
            except: continue
        
        if selected:
            export_for_gephi(selected, df_edges)
            break

if __name__ == "__main__":
    main()