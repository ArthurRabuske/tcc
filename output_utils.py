"""Utilitários para diretórios de saída dos experimentos SDN-BM."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

CONTROLLERS = ("onos", "odl", "floodlight")
TOPOLOGIES = ("mesh", "star", "leaf-spine", "3-tier")

CSV_NAME = "average_topology_discovery_time.csv"
REPORT_NAME = "topology_discovery_time_report.txt"
TOPO_DISC_NAME = "topo_disc.txt"
LINK_LENGTH_NAME = "link_length.txt"

BENCHMARK_DIR_NAME = "output-benchmarking"
LEGACY_OUTPUT_DIR = "output"


def output_dir_name(controller: str, topology: str) -> str:
    return f"output-{controller}-{topology}"


def get_output_dir(controller: str, topology: str, base: Optional[Path] = None) -> Path:
    root = base or Path.cwd()
    return root / output_dir_name(controller, topology)


def get_active_output_dir(base: Optional[Path] = None) -> Path:
    env = os.environ.get("SDNBM_OUTPUT_DIR")
    if env:
        return Path(env)
    root = base or Path.cwd()
    return root / LEGACY_OUTPUT_DIR


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


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
    rest = dirname[len("output-") :]
    for ctrl in CONTROLLERS:
        prefix = f"{ctrl}-"
        if rest.startswith(prefix):
            return ctrl, rest[len(prefix) :]
    return None, None


def discover_test_dirs(base: Optional[Path] = None) -> List[Path]:
    root = base or Path.cwd()
    dirs: List[Path] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        if p.name == BENCHMARK_DIR_NAME or p.name == LEGACY_OUTPUT_DIR:
            continue
        ctrl, topo = parse_test_dir_name(p.name)
        if ctrl and topo and (p / CSV_NAME).exists():
            dirs.append(p)
    return sorted(dirs)


def label_from_dir(test_dir: Path) -> str:
    ctrl, topo = parse_test_dir_name(test_dir.name)
    if ctrl and topo:
        return f"{ctrl} / {topo}"
    return test_dir.name
