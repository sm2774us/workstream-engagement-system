FROM rust:1.81-slim AS build
WORKDIR /src
RUN apt-get update && apt-get install -y protobuf-compiler && rm -rf /var/lib/apt/lists/*
COPY Cargo.toml build.rs ./
COPY proto ./proto
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
COPY --from=build /src/target/release/wes-risk-engine /usr/local/bin/wes-risk-engine
EXPOSE 8080 50051
CMD ["wes-risk-engine"]
