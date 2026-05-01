#!/bin/sh
# Script informativo — a lógica real está inlined no docker-compose.yml.
# Mantido aqui caso você prefira chamar como entrypoint:
#   entrypoint: ["/init.sh"]
set -eu

OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434}"
MODEL="${MODEL:-llama3.2:1b}"

echo "[init] aguardando Ollama em $OLLAMA_HOST ..."
until curl -sf "$OLLAMA_HOST/api/tags" >/dev/null; do
  sleep 2
done

echo "[init] baixando modelo $MODEL ..."
ollama pull "$MODEL"
echo "[init] model ready"
