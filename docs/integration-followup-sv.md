# Integrationsrapport – t_1ac5e6a8

## Bas och metod

Upstream 7672b7f90cc894f69e7a278b8411e3c53ab43660 är redan integrerad i main 4ea777457811af13c3f558bf03da751d0fca7d66. Anfaderskapet verifierades med git merge-base --is-ancestor. Ingen upprepad merge eller publicering. Tidigare integrationscommit är 1afa6e126a21ce7546c20dd535209d79e2cdaad5, med gemensam anfader 1127c8149fb21c329dd6814e31f1798eba8489ce mellan installerad pin och upstream. Historikerna är besläktade trots GitHubs fork:false.

Ny lokal branch: fix/cnrf-target-temperature-safety från 4ea7774 i arbetsytans cnrf-provenance. Ändringen är en vanlig efterföljande commit, utan omskriven historik. Befintliga repo/ lämnas orörda. Remoter:

- https://github.com/mw-slc/esphome-ecodan-remote-thermostat.git
- https://github.com/gekkekoe/esphome-ecodan-remote-thermostat.git

Ingen push, release, HA-ändring eller firmwareinstallation utförs. Fulla byggen och slutgranskning ägs av efterföljande verifieringskort.

## Fastställd avvikelsematris

Matrisen kompletterar den uttömmande blob-/fillistan i föräldrarapporten cnrf-audit/proveniens-och-avvikelsematris.md. Besluten gäller samtliga lager, inte bara ändrade rader i denna nya commit.

| Lager | Faktiskt beslut och motivering |
|---|---|
| Hela components/ecodan → ecodan_cnrf | Bevarad katalogflytt; HP kan laddas separat. |
| C++ climate.cpp, commands.cpp, ecodan.cpp/h, proto.h, proxy.cpp, response.cpp, serial.cpp, status.h | Bevarad esphome::ecodan_cnrf och kvalificerade Status/OperationMode-typer; undviker HP-bindningar. |
| Python __init__.py | Bevarad hub_ns ecodan_cnrf och relativa importer; inga HP-importer. |
| Python climate.py | Bevarad rättning av klassnamespace samt AUTO_LOAD och genererad Status-referens. Det lokala variabelnamnet ecodan_ns lämnas eftersom det inte är komponentidentitet. |
| Python sensor.py, binary_sensor.py, text_sensor.py | Bevarad AUTO_LOAD ecodan_cnrf; relativa importer är intakta. |
| Headers, makron, loggtagg | Bevarade relativa ecodan.h-includes, CHECK_BIT, MAX_STATUS_CMD_SIZE och loggtagg. Ingen konkret kollision kräver omdöpning; loggtaggen kan vara diagnostiskt tvetydig. |
| Hubb-ID, schema, UART | Bevarade ecodan_instance/ecodan_id och proxy-/UART-nycklar. HP får separat hp_instance och egen UART i fixturen. |
| confs/thermostat-room.yaml | Bevarad CN-RF-enum och redan rättad platform ecodan_cnrf. |
| Room0/Room1 och API | Bevarade heatpump_climate_room_0/1, room_0/1, set_climate_temperature_room_0/1 och float temperature. ESPHome-genereringen verifierar API-namnen; HA:s nodprefix är installationsberoende. esphome.*_set_climate_temperature_room_0 bibehålls. |
| ClimateTraits | Lokal äldre port borttagen till förmån för upstreams motsvarande feature-flags-implementation. |
| ecodan.h queue | Upstreams explicit include behålls. Dokumentationen är korrigerad: include saknades i både anfader och installerad pin, alltså ingen egen nettoborttagning. |
| Current-temp-setter | Befintlig bounds/isfinite/sentinel-rättning och cmath bevarade. Ogiltigt index skriver inte; icke-ändlig avläsning blir 0xff. |
| Target-temp-setter | Ny riktad rättning: index < 8, isfinite samt representerbart target-intervall -64..63,5 °C före mutation/köning. Avvisar ogiltigt börvärde utan att skicka sentinel som nytt börvärde. Explicit cmath tillagd. |
| response.cpp | Båda befintliga break bevarade; kända svar loggas inte längre som okända. |
| Huvudexempel | Bevarad egen fork/paketkälla och ecodan_cnrf, även kommenterat lokalt exempel. Floating main är exempel, inte reproducerbar pin. |
| confs/base.yaml och sparad rumstemperatur | Upstreams restart_button och saved_temp_room_* med restore/fallback behålls. Hela HP/CN-RF-baspaket får inte inkluderas blint med dubbla ID:n. |
| README | Upstream/Asgard-tillskrivning samt eget namespace-/hubb-ID-/testtillägg bevarade. Upstream-binärer är inte forkbevis. |
| Releaseworkflow | Upstream room-1/room-2-split behålls; inte PR-CI. Ingen release körs. Python 3.12, floating ESPHome och historiska build-sökvägar är fortfarande inte verifierade här. |
| Dokumentation | fork-integration.md behålls med korrigerad queue-proveniens, tidsbundet HP-latest och tydlig skillnad mellan setters. Denna rapport tillagd. |
| .gitignore | Befintliga cache/core-ignore bevarade. Ingen ändring av gamla repo/tests/.gitignore. |
| tests/dual-uart.yaml | Befintlig syntetisk lokal-CN-RF/HP-pin-fixture och select: [] behålls. |
| test_codegen.py, test_coexistence.py | Befintliga regressionskontroller bevarade och omkörda inklusive faktisk ESPHome-kodgenerering. |
| test_temperature.py, test_responses.py | Befintliga beteendetester bevarade och omkörda. |
| test_target_temperature.py | Ny testfil använder faktisk setter och faktisk proto.h-encoder. Endast transport/köning ersätts av insamling, inte temperaturkodningen. |
| Övriga filer | Inga nya egna patchar; förälderns manifest täcker oförändrade protokolldokument, LICENSE, språk/kort/wifi-paket och övriga pipelinefiler. |

