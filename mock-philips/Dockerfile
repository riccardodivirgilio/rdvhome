FROM rust:1-alpine AS build
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release

FROM alpine:3
WORKDIR /app
COPY --from=build /app/target/release/mock-philips /app/mock-philips
CMD ["/app/mock-philips"]
