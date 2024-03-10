from .constants import Directions, GhostColors
from .location import Location

class Ghost:
    '''
    Location and auxiliary info of a ghost in the game engine
    '''

    def __init__(self, color: GhostColors) -> None: # type: ignore
        '''
        Construct a new ghost state object
        '''

        # Ghost information
        self.color: GhostColors = color
        self.location: Location = Location() # type: ignore
        self.frightSteps: int = 0
        self.spawning: bool = True

        # (For simulation) Planned next direction the ghost will take
        self.plannedDirection: Directions = Directions.NONE

    def updateAux(self, auxInfo: int) -> None:
        '''
        Update auxiliary info (fright steps and spawning flag, 1 byte)
        '''

        self.frightSteps = auxInfo & 0x3f
        self.spawning = bool(auxInfo >> 7)

    def serializeAux(self) -> int:
        '''
        Serialize auxiliary info (fright steps and spawning flag, 1 byte)
        '''

        return (self.spawning << 7) | (self.frightSteps)

    def isFrightened(self) -> bool:
        '''
        Return whether this ghost is frightened
        '''

        return self.frightSteps > 0

