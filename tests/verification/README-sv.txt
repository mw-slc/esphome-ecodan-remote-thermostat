Syntetisk dual-UART-fixture och API-regressionsplan — t_38d7807f

Omfattning
Detta är förberedelsekortets körda smoke-tester, inte slutligt firmwarebygggodkännande.
Ingen flashning, ingen HA-anslutning, inga HA-ändringar, inga Git-pushar.
Alla nya filer ligger under fixture-t_38d7807f; befintlig repo-checkout är endast läst/exporterad med git archive.

Källor och proveniens
Läst tidigare source_review.py och file_esphome_confs_thermostat-room.yaml.json i /home/michael/.hermes/kanban/workspaces/t_90461d4c/.
Den historiska lokala rumskonfigurationen använder ecodan_cnrf_instance, ecodan_cnrf-plattformen, Room-identifierare och set_climate_temperature_room_${room_identifier}(temperature: float).
Forkens nuvarande paket använder i stället ecodan_instance internt. Detta är avsiktligt i fixturen: hp_instance är HP-hubben och ecodan_instance är CN-RF-hubben. Interna hubb-ID:n är inte HA-tjänstenamnet. Ersätt inte ecodan_instance globalt och ge inte HP samma ID.
Historiska paketet saknar också forkens sparade rumstemperatur/number-entiteter; kopiera det därför inte blint över integrationspaketet. Fixturen inkluderar det faktiskt testade integrationspaketet för båda rummen.
Inga råa huvudkonfigurationer eller hemligheter har kopierats till testpaketet.

Låsningar och faktiskt utfall
ESPHome: exakt 2026.8.2 (lokalt verifierad build-complete/bin/esphome version).
CN-RF smoke-test: exporterad commit 1afa6e126a21ce7546c20dd535209d79e2cdaad5 från befintlig repo, inte remote main och inte ocommittade filer.
HP production: aae8c4b072621de46acfb75e5d21df4177673637.
HP senaste vid denna kontroll: 29f0712b7a8d6943378db84ab78378d785b692c0 från git ls-remote https://github.com/gekkekoe/esphome-ecodan-hp.git refs/heads/main. Källhämtning under codegen lyckades för båda SHA.
Båda: schema/ID-validering PASS, samtidig import PASS, C++-generering PASS, genererat Room/API-kontrakt PASS.
Full kompilering/länkning: NOT_RUN i detta kort. Obligatorisk i nästa verifieringskort med dess slutliga commit.
Live HA/API/CN-RF: OUT_OF_SCOPE, inte verifierat.
Varning: GPIO0 är en strapping-pin. Kräv hårdvarugranskning före eventuell framtida driftsättning; ändra inte specificerad TX0 för att tysta varningen.

Levererade filer
  dual-uart.template.yaml: full specificerad Waveshare/W5500/16MB/ESP-IDF dual-UART-mall; inga hemligheter, inget OTA-block.
  prepare.py: git archive av uttrycklig lokal HEAD, skapar source/ samt production.yaml och latest.yaml med SHA-låsta HP-källor och separat build_path.
  check_imports.py: riktig ESPHome-konfigurationsvalidering i en process, båda komponentmodulerna laddade samtidigt; verifierar skilda modulobjekt/filsökvägar, hubb-/climate-typer och relativ importidentitet.
  check_generated.py: verifierar riktig kod (ignorerar YAML-kommentarer), hubbtyper/UART-bindning, unika allokeringar, båda climate-namn/ID/rumsindex, API float-signatur, triggerregistrering och rumssetter. --self-test kräver att sju manipulerade kodvarianter avslås.
  check_negative.py: kör tre verkliga negativa konfigurations/importkontroller i temporära källkopior, aldrig mot checkouten. Kräver ID-redefined respektive assertionfel. Avbryter vid Git-autentiseringsfel.
  smoke/: körda YAML-filer, exporterad source och maskinläsbar låsmatris.
  result.json och *.log: verkliga körresultat. matrix.json genereras som NOT_RUN; result.json är kvittot för denna smoke-körning.

Körkommandon för nästa verifierare
Kör från denna katalog. Sätt FINAL_REPO till integrationskortets verifierade checkout och committa först de ändringar som ska testas: prepare exporterar endast HEAD. Befintligt mål för --out vägras för att undvika blandade revisioner.

  set -euo pipefail
  export PATH=/home/michael/.hermes/kanban/workspaces/t_18ba6a21/build-complete/bin:$PATH
  esphome version
  python -c 'import importlib.metadata; assert importlib.metadata.version("esphome") == "2026.8.2"'
  git -C "$FINAL_REPO" status --short
  git -C "$FINAL_REPO" rev-parse HEAD
  git ls-remote https://github.com/gekkekoe/esphome-ecodan-hp.git refs/heads/main

