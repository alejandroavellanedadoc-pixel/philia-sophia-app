
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict

from .normalizer import load_curriculum_from_excel, analyze_workbook
from .database import insert_curriculum

SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm"}


def list_excel_files(data_dir: str | Path) -> List[Path]:
    data_dir = Path(data_dir)
    return sorted([p for p in data_dir.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS])


def import_excel_file(path: str | Path) -> int:
    records = load_curriculum_from_excel(path)
    return insert_curriculum(records)


def import_excel_folder(data_dir: str | Path) -> Dict[str, int]:
    results = {}
    for path in list_excel_files(data_dir):
        results[path.name] = import_excel_file(path)
    return results


def analyze_folder(data_dir: str | Path):
    rows = []
    for path in list_excel_files(data_dir):
        rows.extend(analyze_workbook(path))
    return rows
