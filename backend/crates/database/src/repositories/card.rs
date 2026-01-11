//! Card repository implementation

use crate::error::Result;
use crate::repositories::{Paginated, PaginatedResult, Repository};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use sqlx::PgPool;
use tracing::instrument;
use uuid::Uuid;

/// Card entity representing an MTG card
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Card {
    /// Unique identifier
    pub id: Uuid,
    /// Scryfall ID for the card
    pub scryfall_id: Option<String>,
    /// Card name
    pub name: String,
    /// Mana cost string (e.g., "{2}{U}{U}")
    pub mana_cost: Option<String>,
    /// Converted mana cost / mana value
    pub cmc: Option<f32>,
    /// Card type line
    pub type_line: Option<String>,
    /// Oracle text
    pub oracle_text: Option<String>,
    /// Color identity
    pub colors: Option<Vec<String>>,
    /// Color identity
    pub color_identity: Option<Vec<String>>,
    /// Card rarity
    pub rarity: Option<String>,
    /// Set code
    pub set_code: Option<String>,
    /// Set name
    pub set_name: Option<String>,
    /// Collector number
    pub collector_number: Option<String>,
    /// Image URI
    pub image_uri: Option<String>,
    /// Card power (for creatures)
    pub power: Option<String>,
    /// Card toughness (for creatures)
    pub toughness: Option<String>,
    /// Card loyalty (for planeswalkers)
    pub loyalty: Option<String>,
    /// Whether the card is legal in various formats (stored as JSON)
    pub legalities: Option<serde_json::Value>,
    /// Card prices (stored as JSON)
    pub prices: Option<serde_json::Value>,
    /// When the card was created in the database
    pub created_at: DateTime<Utc>,
    /// When the card was last updated
    pub updated_at: DateTime<Utc>,
}

/// Card filter options for searching
#[derive(Debug, Default, Clone)]
pub struct CardFilter {
    /// Filter by name (partial match)
    pub name: Option<String>,
    /// Filter by set code
    pub set_code: Option<String>,
    /// Filter by colors
    pub colors: Option<Vec<String>>,
    /// Filter by type
    pub type_line: Option<String>,
    /// Filter by rarity
    pub rarity: Option<String>,
    /// Filter by minimum CMC
    pub min_cmc: Option<f32>,
    /// Filter by maximum CMC
    pub max_cmc: Option<f32>,
}

/// Card repository for database operations
#[derive(Clone)]
pub struct CardRepository {
    pool: PgPool,
}

impl CardRepository {
    /// Create a new card repository
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Find a card by its Scryfall ID
    #[instrument(skip(self))]
    pub async fn find_by_scryfall_id(&self, scryfall_id: &str) -> Result<Option<Card>> {
        let card = sqlx::query_as::<_, Card>(
            r#"
            SELECT * FROM cards WHERE scryfall_id = $1
            "#,
        )
        .bind(scryfall_id)
        .fetch_optional(&self.pool)
        .await?;

        Ok(card)
    }

    /// Find cards by name (partial match)
    #[instrument(skip(self))]
    pub async fn find_by_name(&self, name: &str) -> Result<Vec<Card>> {
        let cards = sqlx::query_as::<_, Card>(
            r#"
            SELECT * FROM cards WHERE name ILIKE $1
            ORDER BY name
            "#,
        )
        .bind(format!("%{}%", name))
        .fetch_all(&self.pool)
        .await?;

        Ok(cards)
    }

