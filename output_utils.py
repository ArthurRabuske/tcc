"""Utilitários para diretórios de saída dos experimentos SDN-BM."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

CONTROLLERS = ("onos", "odl", "floodlight")
TOPOLOGIES = ("mesh", "star", "leaf-spine", "3-tier")

CSV_NAME = "average_topology_discovery_time.csv"
REPORT_NAME = "topology_discovery_time_report.txt"
TOPO_DISC_NAME = "topo_disc.txt"
LINK_LENGTH_NAME = "link_length.txt"

LEGACY_OUTPUT_DIR = "output"
RUN_TIMESTAMP_FMT = "%Y-%m-%d_%H-%M-%S"


def output_dir_name(controller: str, topology: str) -> str:
    return f"output-{controller}-{topology}"


def benchmark_dir_name(topology: str) -> str:
    return f"output-benchmarking-{topology}"


def get_output_dir(controller: str, topology: str, base: Optional[Path] = None) -> Path:
    root = base or Path.cwd()
    return root / output_dir_name(controller, topology)


def get_benchmark_dir(topology: str, base: Optional[Path] = None) -> Path:
    root = base or Path.cwd()
    return root / benchmark_dir_name(topology)


def get_active_output_dir(base: Optional[Path] = None) -> Path:
    env = os.environ.get("SDNBM_OUTPUT_DIR")
    if env:
        return Path(env)
    root = base or Path.cwd()
    return root / LEGACY_OUTPUT_DIR


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_run_timestamp() -> str:
    return datetime.now().strftime(RUN_TIMESTAMP_FMT)


def create_run_dir(controller: str, topology: str, base: Optional[Path] = None) -> Path:
    """Cria pasta única por execução: output-<ctrl>-<topo>/<timestamp>/."""
    test_base = get_output_dir(controller, topology, base)
    ensure_output_dir(test_base)
    run_dir = test_base / new_run_timestamp()
    ensure_output_dir(run_dir)
    return run_dir


def create_benchmark_run_dir(topology: str, base: Optional[Path] = None) -> Path:
    """Cria pasta única por benchmarking: output-benchmarking-<topo>/<timestamp>/."""
    bench_base = get_benchmark_dir(topology, base)
    ensure_output_dir(bench_base)
    run_dir = bench_base / new_run_timestamp()
    ensure_output_dir(run_dir)
    return run_dir


def csv_path(output_dir: Path) -> Path:
    return output_dir / CSV_NAME


def report_path(output_dir: Path) -> Path:
    return output_dir / REPORT_NAME


def topo_disc_path(output_dir: Path) -> Path:
    return output_dir / TOPO_DISC_NAME


def link_length_path(output_dir: Path) -> Path:
    return output_dir / LINK_LENGTH_NAME


def parse_test_dir_name(dirname: str) -> Tuple[Optional[str], Optional[str]]:
    if not dirname.startswith("output-"):
        return None, None
    if dirname.startswith("output-benchmarking"):
        return None, None
    rest = dirname[len("output-") :]
    for ctrl in CONTROLLERS:
        prefix = f"{ctrl}-"
        if rest.startswith(prefix):
            return ctrl, rest[len(prefix) :]
    return None, None


def is_benchmark_dir(name: str) -> bool:
    return name.startswith("output-benchmarking")


def list_runs_with_csv(test_base: Path) -> List[Path]:
    """Lista todas as execuções com CSV dentro de output-<ctrl>-<topo>/."""
    runs = sorted(
        p for p in test_base.iterdir()
        if p.is_dir() and (p / CSV_NAME).exists()
    )
    if (test_base / CSV_NAME).exists():
        runs = [test_base] + runs
    return runs


def get_latest_run_with_csv(test_base: Path) -> Optional[Path]:
    runs = list_runs_with_csv(test_base)
    if not runs:
        return None
    subdirs = [r for r in runs if r != test_base]
    if subdirs:
        return subdirs[-1]
    return runs[-1]


def discover_test_base_dirs(base: Optional[Path] = None) -> List[Path]:
    root = base or Path.cwd()
    dirs: List[Path] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        if p.name == LEGACY_OUTPUT_DIR or is_benchmark_dir(p.name):
            continue
        ctrl, topo = parse_test_dir_name(p.name)
        if ctrl and topo:
            dirs.append(p)
    return sorted(dirs)


def discover_all_run_dirs(base: Optional[Path] = None) -> List[Path]:
    """Todas as execuções individuais (subpastas com timestamp)."""
    runs: List[Path] = []
    for test_base in discover_test_base_dirs(base):
        runs.extend(list_runs_with_csv(test_base))
    return sorted(runs)


def find_all_csv_files(base: Optional[Path] = None) -> List[Path]:
    csvs = [run_dir / CSV_NAME for run_dir in discover_all_run_dirs(base)]
    legacy = (base or Path.cwd()) / LEGACY_OUTPUT_DIR
    if legacy.is_dir():
        csvs.extend(sorted(legacy.glob("*_average_topology_discovery_time.csv")))
    return sorted({c for c in csvs if c.exists()})


def discover_test_dirs(base: Optional[Path] = None) -> List[Path]:
    """Compatibilidade: retorna a execução mais recente de cada output-<ctrl>-<topo>/."""
    latest: List[Path] = []
    for test_base in discover_test_base_dirs(base):
        run = get_latest_run_with_csv(test_base)
        if run:
            latest.append(run)
    return latest


def discover_controller_runs_for_topology(
    topology: str,
    base: Optional[Path] = None,
    use_latest: bool = True,
) -> List[Path]:
    """
    Retorna pastas de execução com CSV para uma topologia.
    Por padrão usa a execução mais recente de cada controlador.
    """
    root = base or Path.cwd()
    runs: List[Path] = []
    for test_base in discover_test_base_dirs(root):
        ctrl, topo = parse_test_dir_name(test_base.name)
        if topo != topology:
            continue
        if use_latest:
            run = get_latest_run_with_csv(test_base)
            if run:
                runs.append(run)
        else:
            runs.extend(list_runs_with_csv(test_base))
    return sorted(runs, key=lambda p: p.parent.name)


def label_from_dir(test_dir: Path) -> str:
    run_name = test_dir.name
    parent = test_dir.parent
    ctrl, topo = parse_test_dir_name(parent.name)
    if ctrl and topo:
        if (parent / CSV_NAME).exists() and test_dir == parent:
            return f"{ctrl} / {topo}"
        return f"{ctrl} / {topo} ({run_name})"
    ctrl, topo = parse_test_dir_name(test_dir.name)
    if ctrl and topo:
        return f"{ctrl} / {topo}"
    return test_dir.name


def controller_from_run_dir(run_dir: Path) -> str:
    ctrl, _ = parse_test_dir_name(run_dir.parent.name)
    return (ctrl or run_dir.parent.name).upper()
