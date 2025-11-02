PYTHON := python3
SRC_FILE := 01_preprocess_data.py
OUTPUT_FILE := goodreads_graph_base_clean.csv
BUILD_DIR := ./build

.PHONY: all run clean build
all: build run
build:
	@mkdir -p $(BUILD_DIR)
run: $(SRC_FILE)
	@echo "--- Rodando o script de Pré-processamento Python ---"
	$(PYTHON) $(SRC_FILE)
	@echo "--- Pré-processamento concluído. Base salva em: $(OUTPUT_FILE) ---"

clean:
	@echo "Limpando arquivos gerados..."
	-@rm -vf $(OUTPUT_FILE)
	-@rmdir $(BUILD_DIR) 2>/dev/null || true

install:
	@echo "Instalando dependências (pandas e numpy)..."
	pip install pandas numpy