# EIM request/response examples (sanitized)

Status: **Verified** field names and shapes from
`eim-service/docker/eim-core/src/routers/*.py` and
`eim-service/docker/eim-core/src/common/definitions.py`; endpoint usage from
firmware call sites in `sketch_dreambox/A70EIMintegration.ino` and
`sketch_dreambox/A50WIFI.ino`. This is milestone 0, item 4 of the
[Raspberry Pi port plan](raspberry-pi-port-plan.md).

All example values below are fictional placeholders (callsigns, names, IDs).
None are copied from real user data, even though some firmware source
comments contain a real maintainer callsign/name as inline example values —
those were deliberately not reused here. See also
[eim_specification.md](../eim_specification.md) for the original endpoint
sketch this service implements.

## `GET /system/info`

Client: `EIMreadStatus` (`A70EIMintegration.ino:15-52`), URL constant
`EIMstatusUrl = "http://dmrdream.com/api/v1/system/info"` — **plain HTTP**,
flagged in [current-system.md](current-system.md) as a risk to review.

Response model `SysInfo` (`definitions.py`):

```json
{
  "uptime": "3d 4h12m",
  "release": "dmr_dreambox_EXAMPLE-000000-0X",
  "git_commit": "abc1234",
  "maintainer": "Example Maintainer",
  "user": 202000,
  "repeater": 6644
}
```

Firmware only reads `uptime`, `version` (not in current model — mismatch,
see below), `maintainer`, `repeater` (`A50WIFI... ` — actually
`A70EIMintegration.ino:39-42`). **Verified mismatch**: firmware code expects
a `version` field; the current service model exposes `release` and
`git_commit` instead, no `version` key. This is a live contract drift between
firmware and service that the port must resolve explicitly rather than carry
forward silently.

## `GET /user/{dmr_id}`

Client: commented-out `radioIdUrl` path in `A50WIFI.ino` targets a different,
external service (`database.radioid.net`); the currently *active* call
(`wifiGetDMRIDswe`, `A50WIFI.ino:64-141`) hits `dmrdreamUrl` (an EIM-compatible
endpoint), not this router directly — but the JSON shape consumed matches
`DmrUser`.

Response model `DmrUser` (`definitions.py`):

```json
{
  "dmr_id": 2400011,
  "call_sign": "EX1AMP",
  "name": "Example Person",
  "city": "Example City",
  "state": "Example Region",
  "country": "Exampleland"
}
```

Firmware treats `dmr_id == 0` in the response as "not found" and falls back
to the originally-queried contact ID (`A50WIFI.ino:110-113`). `state` is
sometimes empty in real data per a source comment (not enforced by the
current Pydantic model, which requires it) — **Assumption**: the live
service may return `""` for unknown state/region; the port's client should
treat empty string as valid, not an error.

## `GET /dmr/{dmr_id}` (detailed repeater/hotspot lookup)

Client: `EIMreadRepeaterDMRid` → `EIMdeserializeSingleRepeater`
(`A70EIMintegration.ino:207-284`), URL constant
`EIMDMRUrl = "http://dmrdream.com/api/v1/dmr/"`.

Response model `Repeater` (`definitions.py`), with nested `TalkGroup` list:

```json
{
  "dmr_id": 240799,
  "tx": 434587500,
  "rx": 432587500,
  "cc": 4,
  "max_ts": 2,
  "name": "EX7AMP",
  "location": "59.426891,24.819180",
  "city": "Example Town",
  "num_tg": 2,
  "tg": [
    { "tg_id": 2401, "ts": 1, "is_dynamic": false },
    { "tg_id": 240750, "ts": 2, "is_dynamic": true }
  ]
}
```

Firmware note: the deserializer swaps `tx`/`rx` when copying into
`dmrSettings.repeater[k]` — `rx = doc["tx"]`, `tx = doc["rx"]`
(`A70EIMintegration.ino:221-222`). **Verified in source; likely intentional**
given the repeater's TX is the client's RX and vice versa, but flag it as a
naming trap for the port — do not "fix" without checking behavior against a
live bench repeater first, since the field may already compensate correctly
end-to-end.

Firmware caps `tg` parsing at 10 entries (`num_tg > 10 → num_tg = 10`,
`A70EIMintegration.ino:238-240`) regardless of what the service returns.

## `GET /repeater/master/{master_id}`, `GET /repeater/location`, `GET /hotspot/callsign/{call_sign}`

Response model `RepeaterItem` (`definitions.py`) — the same shape as
`Repeater` but without `num_tg`/`tg`:

```json
[
  {
    "dmr_id": 204342,
    "tx": 436800000,
    "rx": 430700000,
    "cc": 4,
    "name": "EX1SPA",
    "location": "56.898484,12.460581",
    "city": "Example City, SE"
  }
]
```

- `master`: firmware builds
  `"{EIMrepeaterUrl}master/{master}?limit={limit}&skip={skip}"`
  (`A70EIMintegration.ino:74-102`).
- `location`: firmware builds
  `"{EIMrepeaterLocationUrl}?longitude=..&latitude=..&distance=..&limit=14&skip=0"`
  (`A70EIMintegration.ino:146-177`); server-side filters results to
  `432000000 < tx < 439000000` and `dmr_id < 9999999` before accepting them
  into the temp repeater list (`reptemplist`) — a firmware-side sanity filter,
  not a service contract.
- `hotspot`: firmware builds `"{EIMhotspotUrl}{callsign}"`
  (`A70EIMintegration.ino:179-206`); service route additionally supports
  `limit`/`skip` query params not currently sent by firmware.

All three plain-HTTP; same endpoint-security caveat as `/system/info`.

## Credentials and PII handling for the port

- No API keys or auth headers are sent by the firmware to any EIM endpoint —
  the service is currently open/unauthenticated over plain HTTP.
- Wi-Fi credentials (`WifiAp`, `dmrSettings` Wi-Fi slots) are never sent to
  EIM; they stay local to the ESP32/settings store. Confirm the Pi port's
  structured logging never includes them (`current-system.md` risk list
  already flags this).
- Real DMR IDs, callsigns, and names returned by these endpoints are
  personal/identifying data for licensed amateur radio operators. Any fixture
  captured from the live service for milestone 1 testing must be replaced
  with placeholder values like the ones above before being committed to the
  repository.
