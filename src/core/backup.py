"""SQLite DB 파일 자동 백업."""
import os
import shutil
from datetime import datetime


def backup_db(db_path: str, backup_dir: str = "backups") -> str:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"백업할 DB 파일이 없습니다: {db_path}")

    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = os.path.splitext(os.path.basename(db_path))[0]
    backup_path = os.path.join(backup_dir, f"{stem}_{timestamp}.db")
    shutil.copy2(db_path, backup_path)
    return backup_path
