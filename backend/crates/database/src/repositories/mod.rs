//! Repository implementations for database entities
//!
//! This module contains repository traits and implementations for
//! accessing and manipulating database entities.

pub mod card;
pub mod deck;

pub use card::CardRepository;
pub use deck::DeckRepository;

use crate::error::Result;
use sqlx::PgPool;

/// Base repository trait for common database operations
#[allow(async_fn_in_trait)]
pub trait Repository<T, ID> {
    /// Find an entity by its ID
    async fn find_by_id(&self, id: ID) -> Result<Option<T>>;

    /// Find all entities
    async fn find_all(&self) -> Result<Vec<T>>;

    /// Create a new entity
    async fn create(&self, entity: &T) -> Result<T>;

    /// Update an existing entity
    async fn update(&self, entity: &T) -> Result<T>;

    /// Delete an entity by its ID
    async fn delete(&self, id: ID) -> Result<bool>;
}

/// Trait for repositories that support pagination
#[allow(async_fn_in_trait)]
pub trait Paginated<T> {
    /// Find entities with pagination
    async fn find_paginated(&self, page: u32, page_size: u32) -> Result<PaginatedResult<T>>;
}

/// Paginated query result
#[derive(Debug, Clone)]
pub struct PaginatedResult<T> {
    /// The items in this page
    pub items: Vec<T>,
    /// Total number of items
    pub total: i64,
    /// Current page (1-indexed)
    pub page: u32,
    /// Number of items per page
    pub page_size: u32,
    /// Total number of pages
    pub total_pages: u32,
}

impl<T> PaginatedResult<T> {
    /// Create a new paginated result
    pub fn new(items: Vec<T>, total: i64, page: u32, page_size: u32) -> Self {
        let total_pages = ((total as f64) / (page_size as f64)).ceil() as u32;
        Self {
            items,
            total,
            page,
            page_size,
            total_pages,
        }
    }

    /// Check if there is a next page
    pub fn has_next(&self) -> bool {
        self.page < self.total_pages
    }

    /// Check if there is a previous page
    pub fn has_previous(&self) -> bool {
        self.page > 1
    }
}

/// Helper struct for database context in axum handlers
#[derive(Clone)]
pub struct DbContext {
    pool: PgPool,
}

impl DbContext {
    /// Create a new database context
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Get a reference to the connection pool
    pub fn pool(&self) -> &PgPool {
        &self.pool
    }

    /// Get the card repository
    pub fn cards(&self) -> CardRepository {
        CardRepository::new(self.pool.clone())
    }

    /// Get the deck repository
    pub fn decks(&self) -> DeckRepository {
        DeckRepository::new(self.pool.clone())
    }
}
