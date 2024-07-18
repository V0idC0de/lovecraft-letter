from dataclasses import dataclass, field

from effect import Effect

CARD_NAMES = {
    "0m": "Gehirnzylinder der Mi-Go",
    "1": "Investigatoren",
    "1m": "Tiefe Wesen",
    "2": "Katzen von Ulthar",
    "2m": "Weltraum-Met",
    "3": "Große Rasse von Yith",
    "3m": "Hund von Tindalos",
    "4": "Älteres Zeichen",
    "4m": "Liber Ivonis",
    "5": "Dr. Henry Armitage",
    "5m": "Mi-Go",
    "6": "Randolph Carter",
    "6m": "Nyarlathotep",
    "7": "Der Silberne Schlüssel",
    "7m": "Der Leuchtende Trapezoeder",
    "8": "Necronomicon",
    "8m": "Cthulhu",
}


@dataclass
class Card:
    code: str
    name: str = field(init=False)
    value: int = field(init=False)
    effect: Effect | None = field(init=False, repr=False, default=None)
    effect_madness: Effect | None = field(init=False, repr=False, default=None)
    effect_on_discard: Effect | None = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self.name = Card.name_by_code(self.code)
        self.value = Card.value_by_code(self.code)
        self.effect = Effect.by_code(self.code.rstrip("m"))
        self.effect_madness = Effect.by_code(self.code) if self.code.endswith("m") else None
        self.effect_on_discard = Effect.by_code(f"{self.code}d")

    @staticmethod
    def name_by_code(code: str) -> str:
        return CARD_NAMES.get(code, "Unknown")

    @staticmethod
    def value_by_code(code: str) -> int:
        if len(code) == 0:
            raise ValueError("Empty code")
        return int(code[0])
