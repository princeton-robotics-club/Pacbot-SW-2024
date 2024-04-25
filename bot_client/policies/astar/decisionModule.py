# JSON (for reading config.json)
import json

# Asyncio (for concurrency)
import asyncio

# Game state
from gameState import *

# A-Star Policy
from policies.astar.aStarPolicy import *

# Comms module type
from robotSocket import RobotSocket

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

	def __init__(self, state: GameState, commsModule: RobotSocket) -> None:
		'''
		Construct a new decision module object
		'''

		# Game state object to store the game information
		self.state = state

		# Policy object, with the game state
		self.policy = AStarPolicy(state, newLocation(5, 21, self.state))


		self.victimColor = GhostColors.NONE
		self.pelletTarget = Location(self.state)
		self.pelletTarget.row = 23
		self.pelletTarget.col = 14

		commsModule.registerDoneHandler(self.doneEventHandler)

	async def makeDecision(self) -> None:

		while self.state.isLocked():
			await asyncio.sleep(0.1)

		if self.state.gameMode == 0:
			return

		# Lock the game state
		self.state.lock()

		print("[ astar calculating...", end=' ')
		self.victimColor, self.pelletTarget = self.policy.act(3, self.victimColor, self.pelletTarget)
		print("]")

		# Unlock the game state
		self.state.unlock()

	def doneEventHandler(self, done: bool):
		if done:
			await self.makeDecision()
		else:
			await asyncio.sleep(1/getGameFPS())


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

			# If the current messages haven't been sent out yet, skip this iteration
			if not self.state.done or self.state.isLocked():
				await asyncio.sleep(0)
				continue

			if wait:
				await asyncio.sleep(1/gameFPS)
				wait = False

			if self.state.gameMode == 0:
				await asyncio.sleep(0)
				continue

			await asyncio.sleep(0.5)


			# Lock the game state
			self.state.lock()


			done = self.state.done

			# Figure out which actions to take, according to the policy

			print("[ astar calculating...", end=' ')
			victimColor, pelletTarget = await self.policy.act(3, victimColor, pelletTarget)
			print("]")

			self.state.done = done

			# Unlock the game state
			self.state.unlock()

			# Free up the event loop
			await asyncio.sleep(0.005)

			wait = True
