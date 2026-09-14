"""Real config/import negative controls, isolated copies only; never changes target repo."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

p = argparse.ArgumentParser()
p.add_argument('fixture_dir', type=Path)
a = p.parse_args()
root = a.fixture_dir.resolve()
checker = Path(__file__).with_name('check_imports.py').resolve()
for case in ('duplicate-id', 'namespace', 'python-import'):
    with tempfile.TemporaryDirectory(prefix='negative-', dir=root.parent) as tmp:
        dst = Path(tmp)
        shutil.copytree(root / 'source', dst / 'source', ignore=shutil.ignore_patterns('__pycache__'))
        config = (root / 'production.yaml').read_text()
        if case == 'duplicate-id':
            assert 'id: hp_instance' in config
            config = config.replace('id: hp_instance', 'id: ecodan_instance')
        else:
            module = dst / 'source/components/ecodan_cnrf/climate.py'
            text = module.read_text()
            old, new = ('namespace("ecodan_cnrf")', 'namespace("ecodan")') if case == 'namespace' else (
                'from . import ECODAN, CONF_ECODAN_ID, ECODAN_CLIMATE',
                'from esphome.components.ecodan import ECODAN, CONF_ECODAN_ID, ECODAN_CLIMATE')
            assert old in text
            module.write_text(text.replace(old, new))
        (dst / 'production.yaml').write_text(config)
        result = subprocess.run([sys.executable, str(checker), str(dst / 'production.yaml')], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (root.parent / f'negative-{case}.log').write_text(result.stdout)
        # Infrastructure/network failures must never be counted as expected test rejection.
        if any(s in result.stdout.lower() for s in ('authentication failed', 'could not read username', 'permission denied (publickey)')):
            raise RuntimeError('Git authentication failed; stop and inspect sanitized log')
        reason = {'duplicate-id': 'redefined', 'namespace': 'AssertionError', 'python-import': 'AssertionError'}[case]
        assert result.returncode != 0 and reason in result.stdout, (case, result.returncode, 'wrong rejection reason; inspect log')
        print('EXPECTED_FAIL:', case)
