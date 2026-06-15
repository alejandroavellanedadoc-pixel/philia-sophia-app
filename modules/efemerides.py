
from __future__ import annotations

from .database import read_table, upsert_record, delete_record


def list_efemerides():
    return read_table("efemerides", "fecha ASC")


def save_efemeride(data, record_id=None):
    return upsert_record("efemerides", data, record_id)


def remove_efemeride(record_id: int):
    delete_record("efemerides", record_id)
