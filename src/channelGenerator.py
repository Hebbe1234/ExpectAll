from enum import Enum

class ChannelGenerator(Enum):
    FASTHEURISTIC=0
    JAPANMIP=1
    OLDMIP=2

class ChannelGeneration(Enum):
    RANDOM=0
    EDGEBASED=1
    NODEBASED=2
class PathType(Enum):
    NAIVE=0
    DISJOINT=1
    SHORTEST=2
    
class BucketType(Enum):
	NAIVE=0
	OVERLAPPING=2