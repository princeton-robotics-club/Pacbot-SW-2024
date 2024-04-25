
from enum import IntEnum


class CommandType(IntEnum):
    STOP=0
    START=1
    FLUSH=2
    MOVE=3


class CommandDirection(IntEnum):
    NONE=-1
    NORTH=0
    EAST=1
    WEST=2
    SOUTH=3