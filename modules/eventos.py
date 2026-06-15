
from __future__ import annotations

from .database import read_table, upsert_record, delete_record


def list_eventos():
    return read_table("eventos", "fecha ASC")


def save_evento(data, record_id=None):
    return upsert_record("eventos", data, record_id)


def remove_evento(record_id: int):
    delete_record("eventos", record_id)
