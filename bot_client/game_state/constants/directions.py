from enum import IntEnum

class Directions(IntEnum):
    '''
    Enum of possible directions for the Pacman agent
    '''

    UP    = 0
    LEFT  = 1
    DOWN  = 2
    RIGHT = 3
    NONE  = 4

# Directions:                 U     L     D     R  None
D_ROW: list[int]        = [  -1,   -0,   +1,   +0,   +0]
D_COL: list[int]        = [  -0,   -1,   +0,   +1,   +0]
D_MESSAGES: list[bytes] = [b'w', b'a', b's', b'd', b'.']

reversedDirections: dict[Directions, Directions] = {
    Directions.UP:    Directions.DOWN,
    Directions.LEFT:  Directions.RIGHT,
    Directions.DOWN:  Directions.UP,
    Directions.RIGHT: Directions.LEFT,
    Directions.NONE:  Directions.NONE
}