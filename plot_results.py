#!/usr/bin/env python3
"""
Gera gráficos (PNG) a partir dos CSVs em output/*average_topology_discovery_time.csv.

Uso rápido:
  python3 plot_results.py
  python3 plot_results.py --input output/onos_mesh_average_topology_discovery_time.csv
  python3 plot_results.py --outdir output/plots
"""

from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from output_utils import (
    CSV_NAME,
    LEGACY_OUTPUT_DIR,
    discover_test_dirs,
    label_from_dir,
)


def _safe_float(v: str) -> Optional[float]:
    try:
        if v is None:
            return None
        v = str(v).strip()
        if v == "":
            return None
        return float(v)
    except Exception:
        return None


@dataclass
class Series:
    x: List[float]
    tdt: List[float]
    ldt: List[float]
    total: List[float]
    lldp_len: List[float]
    pkt_len: List[float]
    lldp_count: List[float]
    pkt_count: List[float]
    cpu: List[float]
    mem: List[float]


def read_average_csv(path: Path) -> Series:
    required = {
        "num_nodes",
        "avg_tdt",
        "avg_ldt",
        "avg_total",
        "avg_lldp_len",
        "avg_pkt_len",
        "avg_lldp_count",
        "avg_pkt_count",
        "avg_cpu",
        "avg_memory",
    }

    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV sem cabeçalho: {path}")
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV com colunas faltando {sorted(missing)}: {path}")

        rows: List[Dict[str, Any]] = []
        for r in reader:
            if not r:
                continue
            if all((str(v).strip() == "" for v in r.values())):
                continue
            rows.append(r)

    def col(name: str) -> List[float]:
        out: List[float] = []
        for r in rows:
            v = _safe_float(r.get(name))
            out.append(v if v is not None else float("nan"))
        return out

    return Series(
        x=col("num_nodes"),
        tdt=col("avg_tdt"),
        ldt=col("avg_ldt"),
        total=col("avg_total"),
        lldp_len=col("avg_lldp_len"),
        pkt_len=col("avg_pkt_len"),
        lldp_count=col("avg_lldp_count"),
        pkt_count=col("avg_pkt_count"),
        cpu=col("avg_cpu"),
        mem=col("avg_memory"),
    )


def infer_title_from_path(csv_path: Path) -> str:
    if csv_path.name == CSV_NAME:
        return label_from_dir(csv_path.parent)
    name = csv_path.name.replace("_average_topology_discovery_time.csv", "")
    parts = name.split("_")
    if len(parts) >= 2:
        return f"{parts[0]} / {parts[1]}"
    return name


