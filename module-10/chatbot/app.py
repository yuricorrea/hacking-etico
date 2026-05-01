"""
SafeBot — wrapper Flask para Ollama com system prompt restritivo.
Vulnerabilidades plantadas:
  - System prompt concatenado com user input sem qualquer separação privilegiada
  - Sem filtro de input/output (você adiciona no Exercício 10.2.8)
  - Sem rate limit
"""
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

OLLAMA = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
MODEL  = os.environ.get("MODEL", "llama3.2:1b")

with open("/app/system_prompt.txt", encoding="utf-8") as f:
    SYSTEM = f.read()


@app.route("/", methods=["GET"])
def index():
    return "SafeBot — POST /chat {message}"


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"error": "missing message"}), 400

    # Vulnerável: concatena system + user sem demarcação privilegiada
    payload = {
        "model": MODEL,
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 600},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": msg},
        ],
    }
    r = requests.post(f"{OLLAMA}/api/chat", json=payload, timeout=120)
    if r.status_code != 200:
        return jsonify({"error": "llm error", "detail": r.text}), 502
    j = r.json()
    reply = (j.get("message") or {}).get("content", "")
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
