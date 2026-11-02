# Living virtual HA contract — isolated candidate

**Актуально 02.11.2026:** комнатные абстракции и погода активированы в live HA. Рабочий пакет — [formapanel-living-runtime.yaml](packages/formapanel-living-runtime.yaml); 46 стандартных Template helpers создаются отдельно по [manifest](formapanel-living-template-helpers.json). Старый formapanel-living.yaml ниже — исторический candidate, его не устанавливать. [Проверки, backup и статус панели](../../docs/06-validation/ha-living-integration-2026-11-02.md).


01.11.2026. **Not installed in HA.** No physical light/HVAC commands exist in
this package. It creates a desired-state interface and a read-only weather
bridge. Auto heat/cool coordination and actual device adapters remain unbound.

Room identity is `living`; the physical panel ID and real HA area ID must be
provisioned and verified before a command adapter is enabled. This package does
not guess the area. All panel writes must use the explicit room allowlist below.
It cannot accept arbitrary entity IDs or act on other rooms. Global ESPHome
source and existing `home_living_*` helpers are untouched.

| Panel intent | New planned entity/action | Type / meaning |
|---|---|---|
| Auto / Manual | `input_select.formapanel_living_mode` | Auto, Manual; desired only |
| Single room target | `input_number.formapanel_living_target` | 16–28 °C, step0.1 |
| Manual heating request | `input_boolean.formapanel_living_manual_heat` | desired only |
| Manual AC request | `input_boolean.formapanel_living_manual_cool` | desired only |
| Primary light tap | `script.formapanel_living_light_toggle` | inverse of actual on/off; otherwise inverse of known desired helper only |
| Desired light readback | `input_boolean.formapanel_living_primary_light_requested` | not physical feedback |

Mode/target/manual/light desired helpers omit `initial` so HA restores them. First installation uses HA
defaults; these are not physical ON/OFF commands. A panel must not reset helpers
on boot/reconnect. The queued light script serializes toggles; it inverts confirmed actual on/off
when known, otherwise known desired state. If both are unknown it sends no change; opening Lighting
or receiving a helper update must not invoke it. A tap still navigates immediately,
but desired confirmation must never be displayed as successful physical change.

`input_boolean.formapanel_living_backend_connected` starts false on every HA
restart and is diagnostic only, excluded from the panel write allowlist. Even
manually turning it ON cannot enable anything: there are no physical actions.
`binary_sensor.formapanel_living_ready` is hard false.
`sensor.formapanel_living_backend_status` is `unbound`, area attribute `unbound`.
`sensor.formapanel_living_primary_light_actual`, `_heating_actual`,
`_cooling_actual` always return `unknown`. UI must say “not connected” and end
pending without claiming success. Unknown is deliberate, not OFF.

A future independent HA coordinator will consume mode/target/manual requests,
own Auto selection of heat/cool, arbitrate existing profile/TPI rules and publish
actual states/reasons. No priorities, deadband or compressor timing are invented
here. Restarting or disconnecting a panel must not stop that coordinator. Turbo
remains UI-only timer/Stop and has no entity/action in this package. Bathroom
two-channel persistent timers remain a separate mandatory follow-up.

## Weather bridge

Only existing HA entities are read: primary `weather.yandex_pogoda`, backup
`weather.home_assistant_gismeteo`. Their registry IDs are verified in the
[inventory](../../docs/05-roadmap/ha-functional-ui-inventory-2026-11-01.md).
No provider HTTP requests, keys or forecast actions are added.

`input_number.formapanel_living_weather_max_age_seconds` has an explicit candidate
`initial: 7200` seconds: an engineering default, not a measured freshness guarantee.
It is adjustable at runtime; `initial` resets it to7200 on HA restart. Before production,
measure provider cadence and either change the configured initial or remove initial
to persist runtime tuning. **0 disables weather publication.** Candidate failover selects a provider with known state, numeric
current temperature, Celsius unit and `0 <= age(last_updated) <= TTL`, preferring
Yandex. Forecast selects independently from valid tomorrow rows of the existing
`forecast_twice_daily` attribute with the same age/unit checks. A reserve with
no such attribute cannot supply forecast. This is conservative availability/age
selection, not a completed cache/backoff/recovery state machine; production
fallback hysteresis and provider-specific forecast timestamps remain to implement.
The age uses the weather entity update time; providers do not expose a separately
verified forecast generation timestamp in the sampled attributes.

| Entity ID (`sensor.formapanel_living_…`) | State / attributes |
|---|---|
| `weather_source` | actual current weather entity ID or unavailable; updated_at and policy attributes |
| `weather_condition` | condition enum or unavailable |
| `weather_temperature` | numeric °C or unavailable |
| `weather_humidity` | numeric % or unavailable |
| `weather_wind_speed` | numeric **km/h** or unavailable; source_unit retained |
| `weather_pressure` | numeric **hPa** or unavailable; converts hPa/mmHg/inHg/Pa |
| `weather_details` | available/unavailable; apparent_temperature, pressure/unit, wind_bearing/gust, temperature/wind units attributes |
| `weather_forecast_source` | actual forecast weather entity ID or unavailable |
| `weather_tomorrow` | available/unavailable; date, source_entity, updated_at, temperature_unit, entries attributes |
| `weather_tomorrow_high` / `_low` | max/min of validated tomorrow periods, °C; unavailable if no rows |
| `weather_tomorrow_condition` | daytime condition if present, otherwise first valid period; source_entity attribute |
| `weather_forecast_days` | available/unavailable; normalized `days` list in attributes, with date/high/low/condition/periods |
| `weather_day_0` … `weather_day_4` | numeric high °C or unavailable; low, condition, date, periods, source_entity, updated_at attributes |

