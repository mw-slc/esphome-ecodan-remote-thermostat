"""Execute the production target setter and packet encoder; replace only transport."""
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('scenario', ['nan', 'bounds', 'encoding_range', 'valid'])
def test_target_temperature_rejects_invalid_without_state_or_command(tmp_path, scenario):
    source = (ROOT / 'components/ecodan_cnrf/commands.cpp').read_text()
    start = source.index('    void EcodanHeatpump::set_room_thermostat_target_temp')
    end = source.index('    bool EcodanHeatpump::schedule_cmd', start)
    harness = r'''
#include <cmath>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cassert>
#include <vector>
#include "proto.h"
#define CHECK_BIT(value, bit) ((value) & (1U << (bit)))
namespace esphome { namespace ecodan_cnrf {
struct EcodanHeatpump {
 struct {
  float TargetRoomTemperatures[8] = {};
  float guard[248] = {};
  float CurrentRoomTemperatures[8] = {20,21,22,23,24,25,26,27};
  uint8_t RcMask = 0x81;
  uint8_t RcMasterZone2 = 8;
 } status;
 std::vector<Message> sent;
 void set_room_thermostat_target_temp(float, ClimateRoomIdentifier);
 float round_nearest_half(float value) { return std::round(value * 2.0f) / 2.0f; }
 bool schedule_cmd(Message& msg) { sent.emplace_back(std::move(msg)); return true; }
};
''' + source[start:end] + r'''
}}
using namespace esphome::ecodan_cnrf;
int main(int argc, char** argv) {
 assert(argc == 2);
 EcodanHeatpump hp;
 if (std::strcmp(argv[1], "nan") == 0) {
  for (float invalid : {NAN, INFINITY, -INFINITY}) {
   hp.set_room_thermostat_target_temp(invalid, ClimateRoomIdentifier::ROOM_0);
   assert(hp.status.TargetRoomTemperatures[0] == 0);
   assert(hp.sent.empty());
  }
 } else if (std::strcmp(argv[1], "bounds") == 0) {
  for (int room = 8; room <= 255; ++room)
   hp.set_room_thermostat_target_temp(21, static_cast<ClimateRoomIdentifier>(room));
  for (float value : hp.status.TargetRoomTemperatures) assert(value == 0);
  for (float guard : hp.status.guard) assert(guard == 0);
  assert(hp.sent.empty());
 } else if (std::strcmp(argv[1], "encoding_range") == 0) {
  for (float invalid : {-65.0f, 64.0f, 1e30f, -1e30f}) {
   hp.set_room_thermostat_target_temp(invalid, ClimateRoomIdentifier::ROOM_1);
   assert(hp.status.TargetRoomTemperatures[1] == 0);
   assert(hp.sent.empty());
  }
  for (float valid : {-64.0f, 63.5f}) {
   hp.set_room_thermostat_target_temp(valid, ClimateRoomIdentifier::ROOM_1);
   assert(hp.status.TargetRoomTemperatures[1] == valid);
   assert(hp.sent.back()[1] == (valid < 0 ? 0 : 255));
  }
 } else {
  for (int room = 0; room < 8; ++room) {
   hp.set_room_thermostat_target_temp(21.3f, static_cast<ClimateRoomIdentifier>(room));
   assert(hp.status.TargetRoomTemperatures[room] == 21.3f);
   assert(hp.sent.size() == static_cast<unsigned>(room + 1));
   auto& msg = hp.sent.back();
   assert(msg.type() == MsgType::THERMOSTAT_TARGET_TEMP_SET);
   assert(msg[1] == 171); // 21.5 C encoded, not unrounded 21.3 C
   assert(msg[2] == 168); // active Room0, 20 C
   assert(msg[9] == 182); // active Room7, 27 C
   for (int pos = 3; pos < 9; ++pos) assert(msg[pos] == 0xff);
   assert(msg[11] == 0x81 && msg[12] == 0xff);
   assert(msg[14] == (room == 7 ? 1 : 0));
  }
 }
}
'''
    cpp = tmp_path / 'target.cpp'
    cpp.write_text(harness)
    exe = tmp_path / 'target'
    subprocess.run(['g++', '-std=c++17', '-fsanitize=undefined,bounds,float-cast-overflow',
                    '-fno-sanitize-recover=all', '-I', str(ROOT / 'components/ecodan_cnrf'),
                    str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe), scenario], check=True)
