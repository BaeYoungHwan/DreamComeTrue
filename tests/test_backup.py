import os

import pytest

from src.core.backup import backup_db


def test_backup_db_creates_timestamped_copy(tmp_path):
    db_path = tmp_path / "farm.db"
    db_path.write_bytes(b"fake sqlite content")
    backup_dir = tmp_path / "backups"

    backup_path = backup_db(str(db_path), str(backup_dir))

    assert os.path.exists(backup_path)
    with open(backup_path, "rb") as f:
        assert f.read() == b"fake sqlite content"
    assert backup_path.startswith(str(backup_dir))


def test_backup_db_raises_if_source_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup_db(str(tmp_path / "missing.db"), str(tmp_path / "backups"))
