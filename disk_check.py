import subprocess 
from pathlib import Path
import argparse
import shutil
import sys
from datetime import datetime

class Data:
    def __init__(self,w):
        self.paths = dict()
        self.w = w

    def get_path(self):
        try:
            output = subprocess.run(["df","-P"],capture_output=True,text=True,check=True)
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败:{e}")
            sys.exit(1)
        except FileNotFoundError:
            print("找不到df命令，可能非Linux环境")
            sys.exit(1)
        for lines in  output.stdout.splitlines()[1:]:
            parts = lines.split()
            if len(parts) >= 6:
                p = ' '.join(parts[5:])
            else:
                p = parts[5]
            self.paths[p] = parts[0]
            

class Log:
    def __init__(self,p):
        if p.is_file():
            self.p=p.parent
        else:
            self.p = p

    def write_log(self,strs):
        name=f"{datetime.now().strftime('%m-%d')}.log"
        file_name=self.p/name
        with file_name.open('a') as f:
            print(strs,file=f)
                
        
    

class Check:
    def __init__(self,w,p):
        self.data = Data(w)
        self.log= Log(p)
        self.data.get_path()
        self.warns=[]
        
    def check_disk(self):
        IGNORE_FS = {'proc','tmpfs','sysfs','devtmpfs','cgroup','cgroup2','overlay','squashfs','autofs','mqueue','debugfs','tracefs'}
        for path in self.data.paths:
            if self.data.paths[path] in IGNORE_FS:
                continue
            else:
                try:
                    usage = shutil.disk_usage(path)
                    if int(usage.used /usage.total*100) > self.data.w:
                        self.warns.append([path,int(usage.used/usage.total*100)])
                except :
                    print(f"挂载点:{path}路径检查失败！")
                    
    
    def show_warns(self):
        for i in self.warns:
            print(f"挂载点{i[0]}:已使用{i[1]},超出警告值{self.data.w},请及时处理")

    def write_warns(self):
        for i in self.warns:
            strs=f"挂载点{i[0]}:已使用{i[1]},超出警告值{self.data.w},请及时处理"
            self.log.write_log(strs)

def main():
    parser = argparse.ArgumentParser(description="自动化巡检")
    parser.add_argument('-w','--warns',type=int,default=80)
        
        
    parser.add_argument('-p')
    args = parser.parse_args()
    if args.p == '':
        p = Path(__file__).resolve().parent
    else:
        p = Path(args.p).resolve()

    check = Check(args.warns,p)
    check.check_disk()
    check.show_warns()
    check.write_warns()

if __name__ == "__main__":
    main()
