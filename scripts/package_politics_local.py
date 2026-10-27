"""Deliver the politics UI release locally with recoverable old installers."""
from pathlib import Path
import hashlib
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'apk'
DESKTOP=Path('/home/chy/桌面/研习三科App-20261027')
source=ROOT/'apps/politics/研习政治-1.7.0.apk'
signer='/home/chy/.cache/yanxi-android/tools/android-16/apksigner'
def certificate(path):
    result=subprocess.check_output([signer,'verify','--print-certs',str(path)],text=True)
    return next(s for s in result.splitlines() if 'certificate SHA-256 digest:' in s)
current=certificate(source)
for old,archive in [(PUBLIC/'yanxi-politics-1.6.1.apk',PUBLIC/'archive/yanxi-politics-1.6.1.apk'),(Path('/home/chy/桌面/yanxi-politics-1.6.1.apk'),DESKTOP/'旧版备份/yanxi-politics-1.6.1.apk')]:
    if old.exists():
        assert certificate(old)==current
        archive.parent.mkdir(parents=True,exist_ok=True)
        if archive.exists():
            assert archive.read_bytes()==old.read_bytes()
            old.unlink()
        else:old.rename(archive)
shutil.copy2(source,PUBLIC/'yanxi-politics-1.7.0.apk')
shutil.copy2(source,DESKTOP/source.name)
for folder in (PUBLIC,DESKTOP):
    (folder/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(folder.glob('*.apk'))))
preview=DESKTOP/'界面预览';preview.mkdir(exist_ok=True)
for stem,label in [('home','政治首页'),('question','政治做题页')]:
    p=Path(f'/tmp/politics-390-{stem}.png')
    if p.exists():shutil.copy2(p,preview/f'{label}.png')
print('Politics 1.7.0 delivered; previous installers archived; signing certificate preserved.')
