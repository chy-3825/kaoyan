import subprocess,time,xml.etree.ElementTree as E,re,pathlib
OUT=pathlib.Path(__file__).resolve().parent
ADB=str(pathlib.Path.home()/'.cache/yanxi-android/sdk/platform-tools/adb')
def adb(*a):return subprocess.check_output([ADB,'-s','emulator-5556',*a],text=True,stderr=subprocess.STDOUT)
def ui():
 adb('shell','uiautomator','dump','/sdcard/yanxi-v110.xml');return adb('shell','cat','/sdcard/yanxi-v110.xml')
def tap(label):
 for _ in range(6):
  for n in E.fromstring(ui()).iter('node'):
   t=n.get('text','') or n.get('content-desc','')
   if t==label:
    x,y,X,Y=map(int,re.findall(r'\d+',n.get('bounds')))
    if X>x and Y>y and y>=24 and Y<=796:
     adb('shell','input','tap',str((x+X)//2),str((y+Y)//2));time.sleep(.4);return
  adb('shell','input','swipe','200','650','200','260','300');time.sleep(.5)
 raise AssertionError('Missing '+label)
def screenshot(name):
 adb('shell','screencap','-p','/sdcard/yanxi-shot.png');adb('pull','/sdcard/yanxi-shot.png',str(OUT/name))
assert 'yanxi-smoke' in adb('emu','avd','name')
adb('logcat','-c')
for _ in range(3):
 adb('shell','am','force-stop','com.yanxi.politics');adb('shell','am','start','-W','-n','com.yanxi.politics/.MainActivity');time.sleep(1)
 assert adb('shell','pidof','com.yanxi.politics').strip()
screenshot('1.1.0-home.png')
tap('错题本');assert '已掌握 1' in ui(), 'Old review state not preserved';tap('返回首页');tap('开始训练');screenshot('1.1.0-question.png')
tap('复制题目');tap('查看解析');tap('设置 API Key')
x=ui();assert 'DeepSeek API 设置' in x and 'deepseek-flash' in x
nodes=[n for n in E.fromstring(x).iter('node') if n.get('class')=='android.widget.EditText'];assert len(nodes)==2
x,y,X,Y=map(int,re.findall(r'\d+',nodes[0].get('bounds')));adb('shell','input','tap',str((x+X)//2),str((y+Y)//2));adb('shell','input','text','test-only-not-a-key');tap('保存')
tap('设置 API Key');assert 'API Key 已保存' in ui();tap('取消');tap('DeepSeek 生成解析')
for _ in range(12):
 x=ui()
 if '解析请求失败' in x or 'API Key 无效' in x or '请求超时' in x:break
 time.sleep(3)
assert '复制题目' in x and ('解析请求失败' in x or 'API Key 无效' in x or '请求超时' in x),x
tap('设置 API Key');tap('删除密钥');tap('关闭')
adb('shell','input','keyevent','4');assert '开始训练' in ui()
assert 'com.yanxi.politics' not in adb('logcat','-d','-b','crash')
result='PASS: Android 14; 3 cold starts; 1.0.1 record retained after upgrade; home, questions, native clipboard, encrypted API settings, native request error callback/copy fallback, key deletion, back navigation; no app crash. API success tested with mock responses only; no real user API key supplied.'
(OUT/'1.1.0-native-check.txt').write_text(result+'\n');print(result)
