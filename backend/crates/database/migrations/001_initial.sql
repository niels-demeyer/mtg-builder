-- Initial migration for MTG Builder database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cards table
CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scryfall_id VARCHAR(255) UNIQUE,
    name VARCHAR(255) NOT NULL,
    mana_cost VARCHAR(100),
    cmc REAL,
    type_line VARCHAR(255),
    oracle_text TEXT,
    colors TEXT[],
    color_identity TEXT[],
    rarity VARCHAR(50),
    set_code VARCHAR(20),
    set_name VARCHAR(255),
    collector_number VARCHAR(20),
    image_uri TEXT,
    power VARCHAR(10),
    toughness VARCHAR(10),
    loyalty VARCHAR(10),
    legalities JSONB,
    prices JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on card name for searching
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards (name);
CREATE INDEX IF NOT EXISTS idx_cards_scryfall_id ON cards (scryfall_id);
CREATE INDEX IF NOT EXISTS idx_cards_set_code ON cards (set_code);
CREATE INDEX IF NOT EXISTS idx_cards_colors ON cards USING GIN (colors);
CREATE INDEX IF NOT EXISTS idx_cards_color_identity ON cards USING GIN (color_identity);

-- Decks table
CREATE TABLE IF NOT EXISTS decks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    format VARCHAR(50),
    is_public BOOLEAN NOT NULL DEFAULT false,
    thumbnail_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for decks
CREATE INDEX IF NOT EXISTS idx_decks_user_id ON decks (user_id);
CREATE INDEX IF NOT EXISTS idx_decks_format ON decks (format);
CREATE INDEX IF NOT EXISTS idx_decks_is_public ON decks (is_public);

-- Deck cards junction table
CREATE TABLE IF NOT EXISTS deck_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deck_id UUID NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    is_sideboard BOOLEAN NOT NULL DEFAULT false,
    is_commander BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (deck_id, card_id, is_sideboard)
);

-- Create indexes for deck_cards
CREATE INDEX IF NOT EXISTS idx_deck_cards_deck_id ON deck_cards (deck_id);
CREATE INDEX IF NOT EXISTS idx_deck_cards_card_id ON deck_cards (card_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_cards_updated_at
    BEFORE UPDATE ON cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_decks_updated_at
    BEFORE UPDATE ON decks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deck_cards_updated_at
    BEFORE UPDATE ON deck_cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
