use std::collections::HashSet;

use crate::error::QueryValidationError;

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
        ]
        .into_iter()
        .collect();

        let valid_operators: HashSet<&'static str> =
            ["or", "and", "-", "not"].into_iter().collect();

        let valid_comparisons: HashSet<&'static str> =
            [":", "=", "!=", "<", ">", "<=", ">="].into_iter().collect();

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
