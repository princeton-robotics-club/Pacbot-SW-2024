from game_state import GameState, GhostColors, GameModes, is_valid_location, Ghost
from bot_client import SCATTER_COL, SCATTER_ROW, Directions, D_COL, D_ROW, reversedDirections

CHASE_MODE_DURATION = 175
SCATTER_MODE_DURATION = 65

def moveToValidLoc(self, game_state: GameState, pacmanDir: Directions) -> bool:

    '''
    Helper function to advance the game state (predicting the new ghost
    positions, modes, and other information) and move Pacman one space in a
    chosen direction, as a high-level path planning step

    Returns: whether this action is safe (True) or unsafe (False), in terms
    of colliding with non-frightened ghosts.
    '''

    # Set the direction of Pacman, as chosen, and try to move one step
    
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
