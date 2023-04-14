#因为set不能加列表，不方便所以搞出来的东西，性能很差,不建议使用
class HashSet:
    def __init__(self):
        self.set=[]
        self.itercount=0
        
    def add(self,elem):
        if len(self.set)!=0:
            for i in self.set:
                if i==elem:
                    return
        self.set.append(elem)
        
    def len(self):
        return len(self.set)
    
    def isEmpty(self):
        if len(self.set)==0:
            return True
        else:
            return False
    def clear(self):
        self.set=[]    
    def __or__(self, __t):
        for i in __t:
            self.add(i)
        return self
        #重写迭代器
    def __iter__(self):
        self.itercount=0
        return self
    def __next__(self):
        if self.itercount>=len(self.set):
            raise StopIteration
        else:
            self.itercount=self.itercount+1
            return self.set[self.itercount-1]        
    def __str__(self) -> str:
        string=""
        for i in self.set:
            string=string+" "+i[0]+" "+i[1]
        return string