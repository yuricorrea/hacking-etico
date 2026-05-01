"""
RAG ingênuo da Acme — Flask + retrieval por overlap de palavras.
Vulnerabilidades plantadas:
  - /upload aberto a qualquer cliente (corpus poluível)
  - /ask aceita user_id no body sem autenticação (privilege confusion)
  - Documentos recuperados são concatenados ao prompt sem demarcação
  - Doc admin entrega flag se a palavra-passe correta aparecer no contexto
"""
import os
import re
import glob
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

OLLAMA = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
MODEL  = os.environ.get("MODEL", "llama3.2:1b")

CORPUS = []  # [{"id": str, "text": str, "admin_only": bool}]

def _tokens(s):
    return set(re.findall(r"[a-záéíóúâêôãõç0-9]{3,}", s.lower()))

def _load_initial():
    for path in sorted(glob.glob("/app/corpus/*.txt")):
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
        doc_id = os.path.basename(path).replace(".txt", "")
        CORPUS.append({
            "id": doc_id,
            "text": text,
            "admin_only": doc_id.startswith("99-"),
        })

_load_initial()


def retrieve(q, k=3, user_id=0):
    qt = _tokens(q)
    scored = []
    for d in CORPUS:
        if d["admin_only"] and user_id != 1:
            continue
        score = len(qt & _tokens(d["text"]))
        if score > 0:
            scored.append((score, d))
    scored.sort(key=lambda x: -x[0])
    return [d for _, d in scored[:k]]


@app.route("/", methods=["GET"])
def index():
    return "ACME RAG — POST /ask {q,user_id} | POST /upload {id,text}"


@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json(force=True, silent=True) or {}
    doc_id = data.get("id") or f"user-{len(CORPUS)}"
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "missing text"}), 400
    CORPUS.append({"id": doc_id, "text": text, "admin_only": False})
    return jsonify({"ok": True, "id": doc_id, "corpus_size": len(CORPUS)})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True, silent=True) or {}
    q = (data.get("q") or "").strip()
    user_id = int(data.get("user_id") or 0)
    if not q:
        return jsonify({"error": "missing q"}), 400

    docs = retrieve(q, k=3, user_id=user_id)
    context = "\n\n".join([f"[doc:{d['id']}]\n{d['text']}" for d in docs]) or "(nenhum)"

    # Prompt clássico de RAG — vulnerável a indirect injection
    system = (
        "Você é o assistente da Acme. Responda APENAS com base nos documentos fornecidos.\n"
        "Se a resposta não estiver nos documentos, diga 'não sei'."
    )
    prompt_user = f"DOCUMENTOS:\n{context}\n\nPERGUNTA: {q}"

    r = requests.post(f"{OLLAMA}/api/chat", json={
        "model": MODEL,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 400},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt_user},
        ],
    }, timeout=120)
    if r.status_code != 200:
        return jsonify({"error": "llm error", "detail": r.text}), 502
    answer = (r.json().get("message") or {}).get("content", "")
    return jsonify({
        "answer": answer,
        "retrieved": [d["id"] for d in docs],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
