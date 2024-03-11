""" Module that contains classes and methods run A* search algorithm to play PACMAN"""

from heapq import heappush, heappop
from enum import IntEnum
from collections import deque

# Game state
from game_state import *

# Location mapping
import policies.astar.genPachattanDistDict as pacdist
import policies.astar.example as ex


# Big Distance
INF = 999999

"""
Cost Explanations:

Started at point	S
Targetting point 	T
Currently at point 	C

gcost = cost from S to C (past, known)
hcost = cost from C to T (future, predicted)

fcost = gcost + hcost

Start-------Current-------Target
S--------------C---------------T
|-----gcost----|-----hcost-----|
|------------fcost-------------|
"""


class DistTypes(IntEnum):
    """
    Enum of distance types
    """

    MANHATTAN_DISTANCE = 0
    EUCLIDEAN_DISTANCE = 1
    PACHATTAN_DISTANCE = 2


# Create new location with row, col
def newLocation(row: int, col: int):
    """
    Construct a new location state
    """
    result = Location()
    result.row = row
    result.col = col
    return result


# Manhattan distance
def distL1(loc1: Location, loc2: Location) -> int:
    return abs(loc1.row - loc2.row) + abs(loc1.col - loc2.col)


# Manhattan distance
def distSqL1(loc1: Location, loc2: Location) -> int:
    dr = abs(loc1.row - loc2.row)
    dc = abs(loc1.col - loc2.col)
    return dr * dr + dc * dc


# Squared Euclidean distance
def distSqL2(loc1: Location, loc2: Location) -> int:
    return (loc1.row - loc2.row) * (loc1.row - loc2.row) + (loc1.col - loc2.col) * (
        loc1.col - loc2.col
    )


# Euclidean distance
def distL2(loc1: Location, loc2: Location) -> int:
    return (
        (loc1.row - loc2.row) * (loc1.row - loc2.row)
        + (loc1.col - loc2.col) * (loc1.col - loc2.col)
    ) ** 0.5


# Pachattan distance
def distL3(loc1: Location, loc2: Location) -> int:
    key = pacdist.getKey(loc1, loc2)
    return ex.PACHATTAN[key]


# Squared Pachattan distance
def distSqL3(loc1: Location, loc2: Location) -> int:
    pacDist = distL3(loc1, loc2)
    return pacDist * pacDist


class AStarNode:
    """
    Node class for running the A-Star Algorithm for Pacbot.
    """

    def __init__(
        self,
        compressedState: GameStateCompressed,
        fCost: int,
        gCost: int,
        directionBuf: list[Directions],
        delayBuf: list[int],
        bufLength: int,
        victimCaught: bool = False,
        pelletTargetCaught: bool = False,
    ) -> None:

        # Compressed game state
        self.compressedState = compressedState

        # Costs
        self.fCost = fCost
        self.gCost = gCost

        # Estimated velocity
        self.estSpeed = 0
        self.direction = Directions.NONE

        # Message buffer
        self.directionBuf = directionBuf
        self.delayBuf = delayBuf
        self.bufLength = bufLength

        # Victim color (catching scared ghosts)
        self.victimCaught: bool = victimCaught

        # Determines whether the target was caught
        self.pelletTargetCaught: bool = pelletTargetCaught

    def __lt__(self, other) -> bool:  # type: ignore
        return self.fCost < other.fCost  # type: ignore

    def __repr__(self) -> str:
        return str(f"g = {self.gCost} ~ f = {self.fCost}")


