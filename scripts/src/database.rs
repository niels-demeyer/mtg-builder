use sqlx::postgres::PgPoolOptions;
use sqlx::{PgConnection, Pool, Postgres};
use std::env;

pub struct Database {
    pool: Pool<Postgres>,
}

impl Database {
    /// Create a new database connection using DATABASE_URL environment variable
    pub async fn new() -> Result<Self, sqlx::Error> {
        let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");

        let pool = PgPoolOptions::new()
            .max_connections(10)
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
                highres_image BOOLEAN,
                image_status TEXT,
                mana_cost TEXT,
                cmc DOUBLE PRECISION,
                type_line TEXT,
                oracle_text TEXT,
                power TEXT,
                toughness TEXT,
                loyalty TEXT,
                defense TEXT,
                colors TEXT,
                color_identity TEXT,
                keywords TEXT,
                legalities TEXT,
                games TEXT,
                reserved BOOLEAN,
                foil BOOLEAN,
                nonfoil BOOLEAN,
                finishes TEXT,
                oversized BOOLEAN,
                promo BOOLEAN,
                reprint BOOLEAN,
                variation BOOLEAN,
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
                digital BOOLEAN,
                rarity TEXT,
                flavor_text TEXT,
                card_back_id TEXT,
                artist TEXT,
                artist_ids TEXT,
                illustration_id TEXT,
                border_color TEXT,
                frame TEXT,
                full_art BOOLEAN,
                textless BOOLEAN,
                booster BOOLEAN,
                story_spotlight BOOLEAN,
                edhrec_rank INTEGER,
                penny_rank INTEGER,
                prices TEXT,
                related_uris TEXT,
                purchase_uris TEXT,
                image_uris TEXT,
                card_faces TEXT,
                all_parts TEXT,
                raw_json TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Add columns that may not exist in older schemas
        sqlx::query("ALTER TABLE cards ADD COLUMN IF NOT EXISTS loyalty TEXT")
            .execute(&self.pool)
            .await?;
        sqlx::query("ALTER TABLE cards ADD COLUMN IF NOT EXISTS defense TEXT")
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

    /// Insert or update a single card from raw JSON
    pub async fn upsert_card(&self, card_json: &serde_json::Value) -> Result<(), sqlx::Error> {
        let mut conn = self.pool.acquire().await?;
        execute_card_upsert(&mut conn, card_json).await
    }

    /// Insert or update a batch of cards within a single transaction
    pub async fn upsert_cards_batch(
        &self,
        cards: &[serde_json::Value],
    ) -> Result<usize, sqlx::Error> {
        let mut tx = self.pool.begin().await?;
        for card in cards {
            execute_card_upsert(&mut *tx, card).await?;
        }
        tx.commit().await?;
        Ok(cards.len())
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
            sqlx::query_as("SELECT raw_json FROM cards WHERE id = $1")
                .bind(id)
                .fetch_optional(&self.pool)
                .await?;

        Ok(row.map(|(json,)| serde_json::from_str(&json).unwrap_or_default()))
    }

    /// Search cards by name
    pub async fn search_by_name(&self, name: &str) -> Result<Vec<serde_json::Value>, sqlx::Error> {
        let rows: Vec<(String,)> =
            sqlx::query_as("SELECT raw_json FROM cards WHERE name ILIKE $1")
                .bind(format!("%{}%", name))
                .fetch_all(&self.pool)
                .await?;

        Ok(rows
            .into_iter()
            .filter_map(|(json,)| serde_json::from_str(&json).ok())
            .collect())
    }
}

/// Execute a card upsert against any Postgres connection (pool connection or transaction).
/// Handles all card layouts: normal, transform, modal_dfc, split, flip, adventure, meld, etc.
async fn execute_card_upsert(
    conn: &mut PgConnection,
    card_json: &serde_json::Value,
) -> Result<(), sqlx::Error> {
    let id = card_json["id"].as_str().unwrap_or_default();
    let raw_json = serde_json::to_string(card_json).unwrap_or_default();

    // For double-faced/split/adventure/flip cards, Scryfall puts per-face fields
    // (mana_cost, oracle_text, power, toughness, loyalty, flavor_text, etc.)
    // in card_faces[] instead of at the top level.
    let front_face = card_json["card_faces"]
        .as_array()
        .and_then(|f| f.first());

    // Helper: get a string field, falling back to front face for multi-face cards
    let get_str = |field: &str| -> Option<&str> {
        card_json[field]
            .as_str()
            .or_else(|| front_face.and_then(|f| f[field].as_str()))
    };

    // Helper: get colors/arrays, falling back to front face for multi-face cards
    let get_colors = |field: &str| -> Option<String> {
        json_array_to_string(&card_json[field])
            .or_else(|| front_face.and_then(|f| json_array_to_string(&f[field])))
    };

    // For image_uris: use top-level if present, else front face (DFCs have per-face images)
    let image_uris_str = if card_json["image_uris"].is_object() {
        card_json["image_uris"].to_string()
    } else if let Some(face) = front_face {
        if face["image_uris"].is_object() {
            face["image_uris"].to_string()
        } else {
            "null".to_string()
        }
    } else {
        "null".to_string()
    };

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
            purchase_uris, image_uris, card_faces, all_parts,
            loyalty, defense, raw_json, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
            $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28,
            $29, $30, $31, $32, $33, $34, $35, $36, $37, $38, $39, $40, $41,
            $42, $43, $44, $45, $46, $47, $48, $49, $50, $51, $52, $53, $54,
            $55, $56, $57, $58, $59, $60, $61, $62, $63, CURRENT_TIMESTAMP
        )
        ON CONFLICT(id) DO UPDATE SET
            oracle_id = EXCLUDED.oracle_id,
            name = EXCLUDED.name,
            lang = EXCLUDED.lang,
            released_at = EXCLUDED.released_at,
            uri = EXCLUDED.uri,
            scryfall_uri = EXCLUDED.scryfall_uri,
            layout = EXCLUDED.layout,
            highres_image = EXCLUDED.highres_image,
            image_status = EXCLUDED.image_status,
            mana_cost = EXCLUDED.mana_cost,
            cmc = EXCLUDED.cmc,
            type_line = EXCLUDED.type_line,
            oracle_text = EXCLUDED.oracle_text,
            power = EXCLUDED.power,
            toughness = EXCLUDED.toughness,
            colors = EXCLUDED.colors,
            color_identity = EXCLUDED.color_identity,
            keywords = EXCLUDED.keywords,
            legalities = EXCLUDED.legalities,
            games = EXCLUDED.games,
            reserved = EXCLUDED.reserved,
            foil = EXCLUDED.foil,
            nonfoil = EXCLUDED.nonfoil,
            finishes = EXCLUDED.finishes,
            oversized = EXCLUDED.oversized,
            promo = EXCLUDED.promo,
            reprint = EXCLUDED.reprint,
            variation = EXCLUDED.variation,
            set_id = EXCLUDED.set_id,
            set_code = EXCLUDED.set_code,
            set_name = EXCLUDED.set_name,
            set_type = EXCLUDED.set_type,
            set_uri = EXCLUDED.set_uri,
            set_search_uri = EXCLUDED.set_search_uri,
            scryfall_set_uri = EXCLUDED.scryfall_set_uri,
            rulings_uri = EXCLUDED.rulings_uri,
            prints_search_uri = EXCLUDED.prints_search_uri,
            collector_number = EXCLUDED.collector_number,
            digital = EXCLUDED.digital,
            rarity = EXCLUDED.rarity,
            flavor_text = EXCLUDED.flavor_text,
            card_back_id = EXCLUDED.card_back_id,
            artist = EXCLUDED.artist,
            artist_ids = EXCLUDED.artist_ids,
            illustration_id = EXCLUDED.illustration_id,
            border_color = EXCLUDED.border_color,
            frame = EXCLUDED.frame,
            full_art = EXCLUDED.full_art,
            textless = EXCLUDED.textless,
            booster = EXCLUDED.booster,
            story_spotlight = EXCLUDED.story_spotlight,
            edhrec_rank = EXCLUDED.edhrec_rank,
            penny_rank = EXCLUDED.penny_rank,
            prices = EXCLUDED.prices,
            related_uris = EXCLUDED.related_uris,
            purchase_uris = EXCLUDED.purchase_uris,
            image_uris = EXCLUDED.image_uris,
            card_faces = EXCLUDED.card_faces,
            all_parts = EXCLUDED.all_parts,
            loyalty = EXCLUDED.loyalty,
            defense = EXCLUDED.defense,
            raw_json = EXCLUDED.raw_json,
            updated_at = CURRENT_TIMESTAMP
        "#,
    )
    .bind(id)                                                          // $1
    .bind(card_json["oracle_id"].as_str())                             // $2
    .bind(card_json["name"].as_str())                                  // $3
    .bind(card_json["lang"].as_str())                                  // $4
    .bind(card_json["released_at"].as_str())                           // $5
    .bind(card_json["uri"].as_str())                                   // $6
    .bind(card_json["scryfall_uri"].as_str())                          // $7
    .bind(card_json["layout"].as_str())                                // $8
    .bind(card_json["highres_image"].as_bool())                        // $9
    .bind(card_json["image_status"].as_str())                          // $10
    .bind(get_str("mana_cost"))                                        // $11
    .bind(card_json["cmc"].as_f64())                                   // $12
    .bind(card_json["type_line"].as_str())                             // $13
    .bind(get_str("oracle_text"))                                      // $14
    .bind(get_str("power"))                                            // $15
    .bind(get_str("toughness"))                                        // $16
    .bind(get_colors("colors"))                                        // $17
    .bind(get_colors("color_identity"))                                // $18
    .bind(json_array_to_string(&card_json["keywords"]))                // $19
    .bind(card_json["legalities"].to_string())                         // $20
    .bind(json_array_to_string(&card_json["games"]))                   // $21
    .bind(card_json["reserved"].as_bool())                             // $22
    .bind(card_json["foil"].as_bool())                                 // $23
    .bind(card_json["nonfoil"].as_bool())                              // $24
    .bind(json_array_to_string(&card_json["finishes"]))                // $25
    .bind(card_json["oversized"].as_bool())                            // $26
    .bind(card_json["promo"].as_bool())                                // $27
    .bind(card_json["reprint"].as_bool())                              // $28
    .bind(card_json["variation"].as_bool())                            // $29
    .bind(card_json["set_id"].as_str())                                // $30
    .bind(card_json["set"].as_str())                                   // $31
    .bind(card_json["set_name"].as_str())                              // $32
    .bind(card_json["set_type"].as_str())                              // $33
    .bind(card_json["set_uri"].as_str())                               // $34
    .bind(card_json["set_search_uri"].as_str())                        // $35
    .bind(card_json["scryfall_set_uri"].as_str())                      // $36
    .bind(card_json["rulings_uri"].as_str())                           // $37
    .bind(card_json["prints_search_uri"].as_str())                     // $38
    .bind(card_json["collector_number"].as_str())                      // $39
    .bind(card_json["digital"].as_bool())                              // $40
    .bind(card_json["rarity"].as_str())                                // $41
    .bind(get_str("flavor_text"))                                      // $42 (DFC fallback)
    .bind(card_json["card_back_id"].as_str())                          // $43
    .bind(get_str("artist"))                                           // $44 (DFC fallback)
    .bind(json_array_to_string(&card_json["artist_ids"]))              // $45
    .bind(get_str("illustration_id"))                                  // $46 (DFC fallback)
    .bind(card_json["border_color"].as_str())                          // $47
    .bind(card_json["frame"].as_str())                                 // $48
    .bind(card_json["full_art"].as_bool())                             // $49
    .bind(card_json["textless"].as_bool())                             // $50
    .bind(card_json["booster"].as_bool())                              // $51
    .bind(card_json["story_spotlight"].as_bool())                      // $52
    .bind(card_json["edhrec_rank"].as_i64().map(|n| n as i32))         // $53
    .bind(card_json["penny_rank"].as_i64().map(|n| n as i32))          // $54
    .bind(card_json["prices"].to_string())                             // $55
    .bind(card_json["related_uris"].to_string())                       // $56
    .bind(card_json["purchase_uris"].to_string())                      // $57
    .bind(&image_uris_str)                                             // $58
    .bind(card_json["card_faces"].to_string())                         // $59
    .bind(card_json["all_parts"].to_string())                          // $60
    .bind(get_str("loyalty"))                                          // $61 (DFC fallback)
    .bind(get_str("defense"))                                          // $62 (DFC fallback)
    .bind(&raw_json)                                                   // $63
    .execute(&mut *conn)
    .await?;

    Ok(())
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
