import requests,pathlib,zipfile,hashlib,concurrent.futures,os
root=pathlib.Path.home()/'.cache/yanxi-android'; root.mkdir(parents=True,exist_ok=True); sdk=root/'sdk';sdk.mkdir(exist_ok=True)
items=[('https://dl.google.com/android/repository/emulator-linux_x64-16489710.zip','ae4d823db841f6b527fe09115cc9defbfaf24a85',353959232,sdk),('https://dl.google.com/android/repository/platform-tools_r37.0.1-linux.zip','477254aa5f903c15cf51001717bdf347fb6b53e0',9054187,sdk),('https://dl.google.com/android/repository/sys-img/android/x86_64-34_r04.zip','5f6a249f9bc3b1b4c459b13ce2eb646c9680bed1',720747116,sdk/'system-images/android-34/default')]
def download(item):
 url,sha,size,dest=item;p=root/url.rsplit('/',1)[-1]
 if not p.exists() or hashlib.sha1(p.read_bytes()).hexdigest()!=sha:
  if not p.exists() or p.stat().st_size!=size:
   with p.open('wb') as f:f.truncate(size)
  step=1024*1024
  def chunk(start):
   end=min(start+step,size)-1
   with p.open('rb') as existing:
    if os.lseek(existing.fileno(),start,os.SEEK_HOLE)>=end+1:return
   for attempt in range(3):
    try:
     with requests.get(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'},stream=True,timeout=45) as r:
      r.raise_for_status();assert r.status_code==206,(r.status_code,url)
      assert r.headers['Content-Range'].startswith(f'bytes {start}-{end}/')
      written=0
      with p.open('r+b') as f:
       f.seek(start)
       for data in r.iter_content(1024*1024):f.write(data);written+=len(data)
      assert written==end-start+1
     return
    except Exception as e:
     print(p.name, start, type(e).__name__, "retry", attempt+1, flush=True)
     if attempt==2:raise
  with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex:list(ex.map(chunk,range(0,size,step)))
 assert hashlib.sha1(p.read_bytes()).hexdigest()==sha
 dest.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(p) as z:
  z.extractall(dest)
  for i in z.infolist():
   mode=i.external_attr>>16
   if mode:os.chmod(dest/i.filename,mode)
 print(dest,'ready',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(download,items))
