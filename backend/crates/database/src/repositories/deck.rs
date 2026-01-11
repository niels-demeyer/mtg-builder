//! Deck repository implementation

use crate::error::Result;
use crate::repositories::{Paginated, PaginatedResult, Repository};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use sqlx::PgPool;
use tracing::instrument;
use uuid::Uuid;

/// Deck entity representing a user's deck
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Deck {
    /// Unique identifier
    pub id: Uuid,
    /// User ID who owns this deck
    pub user_id: Option<Uuid>,
    /// Deck name
    pub name: String,
    /// Deck description
    pub description: Option<String>,
    /// Deck format (Standard, Modern, Commander, etc.)
    pub format: Option<String>,
    /// Whether the deck is public
    pub is_public: bool,
    /// Deck thumbnail image URL
    pub thumbnail_url: Option<String>,
    /// When the deck was created
    pub created_at: DateTime<Utc>,
    /// When the deck was last updated
    pub updated_at: DateTime<Utc>,
}

/// A card entry in a deck
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DeckCard {
    /// Unique identifier
    pub id: Uuid,
    /// Deck ID this card belongs to
    pub deck_id: Uuid,
    /// Card ID
    pub card_id: Uuid,
    /// Number of copies of this card
    pub quantity: i32,
    /// Whether this card is in the sideboard
    pub is_sideboard: bool,
    /// Whether this card is the commander (for Commander format)
    pub is_commander: bool,
    /// When the entry was created
    pub created_at: DateTime<Utc>,
    /// When the entry was last updated
    pub updated_at: DateTime<Utc>,
}

/// Input for adding a card to a deck
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AddCardInput {
    /// Card ID to add
    pub card_id: Uuid,
    /// Number of copies
    pub quantity: i32,
    /// Whether this is a sideboard card
    pub is_sideboard: bool,
    /// Whether this is the commander
    pub is_commander: bool,
}

/// Deck repository for database operations
#[derive(Clone)]
pub struct DeckRepository {
    pool: PgPool,
}

impl DeckRepository {
    /// Create a new deck repository
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Find decks by user ID
    #[instrument(skip(self))]
    pub async fn find_by_user(&self, user_id: Uuid) -> Result<Vec<Deck>> {
        let decks = sqlx::query_as::<_, Deck>(
            r#"
            SELECT * FROM decks WHERE user_id = $1
            ORDER BY updated_at DESC
            "#,
        )
        .bind(user_id)
        .fetch_all(&self.pool)
        .await?;

        Ok(decks)
    }

    /// Find public decks
    #[instrument(skip(self))]
    pub async fn find_public(&self, page: u32, page_size: u32) -> Result<PaginatedResult<Deck>> {
        let offset = (page.saturating_sub(1)) * page_size;

        let decks = sqlx::query_as::<_, Deck>(
            r#"
            SELECT * FROM decks WHERE is_public = true
            ORDER BY updated_at DESC
            LIMIT $1 OFFSET $2
            "#,
        )
        .bind(page_size as i64)
        .bind(offset as i64)
        .fetch_all(&self.pool)
        .await?;

        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM decks WHERE is_public = true")
            .fetch_one(&self.pool)
            .await?;

        Ok(PaginatedResult::new(decks, total.0, page, page_size))
    }

    /// Find decks by format
    #[instrument(skip(self))]
    pub async fn find_by_format(&self, format: &str) -> Result<Vec<Deck>> {
        let decks = sqlx::query_as::<_, Deck>(
            r#"
            SELECT * FROM decks WHERE format = $1 AND is_public = true
            ORDER BY updated_at DESC
            "#,
        )
        .bind(format)
        .fetch_all(&self.pool)
        .await?;

        Ok(decks)
    }

    /// Get all cards in a deck
    #[instrument(skip(self))]
    pub async fn get_deck_cards(&self, deck_id: Uuid) -> Result<Vec<DeckCard>> {
        let cards = sqlx::query_as::<_, DeckCard>(
            r#"
            SELECT * FROM deck_cards WHERE deck_id = $1
            ORDER BY is_sideboard, is_commander DESC
            "#,
        )
        .bind(deck_id)
        .fetch_all(&self.pool)
        .await?;

        Ok(cards)
    }

