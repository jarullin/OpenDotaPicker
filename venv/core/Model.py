from PIL import ImageTk


class Hero:
    id: int
    dotaName: str
    name: str
    attackType: str
    roles = []  # list of int
    attribute: str
    matchups = []  # list of Winrate objects
    image: ImageTk.PhotoImage  # full picture of hero          100x56
    highlightedImage: ImageTk.PhotoImage
    aliases = []
    suggestionImage: ImageTk.PhotoImage
    minMatchupN: int
    maxMatchupN: int
    gpm: float  # gold per minute
    dpm: float  # hero damage per minute
    tdmg: float  # tower damage per ma tch

    def __init__(self):
        self.maxMatchupN = 0
        self.minMatchupN = 10000

    def __dict__(self):
        return {"attack_type": self.attackType,
                "id": self.id,
                "localized_name": self.name,
                "name": self.dotaName,
                "primary_attr": self.attribute,
                "aliases": self.aliases,
                "roles": self.roles,
                "gpm": self.gpm,
                "dpm": self.dpm,
                "tdmg": self.tdmg}


class Winrate:
    enemyId: int
    winrate: float
    n: int

    def __init__(self, _enemyId, _winrate, _n):
        self.enemyId = _enemyId
        self.winrate = _winrate
        self.n = _n
