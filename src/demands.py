class Demand:
    def __init__(self, source: int, target: int,size = 1):
        self.source = source
        self.target = target
        self.size = size

    def __str__(self):
        return f"{self.source} => {self.target} [{self.size}]"
    
    def __repr__(self):
        return str(self)