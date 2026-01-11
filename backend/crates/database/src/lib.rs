//! Database crate for MTG Builder
//!
//! This crate provides database connectivity and query functionality
//! using sqlx with PostgreSQL for the MTG Builder application.

pub mod config;
pub mod error;
pub mod pool;
pub mod repositories;

pub use config::DatabaseConfig;
pub use error::{DatabaseError, Result};
pub use pool::DatabasePool;

/// Re-export commonly used sqlx types
pub use sqlx::{PgPool, Row};
