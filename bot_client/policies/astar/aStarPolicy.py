# Heap Queues
from heapq import heappush, heappop

# Game state
from gameState import *

# Location mapping
import policies.astar.genPachattanDistDict as pacdist
import policies.astar.example as ex

# Big Distance
INF = 999999

# Maximum Buffer size for sending things out
MAX_OUT_QUEUE_SIZE = 6

# Maximum size of path that will be explored
MAX_PATH_SIZE = 6 # TODO: make this dynamic by allowing straighter paths to be longer??

# Asyncio (for concurrency)
import asyncio

'''
Cost Explanations:

Started at point	S
Targetting point 	T
Currently at point 	C

gcost = cost from S to C (past, known)
hcost = cost from C to T (future, predicted)

fcost = gcost + hcost

Start-------Current-------Target
S--------------C---------------T
|-----gcost----|-----hcost-----|
|------------fcost-------------|
'''

class DistTypes(IntEnum):
	'''
	Enum of distance types
	'''
	MANHATTAN_DISTANCE = 0
	EUCLIDEAN_DISTANCE = 1
	PACHATTAN_DISTANCE = 2

# Create new location with row, col
def newLocation(row: int, col: int, state: GameState):
	'''
	Construct a new location state
	'''
	result = Location(state)
	result.row = row
	result.col = col
	return result

# Manhattan distance
def distL1(loc1: Location, loc2: Location) -> int:
	return abs(loc1.row - loc2.row) + abs(loc1.col - loc2.col)

# Manhattan distance
def distSqL1(loc1: Location, loc2: Location) -> int:
	dr = abs(loc1.row - loc2.row)
	dc = abs(loc1.col - loc2.col)
	return dr*dr + dc*dc

# Squared Euclidean distance
def distSqL2(loc1: Location, loc2: Location) -> int:
	return (loc1.row - loc2.row) * (loc1.row - loc2.row) + \
		(loc1.col - loc2.col) * (loc1.col - loc2.col)

# Euclidean distance
def distL2(loc1: Location, loc2: Location) -> int:
	return ((loc1.row - loc2.row) * (loc1.row - loc2.row) + \
		(loc1.col - loc2.col) * (loc1.col - loc2.col)) ** 0.5

# Pachattan distance
def distL3(loc1: Location, loc2: Location) -> int:
	key = pacdist.getKey(loc1, loc2)
	return ex.PACHATTAN[key]

# Squared Pachattan distance
def distSqL3(loc1: Location, loc2: Location) -> int:
	pacDist = distL3(loc1, loc2)
	return pacDist * pacDist


class AStarNode:
	'''
	Node class for running the A-Star Algorithm for Pacbot.
	'''

	def __init__(
		self,
		compressedState: GameStateCompressed,
		fCost: int,
		gCost: int,
		directionBuf: list[tuple[Directions, Location]],
		delayBuf: list[int],
		bufLength: int,
		victimCaught: bool = False,
		targetCaught: bool = False
	) -> None:

		# Compressed game state
		self.compressedState = compressedState

		# Costs
		self.fCost = fCost
		self.gCost = gCost

		# Estimated velocity
		self.estSpeed = 0
		self.direction = Directions.NONE

		# Message buffer
		self.directionBuf: list[tuple[Directions, Location]] = directionBuf
		self.delayBuf = delayBuf
		self.bufLength = bufLength

		# Victim color (catching scared ghosts)
		self.victimCaught: bool = victimCaught

		# Determines whether the target was caught
		self.targetCaught: bool = targetCaught

	def __lt__(self, other) -> bool: # type: ignore
		return self.fCost < other.fCost # type: ignore

	def __repr__(self) -> str:
		return str(f'g = {self.gCost} ~ f = {self.fCost}')

