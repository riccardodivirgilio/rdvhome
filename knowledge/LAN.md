# LAN — RdvHome

Home UniFi network. Single site, so network names drop the site (`Server`, not `Server RdvHome`).

## Controller

**UniFi OS Server 5.1.42 + Network 10.6.101** — TrueNAS custom app `unifi-os-server` on the NAS
`rdvnas` (details in [[NAS]]). UI **`https://10.10.6.15:11443`** (self-signed cert), inform
`http://10.10.6.15:8080/inform`. Migrated 2026-09-14 from the legacy Docker Network app by
restoring a `.unf` in the UOS setup wizard; the legacy app is deleted. Owner is a UI (cloud)
account. UniFi OS has API keys (Integrations / Control Plane), unlike the legacy build.

## API access

UniFi OS paths: login `POST /api/auth/login`, then Network endpoints get a **`/proxy/network`**
prefix (`/proxy/network/api/s/default/...`, `/proxy/network/v2/api/site/default/static-dns`).
Send `X-Csrf-Token` on writes.

**Broken since the migration:** the local admin `claude-automation` (creds in `~/.unifi.env`
`UNIFI_RDVHOME*`) doesn't exist in UniFi OS — login returns 403
`AUTHENTICATION_FAILED_INVALID_CREDENTIALS`. The helper `~/.unifi-rdv.sh METHOD path [json]`
still tunnels to the legacy port `30072` and uses classic paths, so it needs rewriting. The
simplest fix is a UniFi OS API key (header `X-API-KEY`, no login or CSRF needed).

## Conventions

`VLAN = third octet + 100`, second octet is always `10`. Networks named by role. DHCP `.6–.254`,
lease 86400.

| Role          | VLAN         | Subnet        | Notes                                 |
| ------------- | ------------ | ------------- | ------------------------------------- |
| Default       | 1 (untagged) | 10.10.0.0/24  |                                       |
| People        | 101          | 10.10.1.0/24  | staff/personal (the "Staff" slot)     |
| Network       | 102          | 10.10.2.0/24  | infra: switches, APs                  |
| Guest         | 103          | 10.10.3.0/24  |                                       |
| Entertainment | 104          | 10.10.4.0/24  | the VoIP slot, repurposed             |
| IoT           | 105          | 10.10.5.0/24  | lights, sensors — see [[LIGHTS]]      |
| Server        | 106          | 10.10.6.0/24  | NAS — see [[NAS]]                     |

## Hardware & ports

**UXG Fiber** gateway (id `6aa7ff2824a4b6fe4527bbe1`) + **U7 Pro** AP. Ports 1–4 are 2.5G RJ45
(LAN), **port 5 is the 10G WAN** (`eth4`, WAN `195.32.7.119`) — do not touch. Ports 6/7 SFP+ unused.

| UXG port | native VLAN     | device                                         |
| -------- | --------------- | ---------------------------------------------- |
| 1        | Server          | NAS `10.10.6.15`                               |
| 2        | IoT             | dumb 8-port switch → Pi + Hue (see [[LIGHTS]]) |
| 3        | IoT             | free                                           |
| 4        | Network (trunk) | U7 Pro AP mgmt `10.10.2.254`                   |
| 5        | —               | **WAN**                                        |

`port_overrides` per port: access port = `{forward:"customize", native_networkconf_id:<id>}`;
AP uplink is a **trunk** = `{forward:"all", native_networkconf_id:<Network>}` (so all SSID VLANs
still tag). Network ids: Server `6aa818beec3d225546a3746f`, IoT `6aa818beec3d225546a37472`,
Network `6aa82b19ec3d225546a3765b`.

**Gotchas:** a wired device does **not** re-DHCP when you change a port's native VLAN — bounce
the port (`forward:"disabled"`, then re-set) to force it. `stat/sta` shows a **stale IP** for a
minute after — ping the fixed IP for ground truth. A disconnected UXG won't apply port changes,
so reconnect devices first.

## Wi-Fi

One SSID **`RdvHome`** → Default (untagged). Per-client VLAN comes from the client's DHCP
**reservation `network_id`**, not the SSID. A Wi-Fi device only lands on its reserved VLAN after
it renews (kick it via `cmd/stamgr {"cmd":"kick-sta"}` to speed it up).

## DNS

The gateway resolves local records for everyone using it as DNS. Two mechanisms:
- **Per-client**: `rest/user` `local_dns_record` + `local_dns_record_enabled` (needs a fixed IP).
- **Standalone**: `/v2/api/site/default/static-dns` A records (service names → NAS).

`impazzito.it` public wildcard `*` → WAN `195.32.7.119` (so any un-overridden name resolves to the
WAN). Local overrides must be exact names. See [[NAS]] for the `internal.impazzito.it` gotcha.

## Recovering a device that lost the controller

After a renumber/IP change, devices keep the old inform URL and go `state 10` (disconnected).
Fix: set `super_identity.hostname` to the controller's current IP, then from the NAS SSH into each
device (mgmt SSH creds) and `mca-cli-op set-inform http://<controller-ip>:8080/inform`
(UXG: OpenSSH; U7 Pro: dropbear). Device SSH user/pass are in the controller `mgmt` setting.
