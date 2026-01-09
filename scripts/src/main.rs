use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};
use serde::Deserialize;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, Semaphore};

/// Rate limiter that enforces Scryfall's API limits (max 10 req/sec, 100ms between requests)
struct RateLimiter {
    last_request: Mutex<Instant>,
    semaphore: Semaphore,
    min_delay: Duration,
}

impl RateLimiter {
    fn new(max_concurrent: usize, min_delay_ms: u64) -> Self {
        Self {
            last_request: Mutex::new(Instant::now() - Duration::from_secs(1)),
            semaphore: Semaphore::new(max_concurrent),
            min_delay: Duration::from_millis(min_delay_ms),
        }
    }

    async fn acquire(&self) {
        // Acquire semaphore permit to limit concurrency
        let _permit = self.semaphore.acquire().await.unwrap();
        
        // Ensure minimum delay between requests
        let mut last = self.last_request.lock().await;
        let elapsed = last.elapsed();
        if elapsed < self.min_delay {
            tokio::time::sleep(self.min_delay - elapsed).await;
        }
        *last = Instant::now();
    }
}

#[allow(dead_code)]
#[derive(Deserialize, Debug)]
struct ScryfallSearchResponse {
    object: String,
    total_cards: u32,
    has_more: bool,
    next_page: Option<String>,
    data: Vec<Card>,
}

#[allow(dead_code)]
#[derive(Deserialize, Debug, Clone)]
struct Card {
    id: String,
    name: String,
    mana_cost: Option<String>,
    type_line: Option<String>,
    oracle_text: Option<String>,
    set_name: String,
    rarity: String,
}

/// Optimized client with connection pooling and rate limiting
struct ScryfallClient {
    client: reqwest::Client,
    rate_limiter: Arc<RateLimiter>,
    headers: HeaderMap,
}

impl ScryfallClient {
    fn new() -> Self {
        let mut headers = HeaderMap::new();
        headers.insert(USER_AGENT, HeaderValue::from_static("MTGBuilderApp/1.0"));

        // Optimized client with connection pooling and keepalive
        let client = reqwest::Client::builder()
            .pool_max_idle_per_host(5)
            .pool_idle_timeout(Duration::from_secs(30))
            .tcp_keepalive(Duration::from_secs(60))
            .tcp_nodelay(true)
            .timeout(Duration::from_secs(30))
            .connect_timeout(Duration::from_secs(10))
            .build()
            .expect("Failed to build HTTP client");

        // Scryfall allows ~10 req/sec, we use 100ms delay to be safe
        let rate_limiter = Arc::new(RateLimiter::new(5, 100));

        Self {
            client,
            rate_limiter,
            headers,
        }
    }

    async fn fetch_page(&self, url: &str) -> Result<ScryfallSearchResponse, reqwest::Error> {
        self.rate_limiter.acquire().await;

        let response = self
            .client
            .get(url)
            .headers(self.headers.clone())
            .send()
            .await?;

        response.error_for_status()?.json().await
    }

    /// Fetch all cards for a single query (paginated - must be sequential)
    async fn fetch_all_cards(&self, query: &str) -> Result<Vec<Card>, reqwest::Error> {
        let mut all_cards: Vec<Card> = Vec::new();
        let mut next_url: Option<String> = Some(format!(
            "https://api.scryfall.com/cards/search?q={}",
            query
        ));

        let mut page = 1;
        let start = Instant::now();

        while let Some(url) = next_url {
            println!("Fetching page {}...", page);

            let search_result = self.fetch_page(&url).await?;

            println!(
                "  Got {} cards (total: {}) [{:.2}s elapsed]",
                search_result.data.len(),
                search_result.total_cards,
                start.elapsed().as_secs_f64()
            );

            all_cards.extend(search_result.data);

            next_url = if search_result.has_more {
                page += 1;
                search_result.next_page
            } else {
                None
            };
        }

        Ok(all_cards)
    }

    /// Fetch multiple queries concurrently (rate-limited)
    async fn fetch_multiple_queries(&self, queries: Vec<&str>) -> Vec<Result<Vec<Card>, reqwest::Error>> {
        let futures: Vec<_> = queries
            .into_iter()
            .map(|query| self.fetch_all_cards(query))
            .collect();

        // Run all queries concurrently - rate limiter handles throttling
        futures::future::join_all(futures).await
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = ScryfallClient::new();
    let start = Instant::now();

    // Example: fetch all creatures (17,709+ cards)
    let queries = vec!["type:creature"];
    
    println!("Starting concurrent fetch of {} queries...\n", queries.len());
    
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
