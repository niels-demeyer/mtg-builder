use sqlx::{sqlite::SqlitePoolOptions, Pool, Sqlite};
use std::path::Path;

pub struct Database {
    pool: Pool<Sqlite>,
}

impl Database {
    /// Create a new database connection, creating the file if it doesn't exist
    pub async fn new(db_path: &str) -> Result<Self, sqlx::Error> {
        // Create the database file if it doesn't exist
        if !Path::new(db_path).exists() {
            std::fs::File::create(db_path)?;
        }

        let database_url = format!("sqlite:{}", db_path);
        let pool = SqlitePoolOptions::new()
            .max_connections(5)
            .connect(&database_url)
            .await?;

        let db = Self { pool };
        db.initialize().await?;

        Ok(db)
    }

    /// Initialize the database schema
    async fn initialize(&self) -> Result<(), sqlx::Error> {
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY,
                oracle_id TEXT,
                name TEXT NOT NULL,
                lang TEXT,
                released_at TEXT,
                uri TEXT,
                scryfall_uri TEXT,
                layout TEXT,
                highres_image INTEGER,
                image_status TEXT,
                mana_cost TEXT,
                cmc REAL,
                type_line TEXT,
                oracle_text TEXT,
                power TEXT,
                toughness TEXT,
                colors TEXT,
                color_identity TEXT,
                keywords TEXT,
                legalities TEXT,
                games TEXT,
                reserved INTEGER,
                foil INTEGER,
                nonfoil INTEGER,
                finishes TEXT,
                oversized INTEGER,
                promo INTEGER,
                reprint INTEGER,
                variation INTEGER,
                set_id TEXT,
                set_code TEXT,
                set_name TEXT,
                set_type TEXT,
                set_uri TEXT,
                set_search_uri TEXT,
                scryfall_set_uri TEXT,
                rulings_uri TEXT,
                prints_search_uri TEXT,
                collector_number TEXT,
                digital INTEGER,
                rarity TEXT,
                flavor_text TEXT,
                card_back_id TEXT,
                artist TEXT,
                artist_ids TEXT,
                illustration_id TEXT,
                border_color TEXT,
                frame TEXT,
                full_art INTEGER,
                textless INTEGER,
                booster INTEGER,
                story_spotlight INTEGER,
                edhrec_rank INTEGER,
                penny_rank INTEGER,
                prices TEXT,
                related_uris TEXT,
                purchase_uris TEXT,
                image_uris TEXT,
                card_faces TEXT,
                all_parts TEXT,
                raw_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Create indexes for common queries
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name)")
            .execute(&self.pool)
            .await?;
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_cards_set_code ON cards(set_code)")
            .execute(&self.pool)
            .await?;
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_cards_rarity ON cards(rarity)")
            .execute(&self.pool)
            .await?;
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_cards_type_line ON cards(type_line)")
            .execute(&self.pool)
            .await?;

