use std::time::Instant;

use scripts::{Database, ScryfallClient};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load environment variables from .env file
    dotenvy::dotenv().ok();

    let client = ScryfallClient::new();
    let db = Database::new().await?;
    let start = Instant::now();

    // Query to fetch cards
    let query = "t:land";

    println!("=== Fetching cards and storing to database ===\n");
    println!("Query: {}", query);

    // Fetch and store cards immediately as each page is retrieved
    // This ensures data is persisted even if the process is interrupted
    let total_stored = client.fetch_and_store(query, &db).await?;

    println!("\n=== Results ===");
    println!("Total cards stored in database: {}", total_stored);
    println!("Total cards in database: {}", db.get_card_count().await?);
    println!("Total time: {:.2}s", start.elapsed().as_secs_f64());

    // Example: search for cards by name
    println!("\n=== Searching database for {query} ===");
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

