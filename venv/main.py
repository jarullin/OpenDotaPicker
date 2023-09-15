import asyncio
import copy
import datetime
import email.charset
import json
import os
import time
from tkinter import *
from tkinter import ttk, font
import requests
from PIL import Image, ImageTk
from datetime import date, timedelta
import cv2
import numpy as np
from pathlib import Path
import async_tkinter_loop as atl

# Globals
HeroList = []
stats = [0, 10000]  # Stores minimal and maximal number of games played in stats
bgColor = "#282825"  # Stores background color


class Hero:
    id: int
    dotaName: str
    name: str
    attackType: str
    roles = []              # list of int
    attribute: str
    matchups = {}           # list of dictionaries {'hero_id'       : id of enemy hero
                            #                       'games_played'  : self-explanatory
                            #                       'wins'          : self-explanatory}
    picture: ImageTk.PhotoImage             # full picture of hero          100x56
    radiantPicture: ImageTk.PhotoImage      # upper left side of picture    50x41
    radiantPictureHovered: ImageTk.PhotoImage   # green version             50x41
    direPicture: ImageTk.PhotoImage         # upper right side of picture   50x41
    direPictureHovered: ImageTk.PhotoImage  # red version                   50x41
    banPicture: ImageTk.PhotoImage          # bottom side of picture        100x15
    banPictureHovered: ImageTk.PhotoImage   # gray version                  100x15
    banPictureSmall: ImageTk.PhotoImage     # small picture for ban grid    50x28


class App:
    def __init__(self, master: Tk) -> None:
        self.master = master
        # Creating a Font object of "TkDefaultFont"
        self.defaultFont = font.nametofont("TkDefaultFont")
        # Overriding default-font with custom settings
        self.defaultFont.configure(family="Helvetica",
                                   size=20,
                                   weight=font.NORMAL)

class TimedWord:
    _value : str
    def __init__(self):
        self._last_changed = datetime.datetime.utcnow()
        self._value = ''
    def add(self, value : str):
        time_passed = datetime.datetime.utcnow() - self._last_changed
        if time_passed.total_seconds() > 2:
            self._value = value
        else:
            self._value += value
        self._last_changed = datetime.datetime.utcnow()
    def get(self):
        time_passed = datetime.datetime.utcnow() - self._last_changed
        if time_passed.total_seconds() > 2:
            return ''
        else:
            return self._value

word = TimedWord()
# Returns hero object by id
def getHeroById(id: int):
    for hero in HeroList:
        if hero.id == id:
            return hero


# Returns hero object by name
def getHeroByName(heroname: str):
    for hero in HeroList:
        if hero.name == heroname:
            return hero


# Loads hero pictures
def getHeroPictures():
    for hero in HeroList:
        hero.picture = ImageTk.PhotoImage(
            Image.open('img\\' + hero.attribute + "\\" + hero.name + "_icon.gif").resize((100, 56)))
        # Creating button pictures
        _image = ImageTk.getimage(hero.picture)
        _ban_small = _image.resize((50, 28))
        hero.banPictureSmall = ImageTk.PhotoImage(_ban_small)
        # crop((left,top,right,bottom))
        _radiant = _image.crop((0, 0, 50, 41))
        _ban = _image.crop((0, 41, 100, 56))
        _dire = _image.crop((50, 0, 100, 41))
        hero.radiantPicture = ImageTk.PhotoImage(_radiant)
        hero.direPicture = ImageTk.PhotoImage(_dire)
        hero.banPicture = ImageTk.PhotoImage(_ban)
        # Creating hovered version of button pictures
        _radiant_hover = Image.fromarray(getHover(_radiant, (0, 0), (50, 41), (0, 255, 33)))
        _dire_hover = Image.fromarray(getHover(_dire, (0, 0), (50, 41), (255, 0, 0)))
        _ban_hover = Image.fromarray(getHover(_ban, (0, 0), (100, 15), (128, 128, 128)))
        hero.radiantPictureHovered = ImageTk.PhotoImage(_radiant_hover)
        hero.direPictureHovered = ImageTk.PhotoImage(_dire_hover)
        hero.banPictureHovered = ImageTk.PhotoImage(_ban_hover)