    /// Add a card to a deck
    #[instrument(skip(self))]
    pub async fn add_card(&self, deck_id: Uuid, input: &AddCardInput) -> Result<DeckCard> {
        let now = Utc::now();
        let id = Uuid::new_v4();

        let card = sqlx::query_as::<_, DeckCard>(
            r#"
            INSERT INTO deck_cards (id, deck_id, card_id, quantity, is_sideboard, is_commander, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (deck_id, card_id, is_sideboard) DO UPDATE SET
                quantity = deck_cards.quantity + EXCLUDED.quantity,
                updated_at = EXCLUDED.updated_at
            RETURNING *
            "#,
        )
        .bind(id)
        .bind(deck_id)
        .bind(&input.card_id)
        .bind(input.quantity)
        .bind(input.is_sideboard)
        .bind(input.is_commander)
        .bind(now)
        .bind(now)
        .fetch_one(&self.pool)
        .await?;

        // Update deck's updated_at timestamp
        sqlx::query("UPDATE decks SET updated_at = $1 WHERE id = $2")
            .bind(now)
            .bind(deck_id)
            .execute(&self.pool)
            .await?;

        Ok(card)
    }

    /// Remove a card from a deck
    #[instrument(skip(self))]
    pub async fn remove_card(&self, deck_id: Uuid, card_id: Uuid, is_sideboard: bool) -> Result<bool> {
        let result = sqlx::query(
            r#"
            DELETE FROM deck_cards WHERE deck_id = $1 AND card_id = $2 AND is_sideboard = $3
            "#,
        )
        .bind(deck_id)
        .bind(card_id)
        .bind(is_sideboard)
        .execute(&self.pool)
        .await?;

        // Update deck's updated_at timestamp
        sqlx::query("UPDATE decks SET updated_at = $1 WHERE id = $2")
            .bind(Utc::now())
            .bind(deck_id)
            .execute(&self.pool)
            .await?;

        Ok(result.rows_affected() > 0)
    }

    /// Update card quantity in a deck
    #[instrument(skip(self))]
    pub async fn update_card_quantity(
        &self,
        deck_id: Uuid,
        card_id: Uuid,
        quantity: i32,
        is_sideboard: bool,
    ) -> Result<Option<DeckCard>> {
        if quantity <= 0 {
            self.remove_card(deck_id, card_id, is_sideboard).await?;
            return Ok(None);
        }

        let card = sqlx::query_as::<_, DeckCard>(
            r#"
            UPDATE deck_cards SET quantity = $4, updated_at = $5
            WHERE deck_id = $1 AND card_id = $2 AND is_sideboard = $3
            RETURNING *
            "#,
        )
        .bind(deck_id)
        .bind(card_id)
        .bind(is_sideboard)
        .bind(quantity)
        .bind(Utc::now())
        .fetch_optional(&self.pool)
        .await?;

        Ok(card)
    }

    /// Copy a deck
    #[instrument(skip(self))]
    pub async fn copy_deck(&self, deck_id: Uuid, new_user_id: Option<Uuid>, new_name: &str) -> Result<Deck> {
        let mut tx = self.pool.begin().await?;
        let now = Utc::now();
        let new_deck_id = Uuid::new_v4();

        // Copy the deck
        let new_deck = sqlx::query_as::<_, Deck>(
            r#"
            INSERT INTO decks (id, user_id, name, description, format, is_public, thumbnail_url, created_at, updated_at)
            SELECT $1, $2, $3, description, format, false, thumbnail_url, $4, $5
            FROM decks WHERE id = $6
            RETURNING *
            "#,
        )
        .bind(new_deck_id)
        .bind(new_user_id)
        .bind(new_name)
        .bind(now)
        .bind(now)
        .bind(deck_id)
        .fetch_one(&mut *tx)
        .await?;

        // Copy all cards
        sqlx::query(
            r#"
            INSERT INTO deck_cards (id, deck_id, card_id, quantity, is_sideboard, is_commander, created_at, updated_at)
            SELECT gen_random_uuid(), $1, card_id, quantity, is_sideboard, is_commander, $2, $3
            FROM deck_cards WHERE deck_id = $4
            "#,
        )
        .bind(new_deck_id)
        .bind(now)
        .bind(now)
        .bind(deck_id)
        .execute(&mut *tx)
        .await?;

        tx.commit().await?;
        Ok(new_deck)
    }

    /// Get deck statistics
    #[instrument(skip(self))]
    pub async fn get_deck_stats(&self, deck_id: Uuid) -> Result<DeckStats> {
        let stats = sqlx::query_as::<_, DeckStats>(
            r#"
            SELECT
                d.id as deck_id,
                COALESCE(SUM(CASE WHEN dc.is_sideboard = false THEN dc.quantity ELSE 0 END), 0) as main_deck_count,
                COALESCE(SUM(CASE WHEN dc.is_sideboard = true THEN dc.quantity ELSE 0 END), 0) as sideboard_count,
                COALESCE(COUNT(DISTINCT dc.card_id), 0) as unique_cards
            FROM decks d
            LEFT JOIN deck_cards dc ON d.id = dc.deck_id
            WHERE d.id = $1
            GROUP BY d.id
            "#,
        )
        .bind(deck_id)
        .fetch_one(&self.pool)
        .await?;

        Ok(stats)
    }
}

/// Deck statistics
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DeckStats {
    /// Deck ID
    pub deck_id: Uuid,
    /// Number of cards in the main deck
    pub main_deck_count: i64,
    /// Number of cards in the sideboard
    pub sideboard_count: i64,
    /// Number of unique cards
    pub unique_cards: i64,
}

impl Repository<Deck, Uuid> for DeckRepository {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<Deck>> {
        let deck = sqlx::query_as::<_, Deck>(
            r#"
            SELECT * FROM decks WHERE id = $1
            "#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        Ok(deck)
    }

