import json
from fieldnodes import FIELD_NODES

QUAD_WIDTH  = 14
QUAD_HEIGHT = 15

all_pellet_keys = FIELD_NODES.keys()

tupled_pellet_loces = []
for p_key in all_pellet_keys:
  p_key = p_key.removeprefix('(')
  p_key = p_key.removesuffix(')')
  row, col = p_key.split(',')
  row = int(row)
  col = int(col)

  tupled_pellet_loces.append((row, col))

quad_1 = []
quad_2 = []
quad_3 = []
quad_4 = []

for row, col in tupled_pellet_loces:
  # quadrant 1 (topleft)
  if row <= QUAD_HEIGHT and col <= QUAD_WIDTH:
    quad_1.append((row, col))

  # quadrant 2 (topright)
  if row <= QUAD_HEIGHT and col > QUAD_WIDTH:
    quad_2.append((row, col))

  # quadrant 3 (bottomleft)
  if row > QUAD_HEIGHT and col <= QUAD_WIDTH:
    quad_3.append((row, col))

  # quadrant 4 (bottom right)
  if row > QUAD_HEIGHT and col > QUAD_WIDTH:
    quad_4.append((row, col))

f = open('valid_pellet_locations.py', 'w')
f.write(json.dumps({'Q1':quad_1, 'Q2':quad_2, 'Q3':quad_3, 'Q4':quad_4}))
f.close()
