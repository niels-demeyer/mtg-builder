use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};
use serde::Deserialize;
use std::collections::HashSet;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, Semaphore};

/// Validation error types for Scryfall queries
#[derive(Debug, Clone)]
pub enum QueryValidationError {
    EmptyQuery,
    UnbalancedParentheses,
    UnbalancedQuotes,
    InvalidOperator(String),
    InvalidField(String),
    InvalidComparison(String),
    ConsecutiveOperators,
    TrailingOperator,
    LeadingOperator,
}

impl std::fmt::Display for QueryValidationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            QueryValidationError::EmptyQuery => write!(f, "Query cannot be empty"),
            QueryValidationError::UnbalancedParentheses => write!(f, "Unbalanced parentheses in query"),
            QueryValidationError::UnbalancedQuotes => write!(f, "Unbalanced quotes in query"),
            QueryValidationError::InvalidOperator(op) => write!(f, "Invalid operator: '{}'", op),
            QueryValidationError::InvalidField(field) => write!(f, "Invalid field: '{}'", field),
            QueryValidationError::InvalidComparison(cmp) => write!(f, "Invalid comparison: '{}'", cmp),
            QueryValidationError::ConsecutiveOperators => write!(f, "Consecutive operators are not allowed"),
            QueryValidationError::TrailingOperator => write!(f, "Query cannot end with an operator"),
            QueryValidationError::LeadingOperator => write!(f, "Query cannot start with an operator"),
        }
    }
}

impl std::error::Error for QueryValidationError {}

/// Validates Scryfall query syntax before sending requests
#[allow(dead_code)]
pub struct QueryValidator {
    valid_fields: HashSet<&'static str>,
    valid_operators: HashSet<&'static str>,
    valid_comparisons: HashSet<&'static str>,
}

impl QueryValidator {
    pub fn new() -> Self {
        // Scryfall supported search fields
        let valid_fields: HashSet<&'static str> = [
            // Card name and text
            "name", "oracle", "type", "o", "t", "m", "mana", "devotion",
            // Colors and identity
            "c", "color", "id", "identity", "ci",
            // Card stats
            "cmc", "mv", "manavalue", "power", "pow", "toughness", "tou", "loyalty", "loy",
            // Rarity and set info
            "r", "rarity", "s", "set", "e", "edition", "cn", "number",
            // Format legality
            "f", "format", "legal", "banned", "restricted",
            // Card types
            "is", "not", "has",
            // Prices and availability
            "usd", "eur", "tix", "price",
            // Art and frames
            "art", "artist", "flavor", "ft", "watermark", "wm",
            // Misc
            "year", "date", "lang", "game", "new", "order", "unique", "prefer",
            "include", "border", "frame", "stamp", "keyword",
        ].into_iter().collect();

