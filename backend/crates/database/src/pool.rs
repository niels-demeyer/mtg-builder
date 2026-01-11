//! Database connection pool

use crate::config::DatabaseConfig;
use crate::error::{DatabaseError, Result};
use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;
use std::time::Duration;
use tracing::{info, instrument};

/// Database connection pool wrapper
#[derive(Debug, Clone)]
pub struct DatabasePool {
    pool: PgPool,
}

impl DatabasePool {
    /// Create a new database pool from configuration
    #[instrument(skip(config), fields(host = %config.host, database = %config.database))]
    pub async fn new(config: &DatabaseConfig) -> Result<Self> {
        info!("Creating database connection pool");

        let pool = PgPoolOptions::new()
            .max_connections(config.max_connections)
            .min_connections(config.min_connections)
            .acquire_timeout(Duration::from_secs(config.connect_timeout_secs))
            .connect(&config.connection_url())
            .await
            .map_err(|e| DatabaseError::ConnectionError(e.to_string()))?;

        info!("Database connection pool created successfully");

        Ok(Self { pool })
    }

    /// Create a pool from a database URL
    #[instrument(skip(url))]
    pub async fn from_url(url: &str) -> Result<Self> {
        let config = DatabaseConfig::from_url(url)?;
        Self::new(&config).await
    }

    /// Create a pool from environment variables
    #[instrument]
    pub async fn from_env() -> Result<Self> {
        let config = DatabaseConfig::from_env()?;
        Self::new(&config).await
    }

    /// Get a reference to the underlying pool
    pub fn inner(&self) -> &PgPool {
        &self.pool
    }

    /// Get the underlying pool (consumes self)
    pub fn into_inner(self) -> PgPool {
        self.pool
    }

    /// Check if the database connection is healthy
    #[instrument(skip(self))]
    pub async fn health_check(&self) -> Result<()> {
        sqlx::query("SELECT 1")
            .execute(&self.pool)
            .await
            .map_err(|e| DatabaseError::ConnectionError(format!("Health check failed: {}", e)))?;
        Ok(())
    }

    /// Run database migrations
    #[instrument(skip(self))]
    pub async fn run_migrations(&self) -> Result<()> {
        info!("Running database migrations");
        
        sqlx::migrate!("./migrations")
            .run(&self.pool)
            .await
            .map_err(|e| DatabaseError::MigrationError(e.to_string()))?;

        info!("Database migrations completed successfully");
        Ok(())
    }

    /// Close the connection pool
    #[instrument(skip(self))]
    pub async fn close(&self) {
        info!("Closing database connection pool");
        self.pool.close().await;
    }
}

impl AsRef<PgPool> for DatabasePool {
    fn as_ref(&self) -> &PgPool {
        &self.pool
    }
}

impl From<PgPool> for DatabasePool {
    fn from(pool: PgPool) -> Self {
        Self { pool }
    }
}
