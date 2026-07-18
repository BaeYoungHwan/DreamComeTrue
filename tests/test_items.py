from src.core.db import get_connection, init_db
from src.inventory.items import (
    create_item,
    delete_item,
    get_item,
    list_items,
    update_custom_attributes,
)


def _conn(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    return conn


def test_create_item_and_get_item(tmp_path):
    conn = _conn(tmp_path)
    item_id = create_item(conn, "상추", "kg")

    item = get_item(conn, item_id)
    conn.close()

    assert item["name"] == "상추"
    assert item["unit"] == "kg"
    assert item["custom_attributes"] == {}


def test_create_item_with_custom_attributes(tmp_path):
    conn = _conn(tmp_path)
    item_id = create_item(conn, "토마토", "박스", {"당도": "10 브릭스"})

    item = get_item(conn, item_id)
    conn.close()

    assert item["custom_attributes"] == {"당도": "10 브릭스"}


def test_list_items_orders_by_name(tmp_path):
    conn = _conn(tmp_path)
    create_item(conn, "토마토", "박스")
    create_item(conn, "상추", "kg")

    names = [item["name"] for item in list_items(conn)]
    conn.close()

    assert names == ["상추", "토마토"]


def test_update_custom_attributes_can_add_and_remove_fields(tmp_path):
    conn = _conn(tmp_path)
    item_id = create_item(conn, "상추", "kg", {"당도": "5"})

    update_custom_attributes(conn, item_id, {"당도": "5", "재배방식": "노지"})
    item = get_item(conn, item_id)
    assert item["custom_attributes"] == {"당도": "5", "재배방식": "노지"}

    update_custom_attributes(conn, item_id, {"재배방식": "노지"})
    item = get_item(conn, item_id)
    conn.close()

    assert item["custom_attributes"] == {"재배방식": "노지"}


def test_delete_item_removes_row(tmp_path):
    conn = _conn(tmp_path)
    item_id = create_item(conn, "상추", "kg")

    delete_item(conn, item_id)
    item = get_item(conn, item_id)
    conn.close()

    assert item is None


def test_get_item_returns_none_for_missing_id(tmp_path):
    conn = _conn(tmp_path)
    item = get_item(conn, 999)
    conn.close()

    assert item is None