    /// Search cards with filters
    #[instrument(skip(self))]
    pub async fn search(&self, filter: &CardFilter, page: u32, page_size: u32) -> Result<PaginatedResult<Card>> {
        let offset = (page.saturating_sub(1)) * page_size;

        // Build dynamic query based on filters
        let mut query = String::from("SELECT * FROM cards WHERE 1=1");
        let mut count_query = String::from("SELECT COUNT(*) FROM cards WHERE 1=1");
        let mut params: Vec<String> = Vec::new();

        if let Some(ref name) = filter.name {
            params.push(format!("%{}%", name));
            let param_num = params.len();
            query.push_str(&format!(" AND name ILIKE ${}", param_num));
            count_query.push_str(&format!(" AND name ILIKE ${}", param_num));
        }

        if let Some(ref set_code) = filter.set_code {
            params.push(set_code.clone());
            let param_num = params.len();
            query.push_str(&format!(" AND set_code = ${}", param_num));
            count_query.push_str(&format!(" AND set_code = ${}", param_num));
        }

        if let Some(ref rarity) = filter.rarity {
            params.push(rarity.clone());
            let param_num = params.len();
            query.push_str(&format!(" AND rarity = ${}", param_num));
            count_query.push_str(&format!(" AND rarity = ${}", param_num));
        }

        query.push_str(&format!(
            " ORDER BY name LIMIT {} OFFSET {}",
            page_size, offset
        ));

        // For simplicity, we'll use a basic query here
        // In production, you'd want to use a query builder
        let cards = sqlx::query_as::<_, Card>(&query)
            .fetch_all(&self.pool)
            .await?;

        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM cards")
            .fetch_one(&self.pool)
            .await?;

        Ok(PaginatedResult::new(cards, total.0, page, page_size))
    }

