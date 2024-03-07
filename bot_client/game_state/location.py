from .constants import Directions, D_ROW, D_COL

class Location:
	'''
	Location of an entity in the game engine
	'''

	def __init__(self, row: int = 0, col: int = 32, row_dir: int = 0, col_dir: int = 0) -> None:
		self.row = row
		self.col = col
		self.row_dir = row_dir
		self.col_dir = col_dir

	def __str__(self):
		return f'({self.row},{self.col})'

	def hash(self) -> int:
		return self.row * 32 + self.col

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

	def is_valid(self) -> bool:
		"""
		Check if the location is within the valid playing area of the game.

		The game grid is defined as a 30x27 area.

		Returns:
			bool: True if the location is within the grid, False otherwise.
		"""
		
		return 0 <= self.row < 31 and 0 <= self.col < 28
	
	def at(self, row: int, col: int) -> bool:
		
		'''
		Determine whether a row and column intersect with this location
		'''

		return self.is_valid() and self.row == row and self.col == col

	def serialize(self) -> int:
		'''
		Serialize this location state into a 16-bit integer (two bytes)
		'''

		# Serialize the row byte
		row_uint8: int = (((self.rowDir & 0x03) << 6) | (self.row & 0x3f))

		# Serialize the column byte
		col_uint8: int = (((self.colDir & 0x03) << 6) | (self.col & 0x3f))

		# Return the full serialization
		return (row_uint8 << 8) | (col_uint8)

	
	def setDirection(self, direction: Directions) -> None:
		'''
		Given a direction enum object, set the direction of this location
		'''

		# Set the direction of this location
		self.rowDir = D_ROW[direction]
		self.colDir = D_COL[direction]

	def getDirection(self) -> Directions:
		'''
		Return a direction enum object corresponding to this location
		'''

		# Return the matching direction, if applicable
		for direction in Directions:
			if self.rowDir == D_ROW[direction] and self.colDir == D_COL[direction]:
				return direction

		# Return none if no direction matches
		return Directions.NONE
