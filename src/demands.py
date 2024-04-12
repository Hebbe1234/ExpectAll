class Demand:
    def __init__(self, source: int, target: int, size = 1, id = -1):
        self.source = source
        self.target = target
        self.size = size
        self.modulations = [1]
        self.id = id

    def __str__(self):
        return f"{self.source} => {self.target} [{self.size}]"
    
    def __repr__(self):
        return str(self)
    

def original_ordering(demands:dict[int,Demand]):
    return {d.id : d for i,d in demands.items()}
        
