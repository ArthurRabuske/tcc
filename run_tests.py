#!/usr/bin/env python3
"""
run_tests.py — Interface interativa para benchmark SDN
Coloque este arquivo dentro da pasta tcc/ e execute com: sudo python3 run_tests.py
"""

import subprocess
import os
import sys
import time
from pathlib import Path

from output_utils import (
    CSV_NAME,
    controller_from_run_dir,
    discover_controller_runs_for_topology,
    discover_test_base_dirs,
    get_latest_run_with_csv,
    label_from_dir,
    list_runs_with_csv,
    parse_test_dir_name,
)
from plot_benchmark import run_benchmark_for_topology

# ─────────────────────────────────────────────
#  CONFIGURAÇÕES POR CONTROLADOR
# ─────────────────────────────────────────────
CONTROLADORES = {
    "onos": {
        "label":     "ONOS",
        "ip":        "192.168.0.134",
        "name":      "onos",
        "rest_port": "8181",
        "of_port":   "6653",
        "cor":       "\033[1;36m",   # ciano
    },
    "odl": {
        "label":     "OpenDaylight",
        "ip":        "192.168.0.134",
        "name":      "odl",
        "rest_port": "8181",
        "of_port":   "6633",
        "cor":       "\033[1;33m",   # amarelo
    },
}

DEFAULT_IFACE = "enp0s3"

# Cores ANSI
R   = "\033[1;31m"
G   = "\033[1;32m"
Y   = "\033[1;33m"
C   = "\033[1;36m"
M   = "\033[1;35m"
W   = "\033[1;37m"
DIM = "\033[2m"
RST = "\033[0m"

# Controlador ativo (definido no menu inicial)
sdn_ativo = None

# ─────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────
def clear():
    os.system("clear")

def banner():
    cfg = CONTROLADORES[sdn_ativo] if sdn_ativo else None
    cor = cfg["cor"] if cfg else C
    label = f"Controlador: {cfg['label']}  |  IP: {cfg['ip']}" if cfg else "Selecione um controlador"
    print(f"""
{cor}╔══════════════════════════════════════════════════════╗
║        SDN BENCHMARK                                 ║
║        {label:<46}{cor}║
╚══════════════════════════════════════════════════════╝{RST}
""")

def titulo(texto):
    print(f"\n{Y}{'─'*54}")
    print(f"  {texto}")
    print(f"{'─'*54}{RST}\n")

def entrada(prompt, default):
    val = input(f"  {W}{prompt}{RST} {DIM}[{default}]{RST}: ").strip()
    return val if val else default

def confirmar(msg):
    r = input(f"\n  {Y}⚡ {msg} (s/n): {RST}").strip().lower()
    return r in ("s", "sim", "y", "yes", "")

# ─────────────────────────────────────────────
#  RODAR COMANDO
# ─────────────────────────────────────────────
def rodar(cmd, descricao, env=None):
    print(f"\n{G}▶ Executando: {descricao}{RST}")
    print(f"{DIM}  {' '.join(cmd)}{RST}\n")
    try:
        proc = subprocess.run(cmd, check=False, env=env)
        if proc.returncode == 0:
            print(f"\n{G}✔ Concluído com sucesso!{RST}")
        else:
            print(f"\n{R}✘ Processo encerrado (código {proc.returncode}){RST}")
        return proc.returncode == 0
    except KeyboardInterrupt:
        print(f"\n{Y}⚠ Interrompido pelo usuário.{RST}")
        return False
    except FileNotFoundError:
        print(f"\n{R}✘ Erro: script não encontrado. Execute dentro da pasta tcc/{RST}")
        return False

def base_flags(ip, name, rest, of_port, iface, q, c, s, tr, d, maxsize):
    return [
        "-ip",  ip,
        "-n",   name,
        "-r",   rest,
        "-p",   of_port,
        "-if",  iface,
        "-q",   str(q),
        "-c",   str(c),
        "-s",   str(s),
        "-tr",  str(tr),
        "-d",   str(d),
        "-max", str(maxsize),
    ]

# ─────────────────────────────────────────────
#  PARÂMETROS COMUNS
# ─────────────────────────────────────────────
def pedir_params_comuns():
    cfg = CONTROLADORES[sdn_ativo]
    titulo("Parâmetros do Teste")
    ip      = entrada("IP do controlador     ", cfg["ip"])
    name    = entrada("Nome do controlador   ", cfg["name"])
    rest    = entrada("Porta REST            ", cfg["rest_port"])
    of_port = entrada("Porta OpenFlow        ", cfg["of_port"])
    iface   = entrada("Interface de rede     ", DEFAULT_IFACE)
    q       = entrada("Intervalo de consulta (-q) ", "3")
    c       = entrada("Falhas consecutivas   (-c) ", "50")
    tr      = entrada("Tentativas por tamanho(-tr)", "3")
    d       = entrada("Incremento de tamanho (-d) ", "5")
    s       = entrada("Tamanho inicial       (-s) ", "5")
    maxsize = entrada("Tamanho máximo        (-max)", "20")
    return ip, name, rest, of_port, iface, int(q), int(c), int(s), int(tr), int(d), int(maxsize)

