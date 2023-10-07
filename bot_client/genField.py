

field = [
    # 28 across
    0b0000_1111111111111111111111111111, # row 0
	0b0000_1000000000000110000000000001, # row 1
	0b0000_1011110111110110111110111101, # row 2
	0b0000_1011110111110110111110111101, # row 3
	0b0000_1011110111110110111110111101, # row 4
	0b0000_1000000000000000000000000001, # row 5
	0b0000_1011110110111111110110111101, # row 6
	0b0000_1011110110111111110110111101, # row 7
	0b0000_1000000110000110000110000001, # row 8
	0b0000_1111110111110110111110111111, # row 9
	0b0000_1111110111110110111110111111, # row 10
	0b0000_1111110110000000000110111111, # row 11
	0b0000_1111110110111111110110111111, # row 12
	0b0000_1111110110111111110110111111, # row 13
	0b0000_1111110000111111110000111111, # row 14
	0b0000_1111110110111111110110111111, # row 15
	0b0000_1111110110111111110110111111, # row 16
	0b0000_1111110110000000000110111111, # row 17
	0b0000_1111110110111111110110111111, # row 18
	0b0000_1111110110111111110110111111, # row 19
	0b0000_1000000000000110000000000001, # row 20
	0b0000_1011110111110110111110111101, # row 21
	0b0000_1011110111110110111110111101, # row 22
	0b0000_1000110000000000000000110001, # row 23
	0b0000_1110110110111111110110110111, # row 24
	0b0000_1110110110111111110110110111, # row 25
	0b0000_1000000110000110000110000001, # row 26
	0b0000_1011111111110110111111111101, # row 27
	0b0000_1011111111110110111111111101, # row 28
	0b0000_1000000000000000000000000001, # row 29
	0b0000_1111111111111111111111111111, # row 30
]



def main():
    rows = []
    # field.reverse()
    for row in field:
        new_row = [int(d) for d in format(int(row), '032b')]
        rows.append(new_row[4:])

    nodes = {}


    node = {
        'A': [('B', 200000)],
        'C': [('D', 200000)],
        'D': [('E', 200000)],
        'E': [('F', 200000)],
        'B': [('D', 200000)],
        'F': []
    }

    def check_node(rows, j, i):

        if i < 0 or j < 0 or i >= len(rows) or j >= len(rows[0]):
            return False
        
        if rows[i][j] == 0:
            return True
        
        return False
        

    def get_neighbors(rows, i, j):

        out = []

        if check_node(rows, j+1, i):
            out.append(('('+str(j+1)+','+str(i)+')', 1))

        if check_node(rows, j-1, i):
            out.append(('('+str(j-1)+','+str(i)+')', 1))

        if check_node(rows, j, i+1):
            out.append(('('+str(j)+','+str(i+1)+')', 1))

        if check_node(rows, j, i-1):
            out.append(('('+str(j)+','+str(i-1)+')', 1))


        if j == 23 and i == 12:
            print(out)

        return out

    for i, row in enumerate(rows):
        for j, col in enumerate(row):
            if col == 0:
                nodes['('+str(j)+','+str(i)+')'] = get_neighbors(rows, i, j)

    
    for i, row in enumerate(rows):
        row_row = []
        for j, col in enumerate(row):
            if rows[i][j]:
                row_row.append('*('+str(j)+','+str(i)+')')
            else:
                row_row.append('_('+str(j)+','+str(i)+')')
        print(row_row)


    print(nodes)

main()