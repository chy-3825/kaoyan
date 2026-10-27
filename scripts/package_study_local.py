"""Package local-only releases; preserve previous installers and signing keys."""
import hashlib
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = Path('/home/chy/桌面/研习三科App-20261027')
PUBLIC = ROOT / 'apk'
SIGNER = '/home/chy/.cache/yanxi-android/tools/android-16/apksigner'
for name, label, old in [('calculus','研习高数','1.2.1'),('linear-algebra','研习线代','1.2.1'),('probability','研习概率','1.2.1')]:
    source = ROOT / 'apps' / name / f'{label}-1.3.0.apk'
    previous = PUBLIC / f'yanxi-{name}-{old}.apk'
    def certificate(path):
        output = subprocess.check_output([SIGNER,'verify','--print-certs',str(path)],text=True)
        return next(line for line in output.splitlines() if 'certificate SHA-256 digest:' in line)
    if previous.exists():
        assert certificate(previous) == certificate(source), name
        archive = PUBLIC / 'archive' / previous.name
        archive.parent.mkdir(exist_ok=True)
        if archive.exists():
            assert archive.read_bytes() == previous.read_bytes()
            previous.unlink()
        else:
            previous.rename(archive)
    old_desktop = DESKTOP / f'{label}-{old}.apk'
    if old_desktop.exists():
        archive = DESKTOP / '旧版备份' / old_desktop.name
        archive.parent.mkdir(exist_ok=True)
        if archive.exists():
            assert archive.read_bytes() == old_desktop.read_bytes()
            old_desktop.unlink()
        else:
            old_desktop.rename(archive)
    shutil.copy2(source, PUBLIC / f'yanxi-{name}-1.3.0.apk')
    shutil.copy2(source, DESKTOP / source.name)
    print(label,'1.3.0 packaged; signing certificate preserved')
(PUBLIC / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(PUBLIC.glob('*.apk'))))
(DESKTOP / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(DESKTOP.glob('*.apk'))))
