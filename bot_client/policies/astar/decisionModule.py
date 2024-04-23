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

	def __init__(self, state: GameState, coalesceFlag: bool=False) -> None:
		'''
		Construct a new decision module object
		'''

		# Game state object to store the game information
		self.state = state

		# Policy object, with the game state
		self.policy = AStarPolicy(state, newLocation(5, 21, self.state), coalesceFlag=coalesceFlag)

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

		# Receive values as long as we have access
		while self.state.isConnected():

			'''
			WARNING: 'await' statements should be routinely placed
			to free the event loop to receive messages, or the
			client may fall behind on updating the game state!
			'''

			# If the current messages haven't been sent out yet and flushing isn't enabled, skip this iteration
			if len(self.state.writeServerBuf):
				await asyncio.sleep(0)
				# wait = True
				continue

			# if len(self.state.writeServerBuf) >= 3:
			# 	await asyncio.sleep(0.25)

			if wait:
				await asyncio.sleep(1/gameFPS)
				wait = False

			# Lock the game state
			self.state.lock()

			# Figure out which actions to take, according to the policy
			if self.state.gameMode != GameModes.PAUSED:
				victimColor, pelletTarget = await self.policy.act(12, victimColor, pelletTarget)

			# Unlock the game state
			self.state.unlock()

			# Free up the event loop
			await asyncio.sleep(0)

			wait = True
