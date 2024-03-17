from game_state.constants.ghost_enums import GhostColors
from game_state.gameState import GameModes, GameState
from game_state.location import Location
from policies.astar.helpers.distanceHelpers import distL3


def selectTarget(
    currState: GameState, victimColor: GhostColors, pelletTarget: Location
) -> Location:
    # TODO: Change ordering to do the route at the beginning

    # already have one
    if victimColor != GhostColors.NONE:
        return currState.ghosts[victimColor].location

    # still starting
    startingTarget = findStartingSequenceTarget(currState)
    if startingTarget:
        return startingTarget

    if currState.gameMode == GameModes.CHASE:
        waiting_location = getWaitingLocation(currState)
    if waiting_location:
        return waiting_location

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
        (25, 3),
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

    NE_PELLET = (3, 1)
    NW_PELLET = (3, 26)
    SW_PELLET = (23, 1)
    SE_PELLET = (23, 26)

    NW_SPOT_1, NW_SPOT_2 = Location(NW_PELLET[0] - 1, NW_PELLET[1]), Location(
        NW_PELLET[0] + 1, NW_PELLET[1]
    )
    NE_SPOT_1, NE_SPOT_2 = Location(NE_PELLET[0] - 1, NE_PELLET[1]), Location(
        NE_PELLET[0] + 1, NE_PELLET[1]
    )
    SW_SPOT_1, SW_SPOT_2 = Location(SW_PELLET[0] - 1, SW_PELLET[1]), Location(
        SW_PELLET[0], SW_PELLET[1] + 1
    )
    SE_SPOT_1, SE_SPOT_2 = Location(SE_PELLET[0] - 1, SE_PELLET[1]), Location(
        SE_PELLET[0], SE_PELLET[1] - 1
    )

    if currState.superPelletAt(*SW_PELLET):
        return getCloserLocation(currState.pacmanLoc, SW_SPOT_1, SW_SPOT_2)
    if currState.superPelletAt(*NE_PELLET):
        return getCloserLocation(currState.pacmanLoc, NE_SPOT_1, NE_SPOT_2)
    if currState.superPelletAt(*NW_PELLET):
        return getCloserLocation(currState.pacmanLoc, NW_SPOT_1, NW_SPOT_2)
    if currState.superPelletAt(*SE_PELLET):
        return getCloserLocation(currState.pacmanLoc, SE_SPOT_1, SE_SPOT_2)

    return None
