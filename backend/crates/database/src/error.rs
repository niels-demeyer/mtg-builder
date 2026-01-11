//! Database error types

use thiserror::Error;

/// Result type alias for database operations
pub type Result<T> = std::result::Result<T, DatabaseError>;

/// Database error types
#[derive(Error, Debug)]
pub enum DatabaseError {
    /// Connection error
    #[error("Failed to connect to database: {0}")]
    ConnectionError(String),

    /// Query execution error
    #[error("Query execution failed: {0}")]
    QueryError(String),

    /// Record not found
    #[error("Record not found: {0}")]
    NotFound(String),

    /// Duplicate record error
    #[error("Duplicate record: {0}")]
    DuplicateRecord(String),

    /// Configuration error
    #[error("Configuration error: {0}")]
    ConfigError(String),

    /// Migration error
    #[error("Migration error: {0}")]
    MigrationError(String),

    /// Transaction error
    #[error("Transaction error: {0}")]
    TransactionError(String),

    /// Sqlx error wrapper
    #[error("Database error: {0}")]
    Sqlx(#[from] sqlx::Error),
}

impl DatabaseError {
    /// Check if the error is a not found error
    pub fn is_not_found(&self) -> bool {
        matches!(self, DatabaseError::NotFound(_))
    }

    /// Check if the error is a duplicate record error
    pub fn is_duplicate(&self) -> bool {
        matches!(self, DatabaseError::DuplicateRecord(_))
    }
}
