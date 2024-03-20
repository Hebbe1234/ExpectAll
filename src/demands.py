from math import ceil


class Demand:
    def __init__(self, source: int, target: int,size = 1, rounding_base=1):
        self.source = source
        self.target = target
        self.size = size
        self.modulations = [1]
        self.rounding_base = rounding_base

    def channel_sizes(self):
        cs = [m*self.size for m in self.modulations]
        return [self.rounding_base * ceil(x/self.rounding_base) for x in cs]
    
    def round(self, m, size):
        return self.rounding_base * ceil(m*size/self.rounding_base)
    def __str__(self):
        return f"{self.source} => {self.target} [{self.size}]"
    
    def __repr__(self):
        return str(self)