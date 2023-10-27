# JSON (for reading config.json)
import json

# Asyncio (for concurrency)
import asyncio
from test import BasicAStar

# Websockets (for communication with the server)
from websockets.sync.client import connect, ClientConnection # type: ignore
from websockets.exceptions import ConnectionClosedError # type: ignore
from websockets.typing import Data # type: ignore

from astar import AStar
from fieldnodes import FIELD_NODES
import math


# Game state
from gameState import GameMode, GameState

# Decision module
from decisionModule import DecisionModule

# Restore the ability to use Ctrl + C within asyncio
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Font color modifiers
RED = '\033[31m'
NORMAL = '\033[0m'

# Get the connect URL from the config.json file
def get_connect_url() -> str:

	# Read the configuration file
	with open('../config.json', 'r', encoding='UTF-8') as config_json:
		config_dict = json.load(config_json)

	# Return the websocket connect address
	return f'ws://{config_dict["ServerIP"]}:{config_dict["WebSocketPort"]}'

class PacbotClient:
	'''
	Sample implementation of a websocket client to communicate with the
	Pacbot game server, using asyncio.
	'''

	def __init__(self, connect_url: str) -> None:
		'''
		Construct a new Pacbot client object
		'''

		# Connection URL (starts with ws://)
		self.connect_url: str = connect_url

		# Private variable to store whether the socket is open
		self._socket_open: bool = False

		# Connection object to communicate with the server
		self.connection: ClientConnection = None

		# Game state object to store the game information
		self.state: GameState = GameState()

		# Decision module (policy) to make high-level decisions
		self.policy: DecisionModule = DecisionModule(self.state)

		# Decision State
		self.decision_state = 0
		self.decision_states = ["State 0", "State 1", "State 2", "State 3"]
		self.decision_goal = '(1,23)'

		# Game Info
		self.game_super_pellet_locs = [(1,23), (26,23), (1,3), (26,3)]

	def game_get_closest_super_pellet(self):
		if len(self.game_super_pellet_locs) == 0:
			return None
		closest_pellet = 0
		smallest_dist = 99
		for i in range(len(self.game_super_pellet_locs)):
			dist = math.sqrt((self.state.pacmanLoc.col - self.game_super_pellet_locs[i][0]) ** 2 \
						+ (self.state.pacmanLoc.row - self.game_super_pellet_locs[i][0]) ** 2)
			if dist < smallest_dist:
				smallest_dist = dist
				closest_pellet = i
		return '(' + str(self.game_super_pellet_locs[closest_pellet][0]) + ',' + str(self.game_super_pellet_locs[closest_pellet][1]) + ')'
	
	def game_get_closest_ghost(self):
		closest_ghost = self.state.ghosts[0]
		smallest_dist = 99
		for i, ghost in enumerate(self.state.ghosts):
			dist = math.sqrt((self.state.pacmanLoc.col - ghost.location.col) ** 2 \
						+ (self.state.pacmanLoc.row - ghost.location.row) ** 2)
			if dist < smallest_dist:
				smallest_dist = dist
				closest_ghost = ghost
		return '(' + str(closest_ghost.location.col) + ',' + str(closest_ghost.location.row) + ')'
	
	def game_get_closest_tasty_ghost(self):
		closest_ghost = self.state.ghosts[0]
		smallest_dist = 500
		for i, ghost in enumerate(self.state.ghosts):
			dist = math.sqrt((self.state.pacmanLoc.col - ghost.location.col) ** 2 \
						+ (self.state.pacmanLoc.row - ghost.location.row) ** 2)
			if dist < smallest_dist and ghost.frightCycles != 0 and ghost.frightCycles != 128 and ghost.spawning == False:
				smallest_dist = dist
				closest_ghost = ghost
		return '(' + str(closest_ghost.location.col) + ',' + str(closest_ghost.location.row) + ')'


	def decision_transition(self):
		# remove each pellet
		for i, super_pellet in enumerate(self.game_super_pellet_locs):
			if '(' + str(self.state.pacmanLoc.col) + ', ' + str(self.state.pacmanLoc.row) + ')' == str(super_pellet):
				del self.game_super_pellet_locs[i]

		# pellet hunter
		if self.decision_state == 0:
			# check if any ghosts are frightened
			for ghost in self.state.ghosts:
				if ghost.frightCycles != 0 and ghost.frightCycles != 128 and ghost.spawning == False:
					self.decision_state = 1
					break

		# ghost hunter
		elif self.decision_state == 1:
			change_state = True
			for ghost in self.state.ghosts:
				if ghost.frightCycles != 0 and ghost.frightCycles != 128 and ghost.spawning == False:
					# print('cycle:' + str(ghost.frightCycles))
					change_state = False
			if change_state == True:
				self.decision_state = 0
		

	async def run(self) -> None:
		'''
		Connect to the server, then run
		'''

		# Connect to the websocket server
		await self.connect()

		try: # Try receiving messages indefinitely
			await asyncio.gather(
				self.recv_loop(),
				self.policy.decision_loop()
			)
		finally: # Disconnect once the connection is over
			await self.disconnect()

	async def connect(self) -> None:
		'''
		Connect to the websocket server
		'''

		# Connect to the specified URL
		try:
			self.connection = connect(self.connect_url)
			self._socket_open = True

		# If the connection is refused, log and return
		except ConnectionRefusedError:
			print(
				f'{RED}Websocket connection refused [{self.connect_url}]\n'
				f'Are the address and port correct, and is the '
				f'server running?{NORMAL}'
			)
			return

	async def disconnect(self) -> None:
		'''
		Disconnect from the websocket server
		'''

		# Close the connection
		if self._socket_open:
			self.connection.close()
		self._socket_open = False

	# Return whether the connection is open
	def is_open(self) -> bool:
		'''
		Check whether the connection is open (unused)
		'''
		return self._socket_open
	
	def get_next_command(self, curr, next) -> bytes:
		'''
		Given a current location and a next location, returns a byte string representing the command to send
		'''
		if curr[0] - next[0] == -1:
			print('d')
			return b'd'
		elif curr[0] - next[0] == 1:
			print('a')
			return b'a'
		elif curr[1] - next[1] == -1:
			print('s')
			return b's'
		print('w')
		return b'w'

	async def recv_loop(self) -> None:
		'''
		Receive loop for capturing messages from the server
		'''
		last_command = None

		# Receive values as long as the connection is open
		while self._socket_open:

			# Try to receive messages (and skip to except in case of an error)
			try:

				# Receive a message from the connection
				message: Data = self.connection.recv()

				# Convert the message to bytes, if necessary
				message_bytes: bytes
				if isinstance(message, bytes):
					message_bytes = message # type: ignore
				else:
					message_bytes = message.encode('ascii') # type: ignore

				# Update the state, given this message from the server
				self.state.update(message_bytes)


				# Free the event loop to allow another decision
				await asyncio.sleep(0)


				# print(str(self.state.ghosts[0].location.row) + ", " + str(self.state.ghosts[0].location.col))
				print('pacloc ' + str(self.state.pacmanLoc.col) + ", " + str(self.state.pacmanLoc.row))

				# make sure pacman in field and game playing
				if self.state.pacmanLoc.col < 0 or self.state.pacmanLoc.col >= 32 \
					or self.state.pacmanLoc.row < 0 or self.state.pacmanLoc.row >= 28 \
					or self.state.gameMode == GameMode.PAUSED:
					continue

				target = None
				if self.decision_state == 0:
					target = self.game_get_closest_super_pellet()
				elif self.decision_state == 1:
					target = self.game_get_closest_tasty_ghost()
				print('target ' + str(target))
				print('state ' + str(self.decision_state))

				path = BasicAStar(FIELD_NODES).astar('(' + str(self.state.pacmanLoc.col) + ',' + str(self.state.pacmanLoc.row) + ')', target)
				new_path = []
				i = 0
				if path is not None:
					for p in path:
						if i < 2:
							new_path.append(p)
							i += 1
				# send one command
				print(new_path)
				if len(new_path) <= 1:
					print('no target')
					self.connection.send(b'd')
				else:
					# avoid sending same command twice
					if last_command != None and last_command[0] == new_path[0] and last_command[1] == new_path[1]:
						continue
					else:
						curr = eval(new_path[0])
						next = eval(new_path[1])
						next_command = self.get_next_command(curr, next)
						self.connection.send(next_command)
						last_command = (new_path[0], new_path[1])

				self.decision_transition()

			# Break once the connection is closed
			except ConnectionClosedError:
				break



# Main function
async def main():

	# Get the URL to connect to
	connect_url = get_connect_url()
	client = PacbotClient(connect_url)
	await client.run()

	# Once the connection is closed, end the event loop
	loop = asyncio.get_event_loop()
	loop.stop()

if __name__ == '__main__':

	# Run the event loop forever
	loop = asyncio.get_event_loop()
	loop.create_task(main())
	loop.run_forever()


