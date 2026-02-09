use std::time::Instant;

use scripts::{Database, ScryfallClient};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load environment variables from .env file
    dotenvy::dotenv().ok();

    let client = ScryfallClient::new();
    let db = Database::new().await?;
    let start = Instant::now();

    println!("=== Downloading and storing all cards from Scryfall bulk data ===\n");

    match client.download_and_store_bulk(&db).await {
        Ok(total_stored) => {
            println!("\n=== Results ===");
            println!("Total cards stored: {}", total_stored);
            println!("Total cards in database: {}", db.get_card_count().await?);
            println!("Total time: {:.2}s", start.elapsed().as_secs_f64());
        }
        Err(e) => {
            eprintln!("\nError during bulk import: {}", e);
            eprintln!("Cards in database so far: {}", db.get_card_count().await?);
            return Err(e.into());
        }
    }

    Ok(())
}
