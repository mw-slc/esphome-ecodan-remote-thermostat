from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def test_climate_codegen_namespace_is_isolated():
    spec = importlib.util.spec_from_file_location(
        'esphome.components.ecodan_cnrf', ROOT / 'components/ecodan_cnrf/__init__.py',
        submodule_search_locations=[str(ROOT / 'components/ecodan_cnrf')])
    import sys
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    from esphome.components.ecodan_cnrf.climate import EcodanClimate
    assert str(EcodanClimate) == 'ecodan_cnrf::EcodanClimate'


def test_example_uses_own_fork_and_component():
    source = (ROOT / 'ecodan-remote-thermostat-esphome.yaml').read_text()
    assert 'github://mw-slc/esphome-ecodan-remote-thermostat@main' in source
    assert 'url: https://github.com/mw-slc/esphome-ecodan-remote-thermostat' in source
    assert 'components: [ ecodan_cnrf ]' in source
    assert '\necodan_cnrf:' in source
