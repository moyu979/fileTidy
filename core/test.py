

class eit:
    def __init__(self) -> None:
        self.l=[0,1,2,3,4,5,6]
        self.i=0
    def i(self):
        pass
    def __iter__(self):
        self.i=0
        return self
    def __next__(self):
        if self.i==len(self.l):
            raise StopIteration
        else:
            self.i=self.i+1
            return self.l[self.i-1]
    
e=eit()
for i in e:
    print(i)
for i in e:
    print(i)