# sorts heroes by attribute in 4 lists
def getAttributeHeroLists():
    _strHeroes = []
    _agiHeroes = []
    _intHeroes = []
    _allHeroes = []
    for hero in HeroList:
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
    return _strHeroes, _agiHeroes, _intHeroes, _allHeroes


# Returns hovered version of picture
def getHover(picture: ImageTk, start: (int, int), end: (int, int), color: (int, int, int)):
    alpha = 0.6
    img_rgb = picture.convert('RGB')
    img_array = np.array(img_rgb)
    overlay = img_array.copy()
    output = img_array.copy()
    cv2.rectangle(overlay, start, end, color, -1)
    cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)
    return output


def initialize():
    # Load hero data
    with open("herotable.json", "r") as f:
        rawData = json.load(f)
        # Create and fill hero instances
        for item in rawData:
            heroInstance = Hero()
            heroInstance.id = item['id']
            heroInstance.dotaName = item['name']
            heroInstance.name = item['localized_name']
            heroInstance.attackType = item['attack_type']
            heroInstance.roles = item['roles']
            heroInstance.attribute = item['primary_attr']
            HeroList.append(heroInstance)
    # Check if there is a matchups file
    isHeroMatchupsPresent = Path('heromatchups.json').is_file()
    # If there is no file, get matchup data from OpenDota
    if not isHeroMatchupsPresent or datetime.datetime.fromtimestamp(
            os.path.getmtime('heromatchups.json')) < datetime.datetime.today() - datetime.timedelta(days=7):
        output = ''
        for hero in HeroList:
            responce = requests.get("https://api.opendota.com/api/heroes/" + str(hero.id) + "/matchups")
            if responce.status_code != 200:
                raise RuntimeError
            hero.matchups = responce.json()
            # Getting minimal und maximal number of games played in matchup
            for matchup in hero.matchups:
                stats[1] = item['games_played'] if stats[1] < matchup['games_played'] else stats[1]
                stats[0] = item['games_played'] if stats[0] > matchup['games_played'] else stats[0]
            # Free OpenDota API limits the number of requests to 60 per minute
            time.sleep(1)
            output += "[\"id \" : " + str(hero.id) + " , \"matchups\" : " + str(responce.json()) + ']\n'
        # Saving data
        with open('heromatchups.json', 'w') as f:
            f.write(output)
    else:
        # Loading matchup data from file
        with open('heromatchups.json', 'r') as f:
            for line in f:
                line = "{" + line[1:-2] + "}"
                matchupData = json.loads(line)
                hero = getHeroById(matchupData['id'])
                hero.matchups = matchupData['matchups']
                for matchup in hero.matchups:
                    stats[1] = item['games_played'] if stats[1] < matchup['games_played'] else stats[1]
                    stats[0] = item['games_played'] if stats[0] > matchup['games_played'] else stats[0]
    # Loading hero pictures
    getHeroPictures()
    # Finding out roles of heroes
    '''
    responce = requests.get("https://api.opendota.com/api/scenarios/laneRoles")
    if responce.status_code != 200:
        raise RuntimeError
    data = responce.json()
    for item in data:
        hero = getHeroById(item['hero_id'])
        # Calculating number of games played on certain line:
        # 1 - Safelane, 2 - Mid, 3 - Offlane
        if item['lane_role'] == 1:
            hero.safelanePlayed += int(item['games'])
        elif item['lane_role'] == 2:
            hero.midlanePlayed += int(item['games'])
        elif item['lane_role'] == 3:
            hero.offlanePlayed += int(item['games'])
    for hero in HeroList:
        if hero.name == 'Enigma':
            print('hi!')
        if hero.safelanePlayed >= hero.offlanePlayed:  # Safelane > Offlane
            if hero.safelanePlayed >= hero.midlanePlayed:  # Safelane > Mid
                if hero.offlanePlayed >= hero.midlanePlayed:  # Safelane > Offlane > Mid
                    if 'Carry' in hero.roles:
                        hero.bestRole = 1
                        hero.secondRole = 3
                    else:
                        hero.bestRole = 5
                        hero.secondRole = 4
                else:  # Safelane > Mid > Offlane
                    if 'Carry' in hero.roles:
                        hero.bestRole = 1
                        hero.secondRole = 2
                    else:
                        hero.bestRole = 5
                        hero.secondRole = 2
            else:  # Mid > Safelane > Offlane
                if 'Carry' in hero.roles:
                    hero.bestRole = 2
                    hero.secondRole = 1
                else:
                    hero.bestRole = 2
                    hero.secondRole = 5
        else:  # Offlane > Safelane
            if hero.offlanePlayed >= hero.midlanePlayed:  # Offlane > Mid
                if hero.safelanePlayed >= hero.midlanePlayed:  # Offlane > Safelane > Mid
                    if 'Initiator' in hero.roles:
                        hero.bestRole = 3
                        hero.secondRole = 1
                    else:
                        hero.bestRole = 4
                        hero.secondRole = 5
                else:  # Offlane > Mid > Safelane
                    if 'Initiator' in hero.roles:
                        hero.bestRole = 3
                        hero.secondRole = 2
                    else:
                        hero.bestRole = 4
                        hero.secondRole = 2
            else:
                if hero.offlanePlayed >= hero.safelanePlayed:  # Mid > Offlane > Safelane
                    hero.bestRole = 2
                    if 'Support' in hero.roles:
                        hero.secondRole = 4
                    else:
                        hero.secondRole = 3
        # Pros maybe not played some hero
        if hero.offlanePlayed == 0 and hero.safelanePlayed == 0 and hero.midlanePlayed == 0:
            if 'Carry' in hero.roles:
                hero.bestRole = 1
                hero.secondRole = 1
            elif 'Support' in hero.roles:
                hero.bestRole = 5
                hero.secondRole = 4
            elif 'Initiator' in hero.roles:
                hero.bestRole = 3
                hero.secondRole = 4
            else:
                hero.bestRole = 2
                hero.secondRole = 2
'''

