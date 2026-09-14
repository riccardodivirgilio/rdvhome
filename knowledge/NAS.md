# NAS — rdvnas

TrueNAS SCALE, x86-64 (ASRock), primary NIC `enp8s0`. On the **Server VLAN** at **`10.10.6.15`**
(UniFi DHCP reservation, UXG port 1), default route `10.10.6.1`. SSH `truenas_admin@10.10.6.15`
(also link-local `fe80::9e6b:ff:feb7:1548%en11` when the laptop shares its L2). `nas.impazzito.it`
→ `10.10.6.15` (a UniFi per-client local DNS record on the NAS reservation).

Moved here from the old pre-UniFi `192.168.67.15` — anything referencing that old IP breaks (see
`internal.impazzito.it` below).

## DNS resolver — important

`/etc/resolv.conf` **nameserver1 = `10.10.6.1`** (the UniFi gateway), `1.1.1.1` fallback — set via
`midclt call network.configuration.update '{"nameserver1":"10.10.6.1","nameserver2":"1.1.1.1"}'`.
This is required so the NAS (and its containers) honor UniFi **local DNS overrides**. **Do not
revert to `1.1.1.1`** or NPM upstreams (which resolve `internal.impazzito.it`) break.

## Apps (TrueNAS, Docker)

`nginx-proxy-manager`, `jellyfin`, `radarr`, `sonarr`, `prowlarr`, `bazarr`, `qbittorrent`,
`filebrowser`, `flaresolverr`, `recyclarr`, `unifi-os-server` (custom app, see below and [[LAN]]),
`nitter` and `kittygram` (custom apps, see below).
Deleted: `unifi-controller` (legacy Network app, replaced by UOS 2026-09-14) and `wg-easy`
(WireGuard).

Manage apps through the **middleware**, not `docker restart`:

    midclt call app.query
    midclt call app.redeploy <name>     # returns a job id; poll core.get_jobs
    midclt call app.delete <name>

## Reverse proxy (nginx-proxy-manager)