Each forecast entry has date, datetime, is_daytime, high, low and condition.
The parallel `rows` attribute contains compact date/condition/high/low objects.
A missing low remains null: the high/condition are kept and the separate low
sensor becomes unavailable if no period supplies low. Never turn missing low into0. Full
periods remain attributes; no long JSON string is stored as sensor state (HA
state limit255). High/low cover only supplied periods; a single period is partial
and UI must not imply a complete daily forecast. Sources of current and forecast
must be shown separately if they differ. On expiry/malformed/absent data show
unavailable, never 0 or demo weather. The five day slots cover tomorrow through
five days ahead, selected by calendar date in HA's local timezone. A slot is
unavailable when its date has no valid supplied period; absent dates are never
filled or shifted into another slot. The normalized list aggregates the maximum
supplied `native_temperature` and minimum numeric `native_templow`, retaining
null when no period supplies a low. Its condition prefers a supplied daytime
period; `periods` states how many valid periods contributed. These are supplied
period bounds, not a guarantee of complete daily coverage. All five slots use
the same selected forecast provider, without borrowing missing days from the
other source. Tomorrow remains the verified live minimum; additional dates are
published only when present in that provider's existing attribute. Older
tomorrow aliases remain compatible. Humidity/pressure may be absent and
must remain missing. Wind speed and gust normalize km/h, m/s, mph, kn to km/h; unsupported/missing
units are unavailable rather than guessed. Pressure normalizes to hPa, including
the details attribute; missing/unknown units yield no value. Current details and
tomorrow attributes expose source_entity and updated_at for adapter freshness.

## Local checks and later activation

Run `python -m unittest discover -s tests -p test_ha_virtual_contract.py` from
the repository. PyYAML validates YAML; structural guards reject physical writes,
unknown actions and other-room targets. If Jinja2 is available, template fixtures
also execute current/forecast selection for unavailable, expired, malformed and
partial data. Jinja2 is not installed by the tests. HA-specific template behavior
still needs actual HA configuration validation before installation; local YAML
parsing is not equivalent to `ha core check`.

No live install/reload/restart is part of this change. Future installation must
first back up HA config, verify existing package includes and entity collisions,
validate in HA and test with helpers only. The planned `default_entity_id` values
are not discovered live entities until then; verify the actual registry after
installation. Removing the candidate file from an uninstalled checkout has no
HA effect. Comfortaa remains the chosen UI font and is outside this HA package.

`sensor.formapanel_living_heartbeat` publishes HA epoch seconds via `now()` every minute. Panel receipt timeout is150 seconds measured by its monotonic clock since the last received value; do not compare wall clocks. Fresh heartbeat plus valid desired mode/target/manual helper values enables editing virtual intentions. `binary_sensor.formapanel_living_ready` remains physical-backend readiness (false), separate from helper edit readiness.

Freshness intentionally uses provider `last_updated` (conservative content-change
age), not `last_reported`: repeated reports of cached data must not make an old
forecast fresh. A provider with unchanged content can therefore expire after2h;
this is documented fail-closed behavior until provider issue-time validation and
recovery hysteresis are implemented. Report presence and weather content freshness
are separate. Heartbeat availability is enforced by the panel receipt timeout,
not by restoring an epoch from a prior connection. The minute heartbeat expression
has no input helper dependency and no physical effects.

Verification 01.11.2026: all15 tests passed with Jinja2 in an isolated temporary
Workshop container directory; it was removed automatically. No Workshop job,
source checkout, HA config, reload or device action was used. Local machine runs
4 structural checks and skips11 Jinja checks when Jinja2 is absent. Fixtures verify
unknown/expired/both-offline/recovery, partial forecast missing low, unit conversion,
heartbeat progression and light actual/desired divergence. Restore behavior is
verified at configuration level (absence of initial on desired helpers); actual
HA restart/restore has not been exercised.

Five-day extension 01.11.2026: local checks cover all five numeric entities and
nullable attributes. Added executable template fixtures cover chronological
aggregation, two periods in one day, daytime condition preference, missing low,
out-of-horizon/malformed rows, source isolation, missing dates, fallback and
expiry. Local Python lacks Jinja2, so the executable fixtures remain skipped
locally until run in an existing environment with Jinja2; no dependency was
installed and this is not HA configuration validation. No HA installation,
reload, physical action or remote job was performed for this extension.

Additional isolated verification 01.11.2026: **19/19 tests passed, zero skips**
with existing Workshop Jinja2 3.1.6. Only the candidate YAML and test file were
copied into `/tmp/formapanel-forecast-contract-2ywje614`; that exact temporary
directory was automatically removed and its absence checked. No Workshop build
job, source checkout or live HA configuration was changed. Private local
evidence: `reports/local/functional-build/ha-forecast-contract-tests.json`, with
source SHA-256 hashes, test output and cleanup result. This remains a template
fixture check, not live HA configuration validation or device acceptance.