        Ok(())
    }

    /// Insert or update a card from raw JSON
    pub async fn upsert_card(&self, card_json: &serde_json::Value) -> Result<(), sqlx::Error> {
        let id = card_json["id"].as_str().unwrap_or_default();
        let raw_json = serde_json::to_string(card_json).unwrap_or_default();

        sqlx::query(
            r#"
            INSERT INTO cards (
                id, oracle_id, name, lang, released_at, uri, scryfall_uri, layout,
                highres_image, image_status, mana_cost, cmc, type_line, oracle_text,
                power, toughness, colors, color_identity, keywords, legalities,
                games, reserved, foil, nonfoil, finishes, oversized, promo, reprint,
                variation, set_id, set_code, set_name, set_type, set_uri, set_search_uri,
                scryfall_set_uri, rulings_uri, prints_search_uri, collector_number,
                digital, rarity, flavor_text, card_back_id, artist, artist_ids,
                illustration_id, border_color, frame, full_art, textless, booster,
                story_spotlight, edhrec_rank, penny_rank, prices, related_uris,
                purchase_uris, image_uris, card_faces, all_parts, raw_json, updated_at
            ) VALUES (
                ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15,
                ?16, ?17, ?18, ?19, ?20, ?21, ?22, ?23, ?24, ?25, ?26, ?27, ?28,
                ?29, ?30, ?31, ?32, ?33, ?34, ?35, ?36, ?37, ?38, ?39, ?40, ?41,
                ?42, ?43, ?44, ?45, ?46, ?47, ?48, ?49, ?50, ?51, ?52, ?53, ?54,
                ?55, ?56, ?57, ?58, ?59, ?60, ?61, CURRENT_TIMESTAMP
            )
            ON CONFLICT(id) DO UPDATE SET
                oracle_id = excluded.oracle_id,
                name = excluded.name,
                lang = excluded.lang,
                released_at = excluded.released_at,
                uri = excluded.uri,
                scryfall_uri = excluded.scryfall_uri,
                layout = excluded.layout,
                highres_image = excluded.highres_image,
                image_status = excluded.image_status,
                mana_cost = excluded.mana_cost,
                cmc = excluded.cmc,
                type_line = excluded.type_line,
                oracle_text = excluded.oracle_text,
                power = excluded.power,
                toughness = excluded.toughness,
                colors = excluded.colors,
                color_identity = excluded.color_identity,
                keywords = excluded.keywords,
                legalities = excluded.legalities,
                games = excluded.games,
                reserved = excluded.reserved,
                foil = excluded.foil,
                nonfoil = excluded.nonfoil,
                finishes = excluded.finishes,
                oversized = excluded.oversized,
                promo = excluded.promo,
                reprint = excluded.reprint,
                variation = excluded.variation,
                set_id = excluded.set_id,
                set_code = excluded.set_code,
                set_name = excluded.set_name,
                set_type = excluded.set_type,
                set_uri = excluded.set_uri,
                set_search_uri = excluded.set_search_uri,
                scryfall_set_uri = excluded.scryfall_set_uri,
                rulings_uri = excluded.rulings_uri,
                prints_search_uri = excluded.prints_search_uri,
                collector_number = excluded.collector_number,
                digital = excluded.digital,
                rarity = excluded.rarity,
                flavor_text = excluded.flavor_text,
                card_back_id = excluded.card_back_id,
                artist = excluded.artist,
                artist_ids = excluded.artist_ids,
                illustration_id = excluded.illustration_id,
                border_color = excluded.border_color,
                frame = excluded.frame,
                full_art = excluded.full_art,
                textless = excluded.textless,
                booster = excluded.booster,
                story_spotlight = excluded.story_spotlight,
                edhrec_rank = excluded.edhrec_rank,
                penny_rank = excluded.penny_rank,
                prices = excluded.prices,
                related_uris = excluded.related_uris,
                purchase_uris = excluded.purchase_uris,
                image_uris = excluded.image_uris,
                card_faces = excluded.card_faces,
                all_parts = excluded.all_parts,
                raw_json = excluded.raw_json,
                updated_at = CURRENT_TIMESTAMP
            "#,
        )
        .bind(id)
        .bind(card_json["oracle_id"].as_str())
        .bind(card_json["name"].as_str())
        .bind(card_json["lang"].as_str())
        .bind(card_json["released_at"].as_str())
        .bind(card_json["uri"].as_str())
        .bind(card_json["scryfall_uri"].as_str())
        .bind(card_json["layout"].as_str())
        .bind(card_json["highres_image"].as_bool().map(|b| b as i32))
        .bind(card_json["image_status"].as_str())
        .bind(card_json["mana_cost"].as_str())
        .bind(card_json["cmc"].as_f64())
        .bind(card_json["type_line"].as_str())
        .bind(card_json["oracle_text"].as_str())
        .bind(card_json["power"].as_str())
        .bind(card_json["toughness"].as_str())
        .bind(json_array_to_string(&card_json["colors"]))
        .bind(json_array_to_string(&card_json["color_identity"]))
        .bind(json_array_to_string(&card_json["keywords"]))
        .bind(card_json["legalities"].to_string())
        .bind(json_array_to_string(&card_json["games"]))
        .bind(card_json["reserved"].as_bool().map(|b| b as i32))
        .bind(card_json["foil"].as_bool().map(|b| b as i32))
        .bind(card_json["nonfoil"].as_bool().map(|b| b as i32))
        .bind(json_array_to_string(&card_json["finishes"]))
        .bind(card_json["oversized"].as_bool().map(|b| b as i32))
        .bind(card_json["promo"].as_bool().map(|b| b as i32))
        .bind(card_json["reprint"].as_bool().map(|b| b as i32))
        .bind(card_json["variation"].as_bool().map(|b| b as i32))
        .bind(card_json["set_id"].as_str())
        .bind(card_json["set"].as_str())
        .bind(card_json["set_name"].as_str())
        .bind(card_json["set_type"].as_str())
        .bind(card_json["set_uri"].as_str())
        .bind(card_json["set_search_uri"].as_str())
        .bind(card_json["scryfall_set_uri"].as_str())
        .bind(card_json["rulings_uri"].as_str())
        .bind(card_json["prints_search_uri"].as_str())
        .bind(card_json["collector_number"].as_str())
        .bind(card_json["digital"].as_bool().map(|b| b as i32))
        .bind(card_json["rarity"].as_str())
        .bind(card_json["flavor_text"].as_str())
        .bind(card_json["card_back_id"].as_str())
        .bind(card_json["artist"].as_str())
        .bind(json_array_to_string(&card_json["artist_ids"]))
        .bind(card_json["illustration_id"].as_str())
        .bind(card_json["border_color"].as_str())
        .bind(card_json["frame"].as_str())
        .bind(card_json["full_art"].as_bool().map(|b| b as i32))
        .bind(card_json["textless"].as_bool().map(|b| b as i32))
        .bind(card_json["booster"].as_bool().map(|b| b as i32))
        .bind(card_json["story_spotlight"].as_bool().map(|b| b as i32))
        .bind(card_json["edhrec_rank"].as_i64().map(|n| n as i32))
        .bind(card_json["penny_rank"].as_i64().map(|n| n as i32))
        .bind(card_json["prices"].to_string())
        .bind(card_json["related_uris"].to_string())
        .bind(card_json["purchase_uris"].to_string())
        .bind(card_json["image_uris"].to_string())
        .bind(card_json["card_faces"].to_string())
        .bind(card_json["all_parts"].to_string())
        .bind(&raw_json)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Insert multiple cards from a search response
    pub async fn upsert_cards_from_response(
        &self,
        response: &serde_json::Value,
    ) -> Result<usize, sqlx::Error> {
        let cards = response["data"].as_array();
        let mut count = 0;

        if let Some(cards) = cards {
            for card in cards {
                self.upsert_card(card).await?;
                count += 1;
            }
        }

        Ok(count)
    }

    /// Get total card count in database
    pub async fn get_card_count(&self) -> Result<i64, sqlx::Error> {
        let row: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM cards")
            .fetch_one(&self.pool)
            .await?;
        Ok(row.0)
    }

    /// Get a card by ID
    pub async fn get_card_by_id(&self, id: &str) -> Result<Option<serde_json::Value>, sqlx::Error> {
        let row: Option<(String,)> =
            sqlx::query_as("SELECT raw_json FROM cards WHERE id = ?")
                .bind(id)
                .fetch_optional(&self.pool)
                .await?;

        Ok(row.map(|(json,)| serde_json::from_str(&json).unwrap_or_default()))
    }

    /// Search cards by name
    pub async fn search_by_name(&self, name: &str) -> Result<Vec<serde_json::Value>, sqlx::Error> {
        let rows: Vec<(String,)> =
            sqlx::query_as("SELECT raw_json FROM cards WHERE name LIKE ?")
                .bind(format!("%{}%", name))
                .fetch_all(&self.pool)
                .await?;

        Ok(rows
            .into_iter()
            .filter_map(|(json,)| serde_json::from_str(&json).ok())
            .collect())
    }
}

/// Helper function to convert JSON arrays to comma-separated strings
fn json_array_to_string(value: &serde_json::Value) -> Option<String> {
    value.as_array().map(|arr| {
        arr.iter()
            .filter_map(|v| v.as_str())
            .collect::<Vec<_>>()
            .join(",")
    })
}
