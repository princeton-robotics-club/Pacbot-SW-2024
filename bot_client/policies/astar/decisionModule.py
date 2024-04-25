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


		self.victimColor = GhostColors.NONE
		self.pelletTarget = Location(self.state)
		self.pelletTarget.row = 23
		self.pelletTarget.col = 14

		# gate for calculations
		self.doPolicy = True

	''' Immediately halt all policy calculations
	break from policy.act() (this updates a flag, break might happen slightly later)
	'''
	async def haltPolicyCalculations(self):
		print("[Decision Module] halting policy calculations")
		await self.policy.breakFromAct()

	async def doneEventHandler(self, done: bool):
		if not done:
			await self.haltPolicyCalculations()

	async def cvUpdateEventHandler(self):
		await self.haltPolicyCalculations()

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

			# if not self.doPolicy:
			# 	continue

			# If the current messages haven't been sent out yet, skip this iteration
			# print("get lock decision loop")
			if self.state.isLocked():
				await asyncio.sleep(0)
				# wait = True
				continue

			# Wait for one game tick, idk why exactly...
			if wait:
				await asyncio.sleep(1/gameFPS)
				wait = False

			# make sure game is not paused
			if self.state.gameMode == 0:
				await asyncio.sleep(0)
				continue

			# Lock the game state
			self.state.lock()
			# print("done get lock decision loop")


			# # TODO: remove later; for testing purposes
			# await asyncio.sleep(0.5)

			# Figure out which actions to take, according to the policy
			print("[ astar calculating...")
			# victimColor, pelletTarget = await self.policy.act(3, victimColor, pelletTarget)
			victimColor, pelletTarget = await self.policy.act(24, victimColor, pelletTarget)
			print("]")

			# Unlock the game state
			self.state.unlock()
			# print("unlock decision loop")

			# Free up the event loop
			await asyncio.sleep(0.005)

			wait = True

			self.doPolicy = False
