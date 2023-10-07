# Asyncio (for concurrency)
import asyncio

# Game state
from gameState import GameState

# Queue for robot commands
from collections import deque

# Priority queue for A-star
from heapq import heappush, heappop

def setBit(flag: int, bitIdx: int) -> int:
    return (flag | (1 << bitIdx))

def clearBit(flag: int, bitIdx: int) -> int:
    return (flag & ~(1 << bitIdx))

def getBit(flag: int, bitIdx: int) -> bool:
    return bool((flag >> bitIdx) & 1)

class AStarPolicy:
    
    def __init__(self, state: GameState, command_buf: deque):
        
        # Game state
        self.state: GameState = state

    async def plan(self) -> None:
        '''
        Plan
        '''

        visited = [0 for _ in range(31)]
        currRow = self.state.pacmanLoc.row
        currCol = self.state.pacmanLoc.col
        
        visited[currRow] = setBit(visited[currRow], currCol)
        
		

        pass