# Entry point
root = Tk()
app = App(root)
root.tk_setPalette(background=bgColor, foreground="white")
initialize()

# Layout
root.title("OpenDotaPicker")
root.geometry('2100x1080')
mainFrame = Frame(root)
mainFrame.grid()
# mainFrame children
# 1. Picks
pickFrame = Frame(mainFrame, height=100, width=root.winfo_screenwidth(), bg=bgColor)
pickFrame.grid(row=0, column=0, sticky=NW)
# 2. Heroes
heroGridFrame = Frame(mainFrame, height=56 * 7, bg=bgColor)
heroGridFrame.grid(row=1, column=0, sticky=W, columnspan=25)
# 3. Suggestions
suggestionsFrame = Frame(mainFrame, bg=bgColor, highlightbackground="gray")
suggestionsFrame.grid(row=2, sticky=W, padx=(30, 0), pady=(5, 0))

# Pick Frame children
# 1.1 Radiant pick
radiantPickGridFrame = Frame(pickFrame, height=88, width=520, bg=bgColor, highlightbackground="gray",
                             highlightthickness=2)
radiantPickGridFrame.grid(row=0, column=0, sticky=W, padx=(20, 20))
radiantPickGridFrame.grid_propagate(0)
radiantPickLabel = Label(radiantPickGridFrame, text="Radiant Pick", fg="white", font=("Verdana", 10), bg=bgColor)
radiantPickLabel.grid(row=0, column=0, columnspan=5)
# 1.2 Banned heroes
banGridFrame = Frame(pickFrame, bg=bgColor, height=88, width=58 * 8, highlightbackground="gray", highlightthickness=2)
banGridFrame.grid(row=0, column=1, sticky=N, padx=(20, 20))
banGridFrame.grid_propagate(0)
banLabel = Label(banGridFrame, text="Bans", fg="white", font=("Verdana", 10), bg=bgColor)
banLabel.grid(row=0, column=0, columnspan=15)
# 1.3 Dire pick
direPickGridFrame = Frame(pickFrame, bg="#282825", height=88, width=520, highlightbackground="gray",
                          highlightthickness=2)
direPickGridFrame.grid(row=0, column=2, sticky=E, padx=(20, 20))
direPickGridFrame.grid_propagate(0)
direPickLabel = Label(direPickGridFrame, text="Dire Pick", fg="white", font=("Verdana", 10), bg=bgColor)
direPickLabel.grid(row=0, column=0, columnspan=5)

