#!/usr/bin/env python3
"""Run database migrations using the existing DATABASE_URL from .env"""

import os
import sys
from pathlib import Path

# Add backend to path so we can import from there
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import psycopg2
from dotenv import load_dotenv

load_dotenv(backend_dir / ".env")


def get_connection():
    """Get a database connection from DATABASE_URL."""
    db_url = os.getenv("DATABASE_URL", "")

    # Normalize the URL for psycopg2
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return psycopg2.connect(db_url)


MIGRATIONS = [
    # Migration 001: Users and Decks
    """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Decks table
    CREATE TABLE IF NOT EXISTS decks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Deck cards junction table
    CREATE TABLE IF NOT EXISTS deck_cards (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        deck_id UUID NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
        card_id VARCHAR(255) NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
        UNIQUE(deck_id, card_id)
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_decks_user_id ON decks(user_id);
    CREATE INDEX IF NOT EXISTS idx_deck_cards_deck_id ON deck_cards(deck_id);
    CREATE INDEX IF NOT EXISTS idx_deck_cards_card_id ON deck_cards(card_id);
    """,
]


def run_migrations():
    """Run all migrations."""
    print("Connecting to database...")
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for i, migration in enumerate(MIGRATIONS, 1):
            print(f"Running migration {i}...")
            cursor.execute(migration)
            conn.commit()
            print(f"Migration {i} complete.")

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
