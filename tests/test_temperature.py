"""Execute the production setter in a minimal host harness, with bounds sanitizer."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_room_temperature_bounds_and_nonfinite(tmp_path):
    source = (ROOT / 'components/ecodan_cnrf/ecodan.cpp').read_text()
    start = source.index('    void EcodanHeatpump::set_room_thermostat_current_temp')
    end = source.index('    void EcodanHeatpump::publish_state', start)
    harness = '''#include <cmath>
#include <cstdint>
#include <cassert>
struct EcodanHeatpump {
  struct { float CurrentRoomTemperatures[8] = {}; float guard[248] = {}; } status;
  void set_room_thermostat_current_temp(float, uint8_t);
};
''' + source[start:end] + '''
int main() {
 EcodanHeatpump hp;
 for (int room = 0; room < 8; ++room) {
   hp.set_room_thermostat_current_temp(23.4f, room);
   assert(hp.status.CurrentRoomTemperatures[room] == 23.4f);
 }
 hp.set_room_thermostat_current_temp(20, 8);
 hp.set_room_thermostat_current_temp(20, 255);
 for (float t : hp.status.CurrentRoomTemperatures) assert(t == 23.4f);
 for (float guard : hp.status.guard) assert(guard == 0);
 hp.set_room_thermostat_current_temp(NAN, 0);
 assert(hp.status.CurrentRoomTemperatures[0] == 255);
 hp.set_room_thermostat_current_temp(INFINITY, 7);
 assert(hp.status.CurrentRoomTemperatures[7] == 255);
 hp.set_room_thermostat_current_temp(-INFINITY, 1);
 assert(hp.status.CurrentRoomTemperatures[1] == 255);
}
'''
    cpp = tmp_path / 'setter.cpp'
    cpp.write_text(harness)
    exe = tmp_path / 'setter'
    subprocess.run(['g++', '-std=c++17', '-fsanitize=undefined,bounds', '-fno-sanitize-recover=all', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
