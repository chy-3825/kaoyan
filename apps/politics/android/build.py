#!/usr/bin/env python3
"""Build the standalone offline APK using JDK 17 and Android SDK build tools 36."""
import os,pathlib,shutil,subprocess,secrets,zipfile,hashlib,xml.etree.ElementTree as ET
P=pathlib.Path(__file__).resolve().parent
SDK=pathlib.Path(os.environ.get('YANXI_ANDROID_SDK',str(pathlib.Path.home()/'.cache/yanxi-android')))
T=next(SDK.glob('tools/*/aapt2')).parent
J=next(SDK.glob('platform/*/android.jar'))
B=P/'build';B.mkdir(exist_ok=True)
for name in ['aapt2','zipalign','apksigner','d8']:(T/name).chmod(0o755)
def run(*args):subprocess.run([str(a) for a in args],check=True,cwd=P)
assets=B/'assets';shutil.copytree(P/'web',assets,dirs_exist_ok=True)
# Source links open in the device browser; all study assets remain offline.
run(T/'aapt2','compile','--dir',P/'res','-o',B/'resources.zip')
run(T/'aapt2','link','-o',B/'unsigned.apk','--manifest',P/'AndroidManifest.xml','-I',J,'-A',assets,'--auto-add-overlay',B/'resources.zip')
classes=B/'classes';classes.mkdir(exist_ok=True)
run('javac','-encoding','UTF-8','--release','8','-classpath',J,'-d',classes,*P.glob('src/**/*.java'))
dex=B/'dex';dex.mkdir(exist_ok=True)
run(T/'d8','--lib',J,'--min-api','26','--output',dex,*classes.rglob('*.class'))
with zipfile.ZipFile(B/'unsigned.apk','a',zipfile.ZIP_DEFLATED) as z:
 for f in dex.glob('*.dex'):z.write(f,f.name)
run(T/'zipalign','-f','4',B/'unsigned.apk',B/'aligned.apk')
S=P/'signing';S.mkdir(exist_ok=True);S.chmod(0o700)
password=S/'password';key=S/'yanxi-release.jks'
if not key.exists():
 if not password.exists():password.write_text(secrets.token_urlsafe(32));password.chmod(0o600)
 run('keytool','-genkeypair','-keystore',key,'-storetype','JKS','-alias','yanxi','-keyalg','RSA','-keysize','2048','-validity','10000','-storepass:file',password,'-keypass:file',password,'-dname','CN=Yanxi Politics, O=Personal Study, C=CN')
 key.chmod(0o600)
version=ET.parse(P/'AndroidManifest.xml').getroot().get('{http://schemas.android.com/apk/res/android}versionName')
out=P.parent/f'研习政治-{version}.apk'
run(T/'apksigner','sign','--ks',key,'--ks-key-alias','yanxi','--ks-pass','file:'+str(password),'--out',out,B/'aligned.apk')
run(T/'apksigner','verify','--verbose',out)
run(T/'zipalign','-c','4',out)
(out.with_suffix('.apk.sha256')).write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n')
print(out)
