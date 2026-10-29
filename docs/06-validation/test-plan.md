# Verification matrix

| Test ID | Requirement | Method | Acceptance |
|---|---|---|---|
| VT-01 | UX-009 | render SVG→480 and 720 | files correct size, no errors |
| VT-02 | NFR-002 | hardware boot log, flash/PSRAM, touch grid | config matches board |
| VT-03 | UX-002 | photo of real room-home | all values readable from expected distance |
| VT-04 | UX-004 | bathroom one-click timer on HA test helper | one tap initiates HA timer; remaining shown |
| VT-05 | FR-007 | disconnect HA service test | on/off is not misrepresented, unavailable indicator |
| VT-06 | FR-006 | HA light automation + manual press | expected script/override semantics |
| VT-07 | NFR-006 | memory and redraw measurement | no OOM/stutter over soak test |
| VT-08 | UX-006 | Russian label/font subset | no missing glyphs or overlaps |
| VT-09 | NFR-008 | build all five configurations | only config differs, visual system same |
| VT-10 | NFR-003 | 720 asset rendering + later P4 bring-up | no assumption of current P4 firmware support |

## Automated bootstrap tests

`python -m unittest discover -s tests -v` checks renderer outputs and JSON token validity. Build/hardware/integration tests are **not** implemented yet and must not be represented as passed.

## Manual smoke procedure

1. Boot test panel; check full RGB pattern and touch coordinates (center, corners, edges).
2. Let UI remain active for at least 24 hours, watch heap and display stalls (target duration, not completed test).
3. Observe screen in daytime and at night; inspect shadow levels, readability and possible flicker.
4. Switch between pages rapidly, change light values in HA, watch actual state confirmation.
5. Disconnect/reconnect HA and verify user feedback; no requirement of autonomous control.
