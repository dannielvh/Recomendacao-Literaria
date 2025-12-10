# Análise de Grafos e Estruturas de Árvores Literárias (Goodreads)

Este projeto implementa uma análise de dados complexa utilizando a base de dados GoodReads_100k_books. O objetivo é modelar subgêneros literários como vértices de um grafo e calcular a similaridade entre eles com base em duas estruturas internas: Popularidade (Nota Ponderada Bayesiana) e Conteúdo (Frequência de Palavras nas Sinopses).

A metodologia combina Árvores de Huffman para modelagem de dados e Algoritmos de Busca em Largura (BFS) para extração de métricas topológicas.

## Como Executar

**Pré-requisitos:**
- Python 3 instalado.
- Arquivo [GoodReads_100k_books.csv](https://www.kaggle.com/datasets/mdhamani/goodreads-books-100k) na pasta principal.
- Instalação e Execução Automática

### Comandos do Makefile
Para facilitar a compilação e execução, este projeto utiliza um `Makefile`.

| Comando | Função |
| :--- | :--- |
| `make` | Cria o ambiente virtual, instala as dependencias e executa o programa automaticamente. |
| `make clean` | Remover todos os ficheiros gerados (CSVs, caches) mas não remove os arquivos .dat .|
| `make clean_relatorio` | Remove apenas os relatórios de texto (.dat), mantendo os dados processados.|

## Estrutura do Projeto

### **src/ (Código Fonte)**
1- baseClean.py (Pré-processamento):
    - Lê a base bruta goodreads_books.csv.
    - Limpa textos (remove stopwords, pontuação).
    - Calcula o Weighted Rating (Nota Ponderada) usando a fórmula Bayesiana do IMDB.
    - Gera: csv/goodreads_graph_base_clean.csv.

2- vertice.py (Estrutura de Dados):
    - Define a classe HuffmanNode.
    - Constrói duas Árvores de Huffman para cada gênero:
        Árvore de Popularidade: Baseada no Weighted Rating.
        Árvore Semântica: Baseada na frequência de palavras da sinopse.

3- arestas.py (Grafo e Métricas):
    - Implementa o algoritmo BFS (Busca em Largura) para percorrer as árvores e calcular a Profundidade Média das Folhas.
    - Calcula a similaridade híbrida entre todos os pares de gêneros.
    - Gera: csv/goodreads_graph_edges.csv (Arestas do Grafo Completo).

4- interface_usuario.py (Gerente):
    - Interface interativa no terminal.
    - Permite escolher o gênero alvo, filtrar subgrafos e exportar dados para o Gephi.
    - Gera: csv/usuario_subgrafo.csv (Subgrafo filtrado para análise).

5- visualizador.py (Relatórios):
    - Gera ficheiros de texto detalhados (.dat) para um gênero específico.
    - Desenha as árvores hierarquicamente e lista o ranking de livros.

6- setup_env.py:
    - Script auxiliar para instalar o pip automaticamente em ambientes restritos.

