import paramiko
from concurrent.futures import ThreadPoolExecutor
import time
import logging

"""
#logging初始化信息配置方法
logging.basicConfig(filename='demo.log',filemode='w',level=logging.DEBUG,
                    format="%(asctime)s|%(levelname)s|%(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
"""

#loggers记录器
app_log = logging.getLogger("app_log")
app_log.setLevel(logging.DEBUG)

check_log = logging.getLogger("check_log")

'''
app_log.addHandler()
app_log.removeHandler()
'''

#Handlers处理器
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.WARNING)

appHandler=logging.FileHandler(filename='demo.log',mode='w')
checkHandler=logging.FileHandler(filename="check.log",mode='a')
#setFormatter()

#Formatters格式
formatter = logging.Formatter(fmt="%(asctime)s|%(levelname)s|%(message)s",datefmt='%Y-%m=%d %H:%M:%S')

#创建过滤器
flt=logging.Filter("cn.cccd")

#关联过滤器
#app_log.addFilter(flt)

#设置处理器格式
consoleHandler.setFormatter(formatter)
appHandler.setFormatter(formatter)
checkHandler.setFormatter(formatter)


#设置记录器所属处理器
app_log.addHandler(consoleHandler)
app_log.addHandler(appHandler)

check_log.addHandler(checkHandler)


class Device:
    def __init__(self,ip=None,username=None,password=None,os=None,port=22,w=80):
        self.ip = ip
        self.username=username
        self.password=password
        self.os=os
        self.port=port
        self.paths=[]
        self.w=w

class Run:
    def disk_check(self,server):
        IGNORE_FS = {'proc','tmpfs','sysfs','devtmpfs','cgroup','cgroup2','overlay','squashfs','autofs','mqueue','debugfs','tracefs'}
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        try:
            ssh.connect(
                hostname=server.ip,
                port=server.port,
                username=server.username,
                password=server.password,
                timeout=10
                )
            app_log.debug(f"{server.ip}连接成功")
            #print(f"{server.ip}连接成功\n")

            stdin,stdout,stderr=ssh.exec_command('df -P')

            output=stdout.read().decode('utf-8')
            errput=stderr.read().decode('utf-8')

            if output:
                for lines in output.splitlines()[1:]:
                    parts=lines.split(maxsplit=5)
                    if parts[0] not in IGNORE_FS:
                        if int(parts[2])//int(parts[3])*100 > server.w:
                            check_log.warnging(f"磁盘分区{parts[5]}使用率过高,已达到{parts[4]},请及时清理磁盘")
                        server.paths.append(parts)
                        app_log.debug(f"{server.ip}巡检任务已完成")
            if errput:
                app_log.warning(f"命令执行失败，详细错误日志为:{errput}")
                    
        except paramiko.AuthenticationException as e:
            app_log.warning(f"{server.ip}认证失败！账户密码错误:{e}")
        except paramiko.SSHException as e:
            app_log.warning(f"{server.ip}SSH连接失败：{e}")
        except Exception as e:
            app_log.warning(f"{server.ip}系统执行失败：{e}")
        finally:
            ssh.close()
            return server.paths



servers=[]
#批量获取服务器清单
for i in range(10):
    servers.append(Device(ip="192.168.1.100",username="root",password="111"))


run=Run()

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(run.disk_check,i) for i in servers]

    for future in futures:
        try:
            future.result(timeout=5)
        except TimeoutError:
            app_log.warning(f"执行任务超时！")

"""
#线程池map方式练习
with ThreadPoolExecutor(max_workers=3) as executor:
    results=list(executor.map(brew_tea,[1,2,3,4,5,6,7]))

    for a in results:
        print(a)
"""
    
