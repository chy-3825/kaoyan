import subprocess,time,xml.etree.ElementTree as E,re,pathlib
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[1]
ADB=str(pathlib.Path.home()/'.cache/yanxi-android/sdk/platform-tools/adb')
def adb(*a):return subprocess.check_output([ADB,'-s','emulator-5556',*a],text=True,stderr=subprocess.STDOUT)
def ui():
 adb('shell','uiautomator','dump','/sdcard/yanxi-interaction.xml')
 return adb('shell','cat','/sdcard/yanxi-interaction.xml')
def tap(label,prefix=False):
 for _ in range(5):
  for n in E.fromstring(ui()).iter('node'):
   t=n.get('text','') or n.get('content-desc','')
   if (t.startswith(label) if prefix else t==label):
    x,y,X,Y=map(int,re.findall(r'\d+',n.get('bounds')))
    if X>x and Y>y and y>=24 and Y<=796:
     adb('shell','input','tap',str((x+X)//2),str((y+Y)//2));time.sleep(.5);return
  adb('shell','input','swipe','200','650','200','260','350');time.sleep(.5)
 raise AssertionError('Missing visible control '+label)
assert 'yanxi-smoke' in adb('emu','avd','name')
adb('shell','svc','wifi','disable');adb('shell','svc','data','disable')
tap('B ',True);tap('提交答案')
assert '这道题已加入错题本' in ui()
tap('▧ 错题本',True)
assert '待复习 1' in ui()
adb('shell','am','force-stop','com.yanxi.politics')
adb('shell','am','start','-W','-n','com.yanxi.politics/.MainActivity');time.sleep(2)
tap('▧ 错题本',True);assert '待复习 1' in ui()
adb('install','--no-incremental','-r',str(ROOT/'研习政治-1.0.1.apk'))
adb('shell','am','start','-W','-n','com.yanxi.politics/.MainActivity');time.sleep(2)
tap('▧ 错题本',True);assert '待复习 1' in ui()
tap('开始重练');tap('A ',True);tap('提交答案')
assert '回答正确，已标记为掌握' in ui()
tap('完成重练');tap('已掌握 1');assert '移回待复习' in ui()
assert 'com.yanxi.politics' not in adb('logcat','-d','-b','crash')
(OUT/'1.0.1-interaction-check.txt').write_text('PASS: Android 14 emulator; offline wrong answer; mistake saved across force-stop and in-place APK reinstall; correct review answer marked mastered; no crash.\n')
print('PASS: offline answering, mistakes, relaunch persistence, reinstall persistence, review mastery; no crash.')
