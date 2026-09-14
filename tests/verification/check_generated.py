"""Check actual generated C++, not echoed YAML comments. ESPHome 2026.8.2 only."""
import argparse
from pathlib import Path
import re


def verify(text):
    code = '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('//'))
    expected = [
        'new(hp_instance) ecodan::EcodanHeatpump();',
        'new(ecodan_instance) ecodan_cnrf::EcodanHeatpump();',
        'hp_instance->set_uart_parent(uart_hp);',
        'ecodan_instance->set_uart_parent(uart_cnrf);',
    ]
    for room in (0, 1):
        expected += [
            f'new(heatpump_climate_room_{room}) ecodan_cnrf::EcodanClimate();',
            f'heatpump_climate_room_{room}->set_room_identifier({room});',
            f'App.register_climate(heatpump_climate_room_{room}, "Room{room}",',
            f'ecodan_instance->set_room_thermostat_current_temp(temperature, {room});',
            f'ClimateRoomIdentifier::ROOM_{room}',
            f'ecodan_instance->update_room_mask({room});',
        ]
        service = rf'new\((\w+)\) api::UserServiceTrigger<api::enums::SUPPORTS_RESPONSE_NONE, float>\("set_climate_temperature_room_{room}", \{{"temperature"\}}\);'
        triggers = re.findall(service, code)
        assert len(triggers) == 1, f'Room{room} API float signature/name missing or duplicated'
        registrations = re.findall(r'initialize_user_services\(\{([^}]+)\}\)', code)
        assert len(registrations) == 1 and triggers[0] in [x.strip() for x in registrations[0].split(',')], 'API trigger not registered'
    for fragment in expected:
        assert fragment in code, f'Missing generated contract: {fragment}'
    allocations = re.findall(r'\bnew\((\w+)\)', code)
    assert len(allocations) == len(set(allocations)), 'Duplicate generated ID allocation'


def self_test(text):
    mutations = [
        ('namespace', 'ecodan_cnrf::EcodanClimate', 'ecodan::EcodanClimate'),
        ('API name', 'set_climate_temperature_room_0', 'set_climate_temperature_zone_0'),
        ('API type', 'SUPPORTS_RESPONSE_NONE, float>', 'SUPPORTS_RESPONSE_NONE, int>'),
        ('Room1 label', '"Room1"', '"RenamedRoom"'),
        ('UART swap', 'ecodan_instance->set_uart_parent(uart_cnrf)', 'ecodan_instance->set_uart_parent(uart_hp)'),
        ('room routing', 'set_room_thermostat_current_temp(temperature, 0)', 'set_room_thermostat_current_temp(temperature, 1)'),
    ]
    for label, old, new in mutations:
        assert old in text
        try:
            verify(text.replace(old, new))
        except AssertionError:
            print('EXPECTED_FAIL:', label)
        else:
            raise AssertionError('Mutation escaped: ' + label)
    try:
        verify(text + '\nnew(hp_instance) ecodan::EcodanHeatpump();\n')
    except AssertionError:
        print('EXPECTED_FAIL: duplicate ID')
    else:
        raise AssertionError('Duplicate ID escaped')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('main_cpp', type=Path)
    p.add_argument('--self-test', action='store_true')
    a = p.parse_args()
    text = a.main_cpp.read_text()
    verify(text)
    print('PASS: generated namespaces, distinct IDs/UARTs, Room0/Room1 and native API contract')
    if a.self_test:
        self_test(text)
