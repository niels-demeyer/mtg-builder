FROM rust:1.85-slim-bookworm AS build

RUN apt-get update && apt-get install -y pkg-config libssl-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY Cargo.toml Cargo.lock* ./
# Create dummy src to cache dependency compilation
RUN mkdir src && echo "fn main() {}" > src/main.rs && echo "" > src/lib.rs
RUN cargo build --release 2>/dev/null || true

COPY src ./src
# Touch main.rs so cargo rebuilds our code, not just deps
RUN touch src/main.rs src/lib.rs
RUN cargo build --release

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y ca-certificates libssl3 && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/target/release/scripts /usr/local/bin/scripts

CMD ["scripts"]
