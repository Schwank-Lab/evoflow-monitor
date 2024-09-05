import subprocess
from pathlib import Path
import argparse 
from datetime import datetime

from evoflow_utils.config import Config


def backup_postgres_db(backup_path: Path):
    # Use PGPASSWORD to avoid interactive password prompt
    env = {
        "PGPASSWORD": Config.DB_PASS
    }
    
    # Build pg_dump command
    command = [
        "pg_dump",
        "-h", Config.DB_HOST,       
        "-p", Config.DB_PORT,       
        "-U", Config.DB_USER,      
        "-d", Config.DB_NAME, 
        "-F", "p",        # Custom format for backup
        "-f", str(backup_path)
    ]

    # Run pg_dump with the provided command and environment variables
    subprocess.run(command, env=env, check=True)
    print(f"Backup successful: {backup_path}")

if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='Backup PostgreSQL database')
    current_date = datetime.now().strftime("%Y-%m-%d")
    default_backup_file = f"backup_{current_date}_{Config.DB_NAME}.sql"
    parser.add_argument('--backup_path', default=default_backup_file, type=Path, help='Path to store the backup file')

    args = parser.parse_args()
    backup_postgres_db(Path(args.backup_path))