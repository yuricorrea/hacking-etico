# Hacking Ético Masterclass: Do Básico ao Avançado com Labs em Docker

> **Curso 100% prático, hands-on, com laboratórios reproduzíveis em Docker.**
> Autor: Yuri Correa
> Versão: 1.0 — 2026
> Idioma: Português (Brasil)

---

## Aviso Legal e Ético

Este curso é exclusivamente educacional. Todos os ataques demonstrados devem ser executados **apenas** em ambientes controlados (seus próprios contêineres Docker, máquinas virtuais ou plataformas com autorização explícita como HackTheBox, TryHackMe, PortSwigger Web Security Academy, etc.).

Atacar sistemas sem autorização é crime na maioria das jurisdições (no Brasil, Lei 12.737/2012 — "Lei Carolina Dieckmann" — e Marco Civil da Internet). Você é o único responsável pelo uso que fizer deste conteúdo.

---

# 📚 ÍNDICE COMPLETO DO CURSO

### Introdução
- Como o curso funciona
- Pré-requisitos e perfil do aluno
- Setup global do ambiente de laboratório
- Metodologia: Cyber Kill Chain + MITRE ATT&CK
- Como abordar os desafios CTF e os write-ups

### [Módulo 0 — Revisão Prática dos Fundamentos](module-0/README.md)
- 0.1 Setup do ambiente Docker para o curso inteiro
- 0.2 Revisão prática de Linux (privilégios, processos, networking)
- 0.3 Revisão prática de redes (TCP/IP, DNS, HTTP, TLS)
- 0.4 Revisão prática de Bash + Python para ofensiva
- 0.5 Revisão prática de criptografia (hashes, simétrica, assimétrica)
- 0.6 Mini-CTF de aquecimento

### Módulo 1 — Network Hacking & Pivoting
- Reconhecimento ativo/passivo, scanning avançado com Nmap NSE
- ARP spoofing, DNS spoofing, NTLM Relay, mitm6
- Tunneling: SSH, Chisel, Ligolo-ng, Sliver
- Pivoting multi-hop e port forwarding dinâmico

### Módulo 2 — Web Application Hacking
- OWASP Top 10 (2021) completo com labs próprios
- API Security (REST, GraphQL, JWT)
- SSTI, SSRF, Prototype Pollution, Race Conditions
- Bypass de WAF e técnicas modernas (HTTP smuggling, cache deception)

### Módulo 3 — Wireless & Mobile Hacking
- Wi-Fi WPA2/WPA3, ataques a Enterprise (EAP), Evil Twin
- Bluetooth/BLE sniffing e replay
- Android: APK reverse, Frida, Objection
- iOS: análise estática + dynamic instrumentation

### Módulo 4 — Cloud Security
- AWS: IAM privilege escalation, S3, Lambda, Metadata Service
- Azure: AAD, Managed Identities, Storage
- GCP: Service Accounts, GKE
- Container Security: Docker escape, Kubernetes attacks

### Módulo 5 — Social Engineering & OSINT
- OSINT digital e físico (Maltego, SpiderFoot, theHarvester)
- Phishing avançado com GoPhish + Evilginx2
- Vishing, pretexting e ataques físicos (badge clone, USB drops)

### Módulo 6 — Reverse Engineering & Malware Analysis
- Análise estática e dinâmica (Ghidra, Radare2, x64dbg)
- Unpacking, anti-debug bypass
- Malware Triage, YARA rules
- Rootkits e Command & Control (C2) com Mythic/Sliver

### Módulo 7 — Exploit Development
- Buffer overflow stack-based (Linux/Windows)
- ASLR/DEP/Stack Canaries bypass
- ROP, JOP, SROP
- Heap exploitation (House of Force, tcache poisoning)
- Use-After-Free e fuzzing com AFL++

### Módulo 8 — IoT & Hardware Hacking
- Firmware extraction e análise (binwalk, firmadyne)
- UART, JTAG, SPI flash dumping
- Radio (SDR) básico — GQRX, GNU Radio
- Side-channel attacks introdutório

### Módulo 9 — Digital Forensics & Incident Response
- Memory forensics (Volatility 3)
- Disk forensics (Autopsy, Sleuthkit)
- Log analysis e timeline
- EDR evasion + Threat Hunting com Sysmon/Sigma

### Módulo 10 — AI/LLM Security & Red Teaming 🔥 *Nova área*
- Prompt Injection direto e indireto
- Jailbreaking de LLMs (DAN, role-play, encoding)
- Prompt Leaking + Data Exfiltration
- Chain-of-Thought manipulation
- Tool/Agent hijacking em agentes autônomos
- RAG poisoning
- Model extraction e Adversarial attacks
- Defesas: guardrails, input/output filtering, isolamento

### Capstone — Projeto Final Red Team
- Cenário corporativo fictício multi-camada
- Stack completo em Docker Compose (web, AD-like, cloud, AI)
- Relatório profissional padrão OSCP/PTES

---

