#gameState import Location


# converts 2d to 1d for union
def flatten(row, col):
    return row * 28 + col

class UnionFind:
    """Weighted quick-union with path compression and connected components.
    The original Java implementation is introduced at
    https://www.cs.princeton.edu/~rs/AlgsDS07/01UnionFind.pdf
    >>> uf = UnionFind(10)
    >>> for (p, q) in [(3, 4), (4, 9), (8, 0), (2, 3), (5, 6), (5, 9),
    ...                (7, 3), (4, 8), (6, 1)]:
    ...     uf.union(p, q)
    >>> uf._id
    [8, 3, 3, 3, 3, 3, 3, 3, 3, 3]
    >>> uf.find(0, 1)
    True
    >>> uf._id
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
    """

    def __init__(self, n):
        self._id = list(range(n))
        self._sz = [1] * n
        self.cc = n  # connected components
        self._largest_size_id = 0

    def _root(self, i):
        j = i
        while (j != self._id[j]):
            self._id[j] = self._id[self._id[j]]
            j = self._id[j]
        return j

    def find(self, p, q):
        return self._root(p) == self._root(q)

    def union(self, p, q):
        i = self._root(p)
        j = self._root(q)
        if i == j:
            return
        if (self._sz[i] < self._sz[j]):
            self._id[i] = j
            self._sz[j] += self._sz[i]

            if (self._sz[self._largest_size_id] < self._sz[j]):
                self._largest_size_id = j
        else:
            self._id[j] = i
            self._sz[i] += self._sz[j]

            if (self._sz[self._largest_size_id] < self._sz[i]):
                self._largest_size_id = i
        self.cc -= 1

    def union_grid(self, row1: int, col1: int, row2: int, col2: int):
        self.union(flatten(row1, col1), flatten(row2, col2))


#u = UnionFind(5)
#print(u._id)
#print(u._sz)
#u.union(3, 0)
#u.union(1, 0)
#print(u._id)
#print(u._sz)
#print(u._largest_size_id)