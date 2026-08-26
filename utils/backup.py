import os
import shutil
import glob
from datetime import datetime


def backup_database(db_path, backup_folder, keep_last=10):
    """
    Copies the database file to a timestamped backup.
    Automatically deletes old backups beyond 'keep_last' count.
    Returns the backup file path on success.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    os.makedirs(backup_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"pos_backup_{timestamp}.db"
    backup_path = os.path.join(backup_folder, backup_filename)

    shutil.copy2(db_path, backup_path)

    # Clean up old backups, keep only the most recent N
    _cleanup_old_backups(backup_folder, keep_last)

    return backup_path


def _cleanup_old_backups(backup_folder, keep_last):
    backups = sorted(
        glob.glob(os.path.join(backup_folder, "pos_backup_*.db")),
        key=os.path.getmtime,
        reverse=True
    )
    for old_backup in backups[keep_last:]:
        try:
            os.remove(old_backup)
        except Exception as e:
            print(f"Failed to remove old backup {old_backup}: {e}")


def get_backup_list(backup_folder):
    """Returns list of (filename, size_mb, modified_datetime), newest first."""
    if not os.path.exists(backup_folder):
        return []

    backups = []
    for path in sorted(
        glob.glob(os.path.join(backup_folder, "pos_backup_*.db")),
        key=os.path.getmtime,
        reverse=True
    ):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        modified = datetime.fromtimestamp(os.path.getmtime(path))
        backups.append({
            "filename": os.path.basename(path),
            "path": path,
            "size_mb": size_mb,
            "modified": modified
        })
    return backups


def restore_database(backup_path, db_path):
    """Restores a backup by overwriting the current database file.
    Creates a safety copy of the current db first, in case restore needs to be undone."""
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    safety_copy = db_path + ".before_restore"
    if os.path.exists(db_path):
        shutil.copy2(db_path, safety_copy)

    shutil.copy2(backup_path, db_path)
    return safety_copy