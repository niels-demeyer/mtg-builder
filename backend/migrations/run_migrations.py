#!/usr/bin/env python3
"""Run database migrations using the existing DATABASE_URL from .env"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Add backend to path so we can import from there
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

load_dotenv(backend_dir / ".env")

MIGRATIONS_DIR = Path(__file__).parent


def get_connection():
    """Get a database connection from DATABASE_URL."""
    db_url = os.getenv("DATABASE_URL", "")

    # Normalize the URL for psycopg2
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return psycopg2.connect(db_url)


def get_migrations() -> list[tuple[str, str]]:
    """Load migrations from .sql files in the migrations directory."""
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    migrations: list[tuple[str, str]] = []
    for sql_file in sql_files:
        migrations.append((sql_file.name, sql_file.read_text()))
    return migrations


def run_migrations():
    """Run all migrations."""
    print("Connecting to database...")
    conn = get_connection()
    cursor = conn.cursor()

    migrations : list[tuple[str, str]] = get_migrations()
    if not migrations:
        print("No .sql migration files found.")
        return

    try:
        for filename, sql in migrations:
            print(f"Running migration: {filename}...")
            cursor.execute(sql)
            conn.commit()
            print(f"Migration {filename} complete.")

        print("\nAll migrations completed successfully!")

        # Show created tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'decks', 'deck_cards')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\nCreated tables: {', '.join(t[0] for t in tables)}")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_migrations()
