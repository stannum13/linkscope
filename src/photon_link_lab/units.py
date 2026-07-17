"""Unit conversion helpers."""

from __future__ import annotations

import math


def db_to_linear(db: float) -> float:
    return 10.0 ** (db / 10.0)


def linear_to_db(value: float, floor: float = 1e-30) -> float:
    return 10.0 * math.log10(max(float(value), floor))


def dbm_to_w(dbm: float) -> float:
    return 1e-3 * 10.0 ** (dbm / 10.0)


def w_to_dbm(watts: float) -> float:
    return 10.0 * math.log10(max(watts, 1e-30) / 1e-3)