# heroFrame children
# 2.1 Strength heroes
strFrame = Frame(heroGridFrame, height=heroGridFrame.winfo_height(), width=460, highlightbackground="gray",
                 highlightthickness=2)
strFrame.grid(column=0, row=1, padx=(30, 0), sticky=NW)
# 2.2 Agility heroes
agiFrame = Frame(heroGridFrame, height=heroGridFrame.winfo_height(), width=460, highlightbackground="gray",
                 highlightthickness=2)
agiFrame.grid(column=1, row=1, padx=(15, 0), sticky=NW)
# 2.3 Intelligence heroes
intFrame = Frame(heroGridFrame, height=heroGridFrame.winfo_height(), width=460, highlightbackground="gray",
                 highlightthickness=2)
intFrame.grid(column=2, row=1, padx=(15, 0), sticky=NW)
# 2.4 Universal heroes
allFrame = Frame(heroGridFrame, height=heroGridFrame.winfo_height(), width=460, highlightbackground="gray",
                 highlightthickness=2)
allFrame.grid(column=3, row=1, padx=(15, 0), sticky=NW)

# suggestionsFrame children
# 3.1 Top 10 heroes to pick
suggestionsFrameGeneral = Frame(suggestionsFrame)
suggestionsFrameGeneral.grid(row=0, sticky=W, padx=(30, 0), pady=(5, 0))
# 3.2 Top 10 carries to pick
suggestionsFrameCarry = Frame(suggestionsFrame, )
suggestionsFrameCarry.grid(row=1, sticky=W, padx=(30, 0), pady=(5, 0))
# 3.3 Top 10 midlaners to pick
suggestionsFrameMidlaner = Frame(suggestionsFrame)
suggestionsFrameMidlaner.grid(row=2, sticky=W, padx=(30, 0), pady=(5, 0))
# 3.4 Top 10 offlanes to pick
suggestionsFrameOfflaner = Frame(suggestionsFrame)
suggestionsFrameOfflaner.grid(row=3, sticky=W, padx=(30, 0), pady=(5, 0))
# 3.5 Top 10 soft supports to pick
suggestionsFrameSoftSupport = Frame(suggestionsFrame)
suggestionsFrameSoftSupport.grid(row=4, sticky=W, padx=(30, 0), pady=(5, 0))
# 3.6 Top 10 hard supports to pick
suggestionsFrameHardSupport = Frame(suggestionsFrame, bg=bgColor)
suggestionsFrameHardSupport.grid(row=5, sticky=W, padx=(30, 0), pady=(5, 0))

# statusBarFrame = Frame(mainFrame, height=20)
# statusBarFrame.grid(row=3)

# Stores hero list sorted by attributes
strHeroes, agiHeroes, intHeroes, allHeroes = getAttributeHeroLists()
# Lists of banned and picked heroes
bannedHeroes, radiantPick, direPick = [], [], []
# Stores buttons in hero grid
strButtonsGrids = []
agiButtonsGrids = []
intButtonsGrids = []
allButtonsGrids = []


### E V E N T    H A N D L E R S
# ---------------------------------------------------------
def onHover(side: str, hero: Hero, button):
    if side == 'radiant':
        button.config(image=hero.radiantPictureHovered)
    elif side == 'ban':
        button.config(image=hero.banPictureHovered)
    elif side == 'dire':
        button.config(image=hero.direPictureHovered)


# removes hero from picked/banned frame
def onPickedClick(hero: Hero, widget):
    widget.destroy()
    button_grid = []
    # get the frame where hero stored on hero grid
    match hero.attribute:
        case 'agi':
            button_grid = next(i for i in agiButtonsGrids if i[0].name == hero.name)
        case 'str':
            button_grid = next(i for i in strButtonsGrids if i[0].name == hero.name)
        case 'int':
            button_grid = next(i for i in intButtonsGrids if i[0].name == hero.name)
        case 'all':
            button_grid = next(i for i in allButtonsGrids if i[0].name == hero.name)
    # ACTIVATE DA BUTTON
    button_grid[1].config(state=NORMAL)
    button_grid[2].config(state=NORMAL)
    button_grid[3].config(state=NORMAL)
    # remove hero from picked/banned list, redraw picked/banned frame
    if hero in radiantPick:
        radiantPick.remove(hero)
        redrawGrid('radiant', radiantPick)
    elif hero in direPick:
        direPick.remove(hero)
        redrawGrid('dire', direPick)
    else:
        bannedHeroes.remove(hero)
        redrawGrid('ban', bannedHeroes)
    # if there is nothing picked or banned, no suggestions are made
    if len(bannedHeroes) == 0 and len(direPick) == 0:
        cleanSuggestions()
        suggestionsFrame.config(highlightthickness=0)
    else:
        recalculatePicks()


