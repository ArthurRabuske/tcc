# TCC — Benchmark de Controladores SDN

Projeto de benchmark baseado na metodologia do **RFC 8456** (*Benchmarking Methodology for Software-Defined Networking (SDN) Controller Performance*). O código mede desempenho de controladores SDN (**ONOS** e **OpenDaylight**) em cenários como descoberta de topologia, API northbound e carga de trabalho em redes emuladas com **Mininet**.

---

## Índice

1. [Visão geral da arquitetura](#visão-geral-da-arquitetura)
2. [Controladores suportados](#controladores-suportados)
3. [Pré-requisitos](#pré-requisitos)
4. [Instalação na VM Mininet](#instalação-na-vm-mininet)
5. [Configuração inicial](#configuração-inicial)
6. [Verificação de conectividade](#verificação-de-conectividade)
7. [Como executar os benchmarks](#como-executar-os-benchmarks)
   - [Forma recomendada: `run_tests.py`](#forma-recomendada-run_testspy)
   - [Execução manual (avançado)](#execução-manual-avançado)
8. [Testes com OpenDaylight](#testes-com-opendaylight)
9. [Onde ficam os resultados](#onde-ficam-os-resultados)
10. [Visualização em gráficos](#visualização-em-gráficos)
11. [Referência de arquivos](#referência-de-arquivos)
12. [Solução de problemas](#solução-de-problemas)
13. [Referências](#referências)

---

## Visão geral da arquitetura

O projeto roda em **duas máquinas virtuais** em rede:

```
┌─────────────────────────────┐         ┌──────────────────────────────┐
│   VM Controlador SDN        │         │       VM Mininet             │
│   (ONOS ou OpenDaylight)    │         │                              │
│                             │         │  • Mininet (topologias)      │
│  • Controlador (Java)       │◄─OpenFlow│  • run_tests.py (menu)      │
│  • REST API (8181)          │◄─8181───│  • Scripts de benchmark      │
│  • SSH (monitoramento)      │◄─22─────│  • Captura OpenFlow (Scapy)  │
└─────────────────────────────┘         │  • plot_results.py (gráficos)│
                                        └──────────────────────────────┘
```

| VM | Papel |
|---|---|
| **VM Controlador** | Executa ONOS ou OpenDaylight. Recebe conexões OpenFlow dos switches e responde à API REST. |
| **VM Mininet** | Executa **todos os scripts deste repositório**. Cria topologias, mede tempos, consulta REST e gera resultados. |

> **Importante:** os benchmarks são sempre executados **na VM Mininet**, apontando para o IP da VM do controlador.

---

## Controladores suportados

| | **ONOS** | **OpenDaylight (ODL)** |
|---|---|---|
| Nome no projeto (`-n`) | `onos` | `odl` |
| Porta OpenFlow | **6653** | **6633** |
| Porta REST | **8181** | **8181** |
| Autenticação REST | `onos` / `rocks` | `admin` / `admin` |
| Endpoint REST (topologia) | `/onos/v1/topology` | `/restconf/operational/opendaylight-inventory:nodes` |
| Processo monitorado (SSH) | `java` | `java` |

---

## Pré-requisitos

### VM do controlador (ONOS ou ODL)

- Controlador instalado e em execução
- Portas liberadas no firewall:
  - **OpenFlow** — 6653 (ONOS) ou 6633 (ODL)
  - **8181** — REST API
  - **22** — SSH (opcional, para monitoramento de CPU/memória)
- Apps/features necessários para descoberta de topologia (OpenFlow, LLDP/link discovery)

### VM Mininet

- Ubuntu/Debian com Mininet instalado
- Python 3 e pip
- Acesso de rede à VM do controlador
- Execução com **`sudo`** (Mininet e Scapy exigem privilégios de root)

---

## Instalação na VM Mininet

```bash
# Dependências do sistema
sudo apt update
sudo apt install -y mininet openvswitch-switch python3-pip

# Dependências Python (na pasta do projeto)
cd tcc
sudo pip3 install requests scapy paramiko psutil mininet

# Dependência opcional para gráficos
pip3 install -r requirements.txt

# Pasta de saída
mkdir -p output output/plots
```

> Rode sempre os scripts **a partir da pasta `tcc/`**, pois eles usam caminhos relativos (`output/`, `json/`).

---

## Configuração inicial

Antes do primeiro teste, ajuste estes arquivos conforme o seu ambiente.

### 1. `run_tests.py` — IP, portas e interface

Edite o dicionário `CONTROLADORES` e a interface padrão:

```python
CONTROLADORES = {
    "onos": {
        "ip":        "192.168.0.134",   # IP da VM ONOS
        "rest_port": "8181",
        "of_port":   "6653",
        ...
    },
    "odl": {
        "ip":        "192.168.0.134",   # IP da VM OpenDaylight
        "rest_port": "8181",
        "of_port":   "6633",            # ODL usa 6633, não 6653
        ...
    },
}

DEFAULT_IFACE = "enp0s3"   # interface que encaminha tráfego ao controlador
```

### 2. `global_variables.py` — monitoramento de CPU/memória via SSH

Usado por `topology_discovery.py` para medir uso do processo Java na VM do controlador:

```python
controller_monitor = ControllerMonitor(
    'java',
    '192.168.0.134',   # IP da VM do controlador
    'onos',            # usuário SSH
    '1234'             # senha SSH
)
```

### 3. `REST_tests/` — testes rápidos de API

| Arquivo | Controlador | O que testa |
|---|---|---|
| `REST_tests/onos.py` | ONOS | Topologia, links e hosts |
| `REST_tests/odl.py` | OpenDaylight | Switches, links e hosts |

Altere `CONTROLLER_IP` em cada arquivo para o IP da VM correspondente.

---

## Verificação de conectividade

Execute **na VM Mininet**, na ordem abaixo.

### Passo 1 — Rede

```bash
ping <IP_CONTROLADOR>
```

### Passo 2 — REST API

**ONOS:**

```bash
cd tcc
python3 REST_tests/onos.py
```

**OpenDaylight:**

```bash
cd tcc
python3 REST_tests/odl.py
```

### Passo 3 — OpenFlow (Mininet)

**ONOS (porta 6653):**

```bash
sudo mn --controller=remote,ip=<IP_ONOS>,port=6653 --switch ovsk,protocols=OpenFlow13 --test pingall
```

**OpenDaylight (porta 6633):**

```bash
sudo mn --controller=remote,ip=<IP_ODL>,port=6633 --switch ovsk,protocols=OpenFlow13 --test pingall
```

### Passo 4 — Interface para captura de pacotes

Os scripts de descoberta capturam tráfego OpenFlow com Scapy. Descubra a interface correta:

```bash
ip route get <IP_CONTROLADOR>
```

Use o nome retornado (ex.: `enp0s3`, `eth0`) no parâmetro `-if` ou em `DEFAULT_IFACE` do `run_tests.py`.

---

## Como executar os benchmarks

### Forma recomendada: `run_tests.py`

**`run_tests.py`** é a interface interativa principal do projeto. Ela automatiza a montagem dos comandos, aplica as configurações corretas de cada controlador (porta OpenFlow, nome, REST) e guia a escolha da topologia.

```bash
cd tcc
sudo python3 run_tests.py
```

#### Menu principal

```
[1]  Teste ONOS
[2]  Teste OpenDaylight
[3]  Benchmark ONOS × OpenDaylight  (em desenvolvimento)
[0]  Sair
```

#### Menu de topologias (após escolher o controlador)

```
[1]  Mesh        — todos os switches conectados entre si
[2]  Leaf-Spine  — leafs conectados a spines centrais
[3]  3-Tier      — core → aggregation → access
[0]  Voltar
```

Para cada topologia, o menu solicita os parâmetros do experimento (IP, portas, interface, trials, tamanhos) com valores padrão já preenchidos conforme o controlador selecionado. Ao confirmar, o script executa `script_topology.py` com os argumentos corretos.

#### Fluxo típico com `run_tests.py`

```
1. [VM Controlador]  Iniciar ONOS ou OpenDaylight
2. [VM Mininet]      sudo python3 run_tests.py
3.                  Escolher controlador (1 = ONOS, 2 = ODL)
4.                  Escolher topologia (Mesh / Leaf-Spine / 3-Tier)
5.                  Confirmar parâmetros (Enter aceita o padrão)
6.                  Aguardar conclusão
7.                  Ver resultados em output-<controlador>-<topologia>/
8.                  (gráficos gerados automaticamente ao final do teste)
9.                  Opção [3] → Benchmarking → escolher topologia
```

#### O que o `run_tests.py` executa por baixo dos panos

Para cada teste, monta e roda um comando equivalente a:

```bash
sudo python3 script_topology.py \
  -t <topologia> \
  -ip <IP> -n <onos|odl> -r <REST_PORT> -p <OF_PORT> \
  -if <interface> -q 3 -c 50 -s 5 -tr 3 -d 5 -max 20 \
  --num-switches 10          # mesh
  # ou --num-leafs 4 --num-spines 2   # leaf-spine
  # ou --num-cores 2 --num-aggs 4 --num-access 8  # 3-tier
```

---

### Execução manual (avançado)

Use quando precisar de controle fino sobre os parâmetros ou automação externa.

#### Descoberta de topologia — `script_topology.py`

Orquestrador principal. Para cada tamanho de topologia:

1. Executa `topology_discovery.py` (mede tempo via OpenFlow + REST)
2. Executa `workload.py` (sobe a topologia no Mininet)
3. Agrega resultados em CSV e relatório em `output-<controlador>-<topologia>/`
4. Gera gráficos automaticamente na mesma pasta ao final

**Exemplo — ONOS, mesh:**

```bash
sudo python3 script_topology.py \
  -ip 192.168.0.134 \
  -n onos \
  -p 6653 \
  -r 8181 \
  -t mesh \
  --num-switches 10 \
  -if enp0s3 \
  -q 3 -c 50 -s 5 -tr 3 -d 5 -max 20
```

**Exemplo — OpenDaylight, mesh:**

```bash
sudo python3 script_topology.py \
  -ip 192.168.0.134 \
  -n odl \
  -p 6633 \
  -r 8181 \
  -t mesh \
  --num-switches 10 \
  -if enp0s3 \
  -q 3 -c 50 -s 5 -tr 3 -d 5 -max 20
```

#### Parâmetros de `script_topology.py`

| Parâmetro | Descrição |
|---|---|
| `-ip` | IP da VM do controlador |
| `-n` | Nome: `onos` ou `odl` |
| `-p` | Porta OpenFlow (6653 ONOS / 6633 ODL) |
| `-r` | Porta REST (8181) |
| `-t` | Topologia: `mesh`, `3-tier`, `leaf-spine`, `star` |
| `-if` | Interface de rede para captura OpenFlow |
| `-q` | Intervalo (s) entre consultas REST |
| `-c` | Falhas consecutivas antes de desistir |
| `-s` | Tamanho inicial da topologia |
| `-tr` | Repetições (trials) por tamanho |
| `-d` | Incremento do tamanho a cada rodada |
| `-max` | Tamanho máximo agregado |
| `-k` / `--no_links` | Medir só switches, sem esperar links |

#### API Northbound — `northbound_api.py`

Mede tempo de resposta (`-rt`) e throughput (`-tp`) da API REST com topologia ativa:

```bash
sudo python3 northbound_api.py \
  -ip 192.168.0.134 -n onos -r 8181 \
  -t mesh -s 10 -q 3 -nt 100 \
  -rt -tp -mr 100 -d 30 -i 10
```

#### Componentes individuais (depuração)

| Script | Função |
|---|---|
| `workload.py` | Sobe topologia no Mininet conectada ao controlador remoto |
| `topology_discovery.py` | Mede tempo de descoberta (requer topologia ativa) |
| `northbound_api.py` | Benchmark completo da API REST |
| `ofpt_packetin_record.py` | Registra timestamps de Packet-In OpenFlow |
| `host_links_onoff.py` | Testes de descoberta de links/hosts (ligar/desligar) |

---

## Testes com OpenDaylight

Esta seção detalha o que é diferente ao benchmarkar o **OpenDaylight** em relação ao ONOS.

### 1. Preparar a VM OpenDaylight

Inicie o Karaf/ODL e instale as features necessárias:

```bash
# Na VM OpenDaylight (console Karaf)
feature:install odl-restconf odl-l2switch-switch odl-mdsal-apidocs
```

Confirme que a REST responde:

```bash
curl -u admin:admin http://<IP_ODL>:8181/restconf/operational/opendaylight-inventory:nodes
```

### 2. Diferenças importantes em relação ao ONOS

| Aspecto | ONOS | OpenDaylight |
|---|---|---|
| Porta OpenFlow no Mininet | `-p 6653` | `-p 6633` |
| Nome do controlador (`-n`) | `onos` | `odl` |
| Credenciais REST | `onos:rocks` | `admin:admin` |
| Contagem de links | direto da API | ODL adiciona 1 link local por switch; o código subtrai isso |
| Endpoint REST usado | `/onos/v1/topology` | `/restconf/operational/opendaylight-inventory:nodes` |

### 3. Executar via `run_tests.py` (recomendado)

```bash
cd tcc
sudo python3 run_tests.py
# Escolha [2] Teste OpenDaylight
# Escolha a topologia desejada
# Confirme os parâmetros (porta OpenFlow já vem como 6633)
```

### 4. Executar manualmente

```bash
# Validar REST
python3 REST_tests/odl.py

# Validar OpenFlow (porta 6633!)
sudo mn --controller=remote,ip=<IP_ODL>,port=6633 --switch ovsk,protocols=OpenFlow13 --test pingall

# Benchmark mesh
sudo python3 script_topology.py \
  -ip <IP_ODL> -n odl -p 6633 -r 8181 \
  -t mesh --num-switches 10 \
  -if enp0s3 -q 3 -c 50 -s 5 -tr 3 -d 5 -max 20
```

### 5. Resultados do OpenDaylight

Os resultados ficam em pastas dedicadas:

```
output-odl-mesh/
output-odl-leaf-spine/
output-odl-3-tier/
```

### 6. Comparar ONOS vs OpenDaylight

1. Rode os mesmos parâmetros para ONOS e ODL (mesma topologia, `-s`, `-tr`, `-d`, `-max`)
2. No `run_tests.py`, escolha **[3] Benchmark comparativo**
3. Os gráficos comparativos são gerados em `output-benchmarking-<topologia>/<timestamp>/`

Ou via linha de comando:

```bash
python3 plot_benchmark.py -t mesh
python3 plot_benchmark.py -t leaf-spine
python3 plot_benchmark.py -t 3-tier
```

---

## Onde ficam os resultados

Cada **execução** de teste cria uma subpasta com timestamp, sem sobrescrever execuções anteriores:

```
output-onos-mesh/
├── 2026-06-09_19-15-30/
│   ├── average_topology_discovery_time.csv
│   ├── topology_discovery_time_report.txt
│   ├── topo_disc.txt
│   ├── link_length.txt
│   ├── plot_times.png
│   ├── plot_cpu_mem.png
│   └── plot_summary.png
└── 2026-06-10_10-00-00/          ← nova execução, pasta separada
    └── ...
```

Cada **benchmarking comparativo** também cria pasta com timestamp:

```
output-benchmarking-mesh/
├── 2026-06-09_20-00-00/
│   ├── compare_avg_total.png
│   ├── compare_tdt_ldt.png
│   ├── compare_cpu_mem.png
│   └── compare_summary.png
└── 2026-06-10_11-00-00/
    └── ...
```

| Pasta / arquivo | Conteúdo |
|---|---|
| `output-<ctrl>-<topo>/<timestamp>/` | Resultados de uma execução individual |
| `output-benchmarking-<topo>/<timestamp>/` | Gráficos comparativos ONOS × ODL |
| `average_topology_discovery_time.csv` | Médias por tamanho de topologia |
| `topology_discovery_time_report.txt` | Parâmetros + dados brutos por trial |
| `plot_*.png` | Gráficos gerados automaticamente ao final do teste |
| `compare_*.png` | Gráficos comparativos do benchmarking |

### Exemplos de estrutura

```
output-onos-mesh/2026-06-09_19-15-30/
output-onos-leaf-spine/2026-06-09_19-30-00/
output-odl-mesh/2026-06-09_20-00-00/
output-benchmarking-mesh/2026-06-09_21-00-00/
output-benchmarking-leaf-spine/2026-06-09_21-15-00/
```

### Colunas do CSV

| Coluna | Significado |
|---|---|
| `num_nodes` | Tamanho da topologia (switches) |
| `avg_tdt` | Tempo médio de descoberta de switches (Topology Discovery Time) |
| `avg_ldt` | Tempo médio de descoberta de links (Link Discovery Time) |
| `avg_total` | Soma TDT + LDT |
| `avg_lldp_len` / `avg_pkt_len` | Volume de tráfego LLDP/pacotes observado |
| `avg_lldp_count` / `avg_pkt_count` | Contagem de eventos LLDP/pacotes |
| `avg_cpu` / `avg_memory` | Uso médio de CPU/memória do controlador (via SSH) |

---

## Visualização em gráficos

### Gráficos individuais (automático)

Ao final de cada teste, `script_topology.py` gera automaticamente os gráficos **dentro da pasta do teste** (`output-<controlador>-<topologia>/`).

Para regenerar manualmente:

```bash
python3 plot_results.py --input output-onos-mesh
```

### Gráficos comparativos (ONOS × ODL)

No menu:

```bash
sudo python3 run_tests.py
# [3] Benchmark comparativo
#   [1] Mesh
#   [2] Leaf-Spine
#   [3] 3-Tier
```

Ou via linha de comando:

```bash
python3 plot_benchmark.py -t mesh
python3 plot_benchmark.py -t leaf-spine
python3 plot_benchmark.py -t 3-tier
```

Cada execução cria uma nova pasta em `output-benchmarking-<topo>/<timestamp>/`:

| Arquivo PNG | Conteúdo |
|---|---|
| `compare_avg_total.png` | Tempo total de descoberta — todos os controladores |
| `compare_tdt_ldt.png` | TDT e LDT lado a lado |
| `compare_cpu_mem.png` | CPU e memória comparados |
| `compare_summary.png` | Resumo consolidado |

> Requisito: pelo menos **2 controladores** testados na mesma topologia (ex.: `output-onos-mesh/` e `output-odl-mesh/`). O benchmark usa a **execução mais recente** de cada controlador.

### Instalar dependência

```bash
cd tcc
pip3 install -r requirements.txt
```

### Gerar gráficos para todas as pastas de teste

```bash
python3 plot_results.py
```

### Gráficos individuais gerados

| Arquivo PNG | Conteúdo |
|---|---|
| `plot_times.png` | `avg_tdt`, `avg_ldt`, `avg_total` vs tamanho da topologia |
| `plot_cpu_mem.png` | CPU e memória vs tamanho |
| `plot_traffic_bytes.png` | Volume de tráfego LLDP/pacotes |
| `plot_traffic_count.png` | Contagem de eventos |
| `plot_summary.png` | Figura consolidada com os 4 painéis |

---

## Referência de arquivos

### Scripts principais

| Arquivo | Função |
|---|---|
| **`run_tests.py`** | **Interface interativa principal.** Menu ONOS/ODL, topologias e benchmark comparativo. |
| `script_topology.py` | Orquestrador do benchmark. Salva em `output-<ctrl>-<topo>/` e gera gráficos ao final. |
| `plot_results.py` | Gera gráficos PNG individuais a partir das pastas de teste. |
| `plot_benchmark.py` | Gera gráficos comparativos por topologia em `output-benchmarking-<topo>/<timestamp>/`. |
| `output_utils.py` | Utilitários de caminhos e descoberta de pastas de teste. |
| `topology_discovery.py` | Métrica RFC 8456: captura OpenFlow (Scapy), consulta REST, calcula tempos TDT/LDT. |
| `workload.py` | Cria topologias no Mininet (`mesh`, `star`, `3-tier`, `leaf-spine`) conectadas ao controlador remoto. |
| `northbound_api.py` | Benchmark da API northbound: tempo de resposta e throughput REST. |
| `plot_results.py` | Gera gráficos PNG a partir dos CSVs de `output/`. |
| `host_links_onoff.py` | Testes de descoberta de links/hosts (ligar/desligar interfaces e medir reconhecimento). |
| `setup_dhcp.py` | Configura DHCP no controlador via REST (ONOS, ODL, Floodlight). |
| `ControllerMonitor.py` | Monitora CPU/memória do processo Java do controlador via SSH. |
| `global_variables.py` | Variáveis globais e instância do `ControllerMonitor`. |
| `arguments_parser.py` | Argumentos de linha de comando centralizados para todos os scripts. |
| `email_sender.py` | Envio opcional de resultados por e-mail (via variáveis de ambiente). |
| `ofpt_packetin_record.py` | Registra timestamps de mensagens OpenFlow Packet-In. |
| `response_time.py` | Mede tempo médio de resposta REST (legado; prefira `northbound_api.py -rt`). |
| `throughput_request.py` | Mede throughput REST sem Mininet (legado; prefira `northbound_api.py -tp`). |

### Pastas auxiliares

| Pasta / arquivo | Função |
|---|---|
| `REST_tests/onos.py` | Teste rápido da API REST do ONOS. |
| `REST_tests/odl.py` | Teste rápido da API REST do OpenDaylight. |
| `REST_tests/floodlight.py` | Teste rápido da API REST do Floodlight. |
| `json/` | Configurações JSON (DHCP, VLANs, switches) por controlador. |
| `json/onos_dhcp.json` | Configuração DHCP para app ONOS. |
| `json/odl.json`, `odl_enabledhcp.json` | Configurações para OpenDaylight. |
| `output/` | Saída de todos os experimentos e gráficos. |
| `requirements.txt` | Dependência Python para gráficos (`matplotlib`). |
| `stats/getThput.py` | Análise de throughput a partir de `.pcap`. |
| `scratch/` | Protótipos experimentais (topologia, tráfego). |
| `apps/` | Versões alternativas para Floodlight. |
| `application-plane/` | Versões alternativas de scripts de topologia. |

---

## Solução de problemas

### `Permission denied` ou Mininet não inicia

```bash
sudo python3 run_tests.py
# ou
sudo python3 script_topology.py ...
```

Limpe o estado do Mininet entre execuções:

```bash
sudo mn -c
```

### REST API não responde

- Confirme o controlador rodando na VM
- Verifique firewall (`ufw`, `iptables`)
- Teste com `REST_tests/onos.py` ou `REST_tests/odl.py`

### OpenFlow não conecta

- **ONOS:** porta **6653**
- **OpenDaylight:** porta **6633** (não confundir!)
- IP correto em `-ip` ou no `run_tests.py`
- Teste manual com `sudo mn --controller=remote,...`

### Descoberta de topologia falha (`-1.0` no resultado)

- Interface `-if` incorreta — use `ip route get <IP_CONTROLADOR>`
- Aumente `-q` (intervalo de consulta REST)
- Aumente `-c` (tolerância a falhas consecutivas)
- Confirme que switches estão subindo (`workload.py` nos logs)

### Erro de SSH no `ControllerMonitor`

Edite `global_variables.py` com IP, usuário e senha corretos. SSH deve estar habilitado na VM do controlador e o processo `java` visível com `ps -C java`.

### E-mail (opcional)

Por padrão o projeto **não envia e-mail**. Para habilitar:

```bash
export SDNBM_SEND_EMAIL=1
export SDNBM_EMAIL_FROM="seu@email.com"
export SDNBM_EMAIL_TO="destino@email.com"
export SDNBM_SMTP_USER="usuario_smtp"
export SDNBM_SMTP_PASS="senha_ou_app_password"
```

### OpenDaylight: switches não aparecem na REST

- Confirme features instaladas: `odl-restconf`, `odl-l2switch-switch`
- Verifique se o Mininet usa porta **6633** (não 6653)
- Use `-n odl` em todos os scripts

### Topologia `star`

O `run_tests.py` e `script_topology.py` suportam `mesh`, `leaf-spine` e `3-tier`. Para `star`, execute `workload.py` e `topology_discovery.py` manualmente em terminais separados.

---

## Referências

- [RFC 8456 — Benchmarking Methodology for SDN Controller Performance](https://www.rfc-editor.org/rfc/rfc8456.html)
- [Documentação ONOS](https://wiki.onosproject.org/)
- [Documentação OpenDaylight](https://docs.opendaylight.org/)
