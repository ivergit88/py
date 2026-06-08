class LifeGame:
    EMPTY = 0
    ROCK = 1
    FISH = 2
    SHRIMP = 3

    def __init__(self, board: list[list[int]]):
        self._board = [row[:] for row in board]

    def get_next_generation(self) -> list[list[int]]:
        rows = len(self._board)
        cols = len(self._board[0]) if rows else 0
        next_board = [[self.EMPTY] * cols for _ in range(rows)]

        for i in range(rows):
            for j in range(cols):
                cell = self._board[i][j]

                if cell == self.ROCK:
                    next_board[i][j] = self.ROCK
                    continue

                fish_neigh = self._count_neighbours(i, j, self.FISH)
                shrimp_neigh = self._count_neighbours(i, j, self.SHRIMP)

                if cell == self.FISH:
                    next_board[i][j] = self.FISH if fish_neigh in (2, 3) else self.EMPTY
                elif cell == self.SHRIMP:
                    next_board[i][j] = self.SHRIMP if shrimp_neigh in (2, 3) else self.EMPTY
                else:
                    if fish_neigh == 3:
                        next_board[i][j] = self.FISH
                    elif shrimp_neigh == 3:
                        next_board[i][j] = self.SHRIMP
                    else:
                        next_board[i][j] = self.EMPTY

        self._board = next_board
        return self._board

    def _count_neighbours(self, i: int, j: int, kind: int) -> int:
        count = 0
        rows = len(self._board)
        cols = len(self._board[0])

        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni = i + di
                nj = j + dj
                if 0 <= ni < rows and 0 <= nj < cols and self._board[ni][nj] == kind:
                    count += 1

        return count
