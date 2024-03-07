from .ghost import GhostColors
from .constants import Directions
from .gameState import GameState

class GameStateCompressed:
	'''
	Compressed copy of the game state, for easier storage for path planning.
	'''

	def __init__(
		self,
		serialized: bytes,
		ghostPlans: dict[GhostColors, Directions]
	) -> None:
		'''
		Construct a new compressed game state object
		'''

		# Serialization of the game state, in bytes
		self.serialized: bytes = serialized

		# Store tentative ghost plans
		self.ghostPlans: dict[GhostColors, Directions] = ghostPlans
		
def compressGameState(state: GameState) -> GameStateCompressed:
	'''
	Function to compress the game state into a smaller object, for easier storage
	'''

	return GameStateCompressed(state.serialize(), state.getGhostPlans())

def decompressGameState(state: GameState, compressed: GameStateCompressed):
	'''
	Function to de-compress game state information for path planning
	'''

	# Serialization (bytes) to state
	state.update(compressed.serialized, lockOverride=True)

	# Unpack the ghost plans
	state.updateGhostPlans(compressed.ghostPlans)