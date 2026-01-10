use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};
use std::sync::Arc;
use std::time::{Duration, Instant};

use crate::error::{QueryValidationError, ScryfallError};
use crate::models::{Card, ScryfallSearchResponse};
use crate::rate_limiter::RateLimiter;
use crate::validator::QueryValidator;

/// Optimized client with connection pooling, rate limiting, and query validation
pub struct ScryfallClient {
    client: reqwest::Client,
    rate_limiter: Arc<RateLimiter>,
    headers: HeaderMap,
    validator: QueryValidator,
}

impl ScryfallClient {
    pub fn new() -> Self {
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
        let validator = QueryValidator::new();

        Self {
            client,
            rate_limiter,
            headers,
            validator,
        }
    }

    /// Validate a query without sending it
    pub fn validate_query(&self, query: &str) -> Result<(), QueryValidationError> {
        self.validator.validate(query)
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

    /// Fetches a single page of JSON response
    async fn fetch_json_page(&self, url: &str) -> Result<serde_json::Value, ScryfallError> {
        self.rate_limiter.acquire().await;

        let response = self
            .client
            .get(url)
            .headers(self.headers.clone())
            .send()
            .await?;

        let json: serde_json::Value = response.error_for_status()?.json().await?;
        Ok(json)
    }

    /// Fetches and prints the full JSON response for a query
    /// Validates the query before sending to ensure correct syntax
    pub async fn print_full_json_response(&self, query: &str) -> Result<(), ScryfallError> {
        // Validate query before sending
        self.validator.validate(query)?;

        let encoded_query = self.validator.encode_query(query);
        let url = format!(
            "https://api.scryfall.com/cards/search?q={}",
            encoded_query
        );

        let json = self.fetch_json_page(&url).await?;
        println!("Query: {}", query);
        println!("{}", serde_json::to_string_pretty(&json).unwrap());

        Ok(())
    }

    /// Fetches all pages of JSON data for a query and returns them
    /// Validates the query before sending to ensure correct syntax
    pub async fn fetch_all_json(
        &self,
        query: &str,
    ) -> Result<Vec<serde_json::Value>, ScryfallError> {
        // Validate query before sending
        self.validator.validate(query)?;

        let encoded_query = self.validator.encode_query(query);
        let mut all_pages: Vec<serde_json::Value> = Vec::new();
        let mut next_url: Option<String> = Some(format!(
            "https://api.scryfall.com/cards/search?q={}",
            encoded_query
        ));

        let mut page = 1;
        let start = std::time::Instant::now();

        while let Some(url) = next_url {
            println!("Fetching page {}...", page);

            let json = self.fetch_json_page(&url).await?;

            let card_count = json["data"].as_array().map(|a| a.len()).unwrap_or(0);
            let total = json["total_cards"].as_u64().unwrap_or(0);

            println!(
                "  Got {} cards (total: {}) [{:.2}s elapsed]",
                card_count,
                total,
                start.elapsed().as_secs_f64()
            );

            let has_more = json["has_more"].as_bool().unwrap_or(false);
            let next_page = json["next_page"].as_str().map(|s| s.to_string());

            all_pages.push(json);

            next_url = if has_more { next_page } else { None };
            page += 1;
        }

        Ok(all_pages)
    }

    /// Fetch all cards for a single query (paginated - must be sequential)
    /// Validates the query before sending to ensure correct syntax
    pub async fn fetch_all_cards(&self, query: &str) -> Result<Vec<Card>, ScryfallError> {
        // Validate query before sending
        self.validator.validate(query)?;

        let encoded_query = self.validator.encode_query(query);
        let mut all_cards: Vec<Card> = Vec::new();
        let mut next_url: Option<String> = Some(format!(
            "https://api.scryfall.com/cards/search?q={}",
            encoded_query
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

    /// Validate multiple queries without sending them
    /// Returns a list of (query, validation_result) tuples
    pub fn validate_queries<'a>(
        &self,
        queries: &[&'a str],
    ) -> Vec<(&'a str, Result<(), QueryValidationError>)> {
        queries
            .iter()
            .map(|q| (*q, self.validator.validate(q)))
            .collect()
    }

    /// Fetch multiple queries concurrently (rate-limited)
    /// All queries are validated before any requests are sent
    pub async fn fetch_multiple_queries(
        &self,
        queries: Vec<&str>,
    ) -> Vec<Result<Vec<Card>, ScryfallError>> {
        // Pre-validate all queries
        let validation_results: Vec<_> = self.validate_queries(&queries);

        // Check if any queries failed validation
        let mut has_invalid = false;
        for (query, result) in &validation_results {
            if let Err(e) = result {
                println!("⚠ Query validation failed for '{}': {}", query, e);
                has_invalid = true;
            }
        }

        if has_invalid {
            println!("\n⚠ Some queries failed validation. Only valid queries will be executed.\n");
        }

        // Filter to only valid queries and track their original indices
        let valid_queries: Vec<(usize, &str)> = validation_results
            .iter()
            .enumerate()
            .filter_map(|(i, (q, r))| r.is_ok().then_some((i, *q)))
            .collect();

        // Execute valid queries
        let futures: Vec<_> = valid_queries
            .iter()
            .map(|(_, query)| self.fetch_all_cards(query))
            .collect();

        let fetch_results = futures::future::join_all(futures).await;

        // Reconstruct results in original order, with validation errors for invalid queries
        let mut results: Vec<Result<Vec<Card>, ScryfallError>> = Vec::with_capacity(queries.len());
        let mut fetch_idx = 0;

        for (_, result) in validation_results {
            match result {
                Ok(()) => {
                    results.push(fetch_results[fetch_idx].clone());
                    fetch_idx += 1;
                }
                Err(e) => {
                    results.push(Err(ScryfallError::ValidationError(e)));
                }
            }
        }

        results
    }
}

impl Default for ScryfallClient {
    fn default() -> Self {
        Self::new()
    }
}
