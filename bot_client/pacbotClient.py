# JSON (for reading config.json)
import json

# Asyncio (for concurrency)
import asyncio

# typing for event handlers
from typing import Any, Awaitable, Callable, Coroutine, List

# Websockets (for communication with the server)
from websockets.sync.client import connect, ClientConnection # type: ignore
from websockets.exceptions import ConnectionClosedError # type: ignore
from websockets.typing import Data # type: ignore

# Game state
from shared import States
from gameState import GameState

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

	# Return the websocket connect address
	return config["PythonSimulation"]

# Get the robot address from the config.json file
def getRobotAddress() -> tuple[str, int]:

	# Read the configuration file
	with open('../config.json', 'r', encoding='UTF-8') as configFile:
		config = json.load(configFile)

	# Return the websocket connect address
	return config["RobotIP"], config['RobotPort']

class PacbotClient:
	'''
	Sample implementation of a websocket client to communicate with the
	Pacbot game server, using asyncio.
	'''

	def __init__(self, connectURL: str, simulationFlag: bool, robotAddress: tuple[str, int]) -> None:
		'''
		Construct a new Pacbot client object
		'''

		# Connection URL (starts with ws://)
		self.connectURL: str = connectURL

		# Simulation flag (bool)
		self.simulationFlag: bool = simulationFlag

		# Robot IP and port
		self.robotIP: str = robotAddress[0]
		self.robotPort: int = robotAddress[1]

		# Private variable to store whether the socket is open
		self._socketOpen: bool = False

		# Connection object to communicate with the server
		self.connection: ClientConnection

		# Game state object to store the game information
		self.state: GameState = GameState()

		# Robot socket (comms) to dispatch low-level commands
		self.robotSocket: RobotSocket = RobotSocket(self.robotIP, self.robotPort)

		# Decision module (policy) to make high-level decisions
		self.decisionModule: DecisionModule = DecisionModule(self.state)

		# CV update event subscribers
		self._cvUpdateEventSubscribers: List[Callable[[],  Awaitable[Any]]] = []
		self.registerCvUpdateHandler(self.decisionModule.cvUpdateEventHandler)

		# Done event subscribers
		self._doneEventSubscribers: List[Callable[[bool],  Awaitable[Any]]] = []
		self.registerDoneHandler(self.doneEventHandler) # example of registering a subscriber
		self.registerDoneHandler(self.decisionModule.doneEventHandler)

		# Gate for sending messages
		self._hasSent = False


		self.stateMachine: States = States.NONE



	""" Incoming CV information event """
	async def notifyCvUpdateEvent(self):
		# print("PacbotClient - Event: CV Update - pacbot location has changed")
		for handler in self._cvUpdateEventSubscribers:
			await handler()

	def registerCvUpdateHandler(self, handler: Callable[[],  Coroutine[Any, Any, None]]):
		self._cvUpdateEventSubscribers.append(handler)

	def unRegisterCvUpdateHandler(self, handler: Callable[[],  Coroutine[Any, Any, None]]):
		self._cvUpdateEventSubscribers.remove(handler)

	""" PB Done moving event """
	async def notifyDoneEvent(self, done: bool):
		# print("PacbotClient - Event: Done Update - " + str(done))
		for handler in self._doneEventSubscribers:
			await handler(done)

	def registerDoneHandler(self, handler: Callable[[bool], Awaitable[Any]]):
		self._doneEventSubscribers.append(handler)

	def unRegisterDoneHandler(self, handler: Callable[[bool], Awaitable[Any]]):
		self._doneEventSubscribers.remove(handler)
	


	async def doneEventHandler(self, newDone: bool):
		if newDone:
			print("PacbotClient - Event: Pacbot needs a new command ")
			# print("get locked doneEventHandler")
			while (self.state.isLocked()):
				await asyncio.sleep(0)
			self.state.lock()
			self._hasSent = False
			self.state.writeServerBuf.clear()
			self.state.unlock()


			if self.stateMachine == States.WAITING_ACK:
				self.updateStateMachine()


			# await self.decisionModule.decisionNoLoop()

			# print("release locked doneEventHandler")
			# print(f'{RED}robot just told us it\'s done{NORMAL}')
		else:
			# print(f'{GREEN}robot has started executing{NORMAL}')
			pass

	# triggers when cv sees pb in new loc
	async def cvUpdateEventHandler(self):
		if self.stateMachine == States.WAITING_GME:
			self.updateStateMachine()
			

	# forwards the game state from its current state
	def updateStateMachine(self):
		if self.stateMachine == States.WAITING_GME:
			self.stateMachine = States.WAITING_AST
		elif self.stateMachine == States.WAITING_AST:
			self.stateMachine = States.WAITING_SEND
		elif self.stateMachine == States.WAITING_SEND:
			self.stateMachine = States.WAITING_GME

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

		pacRow: int = -1
		pacCol: int = -1

		# Receive values as long as the connection is open
		while self.isOpen():
			

			# if self.stateMachine != States.WAITING_GME:
			# 	await asyncio.sleep(0)
			# 	continue

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
				# TODO: why is there no lock here??
				self.state.update(messageBytes)
				# print(f'{CYAN}update from cv:{NORMAL} time={self.state.currTicks}', self.state.pacmanLoc.row, self.state.pacmanLoc.col)

				# Notify subscribers of a CV update event AFTER state has updated
				newRow = self.state.pacmanLoc.row
				newCol = self.state.pacmanLoc.col
				if pacRow != newRow or pacCol != newCol:
					pacRow = newRow
					pacCol = newCol
					await self.notifyCvUpdateEvent()

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
			print("Simulation Mode: No Robot")
			return

		# Keep track if the first iteration has taken place
		firstIt = True

		# keep track of when robot is needs more instructions
		needsNewInstructionOld = False
		oldMsg:bytes=bytes()
		oldRow:int=0
		oldCol:int=0
		oldDist:int=0

		# Keep sending messages as long as the server connection is open
		while self.isOpen():

			# if self.stateMachine != States.WAITING_ACK:
			# 	await asyncio.sleep(0)
			# 	print("\t]comms")
			# 	continue

			# Try to receive messages (and skip to except in case of an error)
			try:

				# notify request for new instruction
				needsNewInstruction = self.robotSocket.wait()
				# edge
				if needsNewInstruction != needsNewInstructionOld:
					# rising edge
					# if needsNewInstruction:
					# 	# notify change - awaiting a coroutine (not creating a new task) justification here: https://stackoverflow.com/a/55766474
					# 	await self.notifyDoneEvent(True)

					await self.notifyDoneEvent(needsNewInstruction)
					
					needsNewInstructionOld = needsNewInstruction

            		
				# Handle first iteration (flush)
				if firstIt:
					self.robotSocket.start()
					# print("get lock commsLoop")
					while (self.state.isLocked()):
						await asyncio.sleep(0)
					self.state.lock()
					self.robotSocket.flush(self.state.pacmanLoc.row, self.state.pacmanLoc.col)
					needsNewInstructionOld = False
					self.state.unlock()
					# print("release lock commsLoop")
					firstIt = False

				# Otherwise, send out relevant messages
				else:
					if not self._hasSent: # has not sent yet

						if self.state.writeServerBuf and self.state.writeServerBuf[0].tick():
							print("sending new command=============")
							srvmsg: ServerMessage = self.state.writeServerBuf.popleft()
							msg = srvmsg.getBytes()
							dist, row, col = srvmsg.dist, srvmsg.row, srvmsg.col
							self.robotSocket.moveNoCoal(msg, row, col, dist)

							oldMsg, oldRow, oldCol, oldDist = (msg, row, col, dist)
							self._hasSent = True # one message at a time
							needsNewInstructionOld = False
							if self.state.writeServerBuf:
								self.state.writeServerBuf[0].skipDelay()
					else: # already has sent
						self.robotSocket.moveNoCoal(oldMsg, oldRow, oldCol, oldDist, updateSeq=False)

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
	robotAddress = getRobotAddress()
	client = PacbotClient(connectURL, simulationFlag, robotAddress)
	await client.run()

	# Once the connection is closed, end the event loop
	loop = asyncio.get_event_loop()
	loop.stop()

if __name__ == '__main__':

	# Run the event loop forever
	loop = asyncio.new_event_loop()
	loop.create_task(main())
	loop.run_forever()