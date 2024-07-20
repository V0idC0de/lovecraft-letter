from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from colorama import Fore

from game_end import RoundEndException, GameOverException
from player import Player


@dataclass(frozen=True)
class Effect:
    card: "Card"
    effect: Callable[["Gamestate", Player], None]
    is_madness: bool
    activation_condition: Callable[["Effect", "Gamestate", Player], bool] | None = None
    description: str = "No Description"

    def __eq__(self, other):
        if callable(other):
            return self.effect == other
        if isinstance(other, self.__class__):
            return (self.effect == other.effect and
                    self.is_madness == other.is_madness and
                    self.activation_condition == other.activation_condition and
                    self.description == other.description)
        raise TypeError(f"Cannot compare Effect with {type(other)}")

    def __hash__(self):
        return id(self)

    @classmethod
    def by_code(cls, code: str | int, card: "Card") -> "Effect":
        code = str(code)
        effect = EFFECT_CODES.get(code)
        description = EFFECT_DESCRIPTIONS.get(code)
        return cls(card=card,
                   effect=effect,
                   is_madness=code.endswith("m"),
                   description=description)

    def can_activate(self, gamestate: "Gamestate", player: Player) -> bool:
        """
        Checks whether this effect can be activated by `player`. If an `activation_condition` is set, this function is
        equivalent to calling the passed function. Otherwise, the default restrictions are applied (see
        `self.activation_default_restrictions`).

        Effects with custom `activation_condition` functions have to invoke `self.activation_default_restrictions`
        themselves, unless they are explicitly intended to override the default restrictions.

        :param gamestate: Current gamestate.
        :param player: Player who wants to activate this effect.
        :return: Whether `player` can activate this effect, given the current `gamestate`.
        """
        if self.activation_condition is not None:
            return self.activation_condition(self, gamestate, player)
        return self.activation_default_restrictions(gamestate, player)

    def activation_default_restrictions(self, gamestate: "Gamestate", player: Player) -> bool:
        return (self.activation_madness_restriction(gamestate, player) and
                self.activation_silver_key_restriction(gamestate, player))

    def activation_madness_restriction(self, gamestate: "Gamestate", player: Player) -> bool:
        """
        Determines, whether this effect can be activated, considering the madness status of the player.
        If the player is not mad and this effect is a madness effect, it cannot be activated.
        """
        return player in gamestate.players_mad or not self.is_madness

    def activation_silver_key_restriction(self, gamestate: "Gamestate", player: Player) -> bool:
        """
        Determines, whether this effect can be activated, considering the other effect in the player's hand.
        If any card, except the card this effect belongs to, has `card7_effect`, this effect cannot be activated.
        """
        # The Silver Key effect is unaffected by its own rule, to avoid a deadlock with two Silver Key effects.
        if self.effect == card7_effect:
            return True
        other_cards_in_hand = [card for card in gamestate.hands.get(player, []) if card is not self.card]
        other_effects = [card.effect for card in other_cards_in_hand if card.effect is not None]
        silver_key_effect_present = card7_effect in other_effects
        # Effect can be activated if ...
        #   1. This effect is from a card with a value less than 5
        #   2. The Silver Key is NOT present in the other effects
        return self.card.value < 5 or not silver_key_effect_present


def card0_effect(gamestate: "Gamestate", activating_player: Player):
    print(f"{Fore.GREEN}The Brain's Cylinder of the Mi-Go whispers to {Fore.YELLOW}{activating_player}{Fore.RESET}")
    gamestate.eliminate_player(activating_player)


def card1_effect(gamestate: "Gamestate", activating_player: Player):
    player_target = gamestate.select_target_player(activating_player)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return
    print(f"{Fore.YELLOW}{gamestate.turn_player.name} is questioned ...{Fore.YELLOW} ")
    guessed_value = gamestate.select_card_value(gamestate.turn_player, start=2)
    if guessed_value == gamestate.hands[player_target][0].value:
        print(f"{Fore.CYAN}{player_target.name} was {Fore.RED} exposed and executed!{Fore.RESET}")
        gamestate.eliminate_player(player_target, activating_player)
    else:
        print(F"{Fore.CYAN}{player_target.name} resisted the accusation ...{Fore.RESET}")


def card1_madness_effect(gamestate: "Gamestate", activating_player: Player):
    player_target = gamestate.select_target_player(activating_player)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return
    if gamestate.hands[player_target][0].value == 1:
        print(f"{Fore.CYAN}{player_target.name} had a [1] card in their hand and was "
              f"{Fore.GREEN}overwhelmed by the Void!{Fore.RESET}")
        gamestate.eliminate_player(player_target, activating_player)
    else:
        print(f"{Fore.CYAN}{player_target.name} had no [1] card and resisted the Void ...{Fore.RESET}")
        card1_effect(gamestate, activating_player)


