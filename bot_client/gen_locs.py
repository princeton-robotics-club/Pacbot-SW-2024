import json
import pprint
from fieldnodes import FIELD_NODES

QUAD_WIDTH  = 14
QUAD_HEIGHT = 15

pellet_arr = [
  '0000000000000000000000000000',
	'0111111111111001111111111110',
	'0100001000001001000001000010',
	'0100001000001001000001000010',
	'0100001000001001000001000010',
	'0111111111111111111111111110',
	'0100001001000000001001000010',
	'0100001001000000001001000010',
	'0111111001111001111001111110',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0000001000000000000001000000',
	'0111111111111001111111111110',
	'0100001000001001000001000010',
	'0100001000001001000001000010',
	'0111001111111001111111001110',
	'0001001001000000001001001000',
	'0001001001000000001001001000',
	'0111111001111001111001111110',
	'0100000000001001000000000010',
	'0100000000001001000000000010',
	'0111111111111111111111111110',
	'0000000000000000000000000000'
]

# parse pellet string
tupled_pellet_locs = []
for row, row_str in enumerate(pellet_arr):
  for col in range(len(row_str)):
    if row_str[col] == '1':
      tupled_pellet_locs.append((row, col))

quad_1 = []
quad_2 = []
quad_3 = []
quad_4 = []

for row, col in tupled_pellet_locs:
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

node_dict = [quad_1, quad_2, quad_3, quad_4]
pretty_json_str = pprint.pformat(node_dict, compact=True).replace("'", '"')

pretty_json_str = 'QUAD_PELLET_LOCS = ' + pretty_json_str

f = open('valid_pellet_locations.py', 'w')
f.write(pretty_json_str)
f.close()
