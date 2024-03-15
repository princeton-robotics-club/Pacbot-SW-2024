from typing import List
import math
from game_state.ghost import Ghost
from game_state.location import Location
from policies.astar.distanceHelpers import distL3


def penaltyCost(currLoc: Location, ghosts: List[Ghost]):
    
    cost: int = 0

    # if self.inStartingMode:
    #     return 0

    lairLoc: Location = Location(row=11, col=13)
    dist_to_lair = distL3(currLoc,lairLoc)

    # Calculate closest non-frightened ghost TODO: this is not scaring pacman from ghost because if some are far, the multiplier goes to 0
    for ghost in ghosts:
        if not ghost.spawning and not ghost.isFrightened():
            dist_to_ghost = distL3(currLoc, ghost.location)
            if dist_to_ghost <= 6:
                cost += inv_dist_cost(dist_to_ghost, 0.1, 50.0)  # type: ignore

    return cost



def hCost(currLoc: Location, target: Location) -> int:
        """
        Extends the existing g_cost delta to estimate a new h-cost due to
        Pachattan distance and estimated speed
        """

        # GAMEOVER handling - return value doesn't matter
        if not currLoc.isValid() or not target.isValid():
            return 0

        # Dist to target
        return distL3(currLoc, target)
        
        # if self.inStartingMode:
        #     return distPellet
        # # if self.fCostMultiplier() < 16 and distTarget == 0:
        # #     return -10000000

        # # Dist to nearest scared ghost
        # distScared: int = INF
        # if (
        #     victimColor != GhostColors.NONE
        #     and not self.state.ghosts[victimColor].spawning
        # ):
        #     distScared = self.dist(
        #         currLoc, self.state.ghosts[victimColor].location
        #     )

        # # Dist to fruit
        # distFruit: int = 999999
        # if self.state.fruitSteps > 0:
        #     distFruit = self.dist(self.state.pacmanLoc, self.state.fruitLoc)

        # # Distance to our chosen target: the minimum
        # dist: int = (
        #     distScared
        #     if (distScared < INF)
        #     else (distPellet if (distPellet < distFruit // 20) else distFruit)
        # )
        # # gCostPerStep: float = 2

        # # Return the result: (g-cost) / (buffer length) * (dist to target)
        # return dist
    
def inv_dist_cost(dist: int, a, b) -> float:
    """
    Exponentially increases as dist decreases.
    Returns a*e^(b/x)
    if dist = 0 returns 0
    """
    return int(a * math.exp(b / dist)) if dist else 0