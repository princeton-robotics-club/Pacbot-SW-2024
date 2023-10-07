# Asyncio (for concurrency)
import asyncio

# Game state
from gameState import GameState
from websockets.sync.client import ClientConnection # type: ignore


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

	

	def connect(self, connection: ClientConnection):
		# Send messages to server for high level testing
		self.connection = connection

	def send_message(self) -> None:
		pass
		# if self.connection:
		# 	print('sending d')
			# self.connection.send(b'd')

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
			await asyncio.sleep(1)

			# Lock the game state
			self.state.unlock()

			# Free up the event loop (a good chance to talk to the bot!)
			await asyncio.sleep(1)


			# send message to game server
			self.send_message()
			
	def get_command(self, state) -> str:
		return ''