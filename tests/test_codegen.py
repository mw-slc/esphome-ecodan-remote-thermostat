"""Generate a real dual-component configuration in an isolated temporary build."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_dual_uart_codegen_preserves_room_api(tmp_path):
    fixture = (ROOT / 'tests/dual-uart.yaml').read_text()
    fixture = fixture.replace('  name: cnrf-coexistence-test',
                              f'  name: cnrf-coexistence-test\n  build_path: {tmp_path / "build"}')
    fixture = fixture.replace('path: ../components', f'path: {ROOT / "components"}')
    fixture = fixture.replace('../confs/thermostat-room.yaml', str(ROOT / 'confs/thermostat-room.yaml'))
    config = tmp_path / 'dual.yaml'
    config.write_text(fixture)
    subprocess.run([sys.executable, '-m', 'esphome', 'compile', str(config), '--only-generate'],
                   check=True, capture_output=True, text=True, timeout=180)
    cpp = (tmp_path / 'build/src/main.cpp').read_text()
    assert 'new(hp_instance) ecodan::EcodanHeatpump()' in cpp
    assert 'new(ecodan_instance) ecodan_cnrf::EcodanHeatpump()' in cpp
    for room in (0, 1):
        assert f'new(heatpump_climate_room_{room}) ecodan_cnrf::EcodanClimate()' in cpp
        assert f'("set_climate_temperature_room_{room}", {{"temperature"}})' in cpp
        assert f'set_room_thermostat_current_temp(temperature, {room})' in cpp
        assert f'App.register_climate(heatpump_climate_room_{room}, "Room{room}",' in cpp
        assert f'heatpump_climate_room_{room}->set_status([=](void) -> const ecodan_cnrf::Status&' in cpp