    /// Bulk insert cards
    #[instrument(skip(self, cards))]
    pub async fn bulk_insert(&self, cards: &[Card]) -> Result<u64> {
        if cards.is_empty() {
            return Ok(0);
        }

        let mut tx = self.pool.begin().await?;
        let mut count = 0u64;

        for card in cards {
            let result = sqlx::query(
                r#"
                INSERT INTO cards (
                    id, scryfall_id, name, mana_cost, cmc, type_line, oracle_text,
                    colors, color_identity, rarity, set_code, set_name,
                    collector_number, image_uri, power, toughness, loyalty,
                    legalities, prices, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
                ON CONFLICT (scryfall_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    mana_cost = EXCLUDED.mana_cost,
                    cmc = EXCLUDED.cmc,
                    type_line = EXCLUDED.type_line,
                    oracle_text = EXCLUDED.oracle_text,
                    colors = EXCLUDED.colors,
                    color_identity = EXCLUDED.color_identity,
                    rarity = EXCLUDED.rarity,
                    set_code = EXCLUDED.set_code,
                    set_name = EXCLUDED.set_name,
                    collector_number = EXCLUDED.collector_number,
                    image_uri = EXCLUDED.image_uri,
                    power = EXCLUDED.power,
                    toughness = EXCLUDED.toughness,
                    loyalty = EXCLUDED.loyalty,
                    legalities = EXCLUDED.legalities,
                    prices = EXCLUDED.prices,
                    updated_at = EXCLUDED.updated_at
                "#,
            )
            .bind(&card.id)
            .bind(&card.scryfall_id)
            .bind(&card.name)
            .bind(&card.mana_cost)
            .bind(&card.cmc)
            .bind(&card.type_line)
            .bind(&card.oracle_text)
            .bind(&card.colors)
            .bind(&card.color_identity)
            .bind(&card.rarity)
            .bind(&card.set_code)
            .bind(&card.set_name)
            .bind(&card.collector_number)
            .bind(&card.image_uri)
            .bind(&card.power)
            .bind(&card.toughness)
            .bind(&card.loyalty)
            .bind(&card.legalities)
            .bind(&card.prices)
            .bind(&card.created_at)
            .bind(&card.updated_at)
            .execute(&mut *tx)
            .await?;

            count += result.rows_affected();
        }

        tx.commit().await?;
        Ok(count)
    }
}

impl Repository<Card, Uuid> for CardRepository {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<Card>> {
        let card = sqlx::query_as::<_, Card>(
            r#"
            SELECT * FROM cards WHERE id = $1
            "#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        Ok(card)
    }

    async fn find_all(&self) -> Result<Vec<Card>> {
        let cards = sqlx::query_as::<_, Card>(
            r#"
            SELECT * FROM cards ORDER BY name
            "#,
        )
        .fetch_all(&self.pool)
        .await?;

        Ok(cards)
    }

    async fn create(&self, card: &Card) -> Result<Card> {
        let created = sqlx::query_as::<_, Card>(
            r#"
            INSERT INTO cards (
                id, scryfall_id, name, mana_cost, cmc, type_line, oracle_text,
                colors, color_identity, rarity, set_code, set_name,
                collector_number, image_uri, power, toughness, loyalty,
                legalities, prices, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
            RETURNING *
            "#,
        )
        .bind(&card.id)
        .bind(&card.scryfall_id)
        .bind(&card.name)
        .bind(&card.mana_cost)
        .bind(&card.cmc)
        .bind(&card.type_line)
        .bind(&card.oracle_text)
        .bind(&card.colors)
        .bind(&card.color_identity)
        .bind(&card.rarity)
        .bind(&card.set_code)
        .bind(&card.set_name)
        .bind(&card.collector_number)
        .bind(&card.image_uri)
        .bind(&card.power)
        .bind(&card.toughness)
        .bind(&card.loyalty)
        .bind(&card.legalities)
        .bind(&card.prices)
        .bind(&card.created_at)
        .bind(&card.updated_at)
        .fetch_one(&self.pool)
        .await?;

        Ok(created)
    }

    async fn update(&self, card: &Card) -> Result<Card> {
        let updated = sqlx::query_as::<_, Card>(
            r#"
            UPDATE cards SET
                scryfall_id = $2,
                name = $3,
                mana_cost = $4,
                cmc = $5,
                type_line = $6,
                oracle_text = $7,
                colors = $8,
                color_identity = $9,
                rarity = $10,
                set_code = $11,
                set_name = $12,
                collector_number = $13,
                image_uri = $14,
                power = $15,
                toughness = $16,
                loyalty = $17,
                legalities = $18,
                prices = $19,
                updated_at = $20
            WHERE id = $1
            RETURNING *
            "#,
        )
        .bind(&card.id)
        .bind(&card.scryfall_id)
        .bind(&card.name)
        .bind(&card.mana_cost)
        .bind(&card.cmc)
        .bind(&card.type_line)
        .bind(&card.oracle_text)
        .bind(&card.colors)
        .bind(&card.color_identity)
        .bind(&card.rarity)
        .bind(&card.set_code)
        .bind(&card.set_name)
        .bind(&card.collector_number)
        .bind(&card.image_uri)
        .bind(&card.power)
        .bind(&card.toughness)
        .bind(&card.loyalty)
        .bind(&card.legalities)
        .bind(&card.prices)
        .bind(Utc::now())
        .fetch_one(&self.pool)
        .await?;

        Ok(updated)
    }

    async fn delete(&self, id: Uuid) -> Result<bool> {
        let result = sqlx::query(
            r#"
            DELETE FROM cards WHERE id = $1
            "#,
        )
        .bind(id)
        .execute(&self.pool)
        .await?;

        Ok(result.rows_affected() > 0)
    }
}

impl Paginated<Card> for CardRepository {
    async fn find_paginated(&self, page: u32, page_size: u32) -> Result<PaginatedResult<Card>> {
        let offset = (page.saturating_sub(1)) * page_size;

        let cards = sqlx::query_as::<_, Card>(
            r#"
            SELECT * FROM cards
            ORDER BY name
            LIMIT $1 OFFSET $2
            "#,
        )
        .bind(page_size as i64)
        .bind(offset as i64)
        .fetch_all(&self.pool)
        .await?;

        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM cards")
            .fetch_one(&self.pool)
            .await?;

        Ok(PaginatedResult::new(cards, total.0, page, page_size))
    }
}
