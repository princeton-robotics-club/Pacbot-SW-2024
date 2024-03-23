class QuadNode:
	def __init__(self, bounds:tuple):
		self._CAPACITY_LIMIT : int = 4
		self.count : int = 0
		self.subdivided : bool = False
		self.nw : QuadNode = None
		self.ne : QuadNode = None
		self.sw : QuadNode = None
		self.se : QuadNode = None
		self.pellets : list = []
		self.bounds : tuple = bounds

	def contains_pos(self, row, col):
		x, y, w, h = self.bounds
		return y <= row < y + h and x <= col < x + w

	def _give_to_child(self, row, col):
		if self.nw.contains_pos(row, col):
			self.nw.insert(row, col)

		if self.ne.contains_pos(row, col):
			self.ne.insert(row, col)

		if self.sw.contains_pos(row, col):
			self.sw.insert(row, col)

		if self.se.contains_pos(row, col):
			self.se.insert(row, col)


	def insert(self, row, col):
		if len(self.pellets) == self._CAPACITY_LIMIT and not self.subdivided and self.bounds[3] // 2 > self._CAPACITY_LIMIT:
			self.subdivide()

			for pellet in self.pellets:
				self._give_to_child(*pellet)

			self._give_to_child(row, col)

			return

		self.pellets.append((row, col))

	def subdivide(self):
		self.subdivided = True
		x, y, w, h = self.bounds

		half_w = w // 2
		half_h = h // 2

		self.nw = QuadNode((x, y, half_w, half_h))
		self.ne = QuadNode((x + half_w, y, half_w, half_h))
		self.sw = QuadNode((x, y + half_h, half_w, half_h))
		self.se = QuadNode((x + half_w, y + half_h, half_w, half_h))

	def remove(self, row, col):
		if self.subdivided:
			if self.nw.contains_pos(row, col):
				self.nw.remove(row, col)
			if self.ne.contains_pos(row, col):
				self.ne.remove(row, col)
			if self.sw.contains_pos(row, col):
				self.sw.remove(row, col)
			if self.ne.contains_pos(row, col):
				self.ne.remove(row, col)

			self.count = self.nw.count + self.ne.count + self.sw.count + self.se.count

			if self.count == 0:
				self.nw = None
				self.ne = None
				self.sw = None
				self.se = None
				self.subdivided = False

			return

		self.pellets.remove((row, col))
		self.count -= 1