#import paramiko
#from concurrent.futures import ThreadPoolExecutor
#import time
import logging
#from concurrent.futures import TimeoutError as FuturesTimeout
import subprocess 
from pathlib import Path
import argparse
import shutil
import sys
#from datetime import datetime
import json
import psutil

#设置loggers
run_log = logging.getLogger("run_log")
run_log.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.WARNING)

runHandler=logging.FileHandler(filename='run.log',mode='w')

formatter=logging.Formatter(fmt="%(asctime)s|%(levelname)s|%(message)s",datefmt='%Y-%m=%d %H:%M:%S')

consoleHandler.setFormatter(formatter)
runHandler.setFormatter(formatter)

run_log.addHandler(consoleHandler)
run_log.addHandler(runHandler)


#定义设备类
class Device:
    def __init__(self,name,w,j):
        self.name = name
        self.w = w
        self.j = j

#数据输出函数
    def show_log(self,strs):
        print("-"*10)
        if self.j:
            logs = json.dumps(strs,ensure_ascii=False,indent=2)
            print(logs)
        else:
            print(strs)

#磁盘检查函数
    def check_disk(self,paths):
        strs = []
        if len(paths) > 0:
            for i in paths:
                if paths[i] > self.w:
                    data = {
                        "path": i,
                        "使用率": f"{paths[i]}%",
                        "磁盘状态": "磁盘容量已不足，需清理！"
                        }
                else:
                     data = {
                        "path": i,
                        "使用率": f"{paths[i]}%",
                        "磁盘状态": "磁盘正常！"
                        }
                strs.append(data)
            self.show_log(strs)
        else:
            run_log.warning(f"操作系统路径未获取成功，请重新获取！！！")

#TOP5CPU进程
    def get_top_cpu(self):
        strs=[]
        procs=self.get_job()
        procs_sorted = sorted(procs,key=lambda x: x['cpu_percent'], reverse=True)
        for p in procs_sorted[:5]:
            data = {
                    "PID":p['pid'],
                    "CPU%":p['cpu_percent'],
                    "NAME":p["name"]
                }
            strs.append(data)
        self.show_log(strs)

#TOP5内存进程
    def get_top_mem(self):
        strs=[]
        procs=self.get_job()
        procs_sorted = sorted(procs,key=lambda x: x['memory_percent'], reverse=True)
        for p in procs_sorted[:5]:
            data = {
                    "PID":p['pid'],
                    "MEM":f"{p['memory_percent']:.2f}",
                    "NAME":p["name"]
                }
            strs.append(data)
        self.show_log(strs)

#计算负载情况
    def judge_load(self):
        proc=int(self.get_cpu_num())
        load=float(f"{self.get_load()['1分钟平均负载']}")
        check=float(load/proc)
        if check > 1:
            strs=f"负载{check}过高，请注意！"
        else:
            strs=f"负载{check},正常"
        self.show_log(strs)

#检查内存使用异常状态
    def check_mem(self):
        mem=self.get_mem()[0]
        user=int(mem['已使用'].rsplit("MB")[0])
        total=int(mem['总容量'].rsplit("MB")[0])
        if user/total*100 > 80:
            strs="内存占用过高，请注意"
        else:
            strs="内存使用正常"
        self.show_log(strs)
        
            
            

#定义单机设备类
class Single_Linux(Device):

#命令执行函数
    def commond(self,strs):
        com = strs.split()
        try:
            output = subprocess.run(com,capture_output=True,text=True,check=True)
            return output
        except subprocess.CalledProcessError as e:
            run_log.warning(f"命令执行失败！\n具体错误原因:{e}")
            sys.exit(1)
        except FileNotFoundError:
            run_log.warning(f"操作系统选择错误，请更换为Linux系统！")
            sys.exit(1)

#磁盘挂载点获取函数
    def get_path(self):
        output=self.commond("df -P")
        paths=dict()
        IGNORE_FS = {'proc','tmpfs','sysfs','devtmpfs','cgroup','cgroup2','overlay','squashfs','autofs','mqueue','debugfs','tracefs'}

        for lines in output.stdout.splitlines()[1:]:
            parts = lines.split()
            if len(parts) >=6:
                p = ' '.join(parts[5:])
            else:
                p = parts[5]
            if parts[0]  not in IGNORE_FS:
                try:
                    usage = shutil.disk_usage(p)
                    paths[p]=float(f"{usage.used /usage.total*100:.2f}")                       
                except :
                    run_log.warning(f"{p}路径获取信息失败！")
        return paths

#获取CPU运行状态
    def get_cpu_run(self):
        output=self.commond("vmstat -w 1 1")
        for lines in output.stdout.splitlines()[2:]:
            strs=lines.split()
        data ={
                "用户态CPU占用": strs[12],
                "内核态CPU占用": strs[13],
                "CPU IO等待情况": strs[15]
            }
        self.show_log(data)
        return strs

#获取CPU核数函数
    def get_cpu_num(self):
        cpu=self.commond("nproc")
        return cpu.stdout

#获取内存数据
    def get_mem(self):
        output=self.commond("free -m")
        strs=[]
        for lines in output.stdout.splitlines()[1:]:
            parts = lines.split()
            if int(parts[2]) != 0:
                data = {
                        "内存类型": parts[0],
                        "总容量": f"{parts[1]}MB",
                        "已使用": f"{parts[2]}MB",
                        "可用容量": f"{parts[3]}MB",
                        "缓存占用": f"{parts[5]}MB"
                        }
                strs.append(data)
            else:
                data = {
                        "内存类型": parts[0],
                        "总容量": f"{parts[1]}MB",
                        "已使用": f"{parts[2]}MB",
                        "可用容量": f"{parts[3]}MB"
                        }
                strs.append(data)
        self.show_log(strs)
        return strs
                
            
#获取CPU平均负载
    def get_load(self):
        output=self.commond("uptime")
        strs = output.stdout.split()
        index=strs.index("load")
        data= {
            "1分钟平均负载":strs[index+2].rsplit(",")[0],
            "5分钟平均负载":strs[index+3].rsplit(",")[0],
            "15分钟平均负载":strs[index+4]
            }
        self.show_log(data)
        return data

#获取进程
    def get_job(self):
        procs=[]
        for p in psutil.process_iter(['pid','name','cpu_percent','memory_percent']):
            try:
                procs.append(p.info)
            except (pstuil.NoSuchProcess,psutil.AccessDenied) as e:
                run_log.warning(f"运行错误，错误日志为:{e}")
        return procs

def main():
    parser = argparse.ArgumentParser(description="自动化巡检")
    parser.add_argument('-w','--warns',type=int,default=80)
    parser.add_argument('-j','--json',action='store_true',default=False)
    parser.add_argument('--only',default=None)

    args = parser.parse_args()


    cs=Single_Linux("cs",args.warns,args.json)
    if args.only == None:
        cs.check_disk(cs.get_path())
        cs.check_mem()
        cs.get_cpu_run()
        cs.get_top_cpu()
        cs.get_top_mem()
        cs.judge_load()
    elif args.only == "cpu":
        cs.get_cpu_run()
        cs.get_top_cpu()
        cs.get_top_mem()
        cs.judge_load()
    elif args.only == "mem":
        cs.check_mem()
    elif args.only == "disk":
        cs.check_disk(cs.get_path())
    else:
        run_log.warning("参数错误，请输入--only内容为: cup、mem、disk")



if __name__ == "__main__":
    main()
        