## Reproduktion och verkliga resultat

Från cnrf-provenance:

    ../build-complete/bin/python -m pytest tests/test_target_temperature.py -q
    ../build-complete/bin/python -m pytest tests -q

Miljö: CPython 3.13.14, ESPHome 2026.8.2, host g++. Target-test kompileras med -fsanitize=undefined,bounds,float-cast-overflow -fno-sanitize-recover=all.

- RED mot tidigare target-setter: 2 failed, 1 passed. UBSan visar NaN utanför unsigned-char-intervallet i verkliga proto.h samt index 8 utanför float[8]. Logg: target-red.log.
- GREEN efter index/isfinite: 3 passed.
- Separat RED för ändlig men orepresenterbar temperatur: 1 failed, 3 deselected; UBSan visar -2 utanför unsigned-char-intervallet. Logg: target-range-red.log.
- GREEN efter även encoding-range-skydd: hela sviten 9 passed in 17.45s. Logg: integration-green.log.

Giltiga rum 0–7, ogiltiga 8–255, NaN/±inf, ändpunkter/överskridet byteintervall, avrundning, aktiva/inaktiva rum, mask och zon-2-byte testas. Testerna kontrollerar tillstånd och faktiska paketbytes, inte endast frånvaro av varningar.

Alla tre ursprungliga varningsorsaker finns kvar i upstream 7672b7f: current-temp-setterns oskyddade else-index, uint8 room>=0 och två fallthrough. De är redan rättade i 4ea7774 och regressionerna passerar fortsatt. Ingen varningsundertryckning tillagd.

## Överlämning och begränsningar

Använd denna lokala branch, inte remote main som saknar target-fixen. t_c7cbc1eb ska köra slutliga fulla dual-UART-byggen och API-verifiering på den nya koden; tidigare firmwarebyggkvitto får inte tillskrivas denna nya commit.

Range-skyddet gäller bytekodningens tekniska gräns, inte rekommenderad klimatinställning. UI:s intervall ändras inte. Host-testet visar ingen fysisk CN-RF-ack, ingen lösning på JO403, och är inte en fullständig revision av protokolldekodern eller alla current-temperature-värden som följer med ett target-kommando. GPIO0-strapping och releaseworkflowets tidigare dokumenterade begränsningar kvarstår.

Ingen code-agent-skill med exakt det namnet finns i den erbjudna skillkatalogen; den lilla ändringen gjordes direkt med TDD-skill och riktiga verktyg. För återkommande CN-RF/ESPHome-underhåll rekommenderas en dedikerad ESPHome-specialistprofil.
