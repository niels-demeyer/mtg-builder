//! Database configuration

use crate::error::{DatabaseError, Result};

/// Database configuration
#[derive(Debug, Clone)]
pub struct DatabaseConfig {
    /// Database host
    pub host: String,
    /// Database port
    pub port: u16,
    /// Database username
    pub username: String,
    /// Database password
    pub password: String,
    /// Database name
    pub database: String,
    /// Maximum number of connections in the pool
    pub max_connections: u32,
    /// Minimum number of connections in the pool
    pub min_connections: u32,
    /// Connection timeout in seconds
    pub connect_timeout_secs: u64,
    /// Enable SSL
    pub ssl_mode: SslMode,
}

/// SSL mode for database connections
#[derive(Debug, Clone, Default)]
pub enum SslMode {
    /// Disable SSL
    #[default]
    Disable,
    /// Prefer SSL but allow non-SSL
    Prefer,
    /// Require SSL
    Require,
}

impl SslMode {
    fn as_str(&self) -> &'static str {
        match self {
            SslMode::Disable => "disable",
            SslMode::Prefer => "prefer",
            SslMode::Require => "require",
        }
    }
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            host: "localhost".to_string(),
            port: 5432,
            username: "postgres".to_string(),
            password: String::new(),
            database: "mtg_builder".to_string(),
            max_connections: 10,
            min_connections: 1,
            connect_timeout_secs: 30,
            ssl_mode: SslMode::default(),
        }
    }
}

impl DatabaseConfig {
    /// Create a new database configuration
    pub fn new(host: &str, port: u16, username: &str, password: &str, database: &str) -> Self {
        Self {
            host: host.to_string(),
            port,
            username: username.to_string(),
            password: password.to_string(),
            database: database.to_string(),
            ..Default::default()
        }
    }

    /// Create configuration from environment variables
    pub fn from_env() -> Result<Self> {
        let host = std::env::var("DATABASE_HOST").unwrap_or_else(|_| "localhost".to_string());
        let port = std::env::var("DATABASE_PORT")
            .unwrap_or_else(|_| "5432".to_string())
            .parse::<u16>()
            .map_err(|e| DatabaseError::ConfigError(format!("Invalid port: {}", e)))?;
        let username =
            std::env::var("DATABASE_USER").unwrap_or_else(|_| "postgres".to_string());
        let password = std::env::var("DATABASE_PASSWORD").unwrap_or_default();
        let database =
            std::env::var("DATABASE_NAME").unwrap_or_else(|_| "mtg_builder".to_string());
        let max_connections = std::env::var("DATABASE_MAX_CONNECTIONS")
            .unwrap_or_else(|_| "10".to_string())
            .parse::<u32>()
            .map_err(|e| DatabaseError::ConfigError(format!("Invalid max_connections: {}", e)))?;

        Ok(Self {
            host,
            port,
            username,
            password,
            database,
            max_connections,
            ..Default::default()
        })
    }

    /// Create configuration from a database URL
    pub fn from_url(url: &str) -> Result<Self> {
        // Parse the URL to extract components
        // Format: postgres://user:password@host:port/database
        let url = url::Url::parse(url)
            .map_err(|e| DatabaseError::ConfigError(format!("Invalid database URL: {}", e)))?;

        let host = url
            .host_str()
            .ok_or_else(|| DatabaseError::ConfigError("Missing host in URL".to_string()))?
            .to_string();

        let port = url.port().unwrap_or(5432);
        let username = url.username().to_string();
        let password = url.password().unwrap_or("").to_string();
        let database = url.path().trim_start_matches('/').to_string();

        if database.is_empty() {
            return Err(DatabaseError::ConfigError(
                "Missing database name in URL".to_string(),
            ));
        }

        Ok(Self {
            host,
            port,
            username,
            password,
            database,
            ..Default::default()
        })
    }

    /// Build the connection URL
    pub fn connection_url(&self) -> String {
        format!(
            "postgres://{}:{}@{}:{}/{}?sslmode={}",
            self.username,
            self.password,
            self.host,
            self.port,
            self.database,
            self.ssl_mode.as_str()
        )
    }

    /// Set the maximum number of connections
    pub fn with_max_connections(mut self, max: u32) -> Self {
        self.max_connections = max;
        self
    }

    /// Set the minimum number of connections
    pub fn with_min_connections(mut self, min: u32) -> Self {
        self.min_connections = min;
        self
    }

    /// Set the connection timeout
    pub fn with_connect_timeout(mut self, secs: u64) -> Self {
        self.connect_timeout_secs = secs;
        self
    }

    /// Set the SSL mode
    pub fn with_ssl_mode(mut self, mode: SslMode) -> Self {
        self.ssl_mode = mode;
        self
    }
}
