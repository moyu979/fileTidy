import time
import FileList 
file=FileList.FileList()
print(time.time())
time_tuple = time.localtime(time.time())
name="../fileDirs/downloads/"
for i in range(0,6):
    name=name+str(time_tuple[i])
name=name+".txt"
print(name)