Spara sista kommandots exakta fullständiga SHA och använd som HP_LATEST_SHA. Vid autentiseringsfel: stoppa, lämna sanerat exakt fel; byt inte auth-metod eller version tyst.

  python prepare.py --repo "$FINAL_REPO" --out verification --hp-latest "$HP_LATEST_SHA"
  for variant in production latest; do
    python check_imports.py "verification/$variant.yaml" > "$variant-imports.log" 2>&1
    esphome compile --only-generate "verification/$variant.yaml" > "$variant-codegen.log" 2>&1
    python check_generated.py "verification/.esphome/build/$variant/src/main.cpp" --self-test > "$variant-contract.log" 2>&1
    esphome compile "verification/$variant.yaml" > "$variant-full-build.log" 2>&1
  done
  python check_negative.py verification > negative-summary.log 2>&1

ESPHome placerar den relativa build_path under konfigurationskatalogens .esphome/, inte direkt under katalogen. check_imports.py initierar CORE.config_path och anropar read_config({}) enligt installerad 2026.8.2-signatur.
Om fullbygget för production misslyckas är slutverifieringen BLOCKERAD/UNDERKÄND, aldrig PASS baserat på codegen. För latest får nästa kort dokumentera ett konkret praktiskt hinder. Behåll alla terminala exitkoder, sanerade loggar, käll-SHA samt firmware-/ELF-checksummor vid lyckade byggen. Installera inte en alternativ ESPHome-version. Använd inte esphome run/upload och anslut inte till enheten.

Utökad regressionsplan och förväntat resultat
1. Python-namnrymd/import: riktig samtidig import på båda HP-pinnarna ska passera. Ändra endast en isolerad kopias climate namespace till ecodan: assertionfel. Ändra relativ import till esphome.components.ecodan: assertionfel om fel hubb. Negativtesterna ovan har körts och avslagits av rätt orsaker.
2. ID-kollision: sätt HP:s id till ecodan_instance i isolerad fixture: ESPHome ska avvisa med 'ID ecodan_instance redefined!'. Positiv fixture valideras med separata hubbar/UART-ID:n och Room0/Room1-ID:n. Detta har körts.
3. C++-samexistens: full kompilering och länkning av båda externa komponentkatalogerna ska lyckas. Generering ensam bevisar inte ODR-/include-/länkfrihet. Kontrollera både ecodan och ecodan_cnrf i bygglogg/kompilerade objekt och inga omdirigerade felmoduler. Obligatoriskt nästa kort.
4. Room/API: change Room1 name, action room_0 name, float to int, rumsrouting 0 till 1 eller CN-RF UART till HP UART: checker ska slå larm. Dessa är körda mutationer av genererad text, inte firmwarefunktionstester. Behåll hela schema/codegen/fullbuildkedjan när verklig källkod ändras.
5. De tre C++-riskerna: nästa kort kör forkens befintliga tests/test_* (pytest) mot slutlig källa, inklusive float[8]-index med UBSan för 7/8/255, NaN/inf/ogiltiga temperaturer samt båda response-handlernas fallthrough. Negativ bas ska ge avsedda fel, inte en miljö-/compilerfailure. Dessa tester kördes inte om av detta förberedelsekort; se forkens befintliga regressionstester och integrationens tidigare kvitton. Lägg inga syntaxsträngtester som ersättning för exekverad C++.
6. Efter sista kodändring: exportera ny HEAD till nytt verification-mål och kör om allt. Testa aldrig oavsiktligt gamla remote-forken när lokal integration avses.

Genererad API-kod kontra Home Assistant
Förväntad nativ API-åtgärd är set_climate_temperature_room_0 med en float-parameter temperature (och motsvarande room_1). Med syntetiska nodnamnet blir förväntad HA-namngivning esphome.cnrf_coexistence_test_set_climate_temperature_room_0; prefixet esphome.* sätts i HA och finns inte bokstavligt i main.cpp. Checker verifierar ESPHome-triggern och dess registrering, inte HA-registret.
En framtida separat godkänd liveverifiering måste läsa verkligt tjänsteregister och parameterfält, verkliga Room0/Room1-entiteter, automationsreferenser och naturliga spår. Anropa inte temperatursettern som passivt kommunikationstest. Ett uppdaterat current_temperature bevisar inte CN-RF-acknowledgement eller löst JO403, och presentationens avrundning kan skilja sig från temperaturpayload. Ingen sådan liveverifiering ingår här.

Verktygshinder
Inget kvarvarande hinder för fixture/smoke-testerna. execute_code nekades före körning i headless-läget; normala fil-/terminalverktyg fungerade, inga skydd ändrades.
Använd redan tillhandahållen build-complete-miljö med komplett Python 3.13; den äldre build-py313-miljön hade tidigare ensurepip-hinder för IDF. Ingen ny miljö har installerats här. Framtida fullbyggets verktyg/beroenden måste verifieras på nytt, inte antas från denna codegen-körning.