def plot_csv(csv_path: Path, outdir: Optional[Path] = None, file_prefix: str = "plot") -> List[Path]:
    # Import local (evita falhar ao importar matplotlib em ambientes sem)
    import matplotlib

    matplotlib.use("Agg")  # headless
    import matplotlib.pyplot as plt

    series = read_average_csv(csv_path)
    title = infer_title_from_path(csv_path)
    if outdir is None:
        outdir = csv_path.parent
    outdir.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []

    def save(fig, suffix: str) -> None:
        p = outdir / f"{file_prefix}_{suffix}.png"
        fig.tight_layout()
        fig.savefig(p, dpi=160)
        plt.close(fig)
        written.append(p)

    # 1) Tempos (TDT/LDT/Total)
    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(series.x, series.tdt, marker="o", label="avg_tdt (switches)")
    ax.plot(series.x, series.ldt, marker="o", label="avg_ldt (links)")
    ax.plot(series.x, series.total, marker="o", label="avg_total")
    ax.set_title(f"Tempos de descoberta — {title}")
    ax.set_xlabel("Tamanho da topologia (num_nodes)")
    ax.set_ylabel("Tempo (s)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    save(fig, "times")

    # 2) CPU e Memória (médias)
    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(series.x, series.cpu, marker="o", label="avg_cpu (%)")
    ax.plot(series.x, series.mem, marker="o", label="avg_memory (%)")
    ax.set_title(f"Uso do controlador — {title}")
    ax.set_xlabel("Tamanho da topologia (num_nodes)")
    ax.set_ylabel("Uso (%)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    save(fig, "cpu_mem")

    # 3) Tráfego observado (tamanho total em bytes)
    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(series.x, series.lldp_len, marker="o", label="avg_lldp_len (bytes)")
    ax.plot(series.x, series.pkt_len, marker="o", label="avg_pkt_len (bytes)")
    ax.set_title(f"Volume de tráfego observado — {title}")
    ax.set_xlabel("Tamanho da topologia (num_nodes)")
    ax.set_ylabel("Bytes (média)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    save(fig, "traffic_bytes")

    # 4) Contagem de eventos/pacotes
    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(series.x, series.lldp_count, marker="o", label="avg_lldp_count")
    ax.plot(series.x, series.pkt_count, marker="o", label="avg_pkt_count")
    ax.set_title(f"Contagem de eventos observados — {title}")
    ax.set_xlabel("Tamanho da topologia (num_nodes)")
    ax.set_ylabel("Quantidade (média)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    save(fig, "traffic_count")

    # 5) Figura consolidada (4 subplots)
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    (ax1, ax2), (ax3, ax4) = axs

    ax1.plot(series.x, series.tdt, marker="o", label="avg_tdt")
    ax1.plot(series.x, series.ldt, marker="o", label="avg_ldt")
    ax1.plot(series.x, series.total, marker="o", label="avg_total")
    ax1.set_title("Tempos (s)")
    ax1.grid(True, alpha=0.25)
    ax1.legend()

    ax2.plot(series.x, series.cpu, marker="o", label="avg_cpu (%)")
    ax2.plot(series.x, series.mem, marker="o", label="avg_memory (%)")
    ax2.set_title("CPU/Mem (%)")
    ax2.grid(True, alpha=0.25)
    ax2.legend()

    ax3.plot(series.x, series.lldp_len, marker="o", label="avg_lldp_len (bytes)")
    ax3.plot(series.x, series.pkt_len, marker="o", label="avg_pkt_len (bytes)")
    ax3.set_title("Tráfego (bytes)")
    ax3.grid(True, alpha=0.25)
    ax3.legend()

    ax4.plot(series.x, series.lldp_count, marker="o", label="avg_lldp_count")
    ax4.plot(series.x, series.pkt_count, marker="o", label="avg_pkt_count")
    ax4.set_title("Contagens")
    ax4.grid(True, alpha=0.25)
    ax4.legend()

    fig.suptitle(f"Resumo — {title}", y=1.02)
    for ax in (ax1, ax2, ax3, ax4):
        ax.set_xlabel("num_nodes")
    save(fig, "summary")

    return written


def find_csv_files(base: Path) -> List[Path]:
    found: List[Path] = []
    for d in discover_test_dirs(base):
        csv_file = d / CSV_NAME
        if csv_file.exists():
            found.append(csv_file)
    legacy = base / LEGACY_OUTPUT_DIR
    if legacy.is_dir():
        found.extend(sorted(legacy.glob("*_average_topology_discovery_time.csv")))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerar gráficos a partir dos CSVs do SDN-BM.")
    parser.add_argument(
        "--input",
        help="CSV ou pasta de teste (ex.: output-onos-mesh). Se omitido, processa todas as pastas output-* e legado output/.",
        default=None,
    )
    parser.add_argument(
        "--outdir",
        help="Diretório de saída para PNGs. Padrão: mesma pasta do CSV.",
        default=None,
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent

    if args.input:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = base / input_path
        if input_path.is_dir():
            inputs = [input_path / CSV_NAME] if (input_path / CSV_NAME).exists() else []
        else:
            inputs = [input_path]
    else:
        inputs = find_csv_files(base)

    if not inputs:
        raise SystemExit("Nenhum CSV encontrado. Rode um teste ou informe --input.")

    all_written: List[Path] = []
    for csv_path in inputs:
        if not csv_path.exists():
            continue
        outdir = None
        if args.outdir:
            outdir = Path(args.outdir)
            if not outdir.is_absolute():
                outdir = base / outdir
        written = plot_csv(csv_path, outdir=outdir)
        all_written.extend(written)

    if not all_written:
        raise SystemExit("Nenhum gráfico gerado.")

    print(f"OK: {len(all_written)} gráfico(s) gerado(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

