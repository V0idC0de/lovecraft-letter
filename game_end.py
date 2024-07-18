class GameOverException(Exception):
    def __init__(self, winner):
        self.winner = winner
        super().__init__(f"Game Over. Winner: {winner.name}")
