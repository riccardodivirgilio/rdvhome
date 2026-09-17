# syntax=docker/dockerfile:1
# Static musl binary in a scratch image, like the mock servers. The frontend is
# embedded in the binary: it comes from the `frontend` build context
# (rdvhome/frontend/dist, see docker-compose.yml).
FROM rust:1-alpine AS build
RUN apk add --no-cache musl-dev
WORKDIR /app/rdvhome-rs
COPY --from=frontend . /app/rdvhome/frontend/dist
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/rdvhome-rs/target \
    cargo build --release && cp target/release/rdvhome /rdvhome

FROM scratch
COPY --from=build /rdvhome /rdvhome
ENV RDV_DATA_DIR=/data
EXPOSE 8500
ENTRYPOINT ["/rdvhome"]
CMD ["run"]
