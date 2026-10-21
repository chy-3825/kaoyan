import requests,pathlib,zipfile,hashlib,concurrent.futures
root=pathlib.Path.home()/'.cache/yanxi-android'; root.mkdir(parents=True,exist_ok=True)
def get(item):
 name,sha,dest=item;p=root/name
 if not p.exists() or hashlib.sha1(p.read_bytes()).hexdigest()!=sha:
  with requests.get('https://dl.google.com/android/repository/'+name,stream=True,timeout=60) as r:
   r.raise_for_status()
   with p.open('wb') as f:
    for c in r.iter_content(1024*1024):f.write(c)
 assert hashlib.sha1(p.read_bytes()).hexdigest()==sha
 target=root/dest;target.mkdir(exist_ok=True)
 with zipfile.ZipFile(p) as z:z.extractall(target)
 print(dest,'ready',flush=True)
with concurrent.futures.ThreadPoolExecutor() as ex:list(ex.map(get,[('platform-36_r02.zip','2c1a80dd4d9f7d0e6dd336ec603d9b5c55a6f576','platform'),('build-tools_r36_linux.zip','b0b6376977657e8ad9b969bacf4093601da2c6fb','tools')]))
