"""
ACME Greeter — Flask app intencionalmente vulnerável.
Vulnerabilidades plantadas:
  - SSTI em /hello (render_template_string com input concatenado)
  - SSRF em /fetch (filtro fraco de localhost)
  - "Internal" admin em /internal/admin que confia em Host loopback
"""
from flask import Flask, request, render_template_string, abort
import requests
import urllib.parse
import re

app = Flask(__name__)


@app.route("/")
def index():
    return (
        "<h1>ACME Greeter</h1>"
        "<p>Try <code>/hello?name=World</code></p>"
        "<p>Or proxy a URL via <code>/fetch?url=https://example.com</code></p>"
    )


@app.route("/hello")
def hello():
    """SSTI clássico: input concatenado no template."""
    name = request.args.get("name", "stranger")
    template = "<h2>Hello " + name + "!</h2>"
    return render_template_string(template)


# Filtro propositalmente fraco — bypass via decimal, IPv6 mapped, 0.0.0.0, etc.
BLOCKED = re.compile(r"(127\.0\.0\.1|localhost|169\.254)", re.IGNORECASE)


@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")
    if not url:
        abort(400, "missing url")
    if BLOCKED.search(url):
        abort(403, "blocked by security policy")
    try:
        # SSRF: segue redirects, sem timeout adequado, aceita scheme arbitrário
        r = requests.get(url, timeout=5, allow_redirects=True)
        return (r.text, r.status_code, {"X-Proxied": "1"})
    except Exception as e:
        return (f"fetch error: {e}", 502)


@app.route("/internal/admin")
def internal_admin():
    """Endpoint que só deveria responder para chamadas locais (mas SSRF passa)."""
    # Confia no Host header — anti-pattern proposital
    host = request.host.split(":")[0]
    if host not in ("localhost", "127.0.0.1", "0.0.0.0", "ssti-app"):
        # Mesmo assim aceita se for IP loopback (vulnerabilidade): observa o "or"
        pass
    return "<h2>Internal Admin Console</h2><p>Token: ADM-DEV-001</p>"


if __name__ == "__main__":
    # debug=False para evitar werkzeug debugger pin
    app.run(host="0.0.0.0", port=5000, debug=False)
