FROM rust:1-alpine AS build
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release

FROM scratch
WORKDIR /app
COPY --from=build /app/target/release/mock-nanoleaf /app/mock-nanoleaf
CMD ["/app/mock-nanoleaf"]
