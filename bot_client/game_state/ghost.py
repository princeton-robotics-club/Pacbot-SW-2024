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
		self.spawning: bool = bool(True)

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

		return (self.frightSteps > 0)

	def move(self) -> None:
		'''
		Update the ghost's position for simulation purposes
		'''

		# As an approximation since we don't have enough info, assume the location
		# of the ghost will not change much if it is spawning (as it might be
		# trapped in the ghost house) - this holds for short-term simulations into
		# the future, but feel free to adjust it if you have a better way to
		# predict how spawning ghosts will behave
		if self.spawning:
			return

		# Advance the ghost's location
		self.location.advance()

		# Set the current direction to the guess of the planned direction
		self.location.setDirection(self.plannedDirection)

		# If the ghost is frightened, drop its steps by 1
		if self.isFrightened():
			self.frightSteps -= 1
