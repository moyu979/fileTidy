class a:
    def __init__(self) -> None:
        self.b=False
        
b=a()
c=b
c.b=True
print(b.b)
