"""Export committed CN-RF sources and render isolated compile-only fixtures. Never flash."""
import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

PIN = 'aae8c4b072621de46acfb75e5d21df4177673637'
URL = 'https://github.com/gekkekoe/esphome-ecodan-hp.git'
p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--hp-latest', required=True, help='Exact SHA from git ls-remote at verification time')
a = p.parse_args()
assert re.fullmatch('[0-9a-f]{40}', a.hp_latest), 'latest must be a full SHA'
out = a.out.resolve()
out.mkdir(parents=True, exist_ok=False)
sha = subprocess.check_output(['git', '-C', str(a.repo), 'rev-parse', 'HEAD'], text=True).strip()
archive = subprocess.check_output(['git', '-C', str(a.repo), 'archive', sha, 'components', 'confs'])
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    tar.extractall(out / 'source', filter='data')
template = (Path(__file__).parent / 'dual-uart.template.yaml').read_text()
matrix = {'esphome': '2026.8.2', 'cnrf_sha': sha, 'hp_url': URL, 'rows': []}
for label, hp in [('production', PIN), ('latest', a.hp_latest)]:
    config = template.replace('@HP_SHA@', hp).replace('@VARIANT@', label)
    (out / f'{label}.yaml').write_text(config)
    matrix['rows'].append({'variant': label, 'hp_sha': hp, 'config': f'{label}.yaml',
                           'config_validation': 'NOT_RUN', 'codegen': 'NOT_RUN', 'full_build': 'NOT_RUN', 'live': 'OUT_OF_SCOPE'})
(out / 'matrix.json').write_text(json.dumps(matrix, indent=2) + '\n')
print(json.dumps(matrix, indent=2))
