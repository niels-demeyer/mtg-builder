use std::time::Instant;

use scripts::{Database, ScryfallClient};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load environment variables from .env file
    dotenvy::dotenv().ok();

    let client = ScryfallClient::new();
    let db = Database::new().await?;
    let start = Instant::now();

    // Fetch cards by type to avoid timeout on large queries
    let card_types = [
        "creature",
        "instant",
        "sorcery",
        "enchantment",
        "artifact",
        "land",
        "planeswalker",
        "battle",
    ];

    println!("=== Fetching all cards by type and storing to database ===\n");

    let mut grand_total = 0;

    for card_type in &card_types {
        let query = format!("type:{}", card_type);
        println!("\n--- Fetching {} cards ---", card_type);
        println!("Query: {}", query);

        match client.fetch_and_store(&query, &db).await {
            Ok(stored) => {
                grand_total += stored;
                println!("Stored {} {} cards", stored, card_type);
            }
            Err(e) => {
                eprintln!("Error fetching {} cards: {}", card_type, e);
                eprintln!("Continuing with next type...");
            }
        }
    }

    println!("\n=== Results ===");
    println!("Total cards stored this run: {}", grand_total);
    println!("Total cards in database: {}", db.get_card_count().await?);
    println!("Total time: {:.2}s", start.elapsed().as_secs_f64());

    // Example: search for cards by name
    println!("\n=== Searching database for 'Lightning' ===");
    let results = db.search_by_name("Lightning").await?;
    for card in results.iter().take(5) {
        println!(
            "  - {} ({}, {})",
            card["name"].as_str().unwrap_or("Unknown"),
            card["set_name"].as_str().unwrap_or("Unknown"),
            card["rarity"].as_str().unwrap_or("Unknown")
        );
    }

    Ok(())
}

