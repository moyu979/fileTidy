import time

def fileTime():
    time_tuple = time.localtime(time.time())
    print(time_tuple)
    name=f"{time_tuple[0]:0>4}:{time_tuple[1]:0>2}:{time_tuple[2]:0>2} {time_tuple[3]:0>2}:{time_tuple[4]:0>2}"
    return name

if __name__=="__main__":
    print(fileTime())