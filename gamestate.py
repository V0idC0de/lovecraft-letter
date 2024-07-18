import random
from typing import Callable

from colorama import Fore
from card import Card, CARD_NAMES
from game_end import GameOverException
from player import Player


class Gamestate:
    deck: list[Card]
    banished_cards: list[Card]
    players: list[Player]
    players_out: set[Player]
    players_mad: set[Player]
    players_protected: set[Player]
    player_on_turn_start: dict[Player, list[Callable[["Gamestate"], None]]]
    turn_player: Player
    hands: dict[Player, list[Card]]
    discard_pile: dict[Player, list[Card]]
    scores: dict[Player, tuple[int, int]]

    @property
    def players_in_game(self) -> list[Player]:
        return [player for player in self.players if player not in self.players_out]

    def __init__(self):
        self.players = [Player("Player 1"), Player("Player 2")]
        self.scores = {player: (0, 0) for player in self.players}
        self.initialize_game()

    def initialize_game(self) -> None:
        with open("deck.txt") as f:
            deck_cards = [tuple(line.strip().split(maxsplit=1)) for line in f.readlines()
                          if not line.strip().startswith("#") and line.strip()]
        self.deck = sum(([Card(code)] * int(n) for n, code in deck_cards if code in CARD_NAMES.keys()), [])
        self.banished_cards = []
        self.players_mad = set()
        self.players_out = set()
        self.players_protected = set()
        self.player_on_turn_start = {}
        self.turn_player = self.players[0]
        self.hands = {player: [] for player in self.players}
        self.discard_pile = {player: [] for player in self.players}

        self.shuffle_deck()
        for player in self.players:
            self.draw_card(player)

    def shuffle_deck(self) -> None:
        print(f"{Fore.CYAN}Shuffling deck...{Fore.RESET}")
        random.shuffle(self.deck)

    def process_turn(self):
        print(f"{Fore.YELLOW}{self.turn_player.name}'s turn{Fore.RESET}")

        # Draw a card
        if len(self.deck) == 0:
            self.deck_out_of_cards()
        self.draw_card(self.turn_player)

        # Select card to play and play
        for card in self.hands[self.turn_player]:
            self.print_card(card)
        card_to_play = self.select_card_from(self.hands[self.turn_player])
        # TODO: Select normal or madness effect

        # Play card
        print(f"{Fore.YELLOW}{self.turn_player.name} plays \"{Fore.RESET}[{card_to_play.value}] {card_to_play.name}\"")
        self.hands[self.turn_player].remove(card_to_play)
        card_to_play.effect(self)
        self.discard_pile[self.turn_player].append(card_to_play)

        # Check whether there is only one player left, who is the winner
        if players_in_game := (set(self.players) - self.players_out):
            if len(players_in_game) == 1:
                last_player = next(iter(players_in_game))
                print(f"{Fore.CYAN}{last_player.name} is the last survivor!{Fore.RESET}")
                raise GameOverException(last_player)

        # Pass to next player
        self.turn_player = self.next_player()

    def next_player(self) -> Player:
        # Determine which players are not out yet. Keep the turn_player in the list to have the current player's index,
        # in case the current player was eliminated in this turn.
        players_in_game = [player for player in self.players
                           if player == self.turn_player or player not in self.players_out]
        next_player_index = (players_in_game.index(self.turn_player) + 1) % len(players_in_game)
        return players_in_game[next_player_index]

    def deck_out_of_cards(self):
        print(f"{Fore.CYAN}Deck out of cards, winner is determined by card value.{Fore.RESET}")
        players_in_game = {player: hand[0].value for player, hand in self.hands.items()
                           if player not in self.players_out}
        for player, hand in players_in_game:
            print(f"{player.name}'s value: {hand[0].value}")

        # Determine Winner by finding the highest value, which is not present multiple times among the players
        highest_value = max(players_in_game.values())
        while sum(1 for n in players_in_game.values() if n == highest_value) > 1:
            players_in_game = {player: value for player, value in players_in_game.items()
                               if value != highest_value}
            if len(players_in_game) == 0:
                print(f"{Fore.CYAN}Game is a Draw!{Fore.RESET}")
                raise GameOverException(None)
            else:
                highest_value = max(players_in_game.values())
        winner = next(player for player, value in players_in_game.items() if value == highest_value)
        print(f"{Fore.CYAN}Winner is {Fore.RESET}{winner.name}")
        raise GameOverException(winner)

    def print_card(self, card: Card):
        print(f"[{card.value}] {Fore.MAGENTA}{card.name}{Fore.RESET}")
        print(f"Effect:\n{card.effect.description or 'None'}")
        if card.effect_madness is not None:
            print(f"{Fore.GREEN}Madness effect:\n{card.effect_madness.description}{Fore.RESET}")
        print()

    def draw_card(self, player: Player):
        print(f"{player.name} draws a card")
        card = self.deck.pop()
        self.hands[player].append(card)

    def select_card_from(self, cards: list[Card]) -> Card:
        if len(cards) == 0:
            raise ValueError("No cards to select from")
        if len(cards) == 1:
            return cards[0]

        for i, card in enumerate(cards, start=1):
            print(f"{i} | {card.name}")
        selection = 0
        while selection not in range(1, len(cards) + 1):
            try:
                selection = int(input(f"Select a card: "))
            except ValueError:
                pass
        return cards[selection - 1]

    def select_target_player(self,
                             activating_player: Player,
                             allow_last_self_target: bool = False,
                             deciding_player: Player = None,
                             custom_target_filter: Callable[["Gamestate", Player, Player], bool] = None
                             ) -> Player | None:
        """
        Ask user to select a target player for an effect.

        :param activating_player: Player who activated the effect.
        :param allow_last_self_target: If no targets are available and this is True, the activating player will be
            selected as "last resort". Otherwise, `None` will be returned, indicating that no valid target exists.
        :param deciding_player: Player who is asked to select a target. Default is the `activating_player`.
        :param custom_target_filter: Functions that takes the `Gamestate`, a player and the `activating_player`
        to determine whether the player is a valid target to select. This function is applied to all players, including
        those who are out of the game, protected or the activating player themselves!
        :return: Selected Player
        """
        if deciding_player is None:
            deciding_player = activating_player
        if custom_target_filter is None:
            possible_targets = list(set(self.players_in_game) - self.players_protected - {activating_player})
        else:
            possible_targets = [player for player in self.players_in_game
                                if custom_target_filter(self, player, activating_player)]
        print(f"{Fore.CYAN}{deciding_player.name} selects a target player ...{Fore.RESET}")
        if len(possible_targets) == 0:
            if allow_last_self_target:
                print(f"{Fore.CYAN}No valid unprotected targets, targeting the activating player{Fore.RESET}")
                return activating_player
            print(f"{Fore.CYAN}No valid unprotected targets available.{Fore.RESET}")
            return None

        for i, player in enumerate(possible_targets, start=1):
            print(f"{i} | {player.name}")
        selection = 0
        while selection not in range(1, len(possible_targets) + 1):
            try:
                selection = int(input(f"Select a player: "))
            except ValueError:
                pass
        return possible_targets[selection - 1]

    def select_card_value(self, deciding_player: Player, start=1, end=8) -> int:
        """
        Asks the player to select a card value between `start` and `end`.

        :param deciding_player: Player who is asked to select a card value.
        :param start: Minimum value to select (inclusive). Default is 1.
        :param end: Maximum value to select (inclusive). Default is 8.
        :return: Selected integer value.
        """
        print(f"{Fore.CYAN}{deciding_player.name} selects a card value ...{Fore.RESET}")
        selection = None
        while selection is None or selection not in range(start, end + 1):
            try:
                selection = int(input("Select a card value: "))
            except ValueError:
                pass
        return selection
