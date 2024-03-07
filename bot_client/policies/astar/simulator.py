from game_state import Location, GameState, Ghost, GhostColors, GameModes
from bot_client import SCATTER_COL, SCATTER_ROW, Directions, D_COL, D_ROW

def simulate_step_transition(current_location: Location, game_state: GameState) -> bool:
    """
    Simulates a step transition for the given location within the game state.
    Returns True if the transition is successful (i.e., the location moves to a valid new position).
    
    Parameters:
    - current_location: The current location of object (i.e. PacMan or Ghost) that needs to be advanced.
    - game_state: The current state of the game, used to check for walls.
    
    Returns:
    - bool: True if the location was successfully advanced; False otherwise.
    """

    # Check if the current position is out of bounds
    if not (0<current_location.row<31 and 0<current_location.col<28):
        return False

    next_row = current_location.row + current_location.row_dir
    next_col = current_location.col + current_location.col_dir

    # Check if the next position is not a wall and update the location if it's not
    if not game_state.is_wall_at(next_row, next_col):
        current_location.row = next_row
        current_location.col = next_col
        return True
    else: 
        return False


def simulate_ghost_transition(curr_ghost: Ghost, game_state: GameState, ) -> None:
    '''
    Use incomplete knowledge of the current game state to predict where the
    ghosts might aim at the next step
    '''

    # For the same reason as in move(), ignore spawning ghosts during short-
    # term projections into the future
    if curr_ghost.spawning:
        return

    # If the ghost is at an empty location, ignore it
    if curr_ghost.location.row >= 32 or curr_ghost.location.col >= 32:
        return

    # Row and column at the next step
    nextRow: int = curr_ghost.location.row + curr_ghost.location.rowDir
    nextCol: int = curr_ghost.location.col + curr_ghost.location.colDir

    # Pacman row and column
    pacmanRow: int = game_state.pacmanLoc.row
    pacmanCol: int = game_state.pacmanLoc.col
    pacmanRowDir: int = game_state.pacmanLoc.rowDir
    pacmanColDir: int = game_state.pacmanLoc.colDir

    # Red ghost's location
    redRow: int = game_state.ghosts[GhostColors.RED].location.row
    redCol: int = game_state.ghosts[GhostColors.RED].location.col

    # Target row and column
    targetRow: int = 0
    targetCol: int = 0

    # Choose a target for the ghost based on its color
    if game_state.gameMode == GameModes.CHASE:

        # Red targets Pacman
        if curr_ghost.color == GhostColors.RED:
            targetRow = pacmanRow
            targetCol = pacmanCol

        # Pink targets the space 4 ahead of Pacman
        elif curr_ghost.color == GhostColors.PINK:
            targetRow = pacmanRow + 4 * pacmanRowDir
            targetRow = pacmanCol + 4 * pacmanColDir

        # Cyan targets the position of red, reflected about the position 2 spaces
        # ahead of Pacman
        elif curr_ghost.color == GhostColors.CYAN:
            targetRow = 2 * pacmanRow + 4 * pacmanRowDir - redRow
            targetCol = 2 * pacmanCol + 4 * pacmanColDir - redCol

        # Orange targets Pacman, but only if Pacman is farther than 8 spaces away
        elif curr_ghost.color == GhostColors.ORANGE:
            distSqToPacman = (nextRow - pacmanRow) * (nextRow - pacmanRow) + \
                                                (nextCol - pacmanCol) * (nextCol - pacmanCol)
            targetRow = pacmanRow if (distSqToPacman < 64) else \
                                        SCATTER_ROW[GhostColors.ORANGE]
            targetCol = pacmanCol if (distSqToPacman < 64) else \
                                        SCATTER_COL[GhostColors.ORANGE]

    # In scatter mode, each ghost tracks a fixed target at a corner of the maze
    if game_state.gameMode == GameModes.SCATTER:
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
            if D_ROW[direction] + curr_ghost.location.rowDir != 0 or \
                D_COL[direction] + curr_ghost.location.colDir != 0:

                # Check whether this new location would be valid (not in a wall)
                newRow = nextRow + D_ROW[direction]
                newCol = nextCol + D_COL[direction]
                
                if not game_state.wallAt(newRow, newCol):

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
