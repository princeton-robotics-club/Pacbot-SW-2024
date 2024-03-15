from enum import IntEnum
import math
# Manhattan distance
from game_state.location import Location
import policies.astar.genPachattanDistDict as pacdist
import policies.astar.example as ex

class DistTypes(IntEnum):
    """
    Enum of distance types
    """

    MANHATTAN_DISTANCE = 0
    EUCLIDEAN_DISTANCE = 1
    PACHATTAN_DISTANCE = 2

def distL1(loc1: Location, loc2: Location) -> int:
    return abs(loc1.row - loc2.row) + abs(loc1.col - loc2.col)

# Manhattan distance
def distSqL1(loc1: Location, loc2: Location) -> int:
    dr = abs(loc1.row - loc2.row)
    dc = abs(loc1.col - loc2.col)
    return dr * dr + dc * dc

# Squared Euclidean distance
def distSqL2(loc1: Location, loc2: Location) -> int:
    return (loc1.row - loc2.row) * (loc1.row - loc2.row) + (loc1.col - loc2.col) * (
        loc1.col - loc2.col
    )

# Euclidean distance
def distL2(loc1: Location, loc2: Location) -> int:
    return (
        (loc1.row - loc2.row) * (loc1.row - loc2.row)
        + (loc1.col - loc2.col) * (loc1.col - loc2.col)
    ) ** 0.5

# Pachattan distance
def distL3(loc1: Location, loc2: Location) -> int:
    key = pacdist.getKey(loc1, loc2)
    return ex.PACHATTAN[key]

# Squared Pachattan distance
def distSqL3(loc1: Location, loc2: Location) -> int:
    pacDist = distL3(loc1, loc2)
    return pacDist * pacDist

