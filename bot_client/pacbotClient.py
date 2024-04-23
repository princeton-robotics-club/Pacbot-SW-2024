# JSON (for reading config.json)
import json

# Asyncio (for concurrency)
import asyncio

# Websockets (for communication with the server)
from websockets.sync.client import connect, ClientConnection # type: ignore
from websockets.exceptions import ConnectionClosedError # type: ignore
from websockets.typing import Data # type: ignore

# Game state
from gameState import GameState, GameModes, Location

# Decision module
from policies.astar.decisionModule import DecisionModule

# Robot socket
from robotSocket import RobotSocket

# Server messages
from serverMessage import *

# Restore the ability to use Ctrl + C within asyncio
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Terminal colors for formatting output text
from terminalColors import *

# for type enforcement of event handler functions
from typing import Callable

# Get the connect URL from the config.json file
def getConnectURL() -> str:

	# Read the configuration file
	with open('../config.json', 'r', encoding='UTF-8') as configFile:
		config = json.load(configFile)

	# Return the websocket connect address
	return f'ws://{config["ServerIP"]}:{config["WebSocketPort"]}'

# Get the simulation flag from the config.json file
def getSimulationFlag() -> bool:

	# Read the configuration file
	with open('../config.json', 'r', encoding='UTF-8') as configFile:
		config = json.load(configFile)

	# Return the simulation flag
	return config["PythonSimulation"]

# Get the robot address from the config.json file
def getRobotAddress() -> tuple[str, int]:

	# Read the configuration file
	with open('../config.json', 'r', encoding='UTF-8') as configFile:
		config = json.load(configFile)

	# Return the robot socket connect address
	return config["RobotIP"], config['RobotPort']

def getCoalesceFlag() -> bool:
	
	# Read the config file
	with open('../config.json', 'r', encoding='UTF-8') as configFile:
		config = json.load(configFile)
	
	coalesce: bool = config["CoalesceCommands"]

	# do not coalesce if doing sim bc server doesn't support
	if coalesce:
		assert(not getSimulationFlag())

	# Return if should coalesce
	return coalesce

