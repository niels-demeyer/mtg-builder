use std::sync::Arc;

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
            QueryValidationError::UnbalancedParentheses => {
                write!(f, "Unbalanced parentheses in query")
            }
            QueryValidationError::UnbalancedQuotes => write!(f, "Unbalanced quotes in query"),
            QueryValidationError::InvalidOperator(op) => write!(f, "Invalid operator: '{}'", op),
            QueryValidationError::InvalidField(field) => write!(f, "Invalid field: '{}'", field),
            QueryValidationError::InvalidComparison(cmp) => {
                write!(f, "Invalid comparison: '{}'", cmp)
            }
            QueryValidationError::ConsecutiveOperators => {
                write!(f, "Consecutive operators are not allowed")
            }
            QueryValidationError::TrailingOperator => {
                write!(f, "Query cannot end with an operator")
            }
            QueryValidationError::LeadingOperator => {
                write!(f, "Query cannot start with an operator")
            }
        }
    }
}

impl std::error::Error for QueryValidationError {}

/// Error type for Scryfall client operations
#[derive(Debug, Clone)]
pub enum ScryfallError {
    ValidationError(QueryValidationError),
    RequestError(Arc<reqwest::Error>),
    DatabaseError(String),
}

impl std::fmt::Display for ScryfallError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ScryfallError::ValidationError(e) => write!(f, "Query validation failed: {}", e),
            ScryfallError::RequestError(e) => write!(f, "Request failed: {}", e),
            ScryfallError::DatabaseError(e) => write!(f, "Database error: {}", e),
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
