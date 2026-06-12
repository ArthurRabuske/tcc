#!/usr/bin/env python3
"""Gera gráficos comparativos a partir das pastas output-<controlador>-<topologia>."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from output_utils import BENCHMARK_DIR_NAME, CSV_NAME, discover_test_dirs, parse_test_dir_name
from plot_results import Series, read_average_csv


def _group_by_topology(test_dirs: List[Path]) -> Dict[str, List[Path]]:
    grouped: Dict[str, List[Path]] = {}
    for d in test_dirs:
        ctrl, topo = parse_test_dir_name(d.name)
        if not topo:
            continue
        grouped.setdefault(topo, []).append(d)
    return grouped


def _controller_label(test_dir: Path) -> str:
    ctrl, _ = parse_test_dir_name(test_dir.name)
    return (ctrl or test_dir.name).upper()


def plot_topology_comparison(
    topology: str,
    test_dirs: List[Path],
    outdir: Path,
) -> List[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    series_list: List[Tuple[str, Series]] = []
    for d in sorted(test_dirs, key=lambda p: p.name):
        csv_file = d / CSV_NAME
        if not csv_file.exists():
            continue
        series_list.append((_controller_label(d), read_average_csv(csv_file)))

    if len(series_list) < 2:
        return []

    outdir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    def save(fig, filename: str) -> None:
        path = outdir / filename
        fig.tight_layout()
        fig.savefig(path, dpi=160)
        plt.close(fig)
        written.append(path)

    # Tempo total
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (label, s) in enumerate(series_list):
        ax.plot(s.x, s.total, marker="o", label=f"{label} — avg_total", color=colors[i % len(colors)])
    ax.set_title(f"Comparativo — tempo total de descoberta ({topology})")
    ax.set_xlabel("Tamanho da topologia (num_nodes)")
    ax.set_ylabel("Tempo (s)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    save(fig, f"compare_{topology}_avg_total.png")

    # TDT e LDT
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    for i, (label, s) in enumerate(series_list):
        c = colors[i % len(colors)]
        ax1.plot(s.x, s.tdt, marker="o", label=label, color=c)
        ax2.plot(s.x, s.ldt, marker="o", label=label, color=c)
    ax1.set_title("TDT (switches)")
    ax2.set_title("LDT (links)")
    for ax in (ax1, ax2):
        ax.set_xlabel("num_nodes")
        ax.set_ylabel("Tempo (s)")
        ax.grid(True, alpha=0.25)
        ax.legend()
    fig.suptitle(f"Comparativo TDT/LDT — {topology}", y=1.02)
    save(fig, f"compare_{topology}_tdt_ldt.png")

    # CPU e memória
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    for i, (label, s) in enumerate(series_list):
        c = colors[i % len(colors)]
        ax1.plot(s.x, s.cpu, marker="o", label=label, color=c)
        ax2.plot(s.x, s.mem, marker="o", label=label, color=c)
    ax1.set_title("CPU (%)")
    ax2.set_title("Memória (%)")
    for ax in (ax1, ax2):
        ax.set_xlabel("num_nodes")
        ax.set_ylabel("Uso (%)")
        ax.grid(True, alpha=0.25)
        ax.legend()
    fig.suptitle(f"Comparativo CPU/Mem — {topology}", y=1.02)
    save(fig, f"compare_{topology}_cpu_mem.png")

    # Resumo consolidado
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    metrics = [
        (axs[0, 0], "total", "avg_total (s)"),
        (axs[0, 1], "tdt", "avg_tdt (s)"),
        (axs[1, 0], "cpu", "avg_cpu (%)"),
        (axs[1, 1], "mem", "avg_memory (%)"),
    ]
    for ax, attr, ylabel in metrics:
        for i, (label, s) in enumerate(series_list):
            ax.plot(s.x, getattr(s, attr), marker="o", label=label, color=colors[i % len(colors)])
        ax.set_xlabel("num_nodes")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=8)
    fig.suptitle(f"Resumo comparativo — {topology}", y=1.02)
    save(fig, f"compare_{topology}_summary.png")

    return written


def run_benchmark_plots(base: Optional[Path] = None, outdir: Optional[Path] = None) -> List[Path]:
    root = base or Path.cwd()
    benchmark_dir = outdir or (root / BENCHMARK_DIR_NAME)
    test_dirs = discover_test_dirs(root)
    grouped = _group_by_topology(test_dirs)

    all_written: List[Path] = []
    for topo, dirs in sorted(grouped.items()):
        if len(dirs) < 2:
            continue
        written = plot_topology_comparison(topo, dirs, benchmark_dir)
        all_written.extend(written)
    return all_written


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerar gráficos comparativos ONOS x ODL por topologia.")
    parser.add_argument("--outdir", default=BENCHMARK_DIR_NAME, help="Pasta de saída dos comparativos.")
    args = parser.parse_args()

    base = Path.cwd()
    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = base / outdir

    written = run_benchmark_plots(base, outdir)
    if not written:
        print("Nenhum comparativo gerado. É necessário ter pelo menos 2 pastas output-<ctrl>-<topo> com CSV para a mesma topologia.")
        return 1

    print(f"OK: {len(written)} gráfico(s) comparativo(s) em: {outdir}")
    for p in written:
        print(f"  - {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
