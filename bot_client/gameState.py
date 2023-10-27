# Enum class (for game mode)
from enum import IntEnum

# Struct class (for processing)
from struct import unpack_from

class GameMode(IntEnum):
	'''
	Enum of possible game modes
	'''

	PAUSED = 0
	SCATTER = 1
	CHASE = 2

class GhostColors(IntEnum):
	'''
	Enum of possible ghost names
	'''

	RED = 0
	PINK = 1
	CYAN = 2
	ORANGE = 3

class Location:
	'''
	Location of an entity in the game engine
	'''

	def __init__(self) -> None:
		'''
		Construct a new location state object
		'''
		self.rowDir: int  = 0
		self.row: int     = 32
		self.colDir: int  = 0
		self.col: int     = 32

	def update(self, loc_uint16: int) -> None:
		'''
		Update a location, based on a 2-byte serialization
		'''

		# Get the row and column bytes
		row_uint8: int = loc_uint16 >> 8
		col_uint8: int = loc_uint16 & 0xff

		# Get the row direction (2's complement of first 2 bits)
		self.rowDir = row_uint8 >> 6
		if self.rowDir >= 2:
			self.rowDir -= 4

		# Get the row value (last 6 bits)
		self.row = row_uint8 & 0x3f

		# Get the col direction (2's complement of first 2 bits)
		self.colDir = col_uint8 >> 6
		if self.colDir >= 2:
			self.colDir -= 4

		# Get the column value (last 6 bits)
		self.col = col_uint8 & 0x3f

class Ghost:
	'''
	Location and auxiliary info of a ghost in the game engine
	'''

	def __init__(self, color: GhostColors) -> None:
		'''
		Construct a new ghost state object
		'''

		# Set the color for this ghost
		self.color: GhostColors = color
		self.location: Location = Location()
		self.frightCycles: int = 0
		self.spawning: bool = bool(True)

	def updateAux(self, aux_info: int) -> None:
		'''
		Update auxiliary info (fright cycles and spawning flag)
		'''

		self.frightCycles = aux_info & 0xff
		self.spawning = bool(aux_info >> 7)

class GameState:
	'''
	Game state object for the Pacbot client, decoding the serialization
	from the server to make querying the game state simple.
	'''

	def __init__(self) -> None:
		'''
		Construct a new game state object
		'''

		# Big endian format specifier
		self.format: str = '>'

		# Internal variable to lock the state
		self._locked: bool = False

		#--- Important game state attributes (from game engine) ---#

		# 2 bytes
		self.currTicks: int = 0
		self.format += 'H'

		# 1 byte
		self.updatePeriod: int = 12
		self.format += 'B'

		# 1 byte
		self.gameMode: GameMode = GameMode.PAUSED
		self.format += 'B'

		# 2 bytes
		self.currScore: int = 0
		self.format += 'H'

		# 1 byte
		self.currLevel: int = 0
		self.format += 'B'

		# 1 byte
		self.currLives: int = 3
		self.format += 'B'

		# 4 * 3 bytes = 4 * (2 bytes location + 1 byte aux info)
		self.ghosts: list[Ghost] = [Ghost(color) for color in GhostColors]
		self.format += 'HBHBHBHB'

		# 2 byte location
		self.pacmanLoc: Location = Location()
		self.format += 'H'

		# 2 byte location
		self.fruitLoc: Location = Location()
		self.format += 'H'

		# 31 * 4 bytes = 31 * (32-bit integer bitset)
		self.pelletArr: list[int]
		self.format += (31 * 'I')

	def lock(self) -> None:
		'''
		Lock the game state, to prevent updates
		'''

		# Lock the state by updating the internal state variable
		self._locked = True

	def unlock(self) -> None:
		'''
		Unlock the game state, to allow updates
		'''

		# Unlock the state by updating the internal state variable
		self._locked = False

	def is_locked(self) -> bool:
		'''
		Check if the game state is locked
		'''

		# Unlock the state by updating the internal state variable
		return self._locked

	#
	def update(self, state: bytes) -> None:
		'''
		Update this game state, given a bytes object from the client
		'''

		# If the state is locked, don't update it
		if self._locked:
			print('o') # TODO: Remove
			return

		# Unpack the values based on the format string
		unpacked: tuple[int, ...] = unpack_from(self.format, state, 0)

		# General game info
		self.currTicks    = unpacked[0]
		self.updatePeriod = unpacked[1]
		self.gameMode     = unpacked[2]
		self.currScore    = unpacked[3]
		self.currLevel    = unpacked[4]
		self.currLives    = unpacked[5]

		# Red ghost info
		self.ghosts[GhostColors.RED].location.update(unpacked[6])
		self.ghosts[GhostColors.RED].updateAux(unpacked[7])

		# Pink ghost info
		self.ghosts[GhostColors.PINK].location.update(unpacked[8])
		self.ghosts[GhostColors.PINK].updateAux(unpacked[9])

		# Cyan ghost info
		self.ghosts[GhostColors.CYAN].location.update(unpacked[10])
		self.ghosts[GhostColors.CYAN].updateAux(unpacked[11])

		# Pink ghost info
		self.ghosts[GhostColors.ORANGE].location.update(unpacked[12])
		self.ghosts[GhostColors.ORANGE].updateAux(unpacked[13])

		# Pacman location info
		self.pacmanLoc.update(unpacked[14])

		# Fruit location info
		self.fruitLoc.update(unpacked[15])

		# Pellet info
		self.pelletArr = list(unpacked)[16:]

		# TODO: Remove
		# print('+')