# ─────────────────────────────────────────────
#  TOPOLOGIAS
# ─────────────────────────────────────────────
def teste_mesh():
    clear(); banner()
    titulo("🔷  Topologia MESH")
    print(f"  {DIM}Todos os switches conectados entre si.{RST}\n")

    ip, name, rest, of_port, iface, q, c, s, tr, d, maxsize = pedir_params_comuns()
    num_sw = entrada("Número de switches (--num-switches)", "10")

    cmd = ["sudo", "python3", "script_topology.py",
           "-t", "mesh", "--num-switches", num_sw,
           ] + base_flags(ip, name, rest, of_port, iface, q, c, s, tr, d, maxsize)

    if confirmar("Iniciar teste MESH?"):
        rodar(cmd, "Benchmark MESH")

def teste_leaf_spine():
    clear(); banner()
    titulo("🔶  Topologia LEAF-SPINE")
    print(f"  {DIM}Switches leaf conectados a spines centrais.{RST}\n")

    ip, name, rest, of_port, iface, q, c, s, tr, d, maxsize = pedir_params_comuns()
    leafs  = entrada("Número de leafs  (--num-leafs) ", "4")
    spines = entrada("Número de spines (--num-spines)", "2")

    cmd = ["sudo", "python3", "script_topology.py",
           "-t", "leaf-spine", "--num-leafs", leafs, "--num-spines", spines,
           ] + base_flags(ip, name, rest, of_port, iface, q, c, s, tr, d, maxsize)

    if confirmar("Iniciar teste LEAF-SPINE?"):
        rodar(cmd, "Benchmark LEAF-SPINE")

def teste_3tier():
    clear(); banner()
    titulo("🔺  Topologia 3-TIER")
    print(f"  {DIM}Camadas: core → aggregation → access.{RST}\n")

    ip, name, rest, of_port, iface, q, c, s, tr, d, maxsize = pedir_params_comuns()
    cores  = entrada("Número de cores  (--num-cores) ", "2")
    aggs   = entrada("Número de aggs   (--num-aggs)  ", "4")
    access = entrada("Número de access (--num-access)", "8")

    cmd = ["sudo", "python3", "script_topology.py",
           "-t", "3-tier", "--num-cores", cores, "--num-aggs", aggs, "--num-access", access,
           ] + base_flags(ip, name, rest, of_port, iface, q, c, s, tr, d, maxsize)

    if confirmar("Iniciar teste 3-TIER?"):
        rodar(cmd, "Benchmark 3-TIER")

# ─────────────────────────────────────────────
#  MENU DE TOPOLOGIAS
# ─────────────────────────────────────────────
def menu_topologias():
    opcoes = {
        "1": ("🔷  Mesh",       teste_mesh),
        "2": ("🔶  Leaf-Spine", teste_leaf_spine),
        "3": ("🔺  3-Tier",     teste_3tier),
        "0": ("↩  Voltar",      None),
    }

    while True:
        clear()
        banner()
        print(f"  {W}Selecione a topologia:{RST}\n")
        for key, (label, _) in opcoes.items():
            cor = R if key == "0" else W
            print(f"  {cor}[{key}]{RST}  {label}")
        print()

        escolha = input(f"  {Y}▶ Opção: {RST}").strip()

        if escolha == "0":
            return

        if escolha in opcoes:
            _, fn = opcoes[escolha]
            fn()
            input(f"\n  {DIM}Enter para voltar ao menu de topologias...{RST}")
        else:
            print(f"\n  {R}Opção inválida.{RST}")
            time.sleep(1)

# ─────────────────────────────────────────────
#  BENCHMARK COMPARATIVO POR TOPOLOGIA
# ─────────────────────────────────────────────
TOPOLOGIAS_BENCH = {
    "1": ("Mesh", "mesh"),
    "2": ("Leaf-Spine", "leaf-spine"),
    "3": ("3-Tier", "3-tier"),
}


