use std::time::{Duration, Instant};
use tokio::sync::{Mutex, Semaphore};

/// Rate limiter that enforces Scryfall's API limits (max 10 req/sec, 100ms between requests)
pub struct RateLimiter {
    last_request: Mutex<Instant>,
    semaphore: Semaphore,
    min_delay: Duration,
}

impl RateLimiter {
    pub fn new(max_concurrent: usize, min_delay_ms: u64) -> Self {
        Self {
            last_request: Mutex::new(Instant::now() - Duration::from_secs(1)),
            semaphore: Semaphore::new(max_concurrent),
            min_delay: Duration::from_millis(min_delay_ms),
        }
    }

    pub async fn acquire(&self) {
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
