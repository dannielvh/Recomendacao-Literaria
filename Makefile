# --- CONFIGURAÇÕES DO AMBIENTE ---
VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python3
PIP := $(VENV_DIR)/bin/pip
SYSTEM_PYTHON := python3

# --- DIRETÓRIOS ---
SRC_DIR := src
OUT_DIR := csv

# --- ARQUIVOS ---
SCRIPT_INTERFACE := $(SRC_DIR)/interface_usuario.py
SCRIPT_SETUP := $(SRC_DIR)/setup_env.py

# Outputs esperados (para limpeza)
OUTPUT_CLEAN_DATA := $(OUT_DIR)/goodreads_graph_base_clean.csv
OUTPUT_EDGES := $(OUT_DIR)/goodreads_graph_edges.csv
OUTPUT_USER := $(OUT_DIR)/usuario_subgrafo.csv
BUILD_DIR := ./build

# Metas
.PHONY: all run clean clean_relatorio install help setup_dirs

# Meta padrão (ao digitar 'make')
all: install setup_dirs run

# 1. Cria a pasta de saída (csv/) se não existir
setup_dirs:
	@mkdir -p $(OUT_DIR)

# 2. Cria o ambiente virtual (Sem pip inicialmente para evitar erros do Ubuntu)
$(VENV_DIR):
	@echo "[Config] A criar ambiente virtual Python..."
	@$(SYSTEM_PYTHON) -m venv $(VENV_DIR) --without-pip

# 3. Instala dependências (Chama o nosso script Python para resolver o pip)
install: $(VENV_DIR)
	@echo "⬇️  [Install] A configurar pip e dependências..."
	@# Roda o script de setup USANDO O PYTHON DO AMBIENTE VIRTUAL
	@$(PYTHON) $(SCRIPT_SETUP)
	@# Agora instala as libs
	@$(PIP) install pandas numpy > /dev/null 2>&1
	@echo "✅ Ambiente pronto."

# 4. Execução: Roda a Interface
run: install setup_dirs
	@echo "\n A iniciar Interface do Utilizador..."
	@# O PYTHONPATH garante que o Python encontre os módulos na pasta src
	@PYTHONPATH=$(SRC_DIR) $(PYTHON) $(SCRIPT_INTERFACE)

# Limpeza Geral
# --- LIMPEZA GERAL (NÃO APAGA RELATÓRIOS) ---
clean:
	@echo "A limpar ambiente, caches e dados brutos..."
	-@rm -vf $(OUTPUT_CLEAN_DATA) $(OUTPUT_EDGES) $(OUTPUT_USER)
	-@rm -rf $(BUILD_DIR) __pycache__ *.pyc */__pycache__ $(SRC_DIR)/__pycache__
	-@rm -rf $(VENV_DIR)
	-@rmdir $(OUT_DIR) 2>/dev/null || true
	@echo "Limpeza de sistema concluída (Relatórios .dat mantidos)."

# Limpeza Específica de Relatórios (.dat)
clean_relatorio:
	@echo "📄 A remover relatórios .dat..."
	-@rm -vf *.dat

help:
	@echo "Comandos disponíveis:"
	@echo "  make              : Instala tudo e abre o programa."
	@echo "  make clean        : Apaga venv e csv."
	@echo "  make clean_relatorio : Apaga apenas os relatórios de texto."