class PacbotClient:
	'''
	Sample implementation of a websocket client to communicate with the
	Pacbot game server, using asyncio.
	'''

	def __init__(self, connectURL: str, simulationFlag: bool, coalesceFlag: bool, robotAddress: tuple[str, int]) -> None:
		'''
		Construct a new Pacbot client object
		'''

		# Connection URL (starts with ws://)
		self.connectURL: str = connectURL

		# Simulation flag (bool)
		self.simulationFlag: bool = simulationFlag

		# Coalesce flag (bool)
		self.coalesceFlag: bool = coalesceFlag

		# Robot IP and port
		self.robotIP: str = robotAddress[0]
		self.robotPort: int = robotAddress[1]

		# Private variable to store whether the socket is open
		self._socketOpen: bool = False

		# Connection object to communicate with the server
		self.connection: ClientConnection

		# event handlers
		self.gameModeStartStopEventHandlers: list[Callable[[bool, Location], None]] = []

		# Game state object to store the game information
		self.state: GameState = GameState()
		self.state.simulationFlag = simulationFlag

		# Decision module (policy) to make high-level decisions
		self.decisionModule: DecisionModule = DecisionModule(self.state, self.coalesceFlag)

		# Robot socket (comms) to dispatch low-level commands
		self.robotSocket: RobotSocket = RobotSocket(self.robotIP, self.robotPort, self)


	def notifyGameModeStartStopChange(self, gameMode: bool):
		print("notifying game change")
		for gameModeStartStopEventHandler in self.gameModeStartStopEventHandlers:
			gameModeStartStopEventHandler(gameMode, self.state.pacmanLoc)

	def subscribeToGameModeStartStopChange(self, handler: Callable[[bool, Location], None]):
		self.gameModeStartStopEventHandlers.append(handler)

	def unsubscribeToGameModeStartStopChange(self, handler: Callable[[bool, Location], None]):
		self.gameModeStartStopEventHandlers.remove(handler)


	async def run(self) -> None:
		'''
		Connect to the server, then run
		'''

		# Connect to the websocket server
		await self.connect()

		try: # Try receiving messages indefinitely
			if self._socketOpen:
				await asyncio.gather(
					self.receiveLoop(),
					self.commsLoop(),
					self.decisionModule.decisionLoop()
				)
		finally: # Disconnect once the connection is over
			await self.disconnect()

	async def connect(self) -> None:
		'''
		Connect to the websocket server
		'''

		# Connect to the specified URL
		try:
			self.connection = connect(self.connectURL)
			self._socketOpen = True
			self.state.setConnectionStatus(True)

		# If the connection is refused, log and return
		except ConnectionRefusedError:
			print(
				f'{RED}Websocket connection refused [{self.connectURL}]\n'
				f'Are the address and port correct, and is the '
				f'server running?{NORMAL}'
			)
			return

	async def disconnect(self) -> None:
		'''
		Disconnect from the websocket server
		'''

		# Close the connection
		if self._socketOpen:
			self.connection.close()
		self._socketOpen = False
		self.state.setConnectionStatus(False)

	# Return whether the connection is open
	def isOpen(self) -> bool:
		'''
		Check whether the connection is open (unused)
		'''
		return self._socketOpen

	async def receiveLoop(self) -> None:
		'''
		Receive loop for capturing messages from the server
		'''

		# Receive values as long as the connection is open
		while self.isOpen():

			# Try to receive messages (and skip to except in case of an error)
			try:

				# Receive a message from the connection
				message: Data = self.connection.recv()

				# Convert the message to bytes, if necessary
				messageBytes: bytes
				if isinstance(message, bytes):
					messageBytes = message # type: ignore
				else:
					messageBytes = message.encode('ascii') # type: ignore

				# Update the state, given this message from the server
				isRunningOld = GameModes.isRunning(self.state.gameMode)
				self.state.update(messageBytes)

				# trigger gameMode update (stop/start change event)
				isRunningNew = GameModes.isRunning(self.state.gameMode)
				if (isRunningOld != isRunningNew):
					self.notifyGameModeStartStopChange(isRunningNew)

				# Write a response back to the server if necessary
				if (self.simulationFlag):
					if self.state.writeServerBuf and self.state.writeServerBuf[0].tick():
						response: bytes = self.state.writeServerBuf.popleft().getBytes()
						self.connection.send(response)

				# Free the event loop to allow another decision
				await asyncio.sleep(0)

			# Break once the connection is closed
			except ConnectionClosedError:
				print('Connection lost...')
				self.state.setConnectionStatus(False)
				break

	async def commsLoop(self) -> None:
		'''
		Communication loop for sending messages to the robot
		'''

		# Quit if in simulation
		if (self.simulationFlag):
			print(f"{CYAN}Mode: No Robot{NORMAL}")
			return
		else:
			print(f"{CYAN}Mode: Yes Robot{NORMAL}")


		# Keep track if the first iteration has taken place
		firstIt = True

		# Keep sending messages as long as the server connection is open
		while self.isOpen():

			# Try to receive messages (and skip to except in case of an error)
			try:

				# Wait until the bot stops sending messages
				self.robotSocket.wait()
				
				# Handle first iteration (flush)
				if firstIt:
					# begin by flushing buff
					self.robotSocket.flush(self.state.pacmanLoc.row, self.state.pacmanLoc.col)

					# send start/stop depending on the gamestate
					if (GameModes.isRunning(self.state.gameMode)):
						self.robotSocket.start(self.state.pacmanLoc.row, self.state.pacmanLoc.col)
					else:
						self.robotSocket.stop(self.state.pacmanLoc.row, self.state.pacmanLoc.col)
					firstIt = False

				# Otherwise, send out relevant messages
				else:
					if self.state.writeServerBuf and self.state.writeServerBuf[0].tick():
						serverCommand = self.state.writeServerBuf.popleft()
						self.robotSocket.moveNoCoal(serverCommand, self.state.pacmanLoc.row, self.state.pacmanLoc.col)
						self.state.writeServerBuf.clear() # TODO: remove this
						if self.state.writeServerBuf:
							self.state.writeServerBuf[0].skipDelay()

				# Free the event loop to allow another decision
				await asyncio.sleep(0.025)

			# Break once the connection is closed
			except ConnectionClosedError:
				print('Comms lost...')
				self.state.setConnectionStatus(False)
				break

# Main function
async def main():

	# Get the URL to connect to
	connectURL = getConnectURL()
	simulationFlag = getSimulationFlag()
	coalesceFlag = getCoalesceFlag()
	robotAddress = getRobotAddress()
	client = PacbotClient(connectURL, simulationFlag, coalesceFlag, robotAddress)
	await client.run()

	# Once the connection is closed, end the event loop
	loop = asyncio.get_event_loop()
	loop.stop()

if __name__ == '__main__':

	# Run the event loop forever
	loop = asyncio.new_event_loop()
	loop.create_task(main())
	loop.run_forever()