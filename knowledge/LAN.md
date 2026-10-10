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

The local admin `claude-automation` (creds in `~/.unifi.env` `UNIFI_RDVHOME*`) is a Network
admin only, not a UniFi OS user, so `/api/auth/login` returns 403. It **does** work against the
Network app's internal port, from inside the container on the NAS:
`docker exec ix-unifi-os-server-unifi-os-server-1 curl http://127.0.0.1:8081/api/login` then
classic paths (`/api/s/default/...`, `/v2/api/site/default/...`) with `X-Csrf-Token` on writes.
The `.unf` restore dropped its site role (`api.err.NoSiteContext`); it was re-added on
2026-10-02 as an `ace.privilege` row (admin on site `default`). The helper `~/.unifi-rdv.sh`
still tunnels to the legacy port `30072`, so it needs rewriting to this path. A UniFi OS API key
(header `X-API-KEY`) would avoid the docker hop.

## Conventions

`VLAN = third octet + 100`, second octet is always `10`. Networks named by role. DHCP `.6–.254`,
lease 86400.

| Role          | VLAN         | Subnet        | Notes                                 |
| ------------- | ------------ | ------------- | ------------------------------------- |
| Default       | 1 (untagged) | 10.10.0.0/24  |                                       |
| People        | 101          | 10.10.1.0/24  | staff/personal (the "Staff" slot)     |
| Network       | 102          | 10.10.2.0/24  | infra: switches, APs                  |
| Guest         | 103          | 10.10.3.0/24  | named **Jail** in the controller      |
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
| 3        | People          | free                                           |
| 4        | Default (trunk) | **USW Flex 2.5G** "RdvHome Switch" (below)     |
| 5        | —               | **WAN**                                        |

**USW Flex 2.5G 5** "RdvHome Switch" (`74:f9:2c:96:f0:fb`, id `6abf5206ed2879fb09d71c3f`),
added 2026-10-02. Port 5 is the uplink to UXG port 4. Its management is **tagged on Network**
(`mgmt_network_id`) → `10.10.2.25`. It must stay on Network: the firewall only lets Network reach
the controller (see below), so a Flex managed on Default goes offline.

| Flex port | native VLAN     | device                          |
| --------- | --------------- | ------------------------------- |
| 1         | People          | RdvMacbook (wired)              |
| 2         | Entertainment   | RdvTv                           |
| 3         | Entertainment   | Playstation 5                   |
| 4         | Network (trunk) | U7 Pro AP mgmt `10.10.2.254`    |
| 5         | —               | uplink → UXG 4                  |

`port_overrides` per port: access port = `{forward:"customize", native_networkconf_id:<id>,
tagged_vlan_mgmt:"block_all"}`; trunk = same with `tagged_vlan_mgmt:"auto"` (all VLANs tagged, so
the SSID VLANs still reach the AP). Network ids: Default `6a88bb1e4d68c34c6d94f705`, People
`6aa82b19ec3d225546a37658`, Network `6aa82b19ec3d225546a3765b`, Entertainment
`6aa82b57ec3d225546a3766d`, IoT `6aa818beec3d225546a37472`, Server `6aa818beec3d225546a3746f`.

**Firewall** (legacy `rest/firewallrule`, `LAN_IN`, indexes must be ≥ 20000): allow
established/related, People → all, Server → IoT+Network, Network → Server, Entertainment →
Server+IoT, then `fw: drop inter-VLAN` (20005). Default → Server is **not** allowed.

**Gotchas:** a wired device does **not** re-DHCP when you change a port's native VLAN — bounce
the port (`forward:"disabled"`, then re-set) to force it. `stat/sta` shows a **stale IP** for a
minute after — ping the fixed IP for ground truth. A disconnected UXG won't apply port changes,
so reconnect devices first.

## Wi-Fi

One SSID **`RdvHome`** → Default (untagged). Per-client VLAN comes from the client's DHCP
**reservation `network_id`**, not the SSID. A Wi-Fi device only lands on its reserved VLAN after
it renews (kick it via `cmd/stamgr {"cmd":"kick-sta"}` to speed it up).

## DNS

Every network's DHCP hands out its gateway (`10.10.X.1`) as DNS; the UXG's dnsmasq answers local
records and forwards the rest to **`1.1.1.1` (Cloudflare) primary, `8.8.8.8` (Google) secondary** (both WANs
`wan_dns_preference: manual` since 2026-10-10, so the ISP's PPPoE resolvers are ignored; dnsmasq `all-servers` queries both at once). DoH is off.

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
