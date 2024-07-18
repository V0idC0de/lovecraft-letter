from dataclasses import dataclass
from typing import Callable

from colorama import Fore


@dataclass
class Effect:
    effect: Callable[["Gamestate"], None]
    is_madness: bool
    description: str = "No Description"

    def __call__(self, *args, **kwargs):
        self.effect(*args, **kwargs)

    @classmethod
    def by_code(cls, code: str | int) -> "Effect":
        effect = EFFECT_CODES.get(code)
        description = EFFECT_DESCRIPTIONS.get(code)
        return cls(effect=effect,
                   is_madness=code.endswith("m"),
                   description=description)


def card1_effect(gamestate: "Gamestate"):
    player_target = gamestate.select_target_player(gamestate.turn_player)
    if player_target is None:
        print(f"{Fore.CYAN}No target available, effect cannot activate.{Fore.RESET}")
        return
    guessed_value = gamestate.select_card_value(gamestate.turn_player, start=2)
    if guessed_value == gamestate.hands[player_target][0].value:
        print(f"{Fore.CYAN}{player_target.name} was exposed!{Fore.RESET}")
        gamestate.players_out.append(player_target)


def card1_madness_effect(gamestate: "Gamestate"):
    print("card1 madness effect triggered")


def card2_effect(gamestate: "Gamestate"):
    print("card2 effect triggered")


def card2_madness_effect(gamestate: "Gamestate"):
    print("card2 madness effect triggered")


def card3_effect(gamestate: "Gamestate"):
    print("card3 effect triggered")


def card3_madness_effect(gamestate: "Gamestate"):
    print("card3 madness effect triggered")


def card4_effect(gamestate: "Gamestate"):
    print("card4 effect triggered")


def card4_madness_effect(gamestate: "Gamestate"):
    print("card4 madness effect triggered")


def card5_effect(gamestate: "Gamestate"):
    print("card5 effect triggered")


def card5_madness_effect(gamestate: "Gamestate"):
    print("card5 madness effect triggered")


def card6_effect(gamestate: "Gamestate"):
    print("card6 effect triggered")


def card6_madness_effect(gamestate: "Gamestate"):
    print("card6 madness effect triggered")


def card7_effect(gamestate: "Gamestate"):
    print("card7 effect triggered")


def card7_madness_effect(gamestate: "Gamestate"):
    print("card7 madness effect triggered")


def card8_effect(gamestate: "Gamestate"):
    print("card8 effect triggered")


def card8_discard_effect(gamestate: "Gamestate"):
    print("card8 discard effect triggered")


def card8_madness_effect(gamestate: "Gamestate"):
    print("card8 madness effect triggered")


def card8_madness_discard_effect(gamestate: "Gamestate"):
    print("card8 madness discard effect triggered")


EFFECT_CODES = {
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
}

EFFECT_DESCRIPTIONS = {
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
    "5m": "Nimm die Handkarte eines Mitspielers und spiele dann 1 Handkarte aus. Der Mitspieler nimmt sich den 'Gehirnzylinder der Mi-Go'",
    "6": "Tausche deine Handkarte mit der eines Mitspielers.",
    "6m": "Nimm alle Handkarten der Mitspieler. Schaue sie an und gib jedem 1 Karte deiner Wahl zurück.",
    "7": "Wenn du zusätzlich eine Karte mit einer '5' oder höher auf der Hand hast, musst du diese Karte ausspielen.",
    "7m": "Hast du zusätzlich eine '5' oder höher auf der Hand, gewinnst du die Runde.",
    "8": "Wenn du diese Karte ablegst, scheidest du aus.",
    "8m": "Wenn du Cthulhu ablegst und bereits 2+ Wahnsinnskarten hast, gewinnst du das Spiel. Sonst scheidest du aus.",
}
