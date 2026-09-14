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
`filebrowser`, `flaresolverr`, `recyclarr`, `unifi-controller` (see [[LAN]]). `wg-easy` (WireGuard)
was deleted.

Manage apps through the **middleware**, not `docker restart`:

    midclt call app.query
    midclt call app.redeploy <name>     # returns a job id; poll core.get_jobs
    midclt call app.delete <name>

## Reverse proxy (nginx-proxy-manager)

`ix-nginx-proxy-manager-npm-1`, publishes host `:80`/`:443` (admin UI `:30020`). Each service is a
proxy host `<svc>.impazzito.it` with a **UniFi static-dns A record → `10.10.6.15`**
(nas, nginx, files, jellyfin, radarr, sonarr, prowlarr, bazarr, qbittorrent).

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

## Controller

Runs the UniFi Network app (see [[LAN]]). Mongo is v8 at `127.0.0.1:27117` inside the container
with **no shell client** — use an ephemeral one sharing the netns:

    docker run --rm --network container:ix-unifi-controller-unifi-1 mongo:8.0 mongosh mongodb://127.0.0.1:27117/ace ...

## Migration to UniFi OS Server (later)

UOS Server can't run as a TrueNAS app — it needs a dedicated Debian/Ubuntu x86-64 host (~4 GB RAM),
either a **TrueNAS VM** or a mini-PC. Then: install UOS Server (UI at `:11443`) → install Network
app → restore a `.unf` backup from the current controller → `set-inform` the UXG + AP to the new
host → decommission the Docker container. Give the new host `10.10.6.15` (or update inform +
`internal.impazzito.it` + NPM DNS to its IP).
