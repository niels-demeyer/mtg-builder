use std::time::Instant;

use scripts::{Database, ScryfallClient};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = ScryfallClient::new();
    let db = Database::new("cards.db").await?;
    let start = Instant::now();

    // Query to fetch cards
    let query = "name:\"Lightning Bolt\" t:instant";

    println!("=== Fetching cards and storing to database ===\n");
    println!("Query: {}", query);

    // Fetch all pages of JSON data
    let pages = client.fetch_all_json(query).await?;

    // Store each page's cards in the database
    let mut total_stored = 0;
    for page in &pages {
        let count = db.upsert_cards_from_response(page).await?;
        total_stored += count;
    }

    println!("\n=== Results ===");
    println!("Total cards stored in database: {}", total_stored);
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

