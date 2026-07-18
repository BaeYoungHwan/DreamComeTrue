import sqlite3

import pytest

from src.core.db import get_connection, init_db
from src.core.migrations import run_migrations
from src.inventory.items import create_item
from src.sales.sales import record_sale
from src.settlement.channels import (
    ChannelInUseError,
    ChannelNameConflictError,
    create_channel,
    delete_channel,
    get_channel,
    list_channels,
    update_channel,
)


def _conn(tmp_path):
    conn = get_connection(str(tmp_path / "farm.db"))
    init_db(conn)
    run_migrations(conn)
    return conn


def test_create_channel_and_get_channel(tmp_path):
    conn = _conn(tmp_path)

    channel_id = create_channel(conn, "모현점", "consignment", 11.11)
    channel = get_channel(conn, channel_id)
    conn.close()

    assert channel["name"] == "모현점"
    assert channel["channel_type"] == "consignment"
    assert channel["commission_rate"] == 11.11


def test_create_channel_rejects_invalid_type(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError):
        create_channel(conn, "모현점", "wholesale", 10)
    conn.close()


def test_create_channel_rejects_negative_commission_rate(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError):
        create_channel(conn, "모현점", "consignment", -1)
    conn.close()


def test_create_channel_rejects_duplicate_name(tmp_path):
    conn = _conn(tmp_path)
    create_channel(conn, "모현점", "consignment", 10)

    with pytest.raises(ChannelNameConflictError):
        create_channel(conn, "모현점", "consignment", 12)
    conn.close()


def test_list_channels_orders_by_name(tmp_path):
    conn = _conn(tmp_path)
    create_channel(conn, "평화점", "consignment", 10)
    create_channel(conn, "어양점", "consignment", 10)

    names = [c["name"] for c in list_channels(conn)]
    conn.close()

    assert names == ["어양점", "평화점"]


def test_update_channel_changes_fields(tmp_path):
    conn = _conn(tmp_path)
    channel_id = create_channel(conn, "모현점", "consignment", 10)

    update_channel(conn, channel_id, "모현점", "consignment", 11.11)
    channel = get_channel(conn, channel_id)
    conn.close()

    assert channel["commission_rate"] == 11.11


def test_update_channel_rejects_duplicate_name(tmp_path):
    conn = _conn(tmp_path)
    create_channel(conn, "모현점", "consignment", 10)
    other_id = create_channel(conn, "어양점", "consignment", 10)

    with pytest.raises(ChannelNameConflictError):
        update_channel(conn, other_id, "모현점", "consignment", 10)
    conn.close()


def test_delete_channel_removes_row(tmp_path):
    conn = _conn(tmp_path)
    channel_id = create_channel(conn, "모현점", "consignment", 10)

    delete_channel(conn, channel_id)
    channel = get_channel(conn, channel_id)
    conn.close()

    assert channel is None


def test_delete_channel_raises_when_sales_exist(tmp_path):
    conn = _conn(tmp_path)
    channel_id = create_channel(conn, "모현점", "consignment", 10)
    item_id = create_item(conn, "블루베리", "kg")
    from src.inventory.stock import record_transaction

    record_transaction(conn, item_id, "harvest", 10)
    record_sale(conn, item_id, "모현점", 5, 12500, channel_id=channel_id)

    with pytest.raises(ChannelInUseError):
        delete_channel(conn, channel_id)
    conn.close()
