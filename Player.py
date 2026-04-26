from Board import Board

class Player:
    def __init__(self, name):
        self.name = name
        self.board = Board(10)

    def attack(self, opponent_board, x, y):
        return opponent_board.attack(x, y)
