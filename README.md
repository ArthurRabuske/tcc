# TCC — Benchmark de Controladores SDN

Projeto de benchmark baseado na metodologia do **RFC 8456** (*Benchmarking Methodology for Software-Defined Networking (SDN) Controller Performance*). O código mede desempenho de controladores SDN (ONOS, OpenDaylight, Floodlight) em cenários como descoberta de topologia, API northbound e carga de trabalho em redes emuladas com **Mininet**.

---

## Índice

1. [Visão geral da arquitetura](#visão-geral-da-arquitetura)
2. [Pré-requisitos](#pré-requisitos)
3. [Configuração das VMs](#configuração-das-vms)
4. [Instalação na VM Mininet](#instalação-na-vm-mininet)
5. [Verificação de conectividade](#verificação-de-conectividade)
6. [Como executar os benchmarks](#como-executar-os-benchmarks)
7. [Onde ficam os resultados](#onde-ficam-os-resultados)
8. [Referência de arquivos](#referência-de-arquivos)
9. [Solução de problemas](#solução-de-problemas)

---

## Visão geral da arquitetura

O projeto foi pensado para rodar em **duas máquinas virtuais**:

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│      VM ONOS            │         │       VM Mininet             │
│                         │         │                              │
│  • ONOS (Java)          │◄─6653───│  • Mininet (topologias)      │
│  • Porta OpenFlow 6653  │ OpenFlow│  • Scripts de benchmark      │
│  • REST API 8181        │◄─8181───│  • Captura de pacotes (Scapy)│
│  • SSH (monitoramento)  │◄─22─────│  • ControllerMonitor (SSH)   │
└─────────────────────────┘         └──────────────────────────────┘
```

| VM | Papel |
|---|---|
| **VM ONOS** | Executa o controlador SDN. Recebe conexões OpenFlow dos switches e responde à API REST. |
| **VM Mininet** | Executa **todos os scripts deste repositório**. Cria topologias, gera tráfego, consulta a API REST e captura pacotes OpenFlow. |

> **Importante:** os benchmarks são executados **na VM Mininet**, apontando para o IP da VM ONOS com os parâmetros `-ip` e `-r`.

---

## Pré-requisitos

### VM ONOS

- ONOS instalado e em execução
- Portas liberadas no firewall:
  - **6653** — OpenFlow
  - **8181** — REST API
  - **22** — SSH (opcional, para monitoramento de CPU/memória)
- Credenciais REST padrão do ONOS: usuário `onos`, senha `rocks`
- Apps recomendados ativos no ONOS: OpenFlow, LLDP (descoberta de links), Host Location Provider

### VM Mininet

- Ubuntu/Debian com Mininet instalado
- Python 3
- Acesso de rede à VM ONOS (ping + portas 6653 e 8181)
- Execução com **`sudo`** (Mininet e captura de pacotes exigem privilégios de root)

---

## Configuração das VMs

### 1. VM ONOS — iniciar o controlador

Exemplo com serviço ONOS:

```bash
# Na VM ONOS
onos-service start
# ou, se usar Docker/imagem própria, siga o procedimento da sua instalação
```

Confirme que a API responde (na própria VM ONOS ou na Mininet):

```bash
curl -u onos:rocks http://<IP_ONOS>:8181/onos/v1/devices
```

### 2. VM Mininet — editar configurações do projeto

Antes de rodar os testes, ajuste estes arquivos:

#### `global_variables.py` — monitoramento remoto de CPU/memória

O script `topology_discovery.py` usa SSH para medir CPU e memória do processo Java do controlador na VM ONOS:

```python
controller_monitor = ControllerMonitor(
    'java',              # nome do processo a monitorar
    '<IP_VM_ONOS>',      # IP da VM ONOS
    '<usuario_ssh>',     # usuário SSH
    '<senha_ssh>'        # senha SSH
)
```

Substitua os valores pelo IP e credenciais **da sua VM ONOS**. Se não quiser monitorar CPU/memória, o benchmark ainda roda, mas esses campos no CSV ficarão vazios ou podem gerar erro de conexão SSH.

#### `REST_tests/onos.py` — teste rápido de API

Altere o IP para o da sua VM ONOS:

```python
CONTROLLER_IP = '<IP_VM_ONOS>'
REST_PORT = '8181'
```

---

## Instalação na VM Mininet

```bash
# Dependências do sistema (Ubuntu/Debian)
sudo apt update
sudo apt install -y mininet openvswitch-switch python3-pip

# Dependências Python (na pasta do projeto)
cd tcc
sudo pip3 install requests scapy paramiko psutil mininet

# Crie a pasta de saída (se não existir)
mkdir -p output
```

> Rode sempre os scripts **a partir da pasta `tcc/`**, pois eles leem e gravam arquivos em caminhos relativos (`output/`, `json/`).

---

## Verificação de conectividade

Execute **na VM Mininet**, na ordem abaixo.

### Passo 1 — Rede

```bash
ping <IP_VM_ONOS>
```

### Passo 2 — REST API do ONOS

Edite o IP em `REST_tests/onos.py` e execute:

```bash
cd tcc
python3 REST_tests/onos.py
```

Saída esperada (valores variam):

```
Topo = ... | Links = ... | Hosts = ...
```

### Passo 3 — OpenFlow (teste manual com Mininet)

```bash
sudo mn --controller=remote,ip=<IP_VM_ONOS>,port=6653 --switch ovsk,protocols=OpenFlow13 --test pingall
```

Se `pingall` funcionar, a VM Mininet alcança o ONOS via OpenFlow.

### Passo 4 — Interface para captura de pacotes

Os scripts de descoberta de topologia capturam tráfego OpenFlow com Scapy. Use a interface de rede que encaminha tráfego para a VM ONOS (geralmente `eth0`, `ens33` ou similar):

```bash
ip route get <IP_VM_ONOS>
# Anote o nome da interface (ex.: eth0)
```

Use esse nome no parâmetro `-if` dos benchmarks.

---

## Como executar os benchmarks

Todos os comandos abaixo rodam **na VM Mininet**, dentro da pasta `tcc/`, com **`sudo`**.

Substitua `<IP_ONOS>` pelo IP real da VM ONOS e `<IFACE>` pela interface de rede correta (ex.: `eth0`).

---

### Benchmark 1 — Descoberta de topologia (experimento completo)

**Arquivo principal:** `script_topology.py`

Este é o **ponto de entrada recomendado** para o benchmark de descoberta de topologia. Ele:

1. Para cada tamanho de topologia, executa várias tentativas (`-tr`)
2. Em paralelo, roda `topology_discovery.py` (mede tempo via OpenFlow + REST)
3. Roda `workload.py` (sobe a topologia no Mininet conectada ao ONOS remoto)
4. Gera CSV e relatório em `output/`
5. Ao final, tenta enviar e-mail com os resultados (pode falhar se `email_sender.py` não estiver configurado — veja [Solução de problemas](#solução-de-problemas))

#### Exemplo — topologia mesh com ONOS

```bash
sudo python3 script_topology.py \
  -ip <IP_ONOS> \
  -n onos \
  -r 8181 \
  -t mesh \
  --num-switches 10 \
  -if <IFACE> \
  -q 3 \
  -c 50 \
  -s 5 \
  -tr 10 \
  -d 5 \
  -max 50
```

#### Exemplo — topologia 3-tier

```bash
sudo python3 script_topology.py \
  -ip <IP_ONOS> \
  -n onos \
  -t 3-tier \
  --num-cores 2 \
  --num-aggs 4 \
  --num-access 8 \
  -if <IFACE> \
  -q 3 \
  -c 50 \
  -s 2 \
  -tr 5 \
  -d 2 \
  -max 30
```

#### Exemplo — leaf-spine

```bash
sudo python3 script_topology.py \
  -ip <IP_ONOS> \
  -n onos \
  -t leaf-spine \
  --num-leafs 4 \
  --num-spines 2 \
  -if <IFACE> \
  -q 3 \
  -c 50 \
  -s 2 \
  -tr 5 \
  -d 2 \
  -max 20
```

#### Parâmetros principais de `script_topology.py`

| Parâmetro | Descrição |
|---|---|
| `-ip` | IP da VM ONOS |
| `-n` | Nome do controlador: `onos`, `odl` ou `floodlight` |
| `-r` | Porta REST (ONOS: `8181`) |
| `-t` | Tipo de topologia: `mesh`, `3-tier`, `leaf-spine`, `star` |
| `-if` | Interface de rede para captura OpenFlow (Scapy) |
| `-q` | Intervalo (s) entre consultas REST à topologia |
| `-c` | Falhas consecutivas antes de desistir (switches) |
| `-s` | Tamanho inicial da topologia |
| `-tr` | Número de repetições (trials) por tamanho |
| `-d` | Incremento do tamanho a cada rodada |
| `-max` | Tamanho máximo agregado da topologia |
| `-k` / `--no_links` | Medir só switches, sem esperar descoberta de links |

---

### Benchmark 2 — API Northbound (tempo de resposta e throughput)

**Arquivo principal:** `northbound_api.py`

Sobe uma topologia fixa no Mininet e mede:

- **Tempo médio de resposta** da API REST (`-rt`)
- **Throughput máximo** de requisições concorrentes (`-tp`)

```bash
sudo python3 northbound_api.py \
  -ip <IP_ONOS> \
  -n onos \
  -r 8181 \
  -t mesh \
  -s 10 \
  -q 3 \
  -nt 100 \
  -rt \
  -tp \
  -mr 100 \
  -d 30 \
  -i 10
```

| Parâmetro | Descrição |
|---|---|
| `-rt` | Ativa medição de tempo de resposta |
| `-tp` | Ativa medição de throughput |
| `-s` | Tamanho da topologia (parâmetro interno) |
| `-nt` | Número de testes de tempo de resposta |
| `-mr` | Máximo de requisições concorrentes |
| `-d` | Duração (s) de cada etapa de throughput |
| `-i` | Incremento de requisições concorrentes por etapa |

---

### Benchmark 3 — Componentes individuais

Use estes scripts para testes isolados ou depuração.

#### `topology_discovery.py` — descoberta de topologia (uma execução)

Mede o tempo entre o primeiro `Packet-Out` e a confirmação da topologia via REST. **Requer** que a topologia já esteja sendo criada (por `workload.py` em outro terminal ou antes).

```bash
# Terminal 1 — sobe a topologia
sudo python3 workload.py -ip <IP_ONOS> -n onos -t mesh --num-switches 10

# Terminal 2 — mede descoberta (ajuste -l ao número de switches)
sudo python3 topology_discovery.py \
  -ip <IP_ONOS> -n onos -r 8181 \
  -l 10 -q 3 -c 50 -if <IFACE>
```

Resultado em: `output/topo_disc_onos.txt`

#### `workload.py` — gerador de carga / topologia Mininet

Cria a rede no Mininet e conecta ao controlador remoto. Modos extras:

```bash
# Só topologia (modo interativo Mininet CLI)
sudo python3 workload.py -ip <IP_ONOS> -t mesh --num-switches 10

# Teste de descoberta de links (liga/desliga links)
sudo python3 workload.py -ip <IP_ONOS> -n onos -t mesh --num-switches 10 \
  --links --links_to_add 2

# Teste de descoberta de hosts (conecta/desconecta hosts)
sudo python3 workload.py -ip <IP_ONOS> -n onos -t mesh --num-switches 10 \
  --hosts --hosts_to_add 3
```

#### `throughput_request.py` — throughput da API (sem Mininet)

Mede throughput REST **sem** subir topologia. Útil se o controlador já tiver switches conectados.

```bash
python3 throughput_request.py -ip <IP_ONOS> -n onos -r 8181 -mr 100 -d 30
```

> **Nota:** este script referencia um parser `throughput` que pode não estar definido em `arguments_parser.py`. Prefira `northbound_api.py -tp` para throughput completo.

#### `response_time.py` — tempo de resposta (com topologia)

Similar ao modo `-rt` de `northbound_api.py`. Pode exigir ajuste no parser.

#### `ofpt_packetin_record.py` — gravar timestamps de Packet-In

Captura e registra horários de mensagens `OFPTPacketIn`:

```bash
sudo python3 ofpt_packetin_record.py \
  -ip <IP_ONOS> -n onos -p 6653 -if <IFACE>
```

Saída: `output/last_ofpt_packet_in_onos.txt`

---

### Fluxo resumido (ONOS + Mininet)

```
1. [VM ONOS]  Iniciar ONOS
2. [VM Mininet] Editar global_variables.py e REST_tests/onos.py
3. [VM Mininet] python3 REST_tests/onos.py          → validar REST
4. [VM Mininet] sudo mn --controller=remote,...     → validar OpenFlow
5. [VM Mininet] sudo python3 script_topology.py ... → benchmark principal
6. [VM Mininet] Ver resultados em output/
```

---

## Onde ficam os resultados

| Arquivo | Conteúdo |
|---|---|
| `output/<controlador>_<topo>_average_topology_discovery_time.csv` | Médias por tamanho de topologia (TDT, LDT, CPU, memória, pacotes) |
| `output/<controlador>_<topo>_topology_discovery_time_report.txt` | Relatório detalhado com parâmetros e dados por trial |
| `output/topo_disc_<controlador>.txt` | Resultado bruto de cada execução de `topology_discovery.py` |
| `output/link_length.txt` | Número de links da última topologia criada por `workload.py` |
| `output/last_ofpt_packet_in_<controlador>.txt` | Timestamps de Packet-In |

Colunas do CSV (`script_topology.py`):

| Coluna | Significado |
|---|---|
| `num_nodes` | Tamanho da topologia (switches) |
| `avg_tdt` | Tempo médio de descoberta de switches (Topology Discovery Time) |
| `avg_ldt` | Tempo médio de descoberta de links (Link Discovery Time) |
| `avg_total` | Soma TDT + LDT |
| `avg_lldp_len` / `avg_pkt_len` | Volume de tráfego LLDP/pacotes |
| `avg_cpu` / `avg_memory` | Uso médio de CPU/memória do controlador (via SSH) |

---

## Referência de arquivos

### Scripts principais (raiz do projeto)

| Arquivo | Função |
|---|---|
| `script_topology.py` | **Orquestrador principal** do benchmark de descoberta de topologia. Executa trials, agrega resultados em CSV e relatório. |
| `topology_discovery.py` | Implementa a métrica RFC 8456 de descoberta de topologia: captura OpenFlow (Scapy), consulta REST, calcula tempos. |
| `workload.py` | Cria topologias no Mininet (`mesh`, `star`, `3-tier`, `leaf-spine`) conectadas ao controlador remoto. |
| `northbound_api.py` | Benchmark da API northbound: tempo de resposta e throughput de requisições REST. |
| `response_time.py` | Mede tempo médio de resposta da API REST com topologia ativa. |
| `throughput_request.py` | Mede throughput máximo da API REST com requisições concorrentes. |
| `host_links_onoff.py` | Funções para ligar/desligar links e hosts e medir tempo de reconhecimento pelo controlador. |
| `setup_dhcp.py` | Configura DHCP no controlador (ONOS, Floodlight, ODL) via REST — usado em testes com hosts DHCP. |
| `ControllerMonitor.py` | Thread que monitora CPU e memória do processo do controlador via SSH (Paramiko). |
| `global_variables.py` | Variáveis globais compartilhadas e instância do `ControllerMonitor` (IP/credenciais SSH). |
| `arguments_parser.py` | Definição centralizada de argumentos de linha de comando para todos os scripts. |
| `email_sender.py` | Envia resultados por e-mail ao final de `script_topology.py`. |
| `ofpt_packetin_record.py` | Utilitário para registrar timestamps de mensagens OpenFlow Packet-In. |

### Pastas auxiliares

| Pasta / arquivo | Função |
|---|---|
| `REST_tests/onos.py` | Teste simples da API REST do ONOS (topologia, links, hosts). |
| `REST_tests/odl.py` | Teste REST para OpenDaylight. |
| `REST_tests/floodlight.py` | Teste REST para Floodlight. |
| `json/` | Configurações JSON para DHCP e controladores (ONOS, ODL, Floodlight). |
| `json/onos_dhcp.json` | Configuração DHCP para app ONOS. |
| `json/enable.json`, `instance1.json`, `vlans.json` | Configurações DHCP para Floodlight. |
| `json/odl.json`, `odl_enabledhcp.json` | Configurações para OpenDaylight. |
| `json/dnsmasq.conf` | Configuração dnsmasq (referência). |
| `json/switchs.json` | Metadados de switches. |
| `output/` | Diretório de saída de todos os experimentos. |
| `stats/getThput.py` | Análise de throughput a partir de arquivo `.pcap` (Matplotlib + Scapy). |
| `scratch/customTopo.py` | Protótipo/experimento de topologia customizada no Mininet. |
| `scratch/traffGen.py` | Geração de tráfego experimental. |
| `scratch/traffTest.py` | Testes de tráfego experimental. |
| `apps/` | Versões antigas/alternativas de scripts para Floodlight e hub flows. |
| `application-plane/` | Versões alternativas de scripts de topologia e Floodlight (planejamento de aplicação). |

---

## Solução de problemas

### `Permission denied` ou Mininet não inicia

Execute com `sudo`:

```bash
sudo python3 script_topology.py ...
```

Limpe estado do Mininet entre execuções:

```bash
sudo mn -c
```

### REST API não responde

- Confirme ONOS rodando na VM ONOS: `curl -u onos:rocks http://localhost:8181/onos/v1/devices`
- Verifique firewall na VM ONOS (`ufw`, `iptables`)
- Teste da VM Mininet: `python3 REST_tests/onos.py`

### OpenFlow não conecta

- Porta 6653 aberta na VM ONOS
- IP correto em `-ip`
- Teste: `sudo mn --controller=remote,ip=<IP_ONOS>,port=6653 --switch ovsk,protocols=OpenFlow13 --test pingall`

### Descoberta de topologia sempre falha (`-1.0` no resultado)

- Interface `-if` incorreta — use a que encaminha tráfego ao ONOS
- Intervalo `-q` muito curto — aumente (ex.: `5` ou `10`)
- Aumente `-c` (tolerância a falhas consecutivas)
- Confirme que `workload.py` está criando switches (veja logs no terminal)

### Erro de SSH no `ControllerMonitor`

Edite `global_variables.py` com IP, usuário e senha corretos da VM ONOS. SSH deve estar habilitado e o processo `java` (ONOS) visível com `ps -C java`.

### E-mail no final do experimento falha

`script_topology.py` chama `email_sender.py` automaticamente. Se não for usar e-mail, comente a última linha de `script_topology.py`:

```python
# send_email_with_attachment(...)
```

Ou configure `email_sender.py` com suas credenciais SMTP.

### `response_time.py` / `throughput_request.py` dão erro de argumentos

Esses scripts referenciam parsers (`response_time`, `throughput`) que podem não existir em `arguments_parser.py`. Use **`northbound_api.py`** com `-rt` e `-tp`, que possui parser completo.

### Topologia `star` via `script_topology.py`

O orquestrador `script_topology.py` monta comandos para `mesh`, `3-tier` e `leaf-spine`. Para `star`, execute `workload.py` e `topology_discovery.py` manualmente em terminais separados.

---

## Referência

- [RFC 8456 — Benchmarking Methodology for SDN Controller Performance](https://www.rfc-editor.org/rfc/rfc8456.html)
- [Documentação ONOS](https://wiki.onosproject.org/)