# 🎬 INTRODUÇÃO DO CURSO

## Bem-vindo(a) ao Hacking Ético Masterclass

Você já sabe o que é uma porta TCP, sabe escrever um loop em Python e entende a diferença entre simétrico e assimétrico. Ótimo — significa que **podemos pular a parte chata**. Este curso foi desenhado para tirar você do nível "intermediário com fundamentos" e levá-lo a um perfil **Red Team / Pentester Sênior**, capaz de atuar em engajamentos reais cobrindo desde rede até aplicações modernas com IA.

### Filosofia: Aprender Fazendo

A regra de ouro do curso: **toda teoria existe para suportar um lab**. Você não vai ler 30 páginas sobre SSTI antes de explorar uma — você vai *primeiro* quebrar uma aplicação Flask vulnerável dentro de um contêiner, e *depois* a gente formaliza o que aconteceu. Funciona melhor assim porque ataque é uma habilidade motora, não enciclopédica.

### Como cada módulo é estruturado

Cada módulo segue rigorosamente o mesmo padrão para que você crie um ritmo de estudo:

| Seção | O que você encontra |
|---|---|
| 🎯 **Objetivos de Aprendizado** | Lista clara do que você saberá fazer ao final |
| 📖 **Teoria Mínima** | Apenas o "por quê" — não enche linguiça |
| 🐳 **Lab Setup** | `docker-compose.yml` pronto + comandos para subir |
| 🛠️ **Exercícios Práticos** | 4–6 exercícios progressivos com comandos |
| 🚩 **Desafios CTF** | 1–2 desafios com flag no formato `flag{...}` |
| 🔓 **Write-up** | Solução completa **(spoiler — só veja depois!)** |
| 🧰 **Toolbox** | Ferramentas + versões exatas testadas |
| 🐛 **Troubleshooting** | Erros comuns e como resolver |
| 📚 **Recursos Extras** | Papers, vídeos e leituras aprofundadas |

### Metodologia adotada

Vamos seguir uma fusão das duas frameworks mais usadas na indústria:

- **Cyber Kill Chain (Lockheed Martin)** — boa para enxergar o macro de um ataque (Recon → Weaponization → Delivery → Exploitation → Installation → C2 → Actions on Objectives).
- **MITRE ATT&CK** — granular, mapeia táticas e técnicas reais que vamos referenciar (ex.: T1190 — Exploit Public-Facing Application).

Sempre que possível, cada lab é taggeado com seu(s) ID(s) ATT&CK correspondente(s). Isso te ajuda a falar a língua de blue team também — algo que difere o pentester júnior do sênior.

### Como abordar os desafios CTF

1. **Tente sozinho por pelo menos 30 minutos** antes de espiar dicas.
2. **Anote tudo** num caderno de campo — comandos, hipóteses descartadas, screenshots.
3. **Só leia o write-up depois de capturar a flag OU de baterem 2 horas tentando.** O valor pedagógico está no atrito.
4. **Reescreva o ataque do zero** uma segunda vez sem consultar o write-up. É aí que solidifica.

### Carga horária sugerida

Aproximadamente **24 semanas** (6 meses) com dedicação de 10–15h semanais. Você pode acelerar, mas perderá o efeito de "deixar o conhecimento sedimentar entre módulos". Vai por mim.

### Pré-requisitos confirmados (você já deve ter)

- Linux nível usuário avançado (terminal, permissões, processos, systemd)
- Redes nível CCNA básico (modelo OSI, TCP/IP, DNS, HTTP)
- Programação básica em Python e Bash (loops, funções, manipulação de arquivos)
- Criptografia conceitual (hashes, simétrica vs assimétrica, TLS handshake)
- Familiaridade mínima com Docker (rodar um contêiner, ler um Dockerfile)

Se algum item acima soou estranho, **revise antes** ou faça o Módulo 0 com calma extra — ele cobre uma síntese prática.

### Setup global do ambiente

O curso inteiro assume que você tem:

- **Sistema operacional host:** Linux (Ubuntu 22.04+ ou Debian 12 recomendado), macOS (com Docker Desktop) ou Windows com WSL2 + Docker Desktop
- **Docker Engine:** ≥ 24.0
- **Docker Compose:** v2 (plugin `docker compose`, não o legado `docker-compose`)
- **RAM:** mínimo 8 GB, recomendado 16 GB
- **Disco:** ≥ 80 GB livres (imagens são grandes — Kali sozinha tem ~5 GB)
- **CPU:** com suporte a virtualização (VT-x/AMD-V) habilitado

Para módulos específicos (Wireless, Hardware) você precisará de **hardware adicional**: adaptador Wi-Fi com modo monitor (Alfa AWUS036ACH), Bus Pirate / Shikra para JTAG, e SDR USB (RTL-SDR ~R$200). Discutiremos no início de cada módulo.

Pronto? Bora botar a mão na massa.

---

# Módulos do curso

### [Módulo 0 — Fundamentos](module-0/README.md)