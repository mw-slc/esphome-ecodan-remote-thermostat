# CN-RF fork integration

## Provenance

- Owned remote: https://github.com/mw-slc/esphome-ecodan-remote-thermostat.git
- Previously deployed / starting owned main: `23e8864beed1338a7c786bba1f61a0bbb88d7ea5`.
- Upstream remote: https://github.com/gekkekoe/esphome-ecodan-remote-thermostat.git
- Integrated upstream main: `7672b7f90cc894f69e7a278b8411e3c53ab43660`.
- Common ancestor: `1127c8149fb21c329dd6814e31f1798eba8489ce` (Git ancestry exists despite GitHub reporting fork:false).
- Integration branch: `chore/upstream-cnrf-sync`; ordinary two-parent merge, no history rewrite.
- HP dependency production pin and latest main at verification: `aae8c4b072621de46acfb75e5d21df4177673637`.

## Complete customization inventory and decisions

The original owned delta was inspected with rename detection against the common ancestor. All other original files match that ancestor.

| Area / files | Decision and reason |
| --- | --- |
| Entire `components/ecodan` directory moved to `components/ecodan_cnrf` | Retain; allows HP's `ecodan` to load in the same firmware. |
| C++ namespaces in climate.cpp, commands.cpp, ecodan.cpp/h, proto.h, proxy.cpp, response.cpp, serial.cpp, status.h | Retain `esphome::ecodan_cnrf`; class names can remain unchanged inside the isolated namespace. |
| Qualified Status types/enums in climate.cpp and ecodan.h | Retain CN-RF qualification, preventing accidental binding to HP Status. |
| Python namespace in __init__.py | Retain `ecodan_cnrf`; module-relative imports remain valid after the directory move. |
| AUTO_LOAD in climate.py, sensor.py, binary_sensor.py, text_sensor.py | Retain `ecodan_cnrf`; never auto-load HP instead. |
| climate.py generated Status reference | Retain `ecodan_cnrf::Status`. Correct the previously missed climate class namespace to `ecodan_cnrf`. |
| `confs/thermostat-room.yaml` enum reference | Retain CN-RF qualification and correct the previously missed platform from `ecodan` to `ecodan_cnrf`. |
| Local ClimateTraits port in climate.cpp | Replace with latest upstream's equivalent feature-flags implementation; no second local compatibility patch is needed. |
| Removal of queue include in ecodan.h | Drop customization; upstream's explicit `<queue>` is required for std::queue and avoids reliance on transitive headers. |
| Main example | Correct previously unmodified upstream URLs/component selection to the owned fork and `ecodan_cnrf`, including the commented local-source example. |
| Hub and entity IDs / service API | Preserve CN-RF's `ecodan_instance`, `heatpump_climate_room_0/1`, `room_0/1`, and `set_climate_temperature_room_0/1`. The dual fixture gives HP a distinct `hp_instance` and distinct UART IDs. HA exposes these as `esphome.<node>_set_climate_temperature_room_0/1`; node prefix is determined by the deployed name, not this library. |
| Package changes from upstream | Accept restored room-temperature globals (`saved_temp_room_*`) and base restart button. No existing entities/services renamed. Do not include HP/CNRF base packages with duplicate IDs; the fixture only includes CN-RF room packages and HP hub. |
| README and release workflow upstream changes | Accept Asgard documentation and room-1/room-2 release split. Upstream project/hardware links remain attribution, not fork firmware validation. |
| Macro names and relative headers/imports | Original fork did not rename macros. Retain values; the dual compilation is the collision gate. No new HP dependency is introduced in Python. |
| New safety fixes | Guard room index before any write; finite temperatures only, nonfinite values become existing 0xff unknown sentinel. Add missing breaks to both THERMOSTAT_STATE_RES handlers, preserving real unknown-response logging. |
| New test/docs/ignore files | Host behavioral regressions, compile-only board fixture, fork usage guidance; ignore Python caches and sanitizer core dumps. |

## Upstream warnings checked

All three reported causes remain in upstream `7672b7f`:

1. `set_room_thermostat_current_temp` writes to `CurrentRoomTemperatures[room]` in its else branch even when room >= 8. Invalid room indices now return without writing.
2. The uint8_t `room >= 0` comparison is always true; removed. `temp != NAN` is also not a valid NaN test; replaced by `std::isfinite` and existing unknown sentinel.
3. Both thermostat-state response cases fell through to the unknown-response logger; explicit breaks now prevent this.

Host tests compile and execute the actual setter body and actual response.cpp with minimal test scaffolding. Valid slots 0–7, invalid indices 8/255, guard memory, NaN and positive/negative infinity are exercised. Response tests check status-update calls, queue pop, known-response silence and unknown-response diagnostics. These do not prove physical CN-RF acknowledgement.

## Reproduction (compile only; never upload)

Use a complete Python 3.13 installation with ensurepip, ESPHome 2026.8.2, pytest and host g++. ESP-IDF creates its own nested venv; a working outer venv alone is insufficient when the base Python lacks ensurepip. Prepend this environment's bin directory to PATH.

    python -m pytest tests -q
    esphome compile tests/dual-uart.yaml

The fixture uses local CN-RF sources, pinned HP sources, Room0 and Room1, ESP32-S3/ESP-IDF/16 MB flash, W5500 SCK15/MOSI13/MISO14/CS16/INT12/RESET39, HP RX44/TX43 and CN-RF RX1/TX0 at 2400 baud EVEN/1. No credentials or OTA/upload action are present. GPIO0 is a boot-strapping pin: successful compilation does not certify electrical boot safety.

There is no push/PR workflow in the inherited repository: its sole workflow runs on release creation and publishes OTA assets. Do not create a release as a test or claim that workflow passed without running it. Local firmware compilation remains mandatory. Existing release automation uses Python 3.12, unpinned ESPHome and historical PlatformIO output paths; it is not validated by this dual-ESP-IDF build and should not be used to publish these binaries unchanged.

Final build/review/publication evidence is recorded in the task's Swedish report; this document defines provenance and reproducible checks, not a claim of physical installation.
