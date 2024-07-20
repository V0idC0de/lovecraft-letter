class RoundEndException(Exception):
    def __init__(self, winner):
        self.winner = winner
        super().__init__(f"Round is over. Winner: {winner.name}")


class GameOverException(Exception):
    def __init__(self, winner):
        self.winner = winner
        super().__init__(f"Game is over. Winner: {winner.name}")
