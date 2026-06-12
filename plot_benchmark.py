#!/usr/bin/env python3
"""Gera gráficos comparativos a partir das pastas output-<controlador>-<topologia>/."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional, Tuple

from output_utils import (
    CSV_NAME,
    controller_from_run_dir,
    create_benchmark_run_dir,
    discover_controller_runs_for_topology,
)
from plot_results import Series, read_average_csv


def plot_topology_comparison(
    topology: str,
    run_dirs: List[Path],
    outdir: Path,
) -> List[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    series_list: List[Tuple[str, Series]] = []
    for run_dir in sorted(run_dirs, key=lambda p: p.parent.name):
        csv_file = run_dir / CSV_NAME
        if not csv_file.exists():
            continue
        label = controller_from_run_dir(run_dir)
        series_list.append((label, read_average_csv(csv_file)))

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

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (label, s) in enumerate(series_list):
        ax.plot(s.x, s.total, marker="o", label=f"{label} — avg_total", color=colors[i % len(colors)])
    ax.set_title(f"Comparativo — tempo total de descoberta ({topology})")
    ax.set_xlabel("Tamanho da topologia (num_nodes)")
    ax.set_ylabel("Tempo (s)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    save(fig, "compare_avg_total.png")

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
    save(fig, "compare_tdt_ldt.png")

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
    save(fig, "compare_cpu_mem.png")

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
    save(fig, "compare_summary.png")

    return written


def run_benchmark_for_topology(
    topology: str,
    base: Optional[Path] = None,
) -> Tuple[List[Path], Optional[Path]]:
    root = base or Path.cwd()
    run_dirs = discover_controller_runs_for_topology(topology, root)
    if len(run_dirs) < 2:
        return [], None

    outdir = create_benchmark_run_dir(topology, root)
    written = plot_topology_comparison(topology, run_dirs, outdir)
    return written, outdir


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerar gráficos comparativos ONOS x ODL por topologia.")
    parser.add_argument(
        "-t", "--topology",
        required=True,
        choices=["mesh", "leaf-spine", "3-tier"],
        help="Topologia a comparar.",
    )
    args = parser.parse_args()

    written, outdir = run_benchmark_for_topology(args.topology, Path.cwd())
    if not written or outdir is None:
        print(
            f"Nenhum comparativo gerado para '{args.topology}'. "
            "É necessário ter pelo menos 2 controladores testados nessa topologia."
        )
        return 1

    print(f"OK: {len(written)} gráfico(s) comparativo(s) em: {outdir}")
    for p in written:
        print(f"  - {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
