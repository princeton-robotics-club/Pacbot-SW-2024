# Enum class (for game mode)
from enum import IntEnum

# Struct class (for processing)
from struct import unpack_from, pack

# Buffer to collect messages to write to the server
from collections import deque

# Terminal colors for formatting output text
from terminalColors import *

# Server messages
from serverMessage import ServerMessage
from .ghost import Ghost, GhostColors
from .location import Location
from .constants import Directions, reversedDirections, D_MESSAGES
from .board import wallAt


class GameModes(IntEnum):
    """
    Enum of possible game modes
    """

    PAUSED = 0
    SCATTER = 1
    CHASE = 2


# Terminal colors, based on the game mode
GameModeColors = {
    GameModes.PAUSED: DIM,
    GameModes.CHASE: YELLOW,
    GameModes.SCATTER: GREEN,
}


class GameState:
    """
    Game state object for the Pacbot client, decoding the serialization
    from the server to make querying the game state simple.
    """

    def __init__(self) -> None:
        """
        Construct a new game state object
        """

        # Big endian format specifier
        self.format: str = ">"

        # Internal variable to lock the state
        self._locked: bool = False

        # Keep track of whether the client is connected
        self._connected: bool = False

        # Buffer of messages to write back to the server
        self.writeServerBuf: deque[ServerMessage] = deque[ServerMessage](maxlen=64)

        # --- Important game state attributes (from game engine) ---#

        # 2 bytes
        self.currTicks: int = 0
        self.format += "H"

        # 1 byte
        self.updatePeriod: int = 12
        self.format += "B"

        # 1 byte
        self.gameMode: GameModes = GameModes.PAUSED
        self.format += "B"

        # 2 bytes
        self.modeSteps: int = 0
        self.modeDuration: int = 255
        self.format += "BB"

        # 2 bytes
        self.currScore: int = 0
        self.format += "H"

        # 1 byte
        self.currLevel: int = 0
        self.format += "B"

        # 1 byte
        self.currLives: int = 3
        self.format += "B"

        # 4 * 3 bytes = 4 * (2 bytes location + 1 byte aux info)
        self.ghosts: list[Ghost] = [Ghost(color) for color in GhostColors]
        self.format += "HBHBHBHB"

        # 2 byte location
        self.pacmanLoc: Location = Location()
        self.format += "H"

        # 2 byte location
        self.fruitLoc: Location = Location()
        self.format += "H"

        # 2 bytes
        self.fruitSteps: int = 0
        self.fruitDuration: int = 30
        self.format += "BB"

        # 31 * 4 bytes = 31 * (32-bit integer bitset)
        self.pelletArr: list[int] = [0 for _ in range(31)]
        self.format += 31 * "I"

    def lock(self) -> None:
        """
        Lock the game state, to prevent updates
        """

        # Lock the state by updating the internal state variable
        self._locked = True

    def unlock(self) -> None:
        """
        Unlock the game state, to allow updates
        """

        # Unlock the state by updating the internal state variable
        self._locked = False

    def isLocked(self) -> bool:
        """
        Check if the game state is locked
        """

        # Return the internal 'locked' state variable
        return self._locked

    def setConnectionStatus(self, connected: bool) -> None:
        """
        Set the connection status of this game state's client
        """

        # Update the internal 'connected' state variable
        self._connected = connected

    def isConnected(self) -> bool:
        """
        Check if the client attached to the game state is connected
        """

        # Return the internal 'connected' state variable
        return self._connected

    def serialize(self) -> bytes:
        """
        Serialize this game state into a bytes object (for policy state storage)
        """

        # Return a serialization with the same format as server updates
        return pack(
            # Format string
            self.format,
            # General game info
            self.currTicks,
            self.updatePeriod,
            self.gameMode,
            self.modeSteps,
            self.modeDuration,
            self.currScore,
            self.currLevel,
            self.currLives,
            # Red ghost info
            self.ghosts[GhostColors.RED].location.serialize(),
            self.ghosts[GhostColors.RED].serializeAux(),
            # Pink ghost info
            self.ghosts[GhostColors.PINK].location.serialize(),
            self.ghosts[GhostColors.PINK].serializeAux(),
            # Cyan ghost info
            self.ghosts[GhostColors.CYAN].location.serialize(),
            self.ghosts[GhostColors.CYAN].serializeAux(),
            # Orange ghost info
            self.ghosts[GhostColors.ORANGE].location.serialize(),
            self.ghosts[GhostColors.ORANGE].serializeAux(),
            # Pacman location info
            self.pacmanLoc.serialize(),
            # Fruit location info
            self.fruitLoc.serialize(),
            self.fruitSteps,
            self.fruitDuration,
            # Pellet info
            *self.pelletArr,
        )

    def getGhostPlans(self) -> dict[GhostColors, Directions]:
        """
        Return the ghosts' planned directions to compress the game state
        """

        return {ghost.color: ghost.plannedDirection for ghost in self.ghosts}

    def update(self, serializedState: bytes, lockOverride: bool = False) -> None:
        """
        Update this game state, given a bytes object from the client
        """

        # If the state is locked, don't update it
        if self._locked and not lockOverride:
            return

        # Unpack the values based on the format string
        unpacked: tuple[int, ...] = unpack_from(self.format, serializedState, 0)

        # General game info
        self.currTicks = unpacked[0]
        self.updatePeriod = unpacked[1]
        self.gameMode = GameModes(unpacked[2])
        self.modeSteps = unpacked[3]
        self.modeDuration = unpacked[4]
        self.currScore = unpacked[5]
        self.currLevel = unpacked[6]
        self.currLives = unpacked[7]

        # Red ghost info
        self.ghosts[GhostColors.RED].location.update(unpacked[8])
        self.ghosts[GhostColors.RED].updateAux(unpacked[9])

        # Pink ghost info
        self.ghosts[GhostColors.PINK].location.update(unpacked[10])
        self.ghosts[GhostColors.PINK].updateAux(unpacked[11])

        # Cyan ghost info
        self.ghosts[GhostColors.CYAN].location.update(unpacked[12])
        self.ghosts[GhostColors.CYAN].updateAux(unpacked[13])

        # Orange ghost info
        self.ghosts[GhostColors.ORANGE].location.update(unpacked[14])
        self.ghosts[GhostColors.ORANGE].updateAux(unpacked[15])

        # Increment fright steps (for a more risky attack against ghosts)
        # for ghost in self.ghosts:
        # 	if ghost.isFrightened():
        # 		ghost.frightSteps += 1

        # Pacman location info
        self.pacmanLoc.update(unpacked[16])

        # Fruit location info
        self.fruitLoc.update(unpacked[17])
        self.fruitSteps = unpacked[18]
        self.fruitDuration = unpacked[19]

        # Pellet info
        self.pelletArr = list[int](unpacked)[20:]

        # Reset our guesses of the planned ghost directions
        for ghost in self.ghosts:
            ghost.plannedDirection = Directions.NONE

    def updateGhostPlans(self, ghostPlans: dict[GhostColors, Directions]):
        """
        Update this game state, given a list of ghost planned directions
        """

        for ghost in self.ghosts:
            ghost.plannedDirection = ghostPlans[ghost.color]

    def pelletAt(self, row: int, col: int) -> bool:
        """
        Helper function to check if a pellet is at a given location
        """

        return bool((self.pelletArr[row] >> col) & 1)

    def superPelletAt(self, row: int, col: int) -> bool:
        """
        Helper function to check if a super pellet is at a given location
        """

        return (
            self.pelletAt(row, col)
            and ((row == 3) or (row == 23))
            and ((col == 1) or (col == 26))
        )

    def fruitAt(self, row: int, col: int) -> bool:
        """
        Helper function to check if a fruit is at a given location
        """

        return (
            (self.fruitSteps > 0)
            and (row == self.fruitLoc.row)
            and (col == self.fruitLoc.col)
        )

    def numPellets(self) -> int:
        """
        Helper function to compute how many pellets are left in the maze
        """

        return sum(row_arr.bit_count() for row_arr in self.pelletArr)

    def numSuperPellets(self) -> int:
        """
        Helper function to compute how many super pellets are left in the maze
        """

        return (
            self.pelletAt(3, 1)
            + self.pelletAt(3, 26)
            + self.pelletAt(23, 1)
            + self.pelletAt(23, 26)
        )

    def collectPellet(self, row: int, col: int) -> None:
        """
        Helper function to collect a pellet for simulation purposes
        """

        # Return if there are no pellets to collect
        if not self.pelletAt(row, col):
            return

        # Determine the type of pellet (super / normal)
        superPellet: bool = self.superPelletAt(row, col)

        # Remove the pellet at this location
        self.pelletArr[row] &= ~(1 << col)

        # Increase the score by this amount
        self.currScore += 50 if superPellet else 10

        # Spawn the fruit based on the number of pellets, if applicable
        numPellets = self.numPellets()
        if numPellets == 174 or numPellets == 74:
            self.fruitSteps = 30
            self.fruitLoc.row = 17
            self.fruitLoc.col = 13

        # When <= 20 pellets are left, keep the game in chase mode
        # if numPellets <= 20:
        # 	if self.gameMode == GameModes.SCATTER:
        # 		self.gameMode = GameModes.CHASE

        # Scare the ghosts, if applicable
        if superPellet:
            for ghost in self.ghosts:
                ghost.frightSteps = 40
                ghost.plannedDirection = reversedDirections[ghost.plannedDirection]

    def display(self):
        """
        Helper function to display the game state in the terminal
        """

        # Begin by outputting the tick number, colored based on the mode
        out: str = (
            f"{GameModeColors[self.gameMode]}-------"
            f" time = {self.currTicks:5d} -------\033[0m\n"
        )

        # Loop over all 31 rows
        for row in range(31):

            # For each cell, choose a character based on the entities in it
            for col in range(28):

                # Red ghost
                if self.ghosts[GhostColors.RED].location.at(row, col):
                    scared = self.ghosts[GhostColors.RED].isFrightened()
                    out += f"{RED if not scared else BLUE}@{NORMAL}"

                # Pink ghost
                elif self.ghosts[GhostColors.PINK].location.at(row, col):
                    scared = self.ghosts[GhostColors.PINK].isFrightened()
                    out += f"{PINK if not scared else BLUE}@{NORMAL}"

                # Cyan ghost
                elif self.ghosts[GhostColors.CYAN].location.at(row, col):
                    scared = self.ghosts[GhostColors.CYAN].isFrightened()
                    out += f"{CYAN if not scared else BLUE}@{NORMAL}"

                # Orange ghost
                elif self.ghosts[GhostColors.ORANGE].location.at(row, col):
                    scared = self.ghosts[GhostColors.ORANGE].isFrightened()
                    out += f"{ORANGE if not scared else BLUE}@{NORMAL}"

                # Pacman
                elif self.pacmanLoc.at(row, col):
                    out += f"{YELLOW}P{NORMAL}"

                # Fruit
                elif self.fruitLoc.at(row, col):
                    out += f"{GREEN}f{NORMAL}"

                # Wall
                elif wallAt(row, col):
                    out += f"{DIM}#{NORMAL}"

                # Super pellet
                elif self.superPelletAt(row, col):
                    out += "●"

                # Pellet
                elif self.pelletAt(row, col):
                    out += "·"

                # Empty space
                else:
                    out += " "

            # New line at end of row
            out += "\n"

        # Print the output, with a new line at end of display
        print(out)

    def safetyCheck(self) -> bool:
        """
        Helper function to check whether Pacman is safe in the current game state
        (i.e., Pacman is not directly colliding with a non-frightened ghost)
        """

        # Retrieve Pacman's coordinates
        pacmanRow = self.pacmanLoc.row
        pacmanCol = self.pacmanLoc.col

        # Check for collisions
        for ghost in self.ghosts:
            if ghost.location.at(pacmanRow, pacmanCol):
                if not ghost.isFrightened():  # Collision; Pacman loses
                    return False
                # else: # 'Respawn' the ghost
                # 	ghost.location.row = 32
                # 	ghost.location.col = 32
                ghost.spawning = True

        # Otherwise, Pacman is safe
        return True

    def queueAction(self, numTicks: int, pacmanDir: Directions) -> None:
        """
        Helper function to queue a message to be sent to the server, with a
        given Pacbot direction and number of ticks until the message is sent.
        """
        self.writeServerBuf.append(ServerMessage(D_MESSAGES[pacmanDir], numTicks))
