from enum import IntEnum

class GhostColors(IntEnum):
	'''
	Enum of possible ghost names
	'''

	RED    = 0
	PINK   = 1
	CYAN   = 2
	ORANGE = 3
	NONE   = 4

# Scatter targets for each of the ghosts
#               R   P   C   O
SCATTER_ROW = [-3, -3, 31, 31]
SCATTER_COL = [25,  2, 27,  0]