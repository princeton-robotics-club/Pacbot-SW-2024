import math
from pyclbr import Function
from typing import List
from game_state import Location
from game_state.constants.directions import Directions
from game_state.constants.ghost_enums import GhostColors
from game_state.gameState import GameModes, GameState
from game_state.ghost import Ghost
from policies.astar.helpers.distanceHelpers import distL3

NE_PELLET = (3, 1)
NW_PELLET = (3, 26)
SW_PELLET = (23, 1)
SE_PELLET = (23, 26)

NW_SPOT_1, NW_SPOT_2 = (NW_PELLET[0] - 1, NW_PELLET[1]), (NW_PELLET[0] + 1, NW_PELLET[1])
NE_SPOT_1, NE_SPOT_2 = (NE_PELLET[0] - 1, NE_PELLET[1]), (NE_PELLET[0] + 1, NE_PELLET[1])
SW_SPOT_1, SW_SPOT_2 = (SW_PELLET[0] - 1, SW_PELLET[1]), (SW_PELLET[0], SW_PELLET[1] + 1)
SE_SPOT_1, SE_SPOT_2 = (SE_PELLET[0] - 1, SE_PELLET[1]), (SE_PELLET[0], SE_PELLET[1] - 1)

waiting_spots_to_pellets = {
    NW_SPOT_1: NW_PELLET,
    NW_SPOT_2: NW_PELLET,
    NE_SPOT_1: NE_PELLET,
    NE_SPOT_2: NE_PELLET,
    SW_SPOT_1: SW_PELLET,
    SW_SPOT_2: SW_PELLET,
    SE_SPOT_1: SE_PELLET,
    SE_SPOT_2: SE_PELLET,
}

def waitingForGhosts(gameState: GameState, victimColor) -> bool:

    if not victimColor == GhostColors.NONE or not gameState.gameMode == GameModes.CHASE:
        return False
    
    for waitingSpotLoc, superPelletLoc in waiting_spots_to_pellets.items():
        # we are at a waiting spot with a superpellet
        if gameState.pacmanLoc.at(*waitingSpotLoc) and gameState.superPelletAt(*superPelletLoc):
            return True
    
    return False


def getNearestUnfrightenedGhostLocation(currLoc: Location, ghosts: List[Ghost]):

    closestDist = math.inf
    
    if not currLoc.isValid():
        return 0
    
    for ghost in ghosts:
        if not ghost.location.isValid():
            continue
        if not ghost.isFrightened():
            dist = distL3(currLoc, ghost.location)
            if dist < closestDist:
                closestDist = dist

    # Return the closest scared ghost
    return closestDist


def moveToSuperPellet(game_state: GameState, delay) -> None:
    direction_buf, delay = Directions.NONE, 3
    row, col = game_state.pacmanLoc.row, game_state.pacmanLoc.col
    if game_state.superPelletAt(row - 1, col):
        direction_buf = Directions.UP
    if game_state.superPelletAt(row + 1, col):
        direction_buf = Directions.DOWN
    if game_state.superPelletAt(row, col + 1):
        direction_buf = Directions.RIGHT
    if game_state.superPelletAt(row, col - 1):
        direction_buf = Directions.LEFT
    print("direction_buf", direction_buf)
    game_state.queueAction(pacmanDir=direction_buf, numTicks=delay)