class AStarPolicy:
    """
    Policy class for running the A-Star Algorithm for Pacbot.
    """

    def __init__(
        self,
        state: GameState,
        target: Location,
        distType: DistTypes = DistTypes.PACHATTAN_DISTANCE,
    ) -> None:

        # Game state
        self.state: GameState = state
        self.stateCopy: GameState = state

        # Target location
        self.target: Location = target

        # Expected location
        self.expectedLoc: Location = newLocation(23, 13)
        self.error_sum = 0
        self.error_count = 0
        self.dropped_command_count = 0

        # Distance metrics
        self.distType = distType
        match self.distType:
            case DistTypes.MANHATTAN_DISTANCE:
                self.dist = distL1
                self.distSq = distSqL1
            case DistTypes.EUCLIDEAN_DISTANCE:
                self.dist = distL2
                self.distSq = distSqL2
            case DistTypes.PACHATTAN_DISTANCE:
                self.dist = distL3
                self.distSq = distSqL3
            case _:  # pachattan
                self.distType = DistTypes.PACHATTAN_DISTANCE
                self.dist = distL3
                self.distSq = distSqL3

    def getNearestPellet(self) -> Location:

        # Check bounds
        first = self.state.pacmanLoc

        #  BFS traverse
        queue = deque([first])
        visited = {first.hash()}

        while queue:

            # pop from queue
            currLoc = queue.popleft()

            # Base Case: Found a pellet
            if (
                is_valid_location(currLoc.row, currLoc.col)
                and self.state.pelletAt(currLoc.row, currLoc.col)
                and not self.state.superPelletAt(currLoc.row, currLoc.col)
            ):
                # print("Found Pellet")
                return currLoc

            # Loop over the directions
            for direction in Directions:

                # If the direction is none, skip it
                if direction == Directions.NONE:
                    continue

                # Increment direction
                nextLoc = Location(row=currLoc.row, col=currLoc.col)
                nextLoc.setDirection(direction)
                nextMoveValid = nextLoc.move() and not self.state.superPelletAt(
                    nextLoc.row, nextLoc.col
                )

                # avoid same node twice and check this is a valid move
                if nextMoveValid and nextLoc.hash() not in visited:
                    queue.append(nextLoc)
                    visited.add(nextLoc.hash())

        print("No nearest...")
        return first

    def victimNearUnfrightenedGhost(self, victimColor: GhostColors) -> bool:
        """
        Returns True if an unfrightened ghost is very close to the frightened victim.
        Prints 're-assigning victim' if true
        """

        V = self.state.ghosts[victimColor]

        if (victimColor == GhostColors.NONE) or wallAt(V.location.row, V.location.col):
            return False

        if V.spawning:
            return True

        for color in GhostColors:
            G = self.state.ghosts[color]
            if (color != victimColor) and (not G.spawning) and (not G.isFrightened()):
                if not wallAt(G.location.row, G.location.col):
                    if self.dist(V.location, G.location) <= 2:
                        print("re-assigning victim")
                        return True

        return False

    def getNearestVictim(self) -> GhostColors:

        closest, closestDist = GhostColors.NONE, INF
        for color in GhostColors:
            if (
                self.state.ghosts[color].isFrightened()
                and not self.state.ghosts[color].spawning
            ):
                dist = self.dist(
                    self.state.pacmanLoc, self.state.ghosts[color].location
                )
                if dist < closestDist and not self.victimNearUnfrightenedGhost(color):
                    closest = color
                    closestDist = dist

        # Return the closest scared ghost
        return closest

    # def hCost(self) -> int:
    #     # # make sure pacman in bounds (TODO: Why do we have to do this?)
    #     # if 0 > self.state.pacmanLoc.row or 32 <= self.state.pacmanLoc.row or 0 > self.state.pacmanLoc.col or 28 <= self.state.pacmanLoc.col:
    #     #     return 999999999

    #     # Heuristic cost for this location
    #     hCostTarget = 0

    #     # Heuristic cost to estimate ghost locations
    #     hCostGhost = 0

    #     # Catching frightened ghosts
    #     hCostScaredGhost = 0

    #     # Chasing fruit
    #     hCostFruit = 0

    #     # Add a penalty for being close to the ghosts
    #     for ghost in self.state.ghosts:
    #         if not ghost.spawning:
    #             if not ghost.isFrightened():
    #                 hCostGhost += int(
    #                     64 / max(self.distSq(
    #                         self.state.pacmanLoc,
    #                         ghost.location
    #                     ), 1)
    #                 )
    #             else:
    #                 hCostScaredGhost += self.dist(self.state.pacmanLoc, ghost.location)

    #     # Check whether fruit exists, and then add it to target
    #     if self.state.fruitSteps > 0:
    #         hCostFruit = self.dist(self.state.pacmanLoc, self.state.fruitLoc)

    #     # If there are frightened ghosts, chase them
    #     if hCostScaredGhost > 0:
    #         return int(hCostTarget + hCostGhost + hCostScaredGhost + hCostFruit)

    #     # Otherwise, chase the target
    #     hCostTarget = self.dist(self.state.pacmanLoc, self.target)
    #     return int(hCostTarget + hCostGhost + hCostFruit)

    def hCostExtend(self, gCost: int, bufLen: int, victimColor: GhostColors) -> int:
        """
        Extends the existing g_cost delta to estimate a new h-cost due to
        Pachattan distance and estimated speed
        """
        
        # GAMEOVER handling
        if not (self.state.pacmanLoc.isValid() and self.target.isValid()):
            return 0

        # Dist to target
        distTarget: int = self.dist(self.state.pacmanLoc, self.target)  
        if self.fCostMultiplier() < 16 and distTarget == 0:
            return -10000000

        # Dist to nearest scared ghost
        distScared: int = INF
        if (
            victimColor != GhostColors.NONE
            and not self.state.ghosts[victimColor].spawning
        ):
            distScared = self.dist(
                self.state.pacmanLoc, self.state.ghosts[victimColor].location
            )

        # Dist to fruit
        distFruit: int = 999999
        if self.state.fruitSteps > 0:
            distFruit = self.dist(self.state.pacmanLoc, self.state.fruitLoc)

        # Distance to our chosen target: the minimum
        dist: int = (
            distScared
            if (distScared < INF)
            else (distTarget if (distTarget < distFruit // 20) else distFruit)
        )
        gCostPerStep: float = 2

        # If the buffer is too small, then the gCostPerStep should be 2 on average
        if bufLen >= 4:
            gCostPerStep = gCost / bufLen

        # Return the result: (g-cost) / (buffer length) * (dist to target)
        return int(gCostPerStep * dist)

    def fCostMultiplier(self) -> float:

        # Constant for the multiplier
        K: int = 64

        # Multiplier addition term
        multTerm: int = 0

        # Location of the ghost lair
        lairLoc: Location = Location(row=11, col=13)

        # Check if any ghosts are frightened
        fright = False
        # for ghost in self.state.ghosts:
        #     if ghost.isFrightened():
        #         fright = True

        # Calculate closest non-frightened ghost
        for ghost in self.state.ghosts:
            if not ghost.spawning:
                if not ghost.isFrightened():
                    multTerm += int(
                        K >> self.dist(self.state.pacmanLoc, ghost.location)
                    )
            # elif not fright and not wallAt(self.state.pacmanLoc.row, self.state.pacmanLoc.col):
            #     multTerm += int(
            #         K >> self.dist(self.state.pacmanLoc, lairLoc)
            #     )

        # Return the multiplier (1 + constant / distance squared)
        return 1 + multTerm

    def selectTarget(self, pelletTarget: Location) -> None:

        chase = self.state.gameMode == GameModes.CHASE

        # check if top left pellet exists
        if self.state.superPelletAt(3, 1) and chase:
            self.target = newLocation(5, 1)

        # check if top right pellet exists
        elif self.state.superPelletAt(3, 26) and chase:
            self.target = newLocation(5, 26)

        # check if bottom left pellet exists
        elif self.state.superPelletAt(23, 1) and chase:
            self.target = newLocation(22, 1)

        # check if bottom right pellet exists
        elif self.state.superPelletAt(23, 26) and chase:
            self.target = newLocation(22, 26)

        # no super pellets
        else:
            # target the nearest pellet
            self.target = pelletTarget

    async def act(
        self, predicted_delay: int, victimColor: GhostColors, pelletTarget: Location
    ) -> tuple[GhostColors, Location]:

        # Make a priority queue of A-Star Nodes
        priorityQueue: list[AStarNode] = []

        # Construct an initial node
        initialNode = AStarNode(
            compressedState=compressGameState(self.state),
            fCost=self.hCostExtend(0, 0, victimColor),
            gCost=0,
            directionBuf=[],
            delayBuf=[],
            bufLength=0,
        )

        # Add the initial node to the priority queue
        heappush(priorityQueue, initialNode)

        # Select a target
        self.selectTarget(pelletTarget)

        # # Select a victim, if applicable
        # victimCaught = (victimColor != GhostColors.NONE) and ((not self.state.ghosts[victimColor].isFrightened()) or self.state.ghosts[victimColor].spawning)
        victimColor = self.getNearestVictim()

        # # Select a new target, if applicable
        # pelletTargetCaught = wallAt(pelletTarget.row, pelletTarget.col) or not self.state.pelletAt(pelletTarget.row, pelletTarget.col) or self.state.fruitLoc.at(self.state.pacmanLoc.row, self.state.pacmanLoc.col)
        # if pelletTargetCaught:
        #     pelletTarget = self.getNearestPellet()

        # Keep proceeding until a break point is hit
        while priorityQueue:

            # Pop the lowest f-cost node
            currNode = heappop(priorityQueue)
            
            # Reset to the current compressed state
            decompressGameState(self.state, currNode.compressedState)

            # If the g-cost of this node is high enough or we reached the target,
            # make the moves and return

            

            if currNode.pelletTargetCaught and (victimColor == GhostColors.NONE):

                self.queueEntireBuffer(currNode)

                print("target caught")
                pelletTarget = self.getNearestPellet()

                print(
                    ["RED", "PINK", "CYAN", "ORANGE", "NONE"][victimColor], pelletTarget
                )
                return GhostColors.NONE, pelletTarget

            # Nothing was captured but move should be continued
            # Could lower this if algorithm is optimized?

            if currNode.bufLength > 0:

                self.queueEntireBuffer(currNode)

                print(
                    ["RED", "PINK", "CYAN", "ORANGE", "NONE"][victimColor], pelletTarget
                )
                return victimColor, pelletTarget

            # Determines if waiting (none) is allowed as a move
            waitAllowed = victimColor == GhostColors.NONE

            # Loop over the directions
            for direction in Directions:

                # If direction is none, continue
                if (direction == Directions.NONE) and (not waitAllowed):
                    continue

                # Reset to the current compressed state
                decompressGameState(self.state, currNode.compressedState)

                for curr_ghost in self.state.ghosts:
                    curr_ghost.location.move()

                npBefore = self.state.numPellets()
                nspBefore = self.state.numSuperPellets()

                self.state.pacmanLoc.setDirection(direction)

                # new position is either not reachable-  move(), or not safe - safetyCheck()
                if not self.state.pacmanLoc.move() or not self.state.safetyCheck():
                    continue

                self.state.collectPellet(
                    self.state.pacmanLoc.row, self.state.pacmanLoc.col
                )

                npAfter = self.state.numPellets()
                nspAfter = self.state.numSuperPellets()
                ateNormalPellet = (npBefore > npAfter) and (nspBefore == nspAfter)

                # Determines if the scared ghost 'victim' was caught
                victimCaught = (victimColor != GhostColors.NONE) and (
                    (not self.state.ghosts[victimColor].isFrightened())
                    or self.state.ghosts[victimColor].spawning
                )
                
                if victimCaught:
                    print(f"${victimColor} Ghost Caught')")
                    currNode.directionBuf.append(direction)
                    self.queueEntireBuffer(currNode)
                    if currNode.pelletTargetCaught:
                        print("Pellet & Ghost Collected ")
                        pelletTarget = self.getNearestPellet()
                    victimColor = self.getNearestVictim()
                    return victimColor, pelletTarget
                    

                # Determines if the target was caught
                pelletTargetCaught = (
                    (not self.state.pelletAt(pelletTarget.row, pelletTarget.col))
                    or pelletTarget.at(
                        self.state.pacmanLoc.row, self.state.pacmanLoc.col
                    )
                    or (
                        self.state.fruitLoc.at(
                            self.state.pacmanLoc.row, self.state.pacmanLoc.col
                        )
                    )
                )

                # Select a new target
                self.selectTarget(pelletTarget)

                # Determine if there is a frightened ghost to chase
                victimExists = victimColor == GhostColors.NONE

                # If the state is valid, add it to the priority queue
                nextNode = AStarNode(
                    compressGameState(self.state),
                    fCost=int(
                        (
                            self.hCostExtend(
                                currNode.gCost, currNode.bufLength, victimColor
                            )
                            + currNode.gCost
                            + 1
                        )
                        * self.fCostMultiplier()
                    ),
                    gCost=currNode.gCost
                    + 2
                    + 2 * ((not ateNormalPellet) and (victimExists))
                    + 2 * victimExists,
                    directionBuf=currNode.directionBuf + [direction],
                    delayBuf=currNode.delayBuf + [predicted_delay],
                    bufLength=currNode.bufLength + 1,
                    victimCaught=victimCaught,
                    pelletTargetCaught=pelletTargetCaught,
                )

                # Add the next node to the priority queue
                heappush(priorityQueue, nextNode)

        print("Trapped...")
        return victimColor, pelletTarget

    def queueEntireBuffer(self, currNode):
        buf_length = len(currNode.directionBuf)
        
        for index in range(buf_length):
            self.state.queueAction(
                1, currNode.directionBuf[index]
            )