        let valid_operators: HashSet<&'static str> = [
            "or", "and", "-", "not",
        ].into_iter().collect();

        let valid_comparisons: HashSet<&'static str> = [
            ":", "=", "!=", "<", ">", "<=", ">=",
        ].into_iter().collect();

        Self {
            valid_fields,
            valid_operators,
            valid_comparisons,
        }
    }

    /// Validate a query string before sending to Scryfall
    pub fn validate(&self, query: &str) -> Result<(), QueryValidationError> {
        let trimmed = query.trim();

        // Check for empty query
        if trimmed.is_empty() {
            return Err(QueryValidationError::EmptyQuery);
        }

        // Check for balanced parentheses
        self.check_balanced_parens(trimmed)?;

        // Check for balanced quotes
        self.check_balanced_quotes(trimmed)?;

        // Check for valid field:value patterns
        self.check_field_syntax(trimmed)?;

        // Check for operator positioning
        self.check_operator_positioning(trimmed)?;

        Ok(())
    }

    fn check_balanced_parens(&self, query: &str) -> Result<(), QueryValidationError> {
        let mut depth = 0i32;
        let mut in_quotes = false;

        for ch in query.chars() {
            match ch {
                '"' => in_quotes = !in_quotes,
                '(' if !in_quotes => depth += 1,
                ')' if !in_quotes => {
                    depth -= 1;
                    if depth < 0 {
                        return Err(QueryValidationError::UnbalancedParentheses);
                    }
                }
                _ => {}
            }
        }

        if depth != 0 {
            return Err(QueryValidationError::UnbalancedParentheses);
        }

        Ok(())
    }

    fn check_balanced_quotes(&self, query: &str) -> Result<(), QueryValidationError> {
        let quote_count = query.chars().filter(|&c| c == '"').count();
        if quote_count % 2 != 0 {
            return Err(QueryValidationError::UnbalancedQuotes);
        }
        Ok(())
    }

    fn check_field_syntax(&self, query: &str) -> Result<(), QueryValidationError> {
        // Extract field:value patterns, excluding quoted strings
        let mut in_quotes = false;
        let mut current_field = String::new();
        let mut chars = query.chars().peekable();

        while let Some(ch) = chars.next() {
            match ch {
                '"' => {
                    in_quotes = !in_quotes;
                    current_field.clear();
                }
                ':' | '=' | '<' | '>' | '!' if !in_quotes => {
                    // Handle multi-character operators like !=, <=, >=
                    // The '!' is part of '!=' operator, so we treat it as a comparison char
                    // Check if field is valid (only if we have one)
                    let field = current_field.trim().to_lowercase();
                    if !field.is_empty()
                        && !field.starts_with('-')
                        && !self.valid_fields.contains(field.trim_start_matches('-'))
                    {
                        // Allow bare words before comparison operators
                        if !field.chars().all(|c| c.is_alphanumeric() || c == '_') {
                            return Err(QueryValidationError::InvalidField(field));
                        }
                    }
                    current_field.clear();
                }
                ' ' | '(' | ')' if !in_quotes => {
                    current_field.clear();
                }
                _ if !in_quotes => {
                    current_field.push(ch);
                }
                _ => {}
            }
        }

        Ok(())
    }

    fn check_operator_positioning(&self, query: &str) -> Result<(), QueryValidationError> {
        let trimmed = query.trim().to_lowercase();
        let words: Vec<&str> = trimmed.split_whitespace().collect();

        if words.is_empty() {
            return Ok(());
        }

        // Check for leading "or" or "and" operators
        if let Some(first) = words.first() {
            if *first == "or" || *first == "and" {
                return Err(QueryValidationError::LeadingOperator);
            }
        }

        // Check for trailing "or" or "and" operators
        if let Some(last) = words.last() {
            if *last == "or" || *last == "and" {
                return Err(QueryValidationError::TrailingOperator);
            }
        }

        // Check for consecutive operators
        let mut prev_was_operator = false;
        for word in words {
            let is_operator = word == "or" || word == "and";
            if is_operator && prev_was_operator {
                return Err(QueryValidationError::ConsecutiveOperators);
            }
            prev_was_operator = is_operator;
        }

        Ok(())
    }

    /// URL-encode a validated query for use in API requests
    pub fn encode_query(&self, query: &str) -> String {
        urlencoding::encode(query).into_owned()
    }
}

impl Default for QueryValidator {
    fn default() -> Self {
        Self::new()
    }
}

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

/// Error type for Scryfall client operations
#[derive(Debug, Clone)]
pub enum ScryfallError {
    ValidationError(QueryValidationError),
    RequestError(Arc<reqwest::Error>),
}

impl std::fmt::Display for ScryfallError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ScryfallError::ValidationError(e) => write!(f, "Query validation failed: {}", e),
            ScryfallError::RequestError(e) => write!(f, "Request failed: {}", e),
        }
    }
}

impl std::error::Error for ScryfallError {}

impl From<QueryValidationError> for ScryfallError {
    fn from(err: QueryValidationError) -> Self {
        ScryfallError::ValidationError(err)
    }
}

impl From<reqwest::Error> for ScryfallError {
    fn from(err: reqwest::Error) -> Self {
        ScryfallError::RequestError(Arc::new(err))
    }
}

/// Optimized client with connection pooling, rate limiting, and query validation
struct ScryfallClient {
    client: reqwest::Client,
    rate_limiter: Arc<RateLimiter>,
    headers: HeaderMap,
    validator: QueryValidator,
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