def listar_execucoes_topologia(topology: str):
    base = Path.cwd()
    run_dirs = discover_controller_runs_for_topology(topology, base)
    if not run_dirs:
        print(f"\n  {Y}Nenhuma execução encontrada para topologia '{topology}'.{RST}")
        print(f"  {DIM}Rode testes individuais antes (opções 1 ou 2).{RST}")
        return []

    print(f"\n  {W}Execuções usadas no comparativo ({topology}):{RST}\n")
    for run_dir in run_dirs:
        ctrl = controller_from_run_dir(run_dir)
        print(f"  ✔  {ctrl:<12}  {run_dir.parent.name}/{run_dir.name}")
    return run_dirs


def executar_benchmark_topologia(topology: str, label: str):
    clear()
    print(f"""
{M}╔══════════════════════════════════════════════════════╗
║        BENCHMARK — {label:<36}║
╚══════════════════════════════════════════════════════╝{RST}
""")

    run_dirs = listar_execucoes_topologia(topology)
    if len(run_dirs) < 2:
        print(f"\n  {Y}São necessários testes de pelo menos 2 controladores.{RST}")
        print(f"  {DIM}Ex.: output-onos-{topology}/ e output-odl-{topology}/{RST}")
        input(f"\n  {DIM}Enter para voltar...{RST}")
        return

    print(f"""
  {DIM}Será criada uma nova pasta em output-benchmarking-{topology}/<timestamp>/
  com gráficos comparando os controladores nesta topologia.{RST}
""")

    if not confirmar(f"Gerar benchmark comparativo — {label}?"):
        return

    try:
        written, outdir = run_benchmark_for_topology(topology, Path.cwd())
        if not written or outdir is None:
            print(f"\n  {Y}Nenhum comparativo gerado.{RST}")
        else:
            print(f"\n  {G}✔ Resultado salvo em: {outdir}{RST}")
            for p in written:
                print(f"    • {p.name}")
    except Exception as exc:
        print(f"\n  {R}Erro ao gerar comparativos: {exc}{RST}")

    input(f"\n  {DIM}Enter para voltar...{RST}")


def menu_benchmarking():
    opcoes = {
        "1": ("🔷  Benchmark — Mesh", "mesh"),
        "2": ("🔶  Benchmark — Leaf-Spine", "leaf-spine"),
        "3": ("🔺  Benchmark — 3-Tier", "3-tier"),
        "0": ("↩  Voltar", None),
    }

    while True:
        clear()
        print(f"""
{M}╔══════════════════════════════════════════════════════╗
║        BENCHMARKING COMPARATIVO                      ║
║        Escolha a topologia                           ║
╚══════════════════════════════════════════════════════╝{RST}
""")
        print(f"  {DIM}Cada execução gera pasta em output-benchmarking-<topo>/<timestamp>/{RST}\n")

        for key, (label, _) in opcoes.items():
            cor = R if key == "0" else W
            print(f"  {cor}[{key}]{RST}  {label}")
        print()

        escolha = input(f"  {Y}▶ Opção: {RST}").strip()
        if escolha == "0":
            return
        if escolha in opcoes:
            label, topo = opcoes[escolha]
            if topo:
                executar_benchmark_topologia(topo, label.replace("  ", " ").strip())
        else:
            print(f"\n  {R}Opção inválida.{RST}")
            time.sleep(1)

# ─────────────────────────────────────────────
#  MENU INICIAL — ESCOLHA DO CONTROLADOR
# ─────────────────────────────────────────────
def menu_controlador():
    global sdn_ativo

    while True:
        clear()
        print(f"""
{C}╔══════════════════════════════════════════════════════╗
║              SDN BENCHMARK                           ║
║        Selecione o controlador SDN                   ║
╚══════════════════════════════════════════════════════╝{RST}
""")

        titulo("O que deseja fazer?")

        print(f"  {C}[1]{RST}  Teste ONOS")
        print(f"  {Y}[2]{RST}  Teste OpenDaylight")
        print(f"  {M}[3]{RST}  Benchmark comparativo (ONOS × OpenDaylight)")
        print(f"  {R}[0]{RST}  🚪  Sair")
        print()

        escolha = input(f"  {Y}▶ Opção: {RST}").strip()

        if escolha == "0":
            clear()
            print(f"\n{G}  Até logo!{RST}\n")
            sys.exit(0)
        elif escolha == "1":
            sdn_ativo = "onos"
            menu_topologias()
            sdn_ativo = None
        elif escolha == "2":
            sdn_ativo = "odl"
            menu_topologias()
            sdn_ativo = None
        elif escolha == "3":
            menu_benchmarking()
        else:
            print(f"\n  {R}Opção inválida.{RST}")
            time.sleep(1)

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"\n{Y}⚠  Execute com sudo: sudo python3 run_tests.py{RST}\n")
        sys.exit(1)
    menu_controlador()
