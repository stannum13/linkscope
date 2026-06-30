from __future__ import annotations

import math

import pytest

from photon_link_lab.units import db_to_linear, dbm_to_w, linear_to_db, w_to_dbm


def test_db_round_trip() -> None:
    for value_db in [-12.5, -3.0, 0.0, 7.25]:
        assert linear_to_db(db_to_linear(value_db)) == pytest.approx(value_db)


def test_dbm_watt_round_trip() -> None:
    for value_dbm in [-10.0, 0.0, 3.0]:
        assert w_to_dbm(dbm_to_w(value_dbm)) == pytest.approx(value_dbm)


def test_dbm_reference() -> None:
    assert dbm_to_w(0.0) == pytest.approx(1e-3)
    assert math.isfinite(w_to_dbm(1e-6))
