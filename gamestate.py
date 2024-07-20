import random
import time
from collections import defaultdict
from typing import Callable

from colorama import Fore
from card import Card, CARD_NAMES
from effect import Effect
from game_end import RoundEndException, GameOverException
from player import Player


class Gamestate:
    deck: list[Card]
    banished_cards: list[Card]
    players: list[Player]
    players_out: set[Player]
    players_protected: set[Player]
    on_player_turn_start: dict[Player, list[Callable[["Gamestate"], None]]]
    turn_player: Player
    hands: dict[Player, list[Card]]
    discard_pile: dict[Player, list[Card]]
    scores: dict[Player, tuple[int, int]]

    @property
    def players_in_game(self) -> list[Player]:
        return [player for player in self.players if player not in self.players_out]

    @property
    def players_mad(self) -> set[Player]:
        madness_status = {
            player: any(card.effect_madness is not None for card in self.discard_pile.get(player, []))
            for player in self.players
        }
        return {player for player, is_mad in madness_status.items() if is_mad}

    def __init__(self, player_names_or_num: list[str] | int = 2):
        if isinstance(player_names_or_num, int) and player_names_or_num >= 2:
            self.players = [Player(f"Player {i + 1}") for i in range(player_names_or_num)]
        elif isinstance(player_names_or_num, list) and all(isinstance(name, str) for name in player_names_or_num):
            self.players = [Player(name) for name in player_names_or_num]
        else:
            raise ValueError("Invalid player names or number of players")
        self.scores = {player: (0, 0) for player in self.players}

    def initialize_round(self) -> None:
        with open("deck.txt") as f:
            deck_cards = [tuple(line.strip().split(maxsplit=1)) for line in f.readlines()
                          if not line.strip().startswith("#") and line.strip()]
        self.deck = sum(([Card(code)] * int(n) for n, code in deck_cards if code in CARD_NAMES.keys()), [])
        self.shuffle_deck()
        self.banished_cards = []
        # If the game is played with 2 players, banish 5 cards from the deck face-up
        if len(self.players) == 2:
            for i in range(5):
                banish_card = self.deck.pop()
                print(f"{Fore.CYAN}[2-Player-Rule] Banishing \"{Fore.YELLOW}{str(banish_card)}{Fore.RESET}\"")
                self.banished_cards.append(banish_card)
        self.players_out = set()
        self.players_protected = set()
        self.on_player_turn_start = defaultdict(list)
        self.turn_player = self.players[0]
        self.hands = {player: [] for player in self.players}
        self.discard_pile = {player: [] for player in self.players}


        for player in self.players:
            self.draw_card(player)

    def start_game(self) -> None:
        try:
            while True:
                self._start_round()
        except GameOverException as goe:
            print(f"{Fore.CYAN}GAME OVER - Winner: {Fore.RESET}{goe.winner.name}")
        except KeyboardInterrupt:
            print(f"{Fore.CYAN}Game ended by KeyboardInterrupt{Fore.RESET}")

    def _start_round(self) -> None:
        self.initialize_round()
        try:
            while True:
                self.process_turn()
        except RoundEndException as ree:
            if ree.winner is None:
                print(f"{Fore.CYAN}Round is a Draw!{Fore.RESET}")
            else:
                print(f"{Fore.CYAN}Round is over. Winner: {Fore.YELLOW}{ree.winner.name}{Fore.RESET}")
                time.sleep(3)
                sanity_score, madness_score = self.scores[ree.winner]
                if ree.winner in self.players_mad:
                    print(f"1 Point was added to their {Fore.GREEN}INSANITY{Fore.RESET} score!")
                    madness_score += 1
                else:
                    print(f"1 Point was added to their {Fore.YELLOW}SANITY{Fore.RESET} score!")
                    sanity_score += 1
                if sanity_score >= 2 or madness_score >= 3:
                    raise GameOverException(ree.winner)
                self.scores[ree.winner] = sanity_score, madness_score
        print()
        for player, score in self.scores.items():
            print(f"{Fore.CYAN}{player.name}{Fore.RESET} |\t"
                  f"{Fore.YELLOW}SANITY{Fore.RESET}: {score[0]}/2 \t"
                  f"{Fore.GREEN}INSANITY{Fore.RESET}: {score[1]}/3")
        print()
        print()
        time.sleep(3)
    def shuffle_deck(self) -> None:
        print(f"{Fore.CYAN}Shuffling deck...{Fore.RESET}")
        random.shuffle(self.deck)

    def process_turn(self):
        time.sleep(2)
        print()
        print(f">> {Fore.YELLOW}{self.turn_player.name}'s turn{Fore.RESET}")

        self.process_turn_start_hooks(self.turn_player)
        self.insanity_check(self.turn_player)
        self.draw_card(self.turn_player)

        # Print all available cards for convenience
        self.print_state(self.turn_player)

        # Make the player select a card and effect to activate
        self.play_card_effect(self.turn_player)

        # Pass to next player
        self.turn_player = self.next_player()

    def next_player(self) -> Player:
        # Determine which players are not out yet. Keep the turn_player in the list to have the current player's index,
        # in case the current player was eliminated in this turn.
        players_in_game = [player for player in self.players
                           if player == self.turn_player or player not in self.players_out]
        next_player_index = (players_in_game.index(self.turn_player) + 1) % len(players_in_game)
        return players_in_game[next_player_index]

    def check_win_condition(self) -> None:
        """
        Check whether there is only one player left in the game.
        If so, the game is over and the last player is the winner.
        """
        players_in_game = [player for player in self.players if player not in self.players_out]
        if len(players_in_game) == 1:
            last_player = players_in_game[0]
            print(f"{Fore.YELLOW}{last_player.name} {Fore.CYAN}is the last survivor!{Fore.RESET}")
            raise RoundEndException(last_player)

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
                raise RoundEndException(None)
            else:
                highest_value = max(players_in_game.values())
        winner = next(player for player, value in players_in_game.items() if value == highest_value)
        print(f"{Fore.CYAN}Winner is {Fore.RESET}{winner.name}")
        raise RoundEndException(winner)

    def print_state(self, player: Player):
        print(f"{Fore.LIGHTBLUE_EX}Hand Cards:{Fore.RESET}")
        for card in self.hands[player]:
            print(f"\t[{card.value}]"
                  f"{Fore.MAGENTA if card.effect_madness is None else Fore.GREEN} {card.name}"
                  f"{Fore.RESET}")
        print(f"{Fore.LIGHTRED_EX}Discard Pile:{Fore.RESET}")
        if len(self.discard_pile[player]) == 0:
            print(f"--- none ---")
        for card in self.discard_pile[player]:
            print(f"\t[{card.value}]"
                  f"{Fore.MAGENTA if card.effect_madness is None else Fore.GREEN} {card.name}"
                  f"{Fore.RESET}")
        print()

    def draw_card(self, player: Player, append_to_hand: bool = True) -> Card:
        print(f"{player.name} draws a card")
        if len(self.deck) == 0:
            self.deck_out_of_cards()
        card = self.deck.pop()
        if append_to_hand:
            self.hands[player].append(card)
        return card

    def discard_card(self, discarding_player: Player, discard_card: Card):
        if discard_card not in self.hands[discarding_player]:
            return
        print(f"{Fore.YELLOW}{discarding_player.name} discards "
              f"\"{Fore.RESET}[{discard_card.value}] {discard_card.name}\"{Fore.RESET}")
        self.hands[discarding_player].remove(discard_card)
        self.discard_pile[discarding_player].append(discard_card)
        if discard_card.effect_on_discard is not None:
            discard_card.effect_on_discard.effect(self, discarding_player)

    def play_card_effect(self, activating_player: Player) -> None:
        effect_to_activate = self.select_effect_from(self.hands[activating_player], activating_player)
        card_to_play = effect_to_activate.card

        print(f"{Fore.YELLOW}{activating_player.name} plays "
              f"\"{Fore.RESET}[{card_to_play.value}] {card_to_play.name}\""
              f" {Fore.GREEN}(MADNESS){Fore.RESET}" if effect_to_activate.is_madness else "")
        self.hands[activating_player].remove(card_to_play)
        effect_to_activate.effect(self, activating_player)
        self.discard_pile[activating_player].append(card_to_play)

    def eliminate_player(self, eliminated_player: Player, killer_player: Player | None = None) -> bool:
        if eliminated_player in self.players_protected:
            print(f"{Fore.YELLOW}{eliminated_player.name}{Fore.CYAN} is protected and could not be eliminated!"
                  f"{Fore.RESET}")
            return False

        if killer_player is not None and killer_player != eliminated_player:
            print(f"{Fore.YELLOW}{eliminated_player.name}{Fore.RED} was eliminated by "
                  f"{Fore.YELLOW}{killer_player.name}{Fore.RESET}!")
        else:
            print(f"{Fore.YELLOW}{eliminated_player.name}{Fore.RED} was eliminated{Fore.RESET}!")
        self.discard_pile[eliminated_player].extend(self.hands[eliminated_player])
        self.hands[eliminated_player].clear()
        self.players_out.add(eliminated_player)
        self.check_win_condition()
        return True

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

    def select_effect_from(self,
                           cards_or_effects: Card | list[Card] | list[Effect],
                           activating_player: Player,
                           auto_return: bool = False,
                           ignore_activation_condition: bool = False) -> Effect | None:
        if isinstance(cards_or_effects, (Card, Effect)):
            cards_or_effects = [cards_or_effects]

        if all(isinstance(card, Card) for card in cards_or_effects):
            effects = ([card.effect for card in cards_or_effects] +
                       [card.effect_madness for card in cards_or_effects if card.effect_madness is not None])
        elif all(isinstance(effect, Effect) for effect in cards_or_effects):
            effects = cards_or_effects
        else:
            raise ValueError("'cards_or_effects' must be only Effect objects or only Card objects!")

        if not ignore_activation_condition:
            effects_available = {effect: effect.can_activate(self, activating_player) for effect in effects}
        else:
            effects_available = {effect: True for effect in effects}

        num_available_effects = len([e for e, can_activate in effects_available.items() if can_activate])
        if num_available_effects == 0:
            return None
        if num_available_effects == 1 and auto_return:
            return effects[0]

        # Sort effects, so effects of the same card are grouped together - also, the madness effect should be last
        effects.sort(key=lambda e: (e.card.name, e.is_madness))
        for i, effect in enumerate(effects, start=1):
            # Effect can be used
            if effects_available[effect]:
                print(f"{i} | {Fore.MAGENTA}{effect.card.name}{Fore.RESET}")
                print(f"   \t{Fore.GREEN if effect.is_madness else ''}{effect.description}{Fore.RESET}")
            else:
                print(f"{Fore.LIGHTWHITE_EX}  | {effect.card.name}{Fore.RESET} (unavailable)")
                print(f"   \t{Fore.LIGHTGREEN_EX if effect.is_madness else ''}{effect.description}{Fore.RESET}")
        selection = 0
        while selection not in range(1, len(effects) + 1) or not effects_available[effects[selection - 1]]:
            try:
                selection = int(input(f"Select an effect: "))
            except ValueError:
                pass
        return effects[selection - 1]

    def select_target_player(self,
                             activating_player: Player,
                             allow_last_self_target: bool = False,
                             deciding_player: Player = None,
                             custom_target_filter: Callable[["Gamestate", Player, Player], bool] = None,
                             apply_default_target_filter: bool = True
                             ) -> Player | None:
        """
        Ask user to select a target player for an effect.

        :param activating_player: Player who activated the effect.
        :param allow_last_self_target: If no targets are available and this is True, the activating player will be
            selected as "last resort". Otherwise, `None` will be returned, indicating that no valid target exists.
        :param deciding_player: Player who is asked to select a target. Default is the `activating_player`.
        :param custom_target_filter: Functions that takes the `Gamestate`, a potential target player and
            the `activating_player` to determine whether the player is a valid target to select.
        :param apply_default_target_filter: If True, the activating player, protected players and those already
            out of the game will not be evaluated as valid targets.
            This also applies, if `custom_target_filter` is used, so only targets that are not defeated, not protected,
            and not the activating player are passed to the function for evaluation. Default is True.
        :return: Selected Player
        """
        if deciding_player is None:
            deciding_player = activating_player

        if apply_default_target_filter:
            possible_targets = list(set(self.players_in_game) - self.players_protected - {activating_player})
        else:
            possible_targets = self.players

        if custom_target_filter is not None:
            possible_targets = [player for player in possible_targets
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

    def schedule_on_player_turn_start(self, player: Player, effect_func: Callable[["Gamestate"], None]) -> None:
        self.on_player_turn_start[player].append(effect_func)

    def protect_player(self, target_player: Player, indefinitely: bool = False) -> None:
        if indefinitely:
            print(f"{Fore.YELLOW}{target_player.name}{Fore.CYAN} is now protected!{Fore.RESET}")
        else:
            print(f"{Fore.YELLOW}{target_player.name} "
                  f"{Fore.CYAN}is now protected until the start of their next turn!{Fore.RESET}")
            self.schedule_on_player_turn_start(target_player,
                                               lambda game: game.unprotect_player(target_player))
        self.players_protected.add(target_player)

    def unprotect_player(self, player: Player) -> None:
        print(f"{Fore.YELLOW}{player.name}{Fore.CYAN} is no longer protected!{Fore.RESET}")
        self.players_protected.remove(player)

    def insanity_check(self, player: Player) -> None:
        madness_cards = len([card for card in self.discard_pile[player] if card.effect_madness is not None])
        if madness_cards > 0:
            print(f"{Fore.GREEN}The Void whispers to {Fore.YELLOW}{player.name}{Fore.GREEN} demanding "
                  f"{madness_cards} draw{'s' if madness_cards > 1 else ''} ...{Fore.RESET}")
            for i in range(madness_cards):
                drawn_card = self.draw_card(player, append_to_hand=False)
                if drawn_card.effect_madness is not None:
                    print(f"{Fore.YELLOW}{player.name}{Fore.RED} succumbed {Fore.GREEN}to the whispers of the Void,"
                          f"when facing '{drawn_card.name}'!{Fore.RESET}")
                    elimination_successful = self.eliminate_player(player)
                    if elimination_successful:
                        return
                    else:
                        continue
                print(f"{Fore.YELLOW}{player.name}{Fore.GREEN} resisted the temptation of "
                      f"'{drawn_card.name}' ({madness_cards - i - 1} more to go) ...{Fore.RESET}")
        else:
            print(f"{Fore.YELLOW}{player.name}{Fore.CYAN} is resisting the whispers of the Void ... for now"
                  f"{Fore.RESET}")

    def process_turn_start_hooks(self, player: Player):
        while len(self.on_player_turn_start[player]) > 0:
            effect_func = self.on_player_turn_start[player].pop(0)
            effect_func(self)
