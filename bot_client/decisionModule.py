# Asyncio (for concurrency)
import asyncio

# Game state
from gameState import GameState

# Policy
from aStarPolicy import AStarPolicy

# Queue of commands to send to robot
from collections import deque

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

		# Buffer of commands to send to robot
		self.commands: deque = deque()

		# Policy to determine the next action
		self.policy: AStarPolicy = AStarPolicy(state, self.commands)

	async def decision_loop(self) -> None:
		'''
		Decision loop for Pacbot
		'''

		# Receive values as long as we have access
		while True:

			# WARNING: 'await' statements should be routinely placed
			# to free the event loop to receive messages, or the
			# client may fall behind on updating the game state!

			# Lock the game state
			self.state.lock()

			# Replace this with the actual decisions for Pacbot
			await self.policy.plan()

			# Lock the game state
			self.state.unlock()

			# Free up the event loop (a good chance to talk to the bot!)
			await asyncio.sleep(10000000)