    /// Fetch all cards for a single query (paginated - must be sequential)
    /// Validates the query before sending to ensure correct syntax
    async fn fetch_all_cards(&self, query: &str) -> Result<Vec<Card>, ScryfallError> {
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
    pub fn validate_queries<'a>(&self, queries: &[&'a str]) -> Vec<(&'a str, Result<(), QueryValidationError>)> {
        queries
            .iter()
            .map(|q| (*q, self.validator.validate(q)))
            .collect()
    }

    /// Fetch multiple queries concurrently (rate-limited)
    /// All queries are validated before any requests are sent
    async fn fetch_multiple_queries(&self, queries: Vec<&str>) -> Vec<Result<Vec<Card>, ScryfallError>> {
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

#[cfg(test)]
mod tests {
    use super::*;

    fn validator() -> QueryValidator {
        QueryValidator::new()
    }

    // ==================== Valid Query Tests ====================

    #[test]
    fn test_valid_simple_query() {
        let v = validator();
        assert!(v.validate("type:creature").is_ok());
    }

    #[test]
    fn test_valid_color_query() {
        let v = validator();
        assert!(v.validate("c:red").is_ok());
        assert!(v.validate("color:blue").is_ok());
        assert!(v.validate("id:boros").is_ok());
    }

    #[test]
    fn test_valid_comparison_operators() {
        let v = validator();
        assert!(v.validate("cmc<=3").is_ok());
        assert!(v.validate("cmc>=5").is_ok());
        assert!(v.validate("power>4").is_ok());
        assert!(v.validate("toughness<2").is_ok());
        assert!(v.validate("cmc=3").is_ok());
        assert!(v.validate("cmc!=4").is_ok());
    }

    #[test]
    fn test_valid_complex_query() {
        let v = validator();
        assert!(v.validate("type:creature c:red cmc<=3").is_ok());
        assert!(v.validate("set:neo rarity:rare").is_ok());
    }

    #[test]
    fn test_valid_or_operator() {
        let v = validator();
        assert!(v.validate("type:creature or type:instant").is_ok());
        assert!(v.validate("c:red or c:blue").is_ok());
    }

    #[test]
    fn test_valid_and_operator() {
        let v = validator();
        assert!(v.validate("type:creature and c:green").is_ok());
    }

    #[test]
    fn test_valid_parentheses() {
        let v = validator();
        assert!(v.validate("(type:creature)").is_ok());
        assert!(v.validate("(type:creature or type:instant)").is_ok());
        assert!(v.validate("(c:red or c:blue) type:creature").is_ok());
        assert!(v.validate("((type:creature))").is_ok());
    }

    #[test]
    fn test_valid_quoted_strings() {
        let v = validator();
        assert!(v.validate("name:\"Lightning Bolt\"").is_ok());
        assert!(v.validate("o:\"draw a card\"").is_ok());
        assert!(v.validate("ft:\"flavor text here\"").is_ok());
    }

    #[test]
    fn test_valid_negation() {
        let v = validator();
        assert!(v.validate("-type:creature").is_ok());
        assert!(v.validate("type:creature -c:red").is_ok());
    }

    #[test]
    fn test_valid_special_fields() {
        let v = validator();
        assert!(v.validate("is:commander").is_ok());
        assert!(v.validate("has:watermark").is_ok());
        assert!(v.validate("f:modern").is_ok());
        assert!(v.validate("rarity:mythic").is_ok());
    }

    // ==================== Empty Query Tests ====================

    #[test]
    fn test_empty_query() {
        let v = validator();
        assert!(matches!(
            v.validate(""),
            Err(QueryValidationError::EmptyQuery)
        ));
    }

    #[test]
    fn test_whitespace_only_query() {
        let v = validator();
        assert!(matches!(
            v.validate("   "),
            Err(QueryValidationError::EmptyQuery)
        ));
        assert!(matches!(
            v.validate("\t\n"),
            Err(QueryValidationError::EmptyQuery)
        ));
    }

    // ==================== Unbalanced Parentheses Tests ====================

    #[test]
    fn test_unbalanced_open_paren() {
        let v = validator();
        assert!(matches!(
            v.validate("(type:creature"),
            Err(QueryValidationError::UnbalancedParentheses)
        ));
    }

    #[test]
    fn test_unbalanced_close_paren() {
        let v = validator();
        assert!(matches!(
            v.validate("type:creature)"),
            Err(QueryValidationError::UnbalancedParentheses)
        ));
    }

    #[test]
    fn test_multiple_unbalanced_parens() {
        let v = validator();
        assert!(matches!(
            v.validate("((type:creature)"),
            Err(QueryValidationError::UnbalancedParentheses)
        ));
        assert!(matches!(
            v.validate("(type:creature))"),
            Err(QueryValidationError::UnbalancedParentheses)
        ));
    }

    #[test]
    fn test_parens_in_quotes_ignored() {
        let v = validator();
        // Parentheses inside quotes should not affect balance
        assert!(v.validate("name:\"(test)\"").is_ok());
        assert!(v.validate("o:\"(draw a card)\"").is_ok());
    }

    // ==================== Unbalanced Quotes Tests ====================

    #[test]
    fn test_unbalanced_quotes_single() {
        let v = validator();
        assert!(matches!(
            v.validate("name:\"Lightning Bolt"),
            Err(QueryValidationError::UnbalancedQuotes)
        ));
    }

    #[test]
    fn test_unbalanced_quotes_triple() {
        let v = validator();
        assert!(matches!(
            v.validate("name:\"test\" o:\"another"),
            Err(QueryValidationError::UnbalancedQuotes)
        ));
    }

    // ==================== Operator Positioning Tests ====================

    #[test]
    fn test_leading_or_operator() {
        let v = validator();
        assert!(matches!(
            v.validate("or type:creature"),
            Err(QueryValidationError::LeadingOperator)
        ));
    }

    #[test]
    fn test_leading_and_operator() {
        let v = validator();
        assert!(matches!(
            v.validate("and type:creature"),
            Err(QueryValidationError::LeadingOperator)
        ));
    }

    #[test]
    fn test_trailing_or_operator() {
        let v = validator();
        assert!(matches!(
            v.validate("type:creature or"),
            Err(QueryValidationError::TrailingOperator)
        ));
    }

    #[test]
    fn test_trailing_and_operator() {
        let v = validator();
        assert!(matches!(
            v.validate("type:creature and"),
            Err(QueryValidationError::TrailingOperator)
        ));
    }

    #[test]
    fn test_consecutive_operators() {
        let v = validator();
        assert!(matches!(
            v.validate("type:creature and and c:red"),
            Err(QueryValidationError::ConsecutiveOperators)
        ));
        assert!(matches!(
            v.validate("type:creature or or c:blue"),
            Err(QueryValidationError::ConsecutiveOperators)
        ));
        assert!(matches!(
            v.validate("type:creature and or c:green"),
            Err(QueryValidationError::ConsecutiveOperators)
        ));
    }

    // ==================== URL Encoding Tests ====================

    #[test]
    fn test_encode_simple_query() {
        let v = validator();
        assert_eq!(v.encode_query("type:creature"), "type%3Acreature");
    }

    #[test]
    fn test_encode_query_with_spaces() {
        let v = validator();
        let encoded = v.encode_query("type:creature c:red");
        assert!(encoded.contains("%20") || encoded.contains("+"));
    }

    #[test]
    fn test_encode_query_with_quotes() {
        let v = validator();
        let encoded = v.encode_query("name:\"Lightning Bolt\"");
        assert!(encoded.contains("%22"));
    }

    // ==================== Edge Cases ====================

    #[test]
    fn test_valid_single_word() {
        let v = validator();
        // A single word without operators should be valid (searches card names)
        assert!(v.validate("lightning").is_ok());
    }

    #[test]
    fn test_case_insensitive_operators() {
        let v = validator();
        // Operators should be case-insensitive
        assert!(v.validate("type:creature OR type:instant").is_ok());
        assert!(v.validate("type:creature AND c:red").is_ok());
    }

    #[test]
    fn test_mixed_valid_query() {
        let v = validator();
        assert!(v.validate("(type:creature or type:instant) c:red cmc<=3 -is:reprint").is_ok());
    }

    #[test]
    fn test_default_trait() {
        let v = QueryValidator::default();
        assert!(v.validate("type:creature").is_ok());
    }

    // ==================== Error Display Tests ====================

    #[test]
    fn test_error_display() {
        assert_eq!(
            format!("{}", QueryValidationError::EmptyQuery),
            "Query cannot be empty"
        );
        assert_eq!(
            format!("{}", QueryValidationError::UnbalancedParentheses),
            "Unbalanced parentheses in query"
        );
        assert_eq!(
            format!("{}", QueryValidationError::UnbalancedQuotes),
            "Unbalanced quotes in query"
        );
        assert_eq!(
            format!("{}", QueryValidationError::LeadingOperator),
            "Query cannot start with an operator"
        );
        assert_eq!(
            format!("{}", QueryValidationError::TrailingOperator),
            "Query cannot end with an operator"
        );
        assert_eq!(
            format!("{}", QueryValidationError::ConsecutiveOperators),
            "Consecutive operators are not allowed"
        );
    }

    #[test]
    fn test_scryfall_error_display() {
        let validation_err = ScryfallError::ValidationError(QueryValidationError::EmptyQuery);
        assert!(format!("{}", validation_err).contains("Query validation failed"));
    }
}
