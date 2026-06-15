from __future__ import annotations

import re
import pandas as pd
from .database import query_df

MESES_ORDEN = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
NIVELES_ORDEN = ["Nivel Inicial", "Nivel Primario", "Nivel Secundario - Ciclo Básico"]
AREAS_ORDEN = [
    "Lengua / Prácticas del Lenguaje",
    "Matemática",
    "Matemática y Geometría",
]


def _clean(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat", ""}:
        return ""
    return text


def _first_number(text: str) -> int | None:
    match = re.search(r"\d+", str(text))
    return int(match.group(0)) if match else None


def _ordered_by_reference(values: list[str], reference: list[str]) -> list[str]:
    known = [x for x in reference if x in values]
    unknown = sorted([x for x in values if x not in reference], key=lambda x: x.lower())
    return known + unknown


def _natural_key(value: str):
    number = _first_number(value)
    lower = value.lower()
    if "sala" in lower:
        group = 0
    elif "grado" in lower:
        group = 1
    elif "año" in lower or "ano" in lower:
        group = 2
    else:
        group = 9
    return (group, number if number is not None else 9999, lower)


def get_curriculum() -> pd.DataFrame:
    return query_df(
        """
        SELECT * FROM curriculum
        ORDER BY mes_numero, CAST(NULLIF(semana_lectiva, '') AS INTEGER), nivel, unidad, area
        """
    )


def filter_curriculum(nivel=None, unidad=None, area=None, mes=None, semana_lectiva=None, semana_calendario=None) -> pd.DataFrame:
    clauses = []
    params = []
    for field, value in [
        ("nivel", nivel), ("unidad", unidad), ("area", area), ("mes", mes),
        ("semana_lectiva", semana_lectiva), ("semana_calendario", semana_calendario)
    ]:
        if value and value != "Todos":
            clauses.append(f"{field} = ?")
            params.append(str(value))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return query_df(
        f"""
        SELECT * FROM curriculum {where}
        ORDER BY mes_numero, CAST(NULLIF(semana_lectiva, '') AS INTEGER), nivel, unidad, area
        """,
        tuple(params),
    )


def unique_values(df: pd.DataFrame, column: str):
    """Devuelve valores únicos ordenados pedagógicamente.

    Evita el orden alfabético que desacomoda los meses y el orden textual que
    pone las semanas como 1, 10, 11, 2. También oculta valores vacíos o guiones.
    """
    if df.empty or column not in df.columns:
        return []

    raw_values = [_clean(x) for x in df[column].dropna().unique()]
    values = [x for x in raw_values if x and x not in {"—", "-", "--"}]

    if column == "mes":
        return _ordered_by_reference(values, MESES_ORDEN)
    if column == "nivel":
        return _ordered_by_reference(values, NIVELES_ORDEN)
    if column == "area":
        return _ordered_by_reference(values, AREAS_ORDEN)
    if "semana" in column:
        return sorted(values, key=lambda x: (_first_number(x) is None, _first_number(x) or 9999, x.lower()))
    if column == "unidad":
        return sorted(values, key=_natural_key)

    return sorted(values, key=lambda x: x.lower())
