use std::time::Instant;

use scripts::ScryfallClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = ScryfallClient::new();
    let start = Instant::now();

    // Example queries - includes valid and invalid queries to demonstrate validation
    let queries = vec![
        "type:creature",           // Valid
        "c:red cmc<=3",            // Valid: red cards with CMC 3 or less
        "set:neo rarity:rare",     // Valid: rare cards from Kamigawa: Neon Dynasty
    ];

    // Demonstrate validation-only (no requests sent)
    println!("=== Query Validation ===");
    for query in &queries {
        match client.validate_query(query) {
            Ok(()) => println!("✓ Valid: '{}'", query),
            Err(e) => println!("✗ Invalid: '{}' - {}", query, e),
        }
    }
    
    // Test some invalid queries
    let invalid_queries = vec![
        "",                        // Empty query
        "(type:creature",          // Unbalanced parentheses
        "or type:creature",        // Leading operator
        "type:creature and",       // Trailing operator
        "type:creature and and c:red", // Consecutive operators
        "name:\"Lightning Bolt",   // Unbalanced quotes
    ];
    
    println!("\n=== Invalid Query Examples ===");
    for query in &invalid_queries {
        match client.validate_query(query) {
            Ok(()) => println!("✓ Valid: '{}'", query),
            Err(e) => println!("✗ Invalid: '{}' - {}", query, e),
        }
    }
    
    println!("\n=== Starting Fetch ===\n");
    println!("Fetching {} validated queries...\n", queries.len());
    
    let results = client.fetch_multiple_queries(queries).await;

    let mut total = 0;
    for (i, result) in results.iter().enumerate() {
        match result {
            Ok(cards) => {
                println!("Query {} fetched {} cards", i + 1, cards.len());
                total += cards.len();
            }
            Err(e) => println!("Query {} failed: {}", i + 1, e),
        }
    }

    println!("\n=== Results ===");
    println!("Total cards fetched: {}", total);
    println!("Total time: {:.2}s", start.elapsed().as_secs_f64());

    // Print first 10 cards from each successful query
    for (i, result) in results.iter().enumerate() {
        if let Ok(cards) = result {
            println!("\nFirst 10 cards from query {}:", i + 1);
            for card in cards.iter().take(10) {
                println!("  - {} ({}, {})", card.name, card.set_name, card.rarity);
            }
        }
    }

    Ok(())
}

