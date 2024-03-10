wallArr: list[int] = [
  0b0000_1111111111111111111111111111, # row 0
    0b0000_1000000000000110000000000001, # row 1
    0b0000_1011110111110110111110111101, # row 2
    0b0000_1011110111110110111110111101, # row 3
    0b0000_1011110111110110111110111101, # row 4
    0b0000_1000000000000000000000000001, # row 5
    0b0000_1011110110111111110110111101, # row 6
    0b0000_1011110110111111110110111101, # row 7
    0b0000_1000000110000110000110000001, # row 8
    0b0000_1111110111110110111110111111, # row 9
    0b0000_1111110111110110111110111111, # row 10
    0b0000_1111110110000000000110111111, # row 11
    0b0000_1111110110111111110110111111, # row 12
    0b0000_1111110110111111110110111111, # row 13
    0b0000_1111110000111111110000111111, # row 14
    0b0000_1111110110111111110110111111, # row 15
    0b0000_1111110110111111110110111111, # row 16
    0b0000_1111110110000000000110111111, # row 17
    0b0000_1111110110111111110110111111, # row 18
    0b0000_1111110110111111110110111111, # row 19
    0b0000_1000000000000110000000000001, # row 20
    0b0000_1011110111110110111110111101, # row 21
    0b0000_1011110111110110111110111101, # row 22
    0b0000_1000110000000000000000110001, # row 23
    0b0000_1110110110111111110110110111, # row 24
    0b0000_1110110110111111110110110111, # row 25
    0b0000_1000000110000110000110000001, # row 26
    0b0000_1011111111110110111111111101, # row 27
    0b0000_1011111111110110111111111101, # row 28
    0b0000_1000000000000000000000000001, # row 29
    0b0000_1111111111111111111111111111  # row 30
]

NROWS = len(wallArr)
NCOLS = len(bin(wallArr[0])[2:])

def wallAt(row: int, col: int) -> bool:
	'''
	Helper function to check if a wall is at a given location
	'''

    # Return whether there is a wall at the location
    return 0<=row<NROWS and 0<=col<NCOLS and (wallArr[row] & (1 << col))

def is_valid_location(row: int, col: int) -> bool:

    """
    Check if the location is within the valid playing area of the game and not in a wall.

    The game grid is defined as a 30x27 area.

    Returns:
        bool: True if the location is within the grid, False otherwise.
    """

    return 0<=row<NROWS and 0<=col<NCOLS and not wallAt(row, col)