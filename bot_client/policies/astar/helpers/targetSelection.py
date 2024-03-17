import math
import select
from typing import List
from game_state.constants.ghost_enums import GhostColors
from game_state.gameState import GameModes, GameState
from game_state.ghost import Ghost
from game_state.location import Location
from policies.astar.helpers.distanceHelpers import distL3
from policies.astar.helpers.superpelletHelpers import *

# def selectTarget(gameState, victimColor):
#     # move to nearest ghost
#     if victimColor != GhostColors.NONE:
#         return gameState.ghosts[victimColor].location
    
#     return selectPelletTarget
    



def selectPelletTarget(
    currState: GameState, victimColor: GhostColors, pelletTarget: Location
) -> Location:
    # TODO: Change ordering to do the route at the beginning

    # move to nearest ghost
    if victimColor != GhostColors.NONE:
        return currState.ghosts[victimColor].location

    # go to waiting location
    if currState.gameMode == GameModes.CHASE:
        waiting_location = getWaitingLocation(currState)
        if waiting_location:
            return waiting_location

    # dangerous pellets collected? still starting
    startingTarget = findStartingSequenceTarget(currState)
    if startingTarget:
        return startingTarget

    return pelletTarget


def findStartingSequenceTarget(currState: GameState) -> Location | None:
    # pellets to guide opening route
    # This way it gets most dangerous pellets out the way first
    START_PELLETS = [
        (29, 1),
        (29, 26),
        (26, 21),
        (22, 6),
        (5, 6),
        (5, 18),
        (11, 15),
        # fruit location
        (17, 13),
    ]

    for x, y in START_PELLETS:
        # Check if there's a pellet at the current location
        if currState.pelletAt(x, y) or ((x, y) == (17, 13) and currState.fruitSteps):
            # Set the target location and break out of the loop once a pellet is found
            return Location(x, y)
    
    return None


def getCloserLocation(currLoc: Location, l1: Location, l2: Location):
    return l1 if distL3(currLoc, l1) <= distL3(currLoc, l2) else l2


def getWaitingLocation(currState: GameState) -> Location | None:

    if currState.superPelletAt(*SW_PELLET):
        return getCloserLocation(currState.pacmanLoc, Location(*SW_SPOT_1), Location(*SW_SPOT_2))
    if currState.superPelletAt(*NE_PELLET):
        return getCloserLocation(currState.pacmanLoc, Location(*NE_SPOT_1), Location(*NE_SPOT_2))
    if currState.superPelletAt(*NW_PELLET):
        return getCloserLocation(currState.pacmanLoc, Location(*NW_SPOT_1), Location(*NW_SPOT_2))
    if currState.superPelletAt(*SE_PELLET):
        return getCloserLocation(currState.pacmanLoc, Location(*SE_SPOT_1), Location(*SE_SPOT_2))


    return None



