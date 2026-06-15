
from __future__ import annotations

from .database import read_table, upsert_record, delete_record, query_df


def list_recursos():
    return read_table("recursos", "fecha_publicacion ASC, id DESC")


def save_recurso(data, record_id=None):
    return upsert_record("recursos", data, record_id)


def remove_recurso(record_id: int):
    delete_record("recursos", record_id)


def recursos_por_estado():
    return query_df("SELECT estado, COUNT(*) AS cantidad FROM recursos GROUP BY estado ORDER BY cantidad DESC")