# Raised when button on hero grid loses focus
def onLostHover(side: str, hero: Hero, button):
    if side == 'radiant':
        button.config(image=hero.radiantPicture)
    elif side == 'ban':
        button.config(image=hero.banPicture)
    elif side == 'dire':
        button.config(image=hero.direPicture)



async def highlight(hero: Hero):
    button_grid = []
    match hero.attribute:
        case 'agi':
            button_grid = next(i for i in agiButtonsGrids if i[0].name == hero.name)
        case 'str':
            button_grid = next(i for i in strButtonsGrids if i[0].name == hero.name)
        case 'int':
            button_grid = next(i for i in intButtonsGrids if i[0].name == hero.name)
        case 'all':
            button_grid = next(i for i in allButtonsGrids if i[0].name == hero.name)
    parent = button_grid[1].master
    parent.config(highlightthickness=2, highlightcolor = 'red')
    asyncio.sleep(1)
    parent.config(highlightthickness=0)

async def onKeyDown(eventArgs):
    word.add(str(eventArgs.char))
    for hero in HeroList:
        if word.get() in hero.name:
            asyncio.create_task(highlight(hero))

root.bind('<KeyPress>', atl.async_handler(onKeyDown))

# -----------------------------------------------------------

# self-explanatory
def cleanSuggestions():
    for widgets in suggestionsFrame.winfo_children():
        for child in widgets.winfo_children():
            child.destroy()


# Raised when hero picked/banned
# 1. adds a hero to pick/ban
# 2. call redraw of pick/ban grid
# 3. disable hero buttons on hero grid
# 4. recalculate pick suggestions
def onClick(side: str, hero: Hero, button_grid):
    if side == 'radiant':
        if (len(radiantPick) < 5):
            radiantPick.append(hero)
            redrawGrid(side, radiantPick)
            button_grid[1].config(state=DISABLED)
            button_grid[2].config(state=DISABLED)
            button_grid[3].config(state=DISABLED)
            recalculatePicks()
    elif side == 'dire':
        if (len(direPick) < 5):
            direPick.append(hero)
            redrawGrid(side, direPick)
            button_grid[1].config(state=DISABLED)
            button_grid[2].config(state=DISABLED)
            button_grid[3].config(state=DISABLED)
            recalculatePicks()
    else:
        if (len(bannedHeroes) < 15):
            bannedHeroes.append(hero)
            redrawGrid(side, bannedHeroes)
            button_grid[1].config(state=DISABLED)
            button_grid[2].config(state=DISABLED)
            button_grid[3].config(state=DISABLED)
            recalculatePicks()


# Redraws pick grid, called when hero removed from pick/ban
def redrawGrid(side: str, heroes):
    sizeMod = False  # True when hero is banned, so its picture is twise as small
    # get parent frame where picked/banned hero is present
    if side == 'radiant':
        parentFrame = radiantPickGridFrame
    elif side == 'dire':
        parentFrame = direPickGridFrame
    else:
        parentFrame = banGridFrame
        sizeMod = True
    # remonve everything from frame
    for widget in parentFrame.winfo_children():
        # except label
        if isinstance(widget, Button):
            widget.destroy()
    colCounter = 0
    rowCounter = 1
    # add every picked/banned hero again
    for hero in heroes:
        new_button = Button(parentFrame, image=(hero.banPictureSmall if sizeMod else hero.picture))
        new_button.bind("<Button-1>", lambda eventArgs, hero=hero: onPickedClick(hero, eventArgs.widget))
        new_button.grid(column=colCounter, row=rowCounter, sticky=E)
        if colCounter >= 7:
            colCounter = 0
            rowCounter = 2
        else:
            colCounter += 1