def card2_effect(gamestate: "Gamestate", activating_player: Player):
    player_target = gamestate.select_target_player(activating_player)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return
    print(f"{Fore.YELLOW}{activating_player.name}{Fore.YELLOW} "
          f"{Fore.CYAN}peeked at "
          f"{Fore.YELLOW}{player_target.name}{Fore.CYAN}'s hand.{Fore.RESET}")
    card_names = [card.name for card in gamestate.hands.get(player_target, [])]
    print(f"{Fore.CYAN}A hand of {Fore.YELLOW}{", ".join(card_names)} {Fore.CYAN}was revealed ...{Fore.RESET}")


def card2_madness_effect(gamestate: "Gamestate", activating_player: Player):
    card2_effect(gamestate, activating_player)
    print(f"{Fore.YELLOW}{activating_player.name}{Fore.GREEN} is granted another card by the Void ...{Fore.RESET}")
    gamestate.draw_card(activating_player)
    print(f"{Fore.GREEN}The Void demands a card to be played ...{Fore.RESET}")
    gamestate.play_card_effect(activating_player)


def card3_effect(gamestate: "Gamestate", activating_player: Player):
    player_target = gamestate.select_target_player(activating_player)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return
    lower_player: Player = min([activating_player, player_target], key=lambda p: gamestate.hands[p][0].value)
    higher_player: Player = max([activating_player, player_target], key=lambda p: gamestate.hands[p][0].value)
    if lower_player != higher_player:
        print(f"{Fore.YELLOW}{lower_player.name} "
              f"{Fore.CYAN}had a lower card value and was defeated!{Fore.RESET}")
        gamestate.eliminate_player(lower_player)
    else:
        print(f"{Fore.CYAN}The opponents were Evenly Matched ...{Fore.RESET}")


def card3_madness_effect(gamestate: "Gamestate", activating_player: Player):
    player_target = gamestate.select_target_player(activating_player,
                                                   custom_target_filter=lambda p: p in gamestate.players_mad)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return
    print(f"{Fore.YELLOW}{player_target.name} {Fore.RESET}was designated and "
          f"{Fore.GREEN}instantly consumed by the Void!{Fore.RESET}")
    gamestate.eliminate_player(player_target, gamestate.turn_player)


def card4_effect(gamestate: "Gamestate", activating_player: Player):
    gamestate.protect_player(activating_player, indefinitely=False)


def card4_madness_effect(gamestate: "Gamestate", activating_player: Player):
    gamestate.protect_player(activating_player, indefinitely=True)


def card5_effect(gamestate: "Gamestate", activating_player: Player):
    player_target = gamestate.select_target_player(activating_player, allow_last_self_target=True)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return
    print(f"{Fore.YELLOW}{player_target.name} {Fore.CYAN}cannot hold onto their card ...{Fore.RESET}")
    gamestate.discard_card(player_target, gamestate.hands[player_target][0])
    gamestate.draw_card(player_target)


def card5_madness_effect(gamestate: "Gamestate", activating_player: Player):
    from card import Card

    player_target = gamestate.select_target_player(activating_player)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return

    stolen_card = gamestate.hands[player_target].pop(0)
    gamestate.hands[player_target].append(stolen_card)
    print(f"{Fore.YELLOW}{activating_player.name} {Fore.RESET} stole a card from {Fore.YELLOW}{player_target.name}!"
          f"{Fore.RESET}")

    gamestate.hands[player_target].append(Card("0m"))
    print(f"{Fore.YELLOW}{player_target.name} {Fore.RESET}received the 'Brain's Cylinder of the Mi-Go' ...{Fore.RESET}")

    print(f"{Fore.GREEN}The Void demands a card to be played ...{Fore.RESET}")
    gamestate.play_card_effect(activating_player)


def card6_effect(gamestate: "Gamestate", activating_player: Player):
    player_target = gamestate.select_target_player(activating_player)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return
    print(f"{Fore.YELLOW}{activating_player.name} {Fore.RESET}and {Fore.YELLOW}{player_target.name} {Fore.RESET}"
          f"exchanged hands ...")
    target_card = gamestate.hands[player_target].pop(0)
    activator_card = gamestate.hands[activating_player].pop(0)
    gamestate.hands[player_target].append(activator_card)
    gamestate.hands[activating_player].append(target_card)


def card6_madness_effect(gamestate: "Gamestate", activating_player: Player):
    target_players = gamestate.players_in_game - gamestate.players_protected - {activating_player}
    if len(target_players) < 2:
        print(f"{Fore.CYAN}Not enough valid targets to switch hands around.{Fore.RESET}")
        return
    cards = [gamestate.hands[p].pop(0) for p in target_players]
    while len(cards) > 0:
        tar_player = gamestate.select_target_player(activating_player,
                                                    apply_default_target_filter=False,
                                                    custom_target_filter=lambda x, target, y: target in target_players)
        tar_card = gamestate.select_card_from(cards)
        cards.remove(tar_card)
        gamestate.hands[tar_player].append(tar_card)
        print(f"{Fore.YELLOW}{tar_player.name} {Fore.RESET}received a card ...")


