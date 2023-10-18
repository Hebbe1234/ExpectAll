class Demand:
    def __init__(self, source: str, target: str):
        self.source = source
        self.target = target

    def __str__(self):
        return f"{self.source} => {self.target}"
    
    def __repr__(self):
        return str(self)
    
    def __eq__(self, other):
        return ((self.source, self.target) ==
                (other.source, other.target))
    
    def __hash__(self):
        return hash((self.source, self.target))