# Calculates suggestions
def recalculatePicks():
    # hero puool
    pool = []
    # every hero who is not picked/banned
    for hero in HeroList:
        if hero not in direPick and hero not in radiantPick and hero not in bannedHeroes:
            poolitem = dict(hero=hero, value=50)  # By default every hero in pool has 50 points
            pool.append(poolitem)
    # Get a suggested hero from pool
    for suggestion in pool:
        # Get an enemy hero
        for enemyHero in direPick:
            # Get data about winrate of suggested hero against enemy hero
            for matchup in suggestion['hero'].matchups:
                if matchup['hero_id'] == enemyHero.id:
                    # Calculate winrate of suggested hero against a matchup hero
                    winrate_against = (matchup['wins'] / matchup['games_played']) * 100
                    if enemyHero.name == 'Bristleback' and suggestion['hero'].name == 'Clinkz':
                        print(winrate_against)
                    # Find out how much data about matchup we have
                    # max = maximal games played between 2 heroes (best data)
                    # min = minimal games played between 2 heroes (worst data)
                    # factor = 1 - (max - games played)/(max - min)
                    factor = 1 - (stats[1] - matchup['games_played']) / (stats[1] - stats[0])
                    # Matchup gets difference between winrate in matchup and 50% winrate, with consideration
                    # of how data ist trustworthy
                    suggestion['value'] += (winrate_against - 50) * (0.1 + 0.9 * factor)
        # Get a banned hero
        for bannedHero in bannedHeroes:
            # Get data about winrate of suggested hero against banned hero
            for matchup in suggestion['hero'].matchups:
                if matchup['hero_id'] == bannedHero.id:
                    # Calculate winrate of suggested hero against a banned hero
                    winrate_against = (matchup['wins'] / matchup['games_played']) * 100
                    # Same factor of trustworthiness as above
                    #factor = 1 - (stats[1] - matchup['games_played']) / (stats[1] - stats[0])
                    factor = 1
                    # Banned heroes is not so important
                    bannedFactor = 0.3
                    # if suggested hero is good against banned hero, then we don't care
                    if winrate_against - 50 < 0:
                        # if it was bad, we might want to pick this hero
                        suggestion['value'] += (50 - winrate_against) * factor * bannedFactor
    # sort suggested heroes by points
    pool = sorted(pool, key=lambda d: d['value'])
    pool.reverse()
    # clean suggestion frame
    cleanSuggestions()
    # add top 10 best heroes to frame
    label = Label(suggestionsFrameGeneral, text="General")
    label.grid(column=0, row=0)
    c = 0
    for item in pool[0:10]:
        Label(suggestionsFrameGeneral, image=item['hero'].picture).grid(column=c + 1, row=0)
        c += 1
    # add suggested heroes by role
    generateSuggestionGrid(pool, 5, suggestionsFrameHardSupport)
    generateSuggestionGrid(pool, 4, suggestionsFrameSoftSupport)
    generateSuggestionGrid(pool, 3, suggestionsFrameOfflaner)
    generateSuggestionGrid(pool, 2, suggestionsFrameMidlaner)
    generateSuggestionGrid(pool, 1, suggestionsFrameCarry)
    # old role grids
    # generateSuggestionGrid(pool, 'Support', suggestionsFrameSupport)
    # generateSuggestionGrid(pool, 'Nuker', suggestionsFrameNuker)
    # generateSuggestionGrid(pool, 'Disabler', suggestionsFrameDisabler)
    # generateSuggestionGrid(pool, 'Escape', suggestionsFrameEscape)
    # generateSuggestionGrid(pool, 'Carry', suggestionsFrameCarry)
    # generateSuggestionGrid(pool, 'Pusher', suggestionsFramePusher)
    # generateSuggestionGrid(pool, 'Initiator', suggestionsFrameInitiator)
    suggestionsFrame.config(highlightthickness=2)


