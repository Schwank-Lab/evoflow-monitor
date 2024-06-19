import os
import subprocess
import sys
from datetime import datetime
from evoflow_utils.config import Config


def mount_usb(device, mount_point):
    if not os.path.ismount(mount_point):
        os.makedirs(mount_point, exist_ok=True)
        result = subprocess.run(
            ["mount", device, mount_point], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Failed to mount USB device: {device}")
            print(result.stderr)
            sys.exit(1)
    else:
        print(f"Device {device} is already mounted at {mount_point}")


def unmount_usb(mount_point):
    if os.path.ismount(mount_point):
        result = subprocess.run(["umount", mount_point], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to unmount USB device from {mount_point}")
            print(result.stderr)
            sys.exit(1)
    else:
        print(f"No device is mounted at {mount_point}")


def backup_postgres(db_host, db_port, db_name, db_user, db_password, backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d%H%M")
    backup_file = os.path.join(backup_dir, f"{db_name}-{date_str}.sql")

    dump_command = [
        "pg_dump",
        "-h",
        db_host,
        "-p",
        db_port,
        "-U",
        db_user,
        "-F",
        "c",
        "-b",
        "-v",
        "-f",
        backup_file,
        db_name,
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = db_password

    result = subprocess.run(dump_command, env=env, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Backup successful: {backup_file}")
    else:
        print("Backup failed")
        print(result.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) != 6:
        print(
            "Usage: python backup_postgres_to_usb.py <DB_HOST> <DB_PORT> <DB_NAME> <DB_USER> <USB_DEVICE>"
        )
        sys.exit(1)

    db_host = Config.DB_HOST
    db_port = Config.DB_PORT
    db_name = Config.DB_NAME
    db_user = Config.DB_USER
    db_password = Config.DB_PASS

    mount_point = "/mnt/usb"
    backup_dir = os.path.join(mount_point, "Backups")
    usb_device = "/dev/sda1"

    try:
        mount_usb(usb_device, mount_point)
        backup_postgres(db_host, db_port, db_name, db_user, db_password, backup_dir)
    finally:
        unmount_usb(mount_point)


if __name__ == "__main__":
    main()
