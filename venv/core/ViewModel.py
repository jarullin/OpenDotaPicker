import Model as Model
import Loaders as Loaders
import threading
import datetime
import os
from pathlib import Path

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


# sorts heroes by attribute in 4 lists
def getAttributeHeroLists(heroList: []) -> ([], [], [], []):
    _strHeroes = []
    _agiHeroes = []
    _intHeroes = []
    _allHeroes = []
    for hero in heroList:
        match hero.attribute:
            case 'agi':
                _agiHeroes.append(hero)
            case 'str':
                _strHeroes.append(hero)
            case 'int':
                _intHeroes.append(hero)
            case 'all':
                _allHeroes.append(hero)
    _strHeroes = sorted(_strHeroes, key=lambda d: d.name)
    _agiHeroes = sorted(_agiHeroes, key=lambda d: d.name)
    _intHeroes = sorted(_intHeroes, key=lambda d: d.name)
    _allHeroes = sorted(_allHeroes, key=lambda d: d.name)
    return (_strHeroes, _agiHeroes, _intHeroes, _allHeroes)

class HeroListHolder:
    def __init__(self):
        self.value = None
        self.lock = threading.Lock()

def background_role_loader(holder, callback):
    value = Loaders.update_roles()
    callback(value)


