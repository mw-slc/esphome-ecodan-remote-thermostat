"""Load both real external components in one ESPHome validation process."""
import argparse
import importlib
import importlib.metadata
from pathlib import Path
import sys
from esphome.config import read_config

p = argparse.ArgumentParser()
p.add_argument('yaml', type=Path)
a = p.parse_args()
assert importlib.metadata.version('esphome') == '2026.8.2'
from esphome.core import CORE
CORE.config_path = a.yaml.resolve()
config = read_config({})
assert config is not None, 'ESPHome schema/ID validation failed'
hp = importlib.import_module('esphome.components.ecodan')
cnrf = importlib.import_module('esphome.components.ecodan_cnrf')
cl = importlib.import_module('esphome.components.ecodan_cnrf.climate')
assert hp is not cnrf
assert Path(hp.__file__).resolve() != Path(cnrf.__file__).resolve()
assert str(cnrf.ECODAN) == 'ecodan_cnrf::EcodanHeatpump'
assert str(cl.EcodanClimate) == 'ecodan_cnrf::EcodanClimate'
assert cl.ECODAN is cnrf.ECODAN, 'Climate relative import binds wrong hub'
assert str(hp.ECODAN) == 'ecodan::EcodanHeatpump'
assert sys.modules['esphome.components.ecodan'] is hp
assert sys.modules['esphome.components.ecodan_cnrf'] is cnrf
print('PASS: real ecodan/ecodan_cnrf imports coexist, classes and climate hub are isolated')
