# JSON (for reading config.json)
import json

# Asyncio (for concurrency)
import asyncio

# Game state
from gameState import *

# A-Star Policy
from policies.astar.aStarPolicy import *

# Get the FPS of the server from the config.json file
def getGameFPS() -> int:

	# Read the configuration file
	with open('../config.json', 'r', encoding='UTF-8') as configFile:
		config = json.load(configFile)

	# Return the FPS
	return config["GameFPS"]

class DecisionModule:
	'''
	Sample implementation of a decision module for high-level
	programming for Pacbot, using asyncio.
	'''

	def __init__(self, state: GameState) -> None:
		'''
		Construct a new decision module object
		'''

		# Game state object to store the game information
		self.state = state

		# Policy object, with the game state
		self.policy = AStarPolicy(state, newLocation(5, 21, self.state))

	async def decisionLoop(self) -> None:
		'''
		Decision loop for Pacbot
		'''

		wait = True
		gameFPS = getGameFPS()
		victimColor = GhostColors.NONE
		pelletTarget = Location(self.state)
		pelletTarget.row = 23
		pelletTarget.col = 14
		lastRow = 23
		lastCol = 14

		# Receive values as long as we have access
		while self.state.isConnected():

			'''
			WARNING: 'await' statements should be routinely placed
			to free the event loop to receive messages, or the
			client may fall behind on updating the game state!
			'''

			# If the current messages haven't been sent out yet and flushing isn't enabled, skip this iteration
			if not self.state.flushEnabled and len(self.state.writeServerBuf):
				await asyncio.sleep(0)
				continue

			if len(self.state.writeServerBuf) >= 3:
				await asyncio.sleep(0.25)

			if len(self.state.writeServerBuf) >= 5:
				await asyncio.sleep(0.5)

			if wait:
				# print(len(self.state.writeServerBuf))
				await asyncio.sleep(1/gameFPS)
				wait = False

			# Lock the game state
			self.state.lock()

			# Figure out which actions to take, according to the policy
			if self.state.gameMode != GameModes.PAUSED:
				victimColor, pelletTarget, lastRow, lastCol = await self.policy.act(6, victimColor, pelletTarget, lastRow, lastCol)

			# Unlock the game state
			self.state.unlock()

			# Free up the event loop
			await asyncio.sleep(0)

			wait = True
