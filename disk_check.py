from subprocess import run
from pathlib import Path

class Check:
    def __init__(self,w=80,p=Path()):
        self.w = int(w)
        self.path = dict()
        self.check = []
        self.filepath=p

    def get_path(self):
        output = run(["df","-h"],capture_output=True,text=True)
        lines=output.stdout.splitlines()
        for i in lines:
            self.path[i.split()[5]]=i.split()[4]
    
    def check_path(self):
        for i in self.path:
            try:
                if int(self.path[i].replace("%","")) > self.w:
                    self.check.append(i)
                    print(f"{i}:磁盘已满及时清理")
            except ValueError:
                continue
    
    def create_file(self):
        p=self.filepath/"check1.txt"
        with p.open('w') as f:
            for i in self.check:
                txt = i+'磁盘已使用超过'+self.w+'请及时清理'
                f.write(txt)

def main():
    c=Check(1)
    c.get_path()
    c.check_path()
    #c.create_file()


main()
