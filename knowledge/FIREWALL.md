# FIREWALL — RdvHome

Inter-VLAN segmentation. See [[LAN]] for the VLANs.

## Rules (→ = source may initiate to dest; replies always flow back)

| From \ To     | Default | People | Network | Entertain | IoT | Server |
| ------------- | :-----: | :----: | :-----: | :-------: | :-: | :----: |
| Default       |   ✅    |        |         |           |     |        |
| People        |   ✅    |   ✅   |   ✅    |    ✅     | ✅  |   ✅   |
| Network       |         |        |   ✅    |           |     |   ✅   |
| Entertainment |         |        |         |    ✅     | ✅  |   ✅   |
| IoT           |         |        |         |           | ✅  |        |
| Server        |         |        |   ✅    |           | ✅  |   ✅   |
| Guest         |  — internet only, no LAN —                              |

## Why the non-obvious ones

- **Network↔Server** — the AP (Network) must reach the controller (Server); adoption/set-inform is Server→AP.
- **Entertainment→IoT** — Apple TV/HomePod home hub controls HomeKit lights on IoT.
- **Entertainment/People→Server** — Jellyfin & the other NAS services.
- **Server→IoT** — Home Assistant / device polling.
- **People→all** — trusted admin devices (also our tunnel + `./run.sh deploy` path).

## Always allowed (not shown above)

- Every VLAN → **internet** and → its **gateway** (`10.10.x.1`, for DNS/DHCP).
- **mDNS reflection** on across the VLANs above (HomeKit, AirPlay, casting discovery).

## Wi-Fi default

Single SSID `RdvHome` → **Guest** network. New/un-assigned clients land isolated on Guest; a
per-client **`virtual_network_override`** (set the client's *Network* in the UI, or
`rest/user` `virtual_network_override_enabled` + `virtual_network_override_id`) promotes a device
to People / IoT / etc. The override wins over the SSID's default, so existing devices are
unaffected by the SSID→Guest change.

## Implementation (legacy LAN_IN rules on the UXG)

Address groups per subnet (`g_default`…`g_server`, `g_all`=10.10.0.0/16) + combined
`g_iot_net`, `g_server_iot`. Rules (index 20000+, evaluated ascending):
`20000` allow established/related · `20001` People→g_all · `20002` Server→IoT+Network ·
`20003` Network→Server · `20004` Entertainment→Server+IoT · `20005` **drop** g_all→g_all.
Intra-VLAN is L2 (never hits LAN_IN); internet + gateway (DNS/DHCP) are unaffected by the drop.

## External access (port forward)

WAN **80 + 443 → `10.10.6.15`** (NPM) — `rest/portforward`, `pfwd_interface:"wan"`, `proto:"tcp"`.
Public DNS `*.impazzito.it` → WAN `195.32.7.119`, so from the internet a service name resolves to
the WAN; the forward hands it to NPM, which routes by Host and terminates Let's Encrypt TLS. See
[[NAS]] for the NPM upstream (`internal.impazzito.it`). Verified: `WAN:443→302` (jellyfin),
`WAN:80→301`→https.

**Security:** this exposes **every** NPM proxy host to the internet — lock sensitive ones
(radarr/sonarr/prowlarr/qbittorrent/bazarr) down per-host in NPM (access list / auth). The forward
only opens WAN→NAS `:80/:443`; the LAN_IN inter-VLAN firewall above is a separate ruleset and is
unaffected (the forward auto-allows just those two ports in WAN_IN).
