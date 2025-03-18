import Model as Model
import Loaders
import json


# Returns hero object by id
def getHeroById(id: int, heroList: []) -> Model.Hero:
    for hero in heroList:
        if hero.id == id:
            return hero


# Returns hero object by name
def getHeroByName(heroname: str, heroList: []) -> Model.Hero:
    for hero in heroList:
        if hero.name == heroname:
            return hero
    return None


def saveHeroTable(heroList: [], path: str):
    res = "["
    counter = 0
    for hero in heroList:
        counter += 1
        if counter == 125:
            print("")
        res += json.dumps(hero.__dict__())
        res += ",\n"
    res = res[:-2] + "]"
    with open(path, "w") as file:
        file.write(res)
