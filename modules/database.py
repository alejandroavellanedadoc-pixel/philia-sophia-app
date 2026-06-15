
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Iterable, List, Optional

import pandas as pd

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"
DB_PATH = DATA_DIR / "philia_sophia.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: Optional[Path] = None) -> None:
    con = get_connection(db_path)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS curriculum (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            sheet_name TEXT,
            nivel TEXT,
            unidad TEXT,
            area TEXT,
            mes TEXT,
            mes_numero INTEGER,
            semana_mes TEXT,
            semana_lectiva TEXT,
            semana_calendario TEXT,
            estado_calendario TEXT,
            eje TEXT,
            contenido TEXT,
            foco TEXT,
            contexto TEXT,
            momento1 TEXT,
            momento2 TEXT,
            momento3 TEXT,
            momento4 TEXT,
            observaciones TEXT,
            original_json TEXT,
            row_hash TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS efemerides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            nivel_sugerido TEXT,
            area TEXT,
            ideas_recursos TEXT,
            prioridad TEXT DEFAULT 'Media',
            estado TEXT DEFAULT 'Pendiente',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            nombre TEXT NOT NULL,
            tipo TEXT,
            descripcion TEXT,
            responsables TEXT,
            lugar TEXT,
            nivel TEXT,
            estado TEXT DEFAULT 'Pendiente',
            observaciones TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            nivel TEXT,
            unidad TEXT,
            area TEXT,
            mes TEXT,
            semana_lectiva TEXT,
            semana_calendario TEXT,
            efemeride TEXT,
            tipo_recurso TEXT,
            estado TEXT DEFAULT 'Idea',
            responsable TEXT,
            fecha_publicacion TEXT,
            observaciones TEXT,
            curriculum_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(curriculum_id) REFERENCES curriculum(id) ON DELETE SET NULL
        )
        """
    )
    con.commit()
    con.close()


def table_count(table: str) -> int:
    con = get_connection()
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    return int(count)


def insert_curriculum(records: Iterable[Dict]) -> int:
    init_db()
    con = get_connection()
    inserted = 0
    fields = [
        "source_file", "sheet_name", "nivel", "unidad", "area", "mes", "mes_numero", "semana_mes",
        "semana_lectiva", "semana_calendario", "estado_calendario", "eje", "contenido", "foco",
        "contexto", "momento1", "momento2", "momento3", "momento4", "observaciones",
        "original_json", "row_hash",
    ]
    sql = f"""
        INSERT OR IGNORE INTO curriculum ({', '.join(fields)})
        VALUES ({', '.join(['?'] * len(fields))})
    """
    for rec in records:
        before = con.total_changes
        con.execute(sql, [rec.get(f, "") for f in fields])
        if con.total_changes > before:
            inserted += 1
    con.commit()
    con.close()
    return inserted


def query_df(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
    con = get_connection()
    df = pd.read_sql_query(sql, con, params=params or ())
    con.close()
    return df


def read_table(table: str, order_by: str = "id DESC") -> pd.DataFrame:
    return query_df(f"SELECT * FROM {table} ORDER BY {order_by}")


def upsert_record(table: str, data: Dict, record_id: Optional[int] = None) -> int:
    init_db()
    con = get_connection()
    now = datetime.now().isoformat(timespec="seconds")
    data = {k: ("" if v is None else str(v)) for k, v in data.items()}
    data["updated_at"] = now
    if record_id:
        fields = list(data.keys())
        set_clause = ", ".join([f"{k} = ?" for k in fields])
        con.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", [data[k] for k in fields] + [record_id])
        new_id = int(record_id)
    else:
        data["created_at"] = now
        fields = list(data.keys())
        con.execute(
            f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})",
            [data[k] for k in fields],
        )
        new_id = int(con.execute("SELECT last_insert_rowid()").fetchone()[0])
    con.commit()
    con.close()
    return new_id


def delete_record(table: str, record_id: int) -> None:
    con = get_connection()
    con.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
    con.commit()
    con.close()


def seed_efemerides() -> None:
    if table_count("efemerides") > 0:
        return
    efemerides = [
        ("2026-03-24", "Día Nacional de la Memoria por la Verdad y la Justicia", "Propuestas de memoria, identidad, democracia y ciudadanía.", "Primario / Secundario", "Lengua / Ciencias Sociales", "Lecturas breves, línea de tiempo, mural de palabras", "Alta"),
        ("2026-04-02", "Día del Veterano y de los Caídos en la Guerra de Malvinas", "Efeméride nacional para trabajar memoria histórica y territorio.", "Primario / Secundario", "Lengua / Matemática", "Mapa, lectura de testimonios, problemas con distancias", "Alta"),
        ("2026-05-01", "Día Internacional del Trabajador", "Fecha para abordar oficios, comunidad y derechos.", "Inicial / Primario", "Lengua / Matemática", "Entrevistas, conteo de herramientas, afiches", "Media"),
        ("2026-05-25", "Día de la Revolución de Mayo", "Fecha patria central del calendario escolar argentino.", "Inicial / Primario / Secundario", "Lengua / Matemática", "Historietas, recetas coloniales, problemas de compra-venta", "Alta"),
        ("2026-06-17", "Paso a la Inmortalidad del General Martín Miguel de Güemes", "Trabajo sobre liderazgo, territorio y defensa nacional.", "Primario / Secundario", "Lengua", "Biografía breve, lectura guiada, infografía", "Media"),
        ("2026-06-20", "Día de la Bandera", "Efeméride central para identidad nacional y producción simbólica.", "Inicial / Primario", "Lengua / Matemática", "Secuencia con colores, formas, lectura y producción escrita", "Alta"),
        ("2026-07-09", "Día de la Independencia", "Fecha patria para abordar independencia, acta y participación.", "Inicial / Primario / Secundario", "Lengua / Matemática", "Acta escolar, línea de tiempo, problemas con fechas", "Alta"),
        ("2026-08-17", "Paso a la Inmortalidad del General José de San Martín", "Efeméride para trabajar trayectoria, cruce y proyecto colectivo.", "Primario / Secundario", "Lengua / Matemática", "Mapa, cronología, medición de distancias", "Alta"),
        ("2026-09-11", "Día del Maestro", "Reconocimiento a docentes y escuela pública.", "Inicial / Primario", "Lengua", "Cartas, acrósticos, entrevistas", "Media"),
        ("2026-09-21", "Día del Estudiante", "Fecha institucional para convivencia y participación.", "Primario / Secundario", "Lengua / Matemática", "Encuestas, gráficos, mensajes de convivencia", "Media"),
        ("2026-10-12", "Día del Respeto a la Diversidad Cultural", "Trabajo sobre diversidad, interculturalidad y memoria.", "Inicial / Primario / Secundario", "Lengua / Ciencias Sociales", "Relatos, vocabularios, mapas culturales", "Alta"),
        ("2026-11-10", "Día de la Tradición", "Fecha para trabajar identidad cultural, oralidad y prácticas comunitarias.", "Inicial / Primario", "Lengua / Matemática", "Coplas, recetas, juegos tradicionales, conteo", "Media"),
    ]
    for fecha, nombre, descripcion, nivel, area, ideas, prioridad in efemerides:
        upsert_record("efemerides", {
            "fecha": fecha, "nombre": nombre, "descripcion": descripcion,
            "nivel_sugerido": nivel, "area": area, "ideas_recursos": ideas,
            "prioridad": prioridad, "estado": "Pendiente",
        })