`ix-nginx-proxy-manager-npm-1`, publishes host `:80`/`:443` (admin UI `:30020`, also
`https://nginx.impazzito.it`). Single admin user **`nginx@nginx.com`**; creds in `~/.npm.env`
(`NPM_URL`/`NPM_EMAIL`/`NPM_PASSWORD`) for the REST API (`POST /api/tokens` → Bearer JWT, then
`/api/nginx/proxy-hosts`). Data is SQLite `/mnt/bolt/apps/nginx-proxy-manager/data/database.sqlite`
(host has `sqlite3`); a forgotten password can be reset by writing a bcrypt hash (made with the
container's `/app/node_modules/bcrypt`) into `auth.secret`. Create hosts via the API, not raw DB
rows: only the API generates the nginx conf and requests the certificate. Certs are Let's Encrypt
**DNS-01 via DigitalOcean**, one per host; copy `meta` from an existing `certificate` row for a
new one. Each service is a
proxy host `<svc>.impazzito.it` with a **UniFi static-dns A record → `10.10.6.15`**
(nas, nginx, files, jellyfin, radarr, sonarr, prowlarr, bazarr, qbittorrent, x, ig).

NPM forwards to the host via upstream **`internal.impazzito.it:<port>`** — **not** `localhost`,
because NPM is containerized (localhost = the container, not the NAS host). So `internal` must
resolve to the NAS's current IP. It is:
- a public **A record** in DigitalOcean (`doctl ... domain records ... impazzito.it`, id `1768600534`) → `10.10.6.15`, and
- a **UniFi local override** → `10.10.6.15`.

After changing `internal`'s IP: **redeploy NPM** (`midclt call app.redeploy nginx-proxy-manager`)
to flush nginx's cached upstream. Symptom of a stale `internal`: HTTPS handshake succeeds (valid
Let's Encrypt cert) but the request **hangs** (bad upstream), *not* a cert error.

Service upstream ports live in each `/data/nginx/proxy_host/<n>.conf` inside the NPM container
(e.g. jellyfin `internal.impazzito.it:30013`).

## Nitter — `x.impazzito.it` (custom app)

Self-hosted X/Twitter front-end, the same code as xcancel.com. The xcancel fork is archived, so
this runs upstream **`zedeus/nitter`**, pinned to image tag `8142bab1…` (2026-08-24), plus
`redis:7-alpine`. Custom app `nitter`, host port **`30080`** → container `8080`.

- Files in `/mnt/bolt/apps/nitter/`: `nitter.conf` (hostname `x.impazzito.it`, `https = true`
  because NPM terminates TLS, `redisHost = "nitter-redis"`, random `hmacKey`), `sessions.jsonl`,
  `redis/`.
- **Needs X account sessions** — X killed guest access. `sessions.jsonl` holds one JSON object
  per line: `{"kind":"cookie","auth_token":"…","ct0":"…","username":"…"}`, taken from a logged-in
  X browser session or generated with upstream `tools/create_session_browser.py`. Only
  `auth_token` is really needed: X returns a fresh `ct0` in `Set-Cookie` for
  `curl -b "auth_token=…" https://x.com/home` (with a browser User-Agent). Redeploy the app after
  editing the file (`midclt call -j app.redeploy nitter`). The log should say `successfully added
  N valid account sessions`; with none, pages fail with 429 "Instance has no auth tokens". Use a
  throwaway account, since X may suspend accounts used this way. Logging out of X invalidates the
  token.
- DNS: UniFi local record `x.impazzito.it` → `10.10.6.15`; public DigitalOcean A record `x` →
  WAN `195.32.7.119` (id `1832246893`, redundant with the `*` wildcard).

## Kittygram — `ig.impazzito.it` (custom app)

Nitter-style Instagram front-end ([codeberg.org/irelephant/kittygram](https://codeberg.org/irelephant/kittygram)).
Bibliogram is dead and Proxigram is abandoned; Kittygram is the maintained one (v1.2.0, Jul 2026).
Custom app `kittygram`: image `codeberg.org/irelephant/kittygram`, pinned by digest `sha256:ce7fef13…`
(built by its Codeberg CI from `main`), plus `valkey/valkey:8-alpine`, which must be named `redis`.
Host port **`30081`** → container `80`. Public (no NPM access list), NPM proxy host id 18.

- Configured entirely by env vars (`lapis serve docker` profile): `SECRET` (random),
  `ENABLE_ATOM=true`, `BASE_ATOM_PATH=https://ig.impazzito.it/`. No volumes; its SQLite (API tokens,
  id cache) lives in the image and resets on redeploy, which is harmless.
- **No Instagram account needed**; the home IP works anonymously for profiles, posts and reels. Stories
  aren't supported. Optional session cookies (`web_session` in `config.lua`) would add search and
  comments.
- Limit: Instagram rate-limits by IP over an 11-minute window; Kittygram budgets 194 requests per
  window and pauses when limited. Heavy public use would exhaust it.
- Profile `/<user>`, post `/p/<code>`, reel `/reel/<code>`, feed `/<user>/atom.xml`.
- DNS: UniFi local record `ig.impazzito.it` → `10.10.6.15`; public DigitalOcean A record `ig` →
  `195.32.7.119` (id `1832247763`).
- Upgrade: pull `:latest`, take its digest, put it in the app's compose, redeploy.

## Controller — UniFi OS Server (custom app)

Migrated 2026-09-14. There's no official TrueNAS app, but the community image
[`ghcr.io/lemker/unifi-os-server`](https://github.com/lemker/unifi-os-server) repackages the official
UOS Server for Docker. Installed as TrueNAS **custom app `unifi-os-server`** (compose YAML via
`app.create` `custom_compose_config_string`), image pinned to **`v1.7.0`** (UOS 5.1.42). Container
`ix-unifi-os-server-unifi-os-server-1`; it runs systemd, so it needs `cgroup: host`, the
`/sys/fs/cgroup` rw mount, `NET_ADMIN`/`NET_RAW` and the tmpfs mounts (no `privileged`).

- Env `UOS_SYSTEM_IP=10.10.6.15`. Data under `/mnt/bolt/apps/unifi-os-server/*` (root-owned).
- Ports: UI **`https://10.10.6.15:11443`** (self-signed cert, HTTPS only), inform `8080`,
  STUN `3478/udp`, discovery `10003/udp`, speedtest `6789`, syslog `5514/udp`.
- Same IP + inform port as the old controller, so the UXG and AP re-informed on their own — no
  `set-inform` needed.
- Owner is a **UI account** (cloud sign-in). The setup's "Restore From Backup" lists cloud backups
  of the account's **other consoles (Magliana, Tiberio)** — never pick those; use *upload*.
- Restoring a `.unf` from a newer Network version works: setup auto-installs the matching Network
  version first (bundled 10.5.67 → 10.6.101).
- Mongo is **v3.6** (wire version 6) at `127.0.0.1:27117`, db `ace` — `mongosh`/`mongo:8.0`
  refuse it; use the legacy shell:

      docker run --rm --network container:ix-unifi-os-server-unifi-os-server-1 mongo:4.4 mongo mongodb://127.0.0.1:27117/ace ...

- Upgrades: bump the image tag in the app's compose and redeploy.

Backups: `.unf` files in `~/Private/unifi-backups/` on the laptop (pre-migration
`10.6.101_20260914_2303.unf`). The legacy controller app and its data were deleted after the
migration, so these files are the only way back.
