from game_state import GameState, GhostColors, GameModes, is_valid_location
from bot_client import SCATTER_COL, SCATTER_ROW, Directions, D_COL, D_ROW, reversedDirections

CHASE_MODE_DURATION = 175
SCATTER_MODE_DURATION = 65

class Simulator:
    '''
    The Simulator class is designed to perform A* future lookahead simulations. 
    It predicts movements and decisions for both ghosts and Pac-Man based on the current game state.

    Attributes:
        - CHASE_MODE_DURATION: The fixed number of ticks the game remains in CHASE mode before flipping.
        - SCATTER_MODE_DURATION: The fixed number of ticks the game remains in SCATTER mode before flipping.
        - game_state: The current GameState object that the simulator manipulates and predicts future states for.
        - ate_normal_pellet: A boolean flag indicating if a normal pellet was eaten in the last simulation tick.

    '''

    def __init__(self, game_state: GameState) -> None:
        self.game_state = game_state
        self.ate_normal_pellet = False
    
    def predict_ghost_movements(self) -> None:
        '''
        Use incomplete knowledge of the current game state to predict where the
        ghosts might aim at the next step
        '''
        for curr_ghost in self.game_state.ghosts:
         

            # For the same reason as in move(), ignore spawning ghosts during short-
            # term projections into the future
            if curr_ghost.spawning or not is_valid_location(curr_ghost.location.row, curr_ghost.location.col):
                return

            # If the ghost is at an empty location, ignore it
            if curr_ghost.location.row >= 32 or curr_ghost.location.col >= 32:
                return

            # Row and column at the next step
            nextRow: int = curr_ghost.location.row + curr_ghost.location.row_dir
            nextCol: int = curr_ghost.location.col + curr_ghost.location.col_dir

            # Pacman row and column
            pacmanRow: int = self.game_state.pacmanLoc.row
            pacmanCol: int = self.game_state.pacmanLoc.col
            pacmanrow_dir: int = self.game_state.pacmanLoc.row_dir
            pacmancol_dir: int = self.game_state.pacmanLoc.col_dir

            # Red ghost's location
            redRow: int = self.game_state.ghosts[GhostColors.RED].location.row
            redCol: int = self.game_state.ghosts[GhostColors.RED].location.col

            # Target row and column
            targetRow: int = 0
            targetCol: int = 0

            # Choose a target for the ghost based on its color
            if self.game_state.gameMode == GameModes.CHASE:

                # Red targets Pacman
                if curr_ghost.color == GhostColors.RED:
                    targetRow = pacmanRow
                    targetCol = pacmanCol

                # Pink targets the space 4 ahead of Pacman
                elif curr_ghost.color == GhostColors.PINK:
                    targetRow = pacmanRow + 4 * pacmanrow_dir
                    targetRow = pacmanCol + 4 * pacmancol_dir

                # Cyan targets the position of red, reflected about the position 2 spaces
                # ahead of Pacman
                elif curr_ghost.color == GhostColors.CYAN:
                    targetRow = 2 * pacmanRow + 4 * pacmanrow_dir - redRow
                    targetCol = 2 * pacmanCol + 4 * pacmancol_dir - redCol

                # Orange targets Pacman, but only if Pacman is farther than 8 spaces away
                elif curr_ghost.color == GhostColors.ORANGE:
                    distSqToPacman = (nextRow - pacmanRow) * (nextRow - pacmanRow) + \
                                                        (nextCol - pacmanCol) * (nextCol - pacmanCol)
                    targetRow = pacmanRow if (distSqToPacman < 64) else \
                                                SCATTER_ROW[GhostColors.ORANGE]
                    targetCol = pacmanCol if (distSqToPacman < 64) else \
                                                SCATTER_COL[GhostColors.ORANGE]

            # In scatter mode, each ghost tracks a fixed target at a corner of the maze
            if self.game_state.gameMode == GameModes.SCATTER:
                targetRow = SCATTER_ROW[curr_ghost.color]
                targetCol = SCATTER_COL[curr_ghost.color]

            # Calculate the distance squared to the target, for all 4 moves
            minDist = 0xfffffff
            maxDist = -1
            minDir  = Directions.UP
            maxDir  = Directions.UP
            for direction in Directions:
                if direction != Directions.NONE:

                    # Avoid reversals, as ghosts are not typically allowed to reverse
                    if D_ROW[direction] + curr_ghost.location.row_dir != 0 or \
                        D_COL[direction] + curr_ghost.location.col_dir != 0:

                        # Check whether this new location would be valid (not in a wall)
                        newRow = nextRow + D_ROW[direction]
                        newCol = nextCol + D_COL[direction]
                        
                        if not self.game_state.wallAt(newRow, newCol):

                            # Compare the distance squared to the target to the current best;
                            # if it is better, choose it to be the new ghost plan
                            distSqToTarget = (newRow - targetRow) * (newRow - targetRow) + \
                                                                (newCol - targetCol) * (newCol - targetCol)
                            if distSqToTarget < minDist:
                                minDir  = direction
                                minDist = distSqToTarget
                            elif distSqToTarget >= maxDist:
                                maxDir  = direction
                                maxDist = distSqToTarget

            # Update the best direction to be the plan
            curr_ghost.plannedDirection = minDir if (not curr_ghost.isFrightened()) else maxDir

    def run(self, numTicks: int, pacmanDir: Directions) -> bool:
    
        '''
        Helper function to advance the game state (predicting the new ghost
        positions, modes, and other information) and move Pacman one space in a
        chosen direction, as a high-level path planning step

        Returns: whether this action is safe (True) or unsafe (False), in terms
        of colliding with non-frightened ghosts.
        '''

        # # Try to plan the ghost directions if we expect them to be none
        # for ghost in game_state.ghosts:
        #     if ghost.plannedDirection == Directions.NONE:
        #         predict_ghost_movement(ghost, game_state)

        # Loop over every tick
        # for tick in range(1, numTicks+1):
        
        # # Keep ticking until an update
        # if (game_state.currTicks + tick) % game_state.updatePeriod != 0:
        #     continue

        # Update the ghost positions 
        for ghost in self.game_state.ghosts:
            # is this check necessary?
            if not ghost.spawning:
                if ghost.isFrightened():
                    ghost.frightSteps -= 1
                ghost.location.move()

        # Return if Pacman collides with a non-frightened ghost
        if not self.game_state.safetyCheck():
            return False
        
        if pacmanDir != Directions.NONE:
            # Set the direction of Pacman, as chosen, and try to move one step
            pacmanPrevDir = self.game_state.pacmanLoc.getDirection()
            self.game_state.pacmanLoc.setDirection(pacmanDir)
            if not self.game_state.pacmanLoc.advance():
                self.game_state.pacmanLoc.setDirection(pacmanPrevDir)
                return False

            self.game_state.collectPellet(self.game_state.pacmanLoc.row, self.game_state.pacmanLoc.col)

            # If there are no pellets left, return
            if self.game_state.numPellets() == 0:
                return True

        # Return if Pacman collides with a non-frightened ghost
        if not self.game_state.safetyCheck():
            return False
        
        # Update the mode steps counter, and change the mode if necessary
        self.game_state.modeSteps -= 1
        if self.game_state.numPellets() > 20 and self.game_state.modeSteps == 0:
            self.flipGameMode()

        # Guess the next ghost moves (will likely be inaccurate, due to inferring
        # unknown information from other features of the game state)
        for ghost in self.game_state.ghosts:
            self.predict_ghost_movement(ghost, self.game_state)

       

        # Increment the number of ticks by the chosen amount
        self.game_state.currTicks += numTicks

        # Return that Pacman was safe during this transition
        return True

    def flipGameMode(self) -> None :
        '''
        Helper function to change gamemode from SCATTER to CHASE or vice-versa.
        '''
        
        # Scatter -> Chase
        if self.game_state.gameMode == GameModes.SCATTER:
            self.game_state.gameMode = GameModes.CHASE
            self.game_state.modeSteps = self.game_state.modeDuration = CHASE_MODE_DURATION

        # Chase -> Scatter
        elif self.game_state.gameMode == GameModes.CHASE and self.game_state.numPellets() > 20:
            self.game_state.gameMode = GameModes.SCATTER
            self.game_state.modeSteps = self.game_state.modeDuration = SCATTER_MODE_DURATION

            # Reverse the planned directions of all ghosts
            # Not necessarily true: later fix
            for ghost in self.game_state.ghosts:
                ghost.plannedDirection = reversedDirections[ghost.plannedDirection]