def generateSuggestionGrid(pool, role: int, sFrame: Frame):
    count = 0  # counts how many heroes were added
    rolePool = []
    # get best heroes suitable for the role
    for poolitem in pool:
        if role in poolitem['hero'].roles:
            rolePool.append(poolitem['hero'])
            count += 1
        if count > 9:
            break
    # remove old suggestion from grid
    for widgets in sFrame.winfo_children():
        widgets.destroy()
    # find out the rolename TODO: make a dictionary
    rolename = ''
    match role:
        case 1:
            rolename = 'Carry'
        case 2:
            rolename = 'Midlaner'
        case 3:
            rolename = 'Offlaner'
        case 4:
            rolename = 'Soft Support'
        case 5:
            rolename = 'Hard Support'
    # add heroes to grid
    count = 1
    for hero in rolePool:
        Label(sFrame, image=hero.picture).grid(column=count, row=0)
        count += 1
    # add label with role name in first column
    label1 = Label(sFrame, text=rolename)
    label1.grid(column=0, row=0)


# Creates hero grid
# input : list of heroes (of same attribute), frame to place it
# output : array of dicts {Hero, add to radiant button, add to dire button, bun button}
def generateGrid(heroList, frame: Frame):
    rowC = 0
    colC = 0
    counter = 0
    grids = []
    # Creating buttons
    for hero in heroList:
        # Each hero consists of three buttons, two buttons in upper frame, one button in lower frame
        buttonFrame = Frame(frame, height=56, width=100, borderwidth=0, highlightthickness=0)
        buttonFrameTop = Frame(buttonFrame, height=41, width=100, borderwidth=0)
        buttonFrameBot = Frame(buttonFrame, height=15, width=100, borderwidth=0)
        radiantButton = Button(buttonFrameTop, image=hero.radiantPicture, borderwidth=0, highlightthickness=0)
        radiantButton.grid(row=0, column=0, sticky=NW)
        direButton = Button(buttonFrameTop, image=hero.direPicture, borderwidth=0, highlightthickness=0)
        direButton.grid(row=0, column=1, sticky=NW)
        banButton = Button(buttonFrameBot, image=hero.banPicture, borderwidth=0, highlightthickness=0)
        banButton.grid(row=0, column=0, sticky=NW)
        grids.append([hero, radiantButton, direButton, banButton])
        buttonFrameTop.grid(row=0, sticky=NW)
        buttonFrameBot.grid(row=1, sticky=NW)
        buttonFrame.grid(column=colC, row=rowC, sticky=NW, padx=0, pady=0)
        # max 5 heroes in one row
        if colC == 4:
            colC = 0
            rowC += 1
        else:
            colC += 1
    return grids


# Stores button grids, so we can access buttons later
strButtonsGrids = generateGrid(strHeroes, strFrame)
agiButtonsGrids = generateGrid(agiHeroes, agiFrame)
intButtonsGrids = generateGrid(intHeroes, intFrame)
allButtonsGrids = generateGrid(allHeroes, allFrame)


# Binds events so hero highlited when howered and blocked when picked/banned
def eventBinding(grids):
    for i in range(len(grids)):
        # radiant
        grids[i][1].bind("<Enter>", lambda eventArgs, i=i: onHover('radiant', grids[i][0], eventArgs.widget))
        grids[i][1].bind("<Leave>", lambda eventArgs, i=i: onLostHover('radiant', grids[i][0], eventArgs.widget))
        grids[i][1].bind("<Button-1>", lambda eventArgs, i=i: onClick('radiant', grids[i][0], grids[i]))
        # dire
        grids[i][2].bind("<Enter>", lambda eventArgs, i=i: onHover('dire', grids[i][0], eventArgs.widget))
        grids[i][2].bind("<Leave>", lambda eventArgs, i=i: onLostHover('dire', grids[i][0], eventArgs.widget))
        grids[i][2].bind("<Button-1>", lambda eventArgs, i=i: onClick('dire', grids[i][0], grids[i]))
        # ban
        grids[i][3].bind("<Enter>", lambda eventArgs, i=i: onHover('ban', grids[i][0], eventArgs.widget))
        grids[i][3].bind("<Leave>", lambda eventArgs, i=i: onLostHover('ban', grids[i][0], eventArgs.widget))
        grids[i][3].bind("<Button-1>", lambda eventArgs, i=i: onClick('ban', grids[i][0], grids[i]))


eventBinding(strButtonsGrids)
eventBinding(agiButtonsGrids)
eventBinding(intButtonsGrids)
eventBinding(allButtonsGrids)

mainloop()
