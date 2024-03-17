""" Module providing Location class """

from .constants import Directions, D_ROW, D_COL
from .board import is_valid_location


class Location:
    """
    Location of an entity in the game engine
    """

    def __init__(
        self, row: int = 0, col: int = 0, row_dir: int = 0, col_dir: int = 0
    ) -> None:
        self.row = row
        self.col = col
        self.row_dir = row_dir
        self.col_dir = col_dir

    def __str__(self):
        return f"({self.row},{self.col})"

    def hash(self) -> int:
        """
        Hashes location based on row and col
        """
        return self.row * 32 + self.col

    def update(self, loc_uint16: int) -> None:
        """
        Update a location, based on a 2-byte serialization
        """

        # Get the row and column bytes
        row_uint8: int = loc_uint16 >> 8
        col_uint8: int = loc_uint16 & 0xFF

        # Get the row direction (2's complement of first 2 bits)
        self.row_dir = row_uint8 >> 6
        if self.row_dir >= 2:
            self.row_dir -= 4

        # Get the row value (last 6 bits)
        self.row = row_uint8 & 0x3F

        # Get the col direction (2's complement of first 2 bits)
        self.col_dir = col_uint8 >> 6
        if self.col_dir >= 2:
            self.col_dir -= 4

        # Get the column value (last 6 bits)
        self.col = col_uint8 & 0x3F

    def at(self, row: int, col: int) -> bool:
        """
        Determine whether a row and column intersect with this location
        """

        return self.row == row and self.col == col

    def serialize(self) -> int:
        """
        Serialize this location state into a 16-bit integer (two bytes)
        """

        # Serialize the row byte
        row_uint8: int = ((self.row_dir & 0x03) << 6) | (self.row & 0x3F)

        # Serialize the column byte
        col_uint8: int = ((self.col_dir & 0x03) << 6) | (self.col & 0x3F)

        # Return the full serialization
        return (row_uint8 << 8) | (col_uint8)

    def setDirection(self, direction: Directions) -> None:
        """
        Given a direction enum object, set the direction of this location
        """
        # Set the direction of this location
        self.row_dir = D_ROW[direction]
        self.col_dir = D_COL[direction]

    def getDirection(self) -> Directions:
        """
        Return a direction enum object corresponding to this location
        """

        # Return the matching direction, if applicable
        for direction in Directions:
            if self.row_dir == D_ROW[direction] and self.col_dir == D_COL[direction]:
                return direction

        # Return none if no direction matches
        return Directions.NONE

    def move(self) -> bool:
        """
        Simulates one step in the current direction.

        Returns:
        - bool: 
            - True if the location was successfully advanced;
            - False if next step is invalid location.
        """

        # Check if the current position is out of bounds
        if not is_valid_location(self.row, self.col):
            return False

        next_row = self.row + self.row_dir
        next_col = self.col + self.col_dir

        # Check if the next position is not a wall and update the location if it's not
        if is_valid_location(next_row, next_col):
            self.row = next_row
            self.col = next_col

            return True

        return False

    def isValid(self) -> bool:
        return is_valid_location(self.row, self.col)

    def setLocation(self,row,col) -> None:
        self.row = row
        self.col = col