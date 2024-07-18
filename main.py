import gamestate


def main():
    try:
        game = gamestate.Gamestate()
        while True:
            game.process_turn()
    except gamestate.GameOverException as e:
        if e.winner is None:
            print("Game Over - Game is a Draw!")
        else:
            print(f"Game Over - Winner: {e.winner.name}")
        print(f"Winner is{' not' if e.winner not in game.players_mad else ''} mad!")


if __name__ == '__main__':
    main()
