import pytest

from src.core.db import get_connection, init_db
from src.core.migrations import run_migrations
from src.inventory.items import create_item
from src.inventory.stock import record_transaction
from src.inventory.variants import (
    VariantInUseError,
    create_variant,
    delete_variant,
    get_variant,
    list_variants,
    update_variant,
)


def _conn_with_item(tmp_path, name="블루베리", unit="kg"):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    run_migrations(conn)
    item_id = create_item(conn, name, unit)
    return conn, item_id


def test_create_variant_and_get_variant(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    variant_id = create_variant(conn, item_id, size="특", weight="1kg", default_price=15000)

    variant = get_variant(conn, variant_id)
    conn.close()

    assert variant["item_id"] == item_id
    assert variant["size"] == "특"
    assert variant["weight"] == "1kg"
    assert variant["default_price"] == 15000


def test_list_variants_returns_all_variants_for_item(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    create_variant(conn, item_id, size="특", weight="1kg", default_price=15000)
    create_variant(conn, item_id, size="특", weight="500g", default_price=8000)

    variants = list_variants(conn, item_id)
    conn.close()

    assert len(variants) == 2
    assert {(v["size"], v["weight"]) for v in variants} == {
        ("특", "1kg"),
        ("특", "500g"),
    }


def test_update_variant_changes_price(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    variant_id = create_variant(conn, item_id, size="특", weight="1kg", default_price=15000)

    update_variant(conn, variant_id, size="특", weight="1kg", default_price=16000)
    variant = get_variant(conn, variant_id)
    conn.close()

    assert variant["default_price"] == 16000


def test_delete_variant_removes_row(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    variant_id = create_variant(conn, item_id, size="특", weight="1kg", default_price=15000)

    delete_variant(conn, variant_id)
    variant = get_variant(conn, variant_id)
    conn.close()

    assert variant is None


def test_delete_variant_raises_when_transactions_exist(tmp_path):
    conn, item_id = _conn_with_item(tmp_path)
    variant_id = create_variant(conn, item_id, size="특", weight="1kg", default_price=15000)
    record_transaction(conn, item_id, "harvest", 10, variant_id=variant_id)

    with pytest.raises(VariantInUseError):
        delete_variant(conn, variant_id)

    variant = get_variant(conn, variant_id)
    conn.close()

    assert variant is not None
