"""Run actual response handlers with a minimal packet/status test double."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_known_response_does_not_log_unknown(tmp_path):
    header = r'''
#include <cstdint>
#include <queue>
#include <cassert>
inline int logs = 0;
#define ESP_LOGI(...) (++logs)
namespace esphome { namespace ecodan_cnrf {
enum class GetType { THERMOSTAT_STATE_RES = 1 };
enum class MsgType { THERMOSTAT_INITIAL_GET_RES, THERMOSTAT_HOTWATER_SET_RES,
 THERMOSTAT_HOLIDAY_SET_RES, THERMOSTAT_TARGET_TEMP_SET_RES,
 THERMOSTAT_CURRENT_TEMP_SET_RES, CONNECT_RES };
struct Message {
 GetType payload = GetType::THERMOSTAT_STATE_RES;
 MsgType kind = MsgType::THERMOSTAT_INITIAL_GET_RES;
 template<class T> T payload_type() { return static_cast<T>(payload); }
 MsgType type() { return kind; }
 float get_float8_v3(int) { return 21.5f; }
 uint8_t operator[](int) { return 1; }
};
struct EcodanHeatpump {
 struct Status {
 float Zone1SetTemperature, Zone2SetTemperature;
 int RcMasterZone1, RcMasterZone2, updates = 0;
 void set_operation_mode(int) {}
 void set_heating_cooling_mode(int) {}
 void update_target_temperatures() { ++updates; }
 } status;
 std::queue<int> cmdQueue;
 bool connected = false;
 void handle_initial_get_response(Message&);
 void handle_set_response(Message&);
 void handle_connect_response(Message&);
 void handle_response(Message&);
};
}}
'''
    (tmp_path / 'ecodan.h').write_text(header)
    (tmp_path / 'response.cpp').write_bytes((ROOT / 'components/ecodan_cnrf/response.cpp').read_bytes())
    (tmp_path / 'main.cpp').write_text(r'''
#include "ecodan.h"
using namespace esphome::ecodan_cnrf;
int main() {
 EcodanHeatpump hp;
 Message msg;
 hp.handle_initial_get_response(msg);
 assert(hp.status.updates == 1);
 assert(logs == 0);
 hp.cmdQueue.push(1);
 hp.handle_set_response(msg);
 assert(hp.status.updates == 2);
 assert(hp.cmdQueue.empty());
 assert(logs == 0);
 msg.payload = static_cast<GetType>(42);
 hp.handle_initial_get_response(msg);
 assert(logs == 1);
 hp.handle_set_response(msg);
 assert(logs == 2);
}
''')
    exe = tmp_path / 'responses'
    subprocess.run(['g++', '-std=c++17', str(tmp_path / 'response.cpp'), str(tmp_path / 'main.cpp'), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
