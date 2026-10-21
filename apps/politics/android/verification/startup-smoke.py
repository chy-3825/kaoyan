#!/usr/bin/env python3
"""Reproduce 1.0.0 failure, upgrade in place, and check repeated 1.0.1 launches.
Only runs against the dedicated yanxi emulator on emulator-5556.
"""
import subprocess,time,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=pathlib.Path(__file__).resolve().parent
ADB=pathlib.Path.home()/'.cache/yanxi-android/sdk/platform-tools/adb'
DEVICE='emulator-5556'
def adb(*args):
 return subprocess.check_output([str(ADB),'-s',DEVICE,*args],stderr=subprocess.STDOUT,text=True)
def launch():return adb('shell','am','start','-W','-n','com.yanxi.politics/.MainActivity')
assert 'yanxi-smoke' in adb('emu','avd','name'), 'Refuse to test on any other device'
adb('uninstall','com.yanxi.politics')
print(adb('install','--no-incremental','-r',str(ROOT/'研习政治-1.0.0.apk')),flush=True)
adb('logcat','-c')
print(launch(),flush=True);time.sleep(3)
old=adb('logcat','-d','-b','crash');(OUT/'1.0.0-crash.txt').write_text(old)
assert 'com.yanxi.politics' in old and 'NullPointerException' in old,old
print('Reproduced old APK startup crash.',flush=True)
print(adb('install','--no-incremental','-r',str(ROOT/'研习政治-1.0.1.apk')),flush=True)
adb('logcat','-c')
results=[]
for i in range(3):
 adb('shell','am','force-stop','com.yanxi.politics')
 results.append(launch());time.sleep(2)
 assert adb('shell','pidof','com.yanxi.politics').strip()
 assert 'com.yanxi.politics' not in adb('logcat','-d','-b','crash')
time.sleep(4)
for _ in range(5):
 adb('shell','uiautomator','dump','/sdcard/yanxi-window.xml')
 xml=adb('shell','cat','/sdcard/yanxi-window.xml')
 if '2026 年真题' in xml:break
 time.sleep(1)
(OUT/'1.0.1-window.xml').write_text(xml)
assert '继续训练' in xml and '错题本' in xml and '2026 年真题' in xml,xml
adb('shell','screencap','-p','/sdcard/yanxi-startup.png')
adb('pull','/sdcard/yanxi-startup.png',str(OUT/'1.0.1-startup.png'))
results.append('PASS: Android 14 / API 34; old crash reproduced; same-signature upgrade; 3 cold launches; training and mistakes UI visible; no app crash.')
(OUT/'1.0.1-startup-check.txt').write_text('\n'.join(results))
print(results[-1],flush=True)