    async fn find_all(&self) -> Result<Vec<Deck>> {
        let decks = sqlx::query_as::<_, Deck>(
            r#"
            SELECT * FROM decks ORDER BY updated_at DESC
            "#,
        )
        .fetch_all(&self.pool)
        .await?;

        Ok(decks)
    }

    async fn create(&self, deck: &Deck) -> Result<Deck> {
        let created = sqlx::query_as::<_, Deck>(
            r#"
            INSERT INTO decks (id, user_id, name, description, format, is_public, thumbnail_url, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            "#,
        )
        .bind(&deck.id)
        .bind(&deck.user_id)
        .bind(&deck.name)
        .bind(&deck.description)
        .bind(&deck.format)
        .bind(&deck.is_public)
        .bind(&deck.thumbnail_url)
        .bind(&deck.created_at)
        .bind(&deck.updated_at)
        .fetch_one(&self.pool)
        .await?;

        Ok(created)
    }

    async fn update(&self, deck: &Deck) -> Result<Deck> {
        let updated = sqlx::query_as::<_, Deck>(
            r#"
            UPDATE decks SET
                name = $2,
                description = $3,
                format = $4,
                is_public = $5,
                thumbnail_url = $6,
                updated_at = $7
            WHERE id = $1
            RETURNING *
            "#,
        )
        .bind(&deck.id)
        .bind(&deck.name)
        .bind(&deck.description)
        .bind(&deck.format)
        .bind(&deck.is_public)
        .bind(&deck.thumbnail_url)
        .bind(Utc::now())
        .fetch_one(&self.pool)
        .await?;

        Ok(updated)
    }

    async fn delete(&self, id: Uuid) -> Result<bool> {
        // First delete all cards in the deck
        sqlx::query("DELETE FROM deck_cards WHERE deck_id = $1")
            .bind(id)
            .execute(&self.pool)
            .await?;

        // Then delete the deck
        let result = sqlx::query("DELETE FROM decks WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await?;

        Ok(result.rows_affected() > 0)
    }
}

impl Paginated<Deck> for DeckRepository {
    async fn find_paginated(&self, page: u32, page_size: u32) -> Result<PaginatedResult<Deck>> {
        let offset = (page.saturating_sub(1)) * page_size;

        let decks = sqlx::query_as::<_, Deck>(
            r#"
            SELECT * FROM decks
            ORDER BY updated_at DESC
            LIMIT $1 OFFSET $2
            "#,
        )
        .bind(page_size as i64)
        .bind(offset as i64)
        .fetch_all(&self.pool)
        .await?;

        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM decks")
            .fetch_one(&self.pool)
            .await?;

        Ok(PaginatedResult::new(decks, total.0, page, page_size))
    }
}
