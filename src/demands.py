from math import ceil


class Demand:
    def __init__(self, source: int, target: int,size = 1):
        self.source = source
        self.target = target
        self.size = size
        self.modulations = [1]

    def channel_sizes(self):
        cs = [m*self.size for m in self.modulations]
        base = 10
        
        return [base * ceil(x/base) for x in cs]
    
    def __str__(self):
        return f"{self.source} => {self.target} [{self.size}]"
    
    def __repr__(self):
        return str(self)