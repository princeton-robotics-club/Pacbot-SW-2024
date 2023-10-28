# Asyncio (for concurrency)
import asyncio

# Other
from enum import IntEnum
import math
import os
from policies.astar.fieldnodes import FIELD_NODES
from policies.astar.basicAStar import BasicAStar


# Game state
from gameState import Directions, GameModes, GameState
from websockets.sync.client import ClientConnection # type: ignore



INFINITY = 99999999999

COMMAND_TO_BYTES = {
	Directions.RIGHT: b'd',
	Directions.LEFT: b'a',
	Directions.UP: b'w',
	Directions.DOWN: b's'
}

class DecisionStates(IntEnum):
	'''
	Enum of possible game modes
	'''

	SUPER_PELLET_CHASER  	= 0
	GHOST_CHASER		 	= 1
	SMALL_PELLET_CHASER   	= 2
	CHERRY_CHASER			= 3

class DecisionModule:
	'''
	Sample implementation of a decision module for high-level
	programming for Pacbot, using asyncio.
	'''

	def __init__(self, state: GameState, debug=True) -> None:
		'''
		Construct a new decision module object
		'''

		# Game state object to store the game information
		self.state = state

		# Debug
		self.debug = debug
		
		# Decision State
		# 0 = Super Pellet Hunter
		# 1 = Ghost Chaser
		self.decision_state = DecisionStates.SUPER_PELLET_CHASER

		# Game Info
		self.game_super_pellet_locs = [(1,23), (26,23), (1,3), (26,3)]

		# Last command
		self.last_command = None

		# field
		self.field_nodes = FIELD_NODES


	def _log(self, message: str, end='\n'):
		if self.debug:
			print('Decision Module: ' + message, end=end)

	def get_field_location(self, location):
		'''
		Convert location to a field node coordinate
		'''
		return '(' + str(location.col) + ',' + str(location.row) + ')'
	
	def get_distance(self, col1, row1, col2, row2):
		'''
		Calculate euclidian distnace between two points
		'''
		return math.sqrt((col1 - col2)**2 + (row1 - row2)**2)
	
	def calculate_edge_weight(self, prev_weight, distance_to_ghost, k=16):
		'''
		Calculate a weight value according to the inverse square distance to the nearest ghost
		'''
		return int(prev_weight + k * 1/(distance_to_ghost**2))
	
	def propagate_ghost_weights_helper(self, node, recursive_lvl=0, max_recrusive_lvl=5):
		# Base Case: hit the limit of recursive calls (saves computation time) 
		if recursive_lvl >= max_recrusive_lvl: return

		# Base Case: already made calculations for this node
		if node in self.visited_nodes: return

		# add this node as a visited node
		self.visited_nodes.add(node)

		new_edge_nodes = []
		for edge_node, weight in self.field_nodes[node]:
			# get distance to nearest dangerous ghost (TO FIX: other ghosts will be ignored)
			ghost = self.get_closest_dangerous_ghost()
			node_col, node_row = eval(edge_node) # if everything breaks maybe switch col and row
			if ghost:
				distance_to_ghost = max(self.get_distance(ghost.location.col, ghost.location.row, node_col, node_row), 1)
			else:
				distance_to_ghost = INFINITY


			# store the edge weights
			new_edge_nodes.append((edge_node, self.calculate_edge_weight(weight, distance_to_ghost)))

			# recursive call for each adjacent node (we only have to update the directed edges going away from the pacbot)
			self.propagate_ghost_weights_helper(edge_node, recursive_lvl=recursive_lvl+1)
		
		# update field
		self.field_nodes[node] = new_edge_nodes

	def propagate_ghost_weights(self):
		'''
		Update the weight of the edges in the field to reflect the positions of the pacbot relative to the ghosts
		'''
		# Remember to remove updated weights from last
		node 				= self.get_field_location(self.state.pacmanLoc)	# pacman location
		self.visited_nodes 	= set() # contains all of the visited nodes
		self.propagate_ghost_weights_helper(node)

	def clean_edge_weights(self):
		'''
		Based on edge weights that were changed for ghost location, resets all of them to original value
		'''

		if self.visited_nodes == None: return

		for node in self.visited_nodes:
			self.field_nodes[node] = FIELD_NODES[node]


	def game_get_closest_super_pellet(self):
		'''
		returns closest super pellet location
		'''
		if len(self.game_super_pellet_locs) == 0:
			return None
		closest_pellet = 0
		smallest_dist = INFINITY
		for i in range(len(self.game_super_pellet_locs)):
			dist = (self.state.pacmanLoc.col - self.game_super_pellet_locs[i][0]) ** 2 \
						+ (self.state.pacmanLoc.row - self.game_super_pellet_locs[i][0]) ** 2
			if dist < smallest_dist:
				smallest_dist = dist
				closest_pellet = i
		return '(' + str(self.game_super_pellet_locs[closest_pellet][0]) + ',' + str(self.game_super_pellet_locs[closest_pellet][1]) + ')'
	
	def get_closest_ghost(self):
		'''
		Get the closest ghost, note that this includes ghosts that are spawning, running away, or can eat pacbot
		'''
		closest_ghost = self.state.ghosts[0]
		smallest_dist = INFINITY
		for ghost in self.state.ghosts:
			dist = (self.state.pacmanLoc.col - ghost.location.col) ** 2 \
						+ (self.state.pacmanLoc.row - ghost.location.row) ** 2
			if dist < smallest_dist:
				smallest_dist = dist
				closest_ghost = ghost
		return closest_ghost
	
	def get_closest_dangerous_ghost(self):
		'''
		Returns the closest ghost that has the ability to eat the pacbot
		'''
		closest_ghost = None
		smallest_dist = INFINITY
		for ghost in self.state.ghosts:
			dist = (self.state.pacmanLoc.col - ghost.location.col) ** 2 \
						+ (self.state.pacmanLoc.row - ghost.location.row) ** 2
			if dist < smallest_dist and ghost.frightSteps == 0 and ghost.spawning == False:
				smallest_dist = dist
				closest_ghost = ghost
		return closest_ghost
	
	def game_get_closest_edible_ghost(self):
		'''
		Get the closest ghost that can be eaten (this does not include ghosts that are still spawning)
		'''
		closest_ghost = self.state.ghosts[0]
		smallest_dist = INFINITY
		for ghost in self.state.ghosts:
			dist = (self.state.pacmanLoc.col - ghost.location.col) ** 2 \
						+ (self.state.pacmanLoc.row - ghost.location.row) ** 2
			if dist < smallest_dist and ghost.frightSteps != 0 and ghost.spawning == False:
				smallest_dist = dist
				closest_ghost = ghost
		return '(' + str(closest_ghost.location.col) + ',' + str(closest_ghost.location.row) + ')'
		

	def decision_transition(self):
		# remove each pellet
		for i, super_pellet in enumerate(self.game_super_pellet_locs):
			if '(' + str(self.state.pacmanLoc.col) + ', ' + str(self.state.pacmanLoc.row) + ')' == str(super_pellet):
				del self.game_super_pellet_locs[i]

		# transition from super pellet hunter to ...
		if self.decision_state == DecisionStates.SUPER_PELLET_CHASER:
			# check if any ghosts are frightened
			for ghost in self.state.ghosts:
				if ghost.frightSteps != 0 and ghost.spawning == False:
					self.decision_state = DecisionStates.GHOST_CHASER
					break

		# transition from ghost hunter to ...
		elif self.decision_state == DecisionStates.GHOST_CHASER:
			change_state = True
			for ghost in self.state.ghosts:
				if ghost.frightSteps != 0 and ghost.spawning == False:
					change_state = False
					break
			if change_state == True:
				self.decision_state = DecisionStates.SUPER_PELLET_CHASER

	def get_target(self):
		'''
		Get the target to astar to
		'''
		# make a decision based on current state
		if self.decision_state == DecisionStates.SUPER_PELLET_CHASER:
			return self.game_get_closest_super_pellet()
		elif self.decision_state == DecisionStates.GHOST_CHASER:
			return self.game_get_closest_edible_ghost()
		return '(0,0)'
	
	def get_path(self, target):
		'''
		Given a target, generate a path to the target and return the first two nodes in the path
		'''
		# update field to reflect position of ghosts
		self.propagate_ghost_weights()

		# calcualte path
		path = BasicAStar(self.field_nodes).astar(self.get_field_location(self.state.pacmanLoc), target)
		first_two_nodes = []
		i = 0
		if path is not None:
			for p in path:
				if i < 2:
					first_two_nodes.append(p)
					i += 1

		# clean up field
		self.clean_edge_weights()

		return first_two_nodes
				
	def get_command_direction(self, curr, next) -> Directions:
		'''
		Given a current location and a next location, returns a byte string representing the command to send
		'''
		if curr[0] - next[0] == -1:
			return Directions.RIGHT
		elif curr[0] - next[0] == 1:
			return Directions.LEFT
		elif curr[1] - next[1] == -1:
			return Directions.DOWN
		return Directions.UP

	def connect(self, connection: ClientConnection) -> None:
		'''
		Connect to game engine server
		'''
		self.connection = connection

	def get_command(self):
		'''
		Generate one command for pacbot
		'''
		self.decision_transition()
		# print('Decision Module: pacloc - ' + str(self.state.pacmanLoc.col) + ", " + str(self.state.pacmanLoc.row))

		# make sure game is playing
		if self.state.gameMode == GameModes.PAUSED:
			return None

		# make sure pacman in field
		if self.state.pacmanLoc.col < 0 or self.state.pacmanLoc.col >= 32 \
			or self.state.pacmanLoc.row < 0 or self.state.pacmanLoc.row >= 28:
			return None

		# print('Decision Module: target - ' + str(target))
		# print('Decision Module: state - ' + str(self.decision_state))
		
		# get the next move
		target = self.get_target()
		path = self.get_path(target)


		# send one command
		# print('Decision Module: path - ' + str(path))
		if len(path) <= 1:
			self._log('no target')
			return None
		else:
			# avoid sending same command twice
			if self.last_command != None and self.last_command[0] == path[0] and self.last_command[1] == path[1]:
				self._log('avoid sending same command twice')
				return None
			else:
				curr = eval(path[0])
				next = eval(path[1])
				next_command = self.get_command_direction(curr, next)
				self.last_command = (path[0], path[1])
				return next_command

	
		
		

	async def decisionLoop(self) -> None:
		'''
		Decision loop for Pacbot
		'''

		# Receive values as long as we have access
		while self.state.isConnected():

			# WARNING: 'await' statements should be routinely placed
			# to free the event loop to receive messages, or the
			# client may fall behind on updating the game state!

			# Lock the game state
			self.state.lock()

			# print('decision module: ' + str(self.state.ghosts[0].location.col) + ',' + str(self.state.ghosts[0].location.row)) 

			# Make decisions for Pacbot
			command = self.get_command()
			self._log('command - ' + str(command))
			if command == None:
				self.state.unlock()
				await asyncio.sleep(0.1)
				continue

			# self.state.update(self.state.serialize(), lockOverride=True)

			# self.state.display()
			# print(self.state.simulateAction(3, command))
			# self.state.display()

			# Unlock the game state
			# self.state.unlock()

			# Writing back to the server, as a test (move right)
			self.state.writeServerBuf.append(COMMAND_TO_BYTES.get(command, b'd')) # default to d for now

			# Free up the event loop (a good chance to talk to the bot!)
			await asyncio.sleep(0.05) # 1000 previous

			# (REMOVE THIS) Unlock the game state
			self.state.unlock()