class AStarPolicy:
	'''
	Policy class for running the A-Star Algorithm for Pacbot.
	'''

	def __init__(
		self,
		state: GameState,
		target: Location,
		distType: DistTypes = DistTypes.PACHATTAN_DISTANCE,
		coalesceFlag: bool = False
	) -> None:

		# Game state
		self.state: GameState = state
		self.stateCopy: GameState = state

		# Do coalesce
		self.coalesceFlag: bool = coalesceFlag

		# Target location
		self.target: Location = target

		# Expected location
		self.expectedLoc: Location = newLocation(23, 13, self.state)
		self.error_sum = 0
		self.error_count = 0
		self.dropped_command_count = 0

		# Distance metrics
		self.distType = distType
		match self.distType:
			case DistTypes.MANHATTAN_DISTANCE:
				self.dist = distL1
				self.distSq = distSqL1
			case DistTypes.EUCLIDEAN_DISTANCE:
				self.dist = distL2
				self.distSq = distSqL2
			case DistTypes.PACHATTAN_DISTANCE:
				self.dist = distL3
				self.distSq = distSqL3

	def getNearestPellet(self) -> Location:

		# Check bounds
		first = self.state.pacmanLoc
		if self.state.wallAt(first.row, first.col):
			return self.state.pacmanLoc

		#  BFS traverse
		queue = [first]
		visited = {first.hash()}
		while queue:

			# pop from queue
			currLoc = queue.pop(0)

			# Base Case: Found a pellet
			if self.state.pelletAt(currLoc.row, currLoc.col) and not self.state.superPelletAt(currLoc.row, currLoc.col):
				return currLoc

			# Loop over the directions
			for direction in Directions:

				# If the direction is none, skip it
				if direction == Directions.NONE:
					continue

				# Increment direction
				nextLoc = Location(self.state)
				nextLoc.col = currLoc.col
				nextLoc.row = currLoc.row
				nextLoc.setDirection(direction)
				valid = nextLoc.advance() and not self.state.superPelletAt(nextLoc.row, nextLoc.col)

				# avoid same node twice and check this is a valid move
				if nextLoc.hash() not in visited and valid:
					queue.append(nextLoc)
					visited.add(nextLoc.hash())

		#print('No nearest...')
		return first

	def scaryVictim(self, victimColor: GhostColors) -> bool:

		V = self.state.ghosts[victimColor]

		if (victimColor == GhostColors.NONE) or self.state.wallAt(V.location.row, V.location.col):
			return False

		if (V.spawning):
			return True

		for color in GhostColors:
			G = self.state.ghosts[color]
			if (color != victimColor) and (not G.spawning) and (not G.isFrightened()):
				if not self.state.wallAt(G.location.row, G.location.col):
					if self.dist(V.location, G.location) <= 2:
						#print('re-assigning victim')
						return True

		return False

	def getNearestVictim(self) -> GhostColors:

		closest, closestDist = GhostColors.NONE, INF
		for color in GhostColors:
			if self.state.ghosts[color].isFrightened() and not self.state.ghosts[color].spawning:
				dist = self.dist(self.state.pacmanLoc, self.state.ghosts[color].location)
				if dist < closestDist and not self.scaryVictim(color):
					closest = color
					closestDist = dist

		# Return the closest scared ghost
		return closest

	def hCostExtend(self, gCost: int, bufLen: int, victimColor: GhostColors) -> int:
		'''
		Extends the existing g_cost delta to estimate a new h-cost due to
		distance Pachattan distance and estimated speed
		'''

		# make sure pacman in bounds
		if 0 > self.state.pacmanLoc.row or 32 <= self.state.pacmanLoc.row or 0 > self.state.pacmanLoc.col or 28 <= self.state.pacmanLoc.col:
			return 999999999

		# Dist to target
		distTarget: int = self.dist(self.state.pacmanLoc, self.target)
		if (distTarget == 0):
			return -10000000

		# Dist to nearest scared ghost
		distScared: int = INF
		if victimColor != GhostColors.NONE and not self.state.ghosts[victimColor].spawning:
			distScared = self.dist(self.state.pacmanLoc, self.state.ghosts[victimColor].location)

		# Dist to fruit
		distFruit: int = 999999
		if self.state.fruitSteps > 0:
			distFruit = self.dist(self.state.pacmanLoc, self.state.fruitLoc)

		# Distance to our chosen target: the minimum
		dist: int = distScared if (distScared < INF) else (distTarget if (distTarget < distFruit // 20) else distFruit)
		gCostPerStep: float = 2

		# If the buffer is too small, then the gCostPerStep should be 2 on average
		if bufLen >= 4:
			gCostPerStep = gCost / bufLen

		# Return the result: (g-cost) / (buffer length) * (dist to target)
		return int(gCostPerStep * dist)

	def fCostMultiplier(self) -> float:

		# Constant for the multiplier
		K: int = 128

		# Multiplier addition term
		multTerm: int = 0

		# Location of the ghost lair
		lairLoc: Location = Location(self.state)
		lairLoc.row = 11
		lairLoc.col = 13

		# Check if any ghosts are frightened
		fright = False
		for ghost in self.state.ghosts:
			if ghost.isFrightened():
				fright = True

		# Calculate closest non-frightened ghost
		for ghost in self.state.ghosts:
			if not ghost.spawning:
				if not ghost.isFrightened():
					multTerm += int(
						K >> self.dist(self.state.pacmanLoc, ghost.location)
					)
			elif not fright and not self.state.wallAt(self.state.pacmanLoc.row, self.state.pacmanLoc.col):
				multTerm += int(
					K >> self.dist(self.state.pacmanLoc, lairLoc)
				)

		# Return the multiplier (1 + constant / distance squared)
		return 1 + multTerm

	def selectTarget(self, pelletTarget: Location) -> None:

		chase = self.state.gameMode == GameModes.CHASE

		if chase:
			# # check if top left pellet exists
			# if self.state.superPelletAt(3, 1):
			# 	self.target = newLocation(5, 1, self.state)

			# # check if top right pellet exists
			# elif self.state.superPelletAt(3, 26):
			# 	self.target = newLocation(5, 26, self.state)

			# check if bottom left pellet exists
			if self.state.superPelletAt(23, 1):
				self.target = newLocation(20, 3, self.state)

			# check if bottom right pellet exists
			elif self.state.superPelletAt(23, 26):
				self.target = newLocation(20, 24, self.state)



			# no super pellet
			else:
				# target the nearest pellet
				self.target = pelletTarget

		# no super pellets
		else:
			# # check if top left pellet exists
			# if self.state.superPelletAt(3, 1):
			# 	self.target = newLocation(5, 1, self.state)

			# # check if top right pellet exists
			# elif self.state.superPelletAt(3, 26):
			# 	self.target = newLocation(5, 26, self.state)

			# check if bottom left pellet exists
			# if self.state.superPelletAt(23, 1):
			# 	self.target = newLocation(20, 3, self.state)

			# # check if bottom right pellet exists
			# elif self.state.superPelletAt(23, 26):
			# 	self.target = newLocation(20, 24, self.state)

			# else:
			# 	# target the nearest pellet
			self.target = pelletTarget


	def sendMessage(self, currNode: AStarNode, victimColor: GhostColors, pelletTarget: Location)  -> tuple[bool, GhostColors, Location]:

		# coalesce movements (data prep)
		movements: list[list[int | Directions]] = []
		prevDir: Directions = Directions.NONE
		for index in range(len(currNode.directionBuf)):
			if self.coalesceFlag and prevDir == currNode.directionBuf[index][0] and prevDir != Directions.NONE:
				movements[-1][2] += 1
			else:
				# print("Appending " + currNode.directionBuf[index][1].row + " " + currNode.directionBuf[index][1].col)
				movements.append([
					currNode.delayBuf[index] - (index == 0),
					currNode.directionBuf[index][0],
					1,
					currNode.directionBuf[index][1].row,
					currNode.directionBuf[index][1].col
				])

			prevDir = currNode.directionBuf[index][0]

		# If the g-cost of this node is high enough or we reached the target,
		# make the moves and return
		if currNode.victimCaught:
			# queue actions
			for index in range(min(len(movements), MAX_OUT_QUEUE_SIZE)):
				self.state.queueAction(*movements[index])

			print("queueA length: ", len(self.state.writeServerBuf))

			if currNode.targetCaught:
				pelletTarget = self.getNearestPellet()

			return True, victimColor, pelletTarget

		elif currNode.targetCaught and (victimColor == GhostColors.NONE):
			# queue actions
			for index in range(min(len(movements), MAX_OUT_QUEUE_SIZE)):
				self.state.queueAction(*movements[index])

			print("queueB length: ", len(self.state.writeServerBuf))

			pelletTarget = self.getNearestPellet()
			return True, GhostColors.NONE, pelletTarget

		if currNode.bufLength >= 6:
			# queue actions
			for index in range(min(len(movements), MAX_OUT_QUEUE_SIZE)):
				self.state.queueAction(*movements[index])

			print("queueC length: ", len(self.state.writeServerBuf))

			return True, victimColor, pelletTarget

		return False, GhostColors.NONE, pelletTarget


	async def act(self, predicted_delay: int, victimColor: GhostColors, pelletTarget: Location) -> tuple[GhostColors, Location]:

		print("STARTING A*")
		print(f"we think we're at ({self.state.pacmanLoc.row}, {self.state.pacmanLoc.col})")

		# Make a priority queue of A-Star Nodes
		priorityQueue: list[AStarNode] = []

		# Construct an initial node
		initialNode = AStarNode(
			compressGameState(self.state),
			fCost = self.hCostExtend(0, 0, victimColor),
			gCost = 0,
			directionBuf = [],
			delayBuf = [],
			bufLength = 0
		)
		print("pacbot is at: " + str(self.state.pacmanLoc))

		# Add the initial node to the priority queue
		heappush(priorityQueue, initialNode)

		# Select a target
		self.selectTarget(pelletTarget)

		# Select a victim, if applicable
		victimCaught = (victimColor != GhostColors.NONE) and ((not self.state.ghosts[victimColor].isFrightened()) or self.state.ghosts[victimColor].spawning)
		if victimColor == GhostColors.NONE or self.scaryVictim(victimColor) or victimCaught:
			victimColor = self.getNearestVictim()

		# Select a new target, if applicable
		targetCaught = self.state.wallAt(pelletTarget.row, pelletTarget.col) or not self.state.pelletAt(pelletTarget.row, pelletTarget.col) or self.state.fruitLoc.at(self.state.pacmanLoc.row, self.state.pacmanLoc.col)
		if targetCaught:
			pelletTarget = self.getNearestPellet()

		# Flag for first iteration
		firstIt = True

		# Lag for first iteration
		firstItLag = 0

		# Lag for turns
		turnLag = 0

		# Keep proceeding until a break point is hit
		while len(priorityQueue):

			# Pop the lowest f-cost node
			currNode = heappop(priorityQueue)

			# Reset to the current compressed state
			decompressGameState(self.state, currNode.compressedState)

			# check if we should keep computing or stop
			doReturn, ghostColors, pelletTarget = self.sendMessage(currNode, victimColor, pelletTarget)
			if doReturn:
				return ghostColors, pelletTarget

			# Get Pacman's current direction
			prevDir = self.state.pacmanLoc.getDirection()

			# Determines if waiting (none) is allowed as a move
			waitAllowed = (victimColor == GhostColors.NONE)

			# Loop over the directions
			for direction in Directions:

				# If direction is none, continue
				if (direction == Directions.NONE) and (not waitAllowed):
					continue

				# Reset to the current compressed state
				decompressGameState(self.state, currNode.compressedState)

				turnPenalty = 0
				evadePenalty = 0
				if (prevDir != direction):
					turnPenalty = 1

					if (victimColor != GhostColors.NONE) and not self.state.ghosts[victimColor].spawning:

						loc: Location = Location(self.state)
						loc.update(self.state.pacmanLoc.serialize())
						loc.setDirection(direction)
						dist1 = self.dist(loc, self.state.ghosts[victimColor].location)
						loc.advance()
						dist2 = self.dist(loc, self.state.ghosts[victimColor].location)

						if (dist1 < dist2):
							evadePenalty = 10

				# get curr location
				currLoc = self.state.pacmanLoc

				# TODO: calculate a turn penalty based on the amount of previous movements in the same direction (like prevDir but for multiple nodes) to add to sim time

				npBefore = self.state.numPellets()
				nspBefore = self.state.numSuperPellets()
				valid = self.state.simulateAction(predicted_delay + firstItLag * firstIt + turnPenalty * turnLag, direction)
				npAfter = self.state.numPellets()
				nspAfter = self.state.numSuperPellets()
				ateNormalPellet = (npBefore > npAfter) and (nspBefore == nspAfter)

				# Determines if the target was caught
				targetCaught = self.state.wallAt(pelletTarget.row, pelletTarget.col) or \
					(not self.state.pelletAt(pelletTarget.row, pelletTarget.col)) or \
					pelletTarget.at(self.state.pacmanLoc.row, self.state.pacmanLoc.col) or \
					(self.state.fruitLoc.at(self.state.pacmanLoc.row, self.state.pacmanLoc.col))

				# Determines if the scared ghost 'victim' was caught
				victimCaught = (victimColor != GhostColors.NONE) and \
					((not self.state.ghosts[victimColor].isFrightened()) or self.state.ghosts[victimColor].spawning)

				# Select a new target
				self.selectTarget(pelletTarget)

				# Determine if there is a frightened ghost to chase
				victimExists = (victimColor == GhostColors.NONE)

				# If the state is valid, add it to the priority queue
				if valid:
					# targetLoc = Location(self.state)
					# targetLoc.row = self.state.pacmanLoc.row
					# targetLoc.col = self.state.pacmanLoc.col
					targetLoc = Location(self.state)
					targetLoc.row = currLoc.row
					targetLoc.col = currLoc.col

					nextNode = AStarNode(
						compressGameState(self.state),
						fCost = int((self.hCostExtend(currNode.gCost, currNode.bufLength, victimColor) + currNode.gCost + 1) * self.fCostMultiplier()),
						gCost = currNode.gCost + 2 + 2 * ((not ateNormalPellet) and (victimExists)) + 2 * (turnPenalty and victimExists) + 5 * evadePenalty,
						directionBuf = currNode.directionBuf + [(direction, targetLoc)],
						delayBuf = currNode.delayBuf + [predicted_delay + firstItLag * firstIt + turnPenalty * turnLag],
						bufLength = currNode.bufLength + 1,
						victimCaught = victimCaught,
						targetCaught = targetCaught
					)

					# Add the next node to the priority queue
					heappush(priorityQueue, nextNode)

			firstIt = False

			await asyncio.sleep(0)

		print("Trapped...")
		return victimColor, pelletTarget