def card7_effect(gamestate: "Gamestate", activating_player: Player):
    return nop_effect(gamestate, activating_player)


def card7_madness_effect(gamestate: "Gamestate", activating_player: Player):
    if any(card.value >= 5 for card in gamestate.hands[activating_player]):
        print(f"{Fore.YELLOW}{activating_player.name}{Fore.RESET}'s 'Shining Trapezohedron' surges with power, "
              f"{Fore.RED}instantly eliminating all other players!{Fore.RESET}")
        raise RoundEndException(activating_player)
    else:
        card7_effect(gamestate, activating_player)


def card8_effect(gamestate: "Gamestate", activating_player: Player):
    print(f"Dark magic consumes {Fore.YELLOW}{activating_player.name}{Fore.RESET} ...")
    gamestate.eliminate_player(activating_player)


def card8_discard_effect(gamestate: "Gamestate", activating_player: Player):
    return card8_effect(gamestate, activating_player)


def card8_madness_effect(gamestate: "Gamestate", activating_player: Player):
    madness_cards = [card for card in gamestate.discard_pile[activating_player] if card.effect_madness is not None]
    if len(madness_cards) >= 2:
        print(f"{Fore.YELLOW}{activating_player.name}{Fore.GREEN} has summoned Cthulhu and wins the game!{Fore.RESET}")
        raise GameOverException(activating_player)
    else:
        print(f"{Fore.YELLOW}{activating_player.name}{Fore.GREEN} is consumed by the Void ...{Fore.RESET}")
        gamestate.eliminate_player(activating_player)


def card8_madness_discard_effect(gamestate: "Gamestate", activating_player: Player):
    return card8_madness_effect(gamestate, activating_player)


def nop_effect(gamestate: "Gamestate", activating_player: Player):
    print(f"{Fore.CYAN}Nothing happened ...{Fore.RESET}")


EFFECT_CODES: dict[str, Callable[["Gamestate", Player], None]] = defaultdict(lambda: nop_effect, {
    "0m": card0_effect,
    "0md": card0_effect,
    "1": card1_effect,
    "1m": card1_madness_effect,
    "2": card2_effect,
    "2m": card2_madness_effect,
    "3": card3_effect,
    "3m": card3_madness_effect,
    "4": card4_effect,
    "4m": card4_madness_effect,
    "5": card5_effect,
    "5m": card5_madness_effect,
    "6": card6_effect,
    "6m": card6_madness_effect,
    "7": card7_effect,
    "7m": card7_madness_effect,
    "8": card8_effect,
    "8d": card8_discard_effect,
    "8m": card8_madness_effect,
    "8md": card8_madness_discard_effect,
})

EFFECT_DESCRIPTIONS: dict[str, str] = defaultdict(lambda: "Nothing will happen ...", {
    "0m": "Wenn du diese Karte spielst oder ablegst, scheidest du aus.",
    "1": "Errätst du den Wert der Handkarte eines Mitspielers (außer der '1'), scheidet dieser aus.",
    "1m": "Besitzt die Handkarte eines Mitspieler eine '1', scheidet dieser aus. Wenn nicht, wende die normale "
          "Funktion dieser Karte gegen ihn an.",
    "2": "Schaue dir die Handkarte von einem Mitspieler an.",
    "2m": "Schaue dir die Handkarte von einem Mitspieler an. Ziehe 1 Karte und spiele dann 1 Handkarte aus.",
    "3": "Vergleiche deine Handkarte mit der eines Mitspielers. Der Spieler mit dem niedrigeren Wert scheidet aus.",
    "3m": f"Wähle einen Mitspieler, der nicht {Fore.GREEN}wahnsinnig{Fore.RESET} ist. Er scheidet aus.",
    "4": "Du bist bis zu deinem nächsten Zug geschützt.",
    "4m": "Du kannst bis zum Ende der Runde nicht ausscheiden.",
    "5": "Wähle einen Spieler, der seine Handkarte ablegt und eine neue Karte zieht.",
    "5m": "Nimm die Handkarte eines Mitspielers und spiele dann 1 Handkarte aus. Der Mitspieler nimmt sich den 'Gehirnzylinder der Mi-Go'.",
    "6": "Tausche deine Handkarte mit der eines Mitspielers.",
    "6m": "Nimm alle Handkarten der Mitspieler. Schaue sie an und gib jedem 1 Karte deiner Wahl zurück.",
    "7": "Wenn du zusätzlich eine Karte mit einer '5' oder höher auf der Hand hast, musst du diese Karte ausspielen.",
    "7m": "Hast du zusätzlich eine '5' oder höher auf der Hand, gewinnst du die Runde.",
    "8": "Wenn du diese Karte ablegst, scheidest du aus.",
    "8m": "Wenn du Cthulhu spielst oder ablegst, während du bereits 2+ Wahnsinnskarten hast, gewinnst du das Spiel. Sonst scheidest du aus.",
})
