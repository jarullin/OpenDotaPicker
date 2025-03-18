import asyncio
import copy
import email.charset
import json
import os
import time
import datetime
import tkinter.ttk
import threading
from tkinter import *
from tkinter import ttk, font

import Loaders
import requests
from PIL import Image, ImageTk, ImageDraw, ImageFont
from datetime import date, timedelta
import cv2
import numpy as np
from pathlib import Path
import async_tkinter_loop as atl
import ViewModel as ViewModel
from Model import Hero, Winrate

# Globals
bgColor = "#282825"  # Stores background color
HeroList = []
class App:
    def __init__(self, master: Tk) -> None:
        self.master = master
        # Creating a Font object of "TkDefaultFont"
        self.defaultFont = font.nametofont("TkDefaultFont")
        # Overriding default-font with custom settings
        self.defaultFont.configure(family="Helvetica",
                                   size=20,
                                   weight=font.NORMAL)
        style = tkinter.ttk.Style()
        style.theme_use('clam')
        self.factorVar = IntVar()
        self.factorVar.set(1)

def initialize():
    global HeroLists
    print("Loading hero data from file")
    HeroList = Loaders.load_hero_data("herotable.json")
    print("Loading hero data from file complete")
    # Loading hero pictures
    print("Loading hero pictures")
    HeroList[:] = Loaders.getHeroPictures(HeroList)
    print("Pictures are loaded")
    # Check if the file up to date
    HeroListOutdated = datetime.datetime.fromtimestamp(
            os.path.getmtime('../herotable.json')) < datetime.datetime.today() - datetime.timedelta(days=7)
    MatchupsOutdated = not Path('../heromatchups.json').is_file() or datetime.datetime.fromtimestamp(
            os.path.getmtime('../heromatchups.json')) < datetime.datetime.today() - datetime.timedelta(days=7)
    print("Main thread: "+str(threading.get_ident()))
    if HeroListOutdated:
        print("Roles are outdated, starting update")
        role_upd_thread = threading.Thread(target=Loaders.update_roles, args=(HeroList,), daemon=True)
        role_upd_thread.start()
    print("Loading matchup data from file")
    Loaders.load_matchup_data(HeroList)
    # If there is no file or it's more than 1 week old, get matchup data from OpenDota
    if MatchupsOutdated:
        print("Matchups are is outdated, starting update")
        loading_thread = threading.Thread(target=Loaders.update_matchup_data, args=(HeroList,), daemon=True)
        loading_thread.start()
    return HeroList




# Entry point
root = Tk()
app = App(root)
root.tk_setPalette(background=bgColor, foreground="white", highlightbackground="gray")
HeroList = initialize()

# Layout
root.title("OpenDotaPicker")
root.geometry('2100x1080')
mainFrame = Frame(root)
mainFrame.grid(sticky=E + W + N + S)
# mainFrame children
# 1. Picks
pickFrame = Frame(mainFrame, height=100, width=root.winfo_screenwidth(), bg=bgColor)
pickFrame.grid(row=0, column=0, sticky=NW)
# 2. Heroes
heroGridFrame = Frame(mainFrame, height=56 * 7, bg=bgColor)
heroGridFrame.grid(row=1, column=0, sticky=EW, columnspan=4)
# 3. Suggestions
suggestionsFrame = Frame(mainFrame, bg=bgColor, highlightbackground="gray")
suggestionsFrame.grid(row=2, sticky=W, padx=(30, 0), pady=(5, 0))
# 4. Status bar
factorBool = BooleanVar(root)
factorBool.set(True)
greedBool = BooleanVar(root)
greedBool.set(True)
statusBarFrame = Frame(mainFrame, height=30)
statusBarFrame.grid(row=3, sticky=W, padx=(30, 0), pady=(5, 0))
# 5. Footer frame
root.rowconfigure(1, weight=1)
footerFrame = Frame(root)
footerFrame.grid(row=1,sticky=SE)
progressbar = tkinter.ttk.Progressbar(footerFrame, orient='horizontal', length=250, mode='determinate')
updLabel = Label(footerFrame, text='Database is up to date')
updLabel.grid(column=0,row=0,sticky=E)
progressbar.grid(column=1, row=0, sticky=E)
progressbar['value']=Loaders.Status
# Pick Frame children
# 1.1 team pick
teamPickGridFrame = Frame(pickFrame, height=88, width=535, bg=bgColor, highlightthickness=2,
                          highlightbackground="gray")
teamPickGridFrame.grid(row=0, column=0, sticky=W, padx=(20, 20))
teamPickGridFrame.grid_propagate(0)
teamPickLabel = Label(teamPickGridFrame, text="Your team pick", font=("Verdana", 10))
teamPickLabel.grid(row=0, column=0, columnspan=5)
teamPickStatsLabel = Label(teamPickGridFrame, text='', font=("Verdana",8))
teamPickStatsLabel.grid(row=0, column=1, columnspan=4, sticky=W)

# 1.2 Banned heroes
banGridFrame = Frame(pickFrame, bg=bgColor, height=88, width=58 * 8, highlightthickness=2, highlightbackground="gray")
banGridFrame.grid(row=0, column=1, sticky=N, padx=(20, 20))
banGridFrame.grid_propagate(0)
banLabel = Label(banGridFrame, text="Banned", font=("Verdana", 10))
banLabel.grid(row=0, column=0, columnspan=15)
# 1.3 enemy pick
enemyPickGridFrame = Frame(pickFrame, bg="#282825", height=88, width=535, highlightthickness=2,
                           highlightbackground="gray")
enemyPickGridFrame.grid(row=0, column=2, sticky=E, padx=(20, 20))
enemyPickGridFrame.grid_propagate(0)
enemyPickLabel = Label(enemyPickGridFrame, text="Enemy team pick", font=("Verdana", 10))
enemyPickLabel.grid(row=0, column=0, columnspan=5)

heroGridFrame.columnconfigure(0, weight=1)
heroGridFrame.columnconfigure(1, weight=1)
heroGridFrame.columnconfigure(2, weight=1)
heroGridFrame.columnconfigure(3, weight=1)
# heroFrame children
# 2.1 Strength heroes
strFrame = Frame(heroGridFrame, height=heroGridFrame.winfo_height(), width=460, highlightbackground="gray",
                 highlightthickness=2)
strFrame.grid(column=0, row=1, padx=(20, 0), sticky=NW)
# 2.2 Agility heroes
agiFrame = Frame(heroGridFrame, height=heroGridFrame.winfo_height(), width=460, highlightbackground="gray",
                 highlightthickness=2)
agiFrame.grid(column=1, row=1, padx=(5, 0), sticky=NW)
# 2.3 Intelligence heroes
intFrame = Frame(heroGridFrame, height=heroGridFrame.winfo_height(), width=460, highlightbackground="gray",
                 highlightthickness=2)
intFrame.grid(column=2, row=1, padx=(5, 0), sticky=NW)
# 2.4 Universal heroes
allFrame = Frame(heroGridFrame, height=heroGridFrame.winfo_height(), width=460, highlightbackground="gray",
                 highlightthickness=2)
allFrame.grid(column=3, row=1, padx=(5, 0), sticky=NW)

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

# Stores hero list sorted by attributes
strHeroes, agiHeroes, intHeroes, allHeroes = ViewModel.getAttributeHeroLists(HeroList)
# Lists of banned and picked heroes
bannedHeroes, teamPick, enemyPick = [], [], []


### E V E N T    H A N D L E R S
# ---------------------------------------------------------


# Raised when hero picked/banned
# 1. adds a hero to pick/ban
# 2. call redraw of pick/ban grid
# 3. disable hero buttons on hero grid
# 4. recalculate pick suggestions
def onHeroGridLeftClick(hero: Hero, button: Button):
    if (len(teamPick) < 5) and button.widget['state'] != DISABLED:
        teamPick.append(hero)
        button.widget.config(state=DISABLED)
        redrawGrid('team')
        recalculatePicks()


def onHeroGridMiddleClick(hero: Hero, button: Button):
    if (len(bannedHeroes) < 15) and button.widget['state'] != DISABLED:
        bannedHeroes.append(hero)
        button.widget.config(state=DISABLED)
        redrawGrid('ban')
        recalculatePicks()


def onHeroGridRightClick(hero: Hero, button: Button):
    if (len(enemyPick) < 5) and button.widget['state'] != DISABLED:
        enemyPick.append(hero)
        button.widget.config(state=DISABLED)
        redrawGrid('enemy')
        recalculatePicks()


def onPickedLeftClick(hero: Hero, widget):
    # If hero in team pick - remove from picked heroes
    if hero in teamPick:
        teamPick.remove(hero)
        redrawGrid('team')
        button_grid = []
        # find and activate hero button on grid
        match hero.attribute:
            case 'agi':
                button_grid = next(i for i in agiButtonsGrid if i[0].name == hero.name)
            case 'str':
                button_grid = next(i for i in strButtonsGrid if i[0].name == hero.name)
            case 'int':
                button_grid = next(i for i in intButtonsGrid if i[0].name == hero.name)
            case 'all':
                button_grid = next(i for i in allButtonsGrid if i[0].name == hero.name)
        button_grid[1].config(state=NORMAL)
    # if hero banned - move it to team pick
    elif hero in bannedHeroes:
        if len(teamPick) < 5:
            bannedHeroes.remove(hero)
            redrawGrid('ban')
            teamPick.append(hero)
            redrawGrid('team')
    # if hero in enemy pick - move to team pick
    else:
        if len(teamPick) < 5:
            enemyPick.remove(hero)
            redrawGrid('enemy')
            teamPick.append(hero)
            redrawGrid('team')
    recalculatePicks()


def onPickedMiddleClick(hero: Hero, widget):
    # If hero in team pick - move to banned
    if hero in teamPick:
        if len(bannedHeroes) < 15:
            teamPick.remove(hero)
            redrawGrid('team')
            bannedHeroes.append(hero)
            redrawGrid('ban')
    # if hero is banned - remove from grid
    elif hero in bannedHeroes:
        bannedHeroes.remove(hero)
        redrawGrid('ban')
        button_grid = []
        # find and activate hero button on grid
        match hero.attribute:
            case 'agi':
                button_grid = next(i for i in agiButtonsGrid if i[0].name == hero.name)
            case 'str':
                button_grid = next(i for i in strButtonsGrid if i[0].name == hero.name)
            case 'int':
                button_grid = next(i for i in intButtonsGrid if i[0].name == hero.name)
            case 'all':
                button_grid = next(i for i in allButtonsGrid if i[0].name == hero.name)
        button_grid[1].config(state=NORMAL)
    # if hero in enemy pick - move to banned
    else:
        if len(bannedHeroes) < 15:
            enemyPick.remove(hero)
            redrawGrid('enemy')
            bannedHeroes.append(hero)
            redrawGrid('ban')
    recalculatePicks()


def onPickedRightClick(hero: Hero, widget):
    # If hero in team pick - move to enemy
    if hero in teamPick:
        if len(enemyPick) < 5:
            teamPick.remove(hero)
            redrawGrid('team')
            enemyPick.append(hero)
            redrawGrid('enemy')
    # if hero in enemy pick - remove from grid
    elif hero in enemyPick:
        enemyPick.remove(hero)
        redrawGrid('enemy')
        button_grid = []
        # find and activate hero button on grid
        match hero.attribute:
            case 'agi':
                button_grid = next(i for i in agiButtonsGrid if i[0].name == hero.name)
            case 'str':
                button_grid = next(i for i in strButtonsGrid if i[0].name == hero.name)
            case 'int':
                button_grid = next(i for i in intButtonsGrid if i[0].name == hero.name)
            case 'all':
                button_grid = next(i for i in allButtonsGrid if i[0].name == hero.name)
        button_grid[1].config(state=NORMAL)
    # if hero is banned - move to enemy
    else:
        if len(enemyPick) < 5:
            bannedHeroes.remove(hero)
            redrawGrid('ban')
            enemyPick.append(hero)
            redrawGrid('enemy')
    recalculatePicks()

# Label for searching on grid
textLabel = Label(suggestionsFrame, text='')
textLabel.grid(column=1, row=6)


def onKeyDown(e):
    lastUpd.update()
    if is_alpha(e.char):
        textLabel.config(text=textLabel['text'] + e.char)
        enableAllHeroes()
        hideHeroes()
        root.after(2000, lambda: refreshLabel())


root.bind('<KeyPress>', onKeyDown)


class TimedValue:
    def __init__(self):
        self._started_at = datetime.datetime.now(datetime.UTC)

    def __call__(self):
        time_passed = datetime.datetime.utcnow() - self._started_at
        return time_passed.total_seconds() > 1

    def update(self):
        self._started_at = datetime.datetime.utcnow()


lastUpd = TimedValue()


def refreshLabel():
    if lastUpd():
        enableAllHeroes()
        textLabel.config(text='')


def enableAllHeroes():
    for agiHero in agiButtonsGrid:
        if agiHero[0] not in teamPick and agiHero[0] not in enemyPick and agiHero[0] not in bannedHeroes:
            agiHero[1].config(state=NORMAL, image=agiHero[0].image)
        else:
            agiHero[1].config(image=agiHero[0].image)
    for strHero in strButtonsGrid:
        if strHero[0] not in teamPick and strHero[0] not in enemyPick and strHero[0] not in bannedHeroes:
            strHero[1].config(state=NORMAL, image=strHero[0].image)
        else:
            strHero[1].config(image=strHero[0].image)
    for intHero in intButtonsGrid:
        if intHero[0] not in teamPick and intHero[0] not in enemyPick and intHero[0] not in bannedHeroes:
            intHero[1].config(state=NORMAL, image=intHero[0].image)
        else:
            intHero[1].config(image=intHero[0].image)
    for allHero in allButtonsGrid:
        if allHero[0] not in teamPick and allHero[0] not in enemyPick and allHero[0] not in bannedHeroes:
            allHero[1].config(state=NORMAL, image=allHero[0].image)
        else:
            allHero[1].config(image=allHero[0].image)


def hideHeroes():
    hideHero(strButtonsGrid)
    hideHero(agiButtonsGrid)
    hideHero(intButtonsGrid)
    hideHero(allButtonsGrid)


def hideHero(heroGrid):
    for hero in heroGrid:
        if textLabel['text'].lower() not in hero[0].name.lower() and not any(
                textLabel['text'].lower() in s.lower() for s in hero[0].aliases):
            hero[1].config(state=DISABLED)
        else:
            if hero[1]['state'] != DISABLED:
                hero[1].config(image=hero[0].highlightedImage)


# -----------------------------------------------------------

# self-explanatory
def cleanSuggestions():
    for widgets in suggestionsFrame.winfo_children():
        for child in widgets.winfo_children():
            child.destroy()
    suggestionsFrame.config(highlightthickness=0)


def is_alpha(word):
    try:
        return word.encode('ascii').isalpha()
    except:
        return False


# Redraws pick grid, called when hero removed from pick/ban
def redrawGrid(side: str):
    sizeMod = False  # True when hero is banned, so its picture is twise as small
    # get parent frame where picked/banned hero is present
    heroes = []
    if side == 'team':
        parentFrame = teamPickGridFrame
        heroes = teamPick
    elif side == 'enemy':
        parentFrame = enemyPickGridFrame
        heroes = enemyPick
    else:
        parentFrame = banGridFrame
        heroes = bannedHeroes
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
        new_button = Button(parentFrame, image=(hero.banImageSmall if sizeMod else hero.image))
        new_button.bind("<Button-1>", lambda eventArgs, hero=hero: onPickedLeftClick(hero, eventArgs.widget))
        new_button.bind("<Button-3>", lambda eventArgs, hero=hero: onPickedRightClick(hero, eventArgs.widget))
        new_button.bind("<Button-2>", lambda eventArgs, hero=hero: onPickedMiddleClick(hero, eventArgs.widget))
        new_button.grid(column=colCounter, row=rowCounter, sticky=E)
        if colCounter >= 7:
            colCounter = 0
            rowCounter = 2
        else:
            colCounter += 1


# Calculates suggestions
def recalculatePicks():
    if len(enemyPick) == 0 and len(bannedHeroes) == 0 and len(teamPick) == 0:
        cleanSuggestions()
        return
    # Suggested hero pool
    pool = []
    # every hero who is not picked/banned
    for hero in HeroList:
        if hero not in enemyPick and hero not in teamPick and hero not in bannedHeroes:
            poolitem = dict(hero=hero, value=50)  # By default every hero in pool has 50 points
            pool.append(poolitem)
    enemyGreed = 0.0
    enemyDpm = 0.0
    enemyTdmg = 0.0
    for enemyHero in enemyPick:
        enemyGreed += enemyHero.gpm
        enemyDpm += enemyHero.dpm
        enemyTdmg += enemyHero.tdmg
    allyGreed = 0.0
    allyDpm = 0.0
    allyTdmg = 0.0
    for allyHero in teamPick:
        allyGreed += allyHero.gpm
        allyDpm += allyHero.dpm
        allyTdmg += allyHero.tdmg
    if len(teamPick) > 0:
        teamPickStatsLabel.config(text="gpm::{:.2f}, dpm::{:.2f}, towerdmg::{:.2f}".format(allyGreed / len(teamPick), allyDpm / len(teamPick), allyTdmg / len(teamPick)))
    # Get a suggested hero from pool
    for suggestion in pool:
        # Get an enemy hero
        for enemyHero in enemyPick:
            # Get data about winrate of suggested hero against enemy hero
            for matchup in suggestion['hero'].matchups:
                if matchup.enemyId == enemyHero.id:
                    # Calculate winrate of suggested hero against a matchup hero
                    winrate_against = matchup.winrate * 100
                    # Find out how much data about matchup we have
                    # max = maximal games played with suggested hero (best data)
                    # min = minimal games played with suggested hero (worst data)
                    # matchup_factor = 1 - (max games - games played)/(max - min)
                    matchup_factor = 0 - factorBool.get() * (enemyHero.maxMatchupN - matchup.n) / (enemyHero.maxMatchupN - enemyHero.minMatchupN) + 1
                    # Matchup gets difference between winrate in matchup and 50% winrate, with consideration
                    # of how data is trustworthy
                    enemyGreedAvg = enemyGreed / len(enemyPick)
                    allyGreedAvgSugg = (allyGreed + suggestion['hero'].gpm)/(len(teamPick) + 1)
                    greedFactor = 1
                    if greedBool.get() and enemyGreedAvg < allyGreedAvgSugg:
                        greedFactor += (enemyGreedAvg - allyGreedAvgSugg) / 300
                    if winrate_against - 50 >= 0:
                        suggestion['value'] += (winrate_against - 50) * (0.1 + 0.9 * matchup_factor) * greedFactor
                    else:
                        suggestion['value'] += (winrate_against - 50) * (0.1 + 1.8 * matchup_factor) * greedFactor
        # Get a banned hero
        for bannedHero in bannedHeroes:
            # Get data about winrate of suggested hero against banned hero
            for matchup in suggestion['hero'].matchups:
                if matchup.enemyId == bannedHero.id:
                    # Calculate winrate of suggested hero against a banned hero
                    winrate_against = matchup.winrate * 100
                    # Same factor of trustworthiness as above
                    # factor = 1 - (stats[1] - matchup['games_played']) / (stats[1] - stats[0])
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

    for poolItem in pool:
        img = ImageTk.getimage(poolItem['hero'].image)
        draw = ImageDraw.Draw(img)
        # thin border
        x = 60
        y = 40
        font = ImageFont.truetype("Fonts//3574.ttf", size=15)
        draw.text((x - 1, y), "{0:0.2f}".format(poolItem['value']), font=font, fill='black')
        draw.text((x + 1, y), "{0:0.2f}".format(poolItem['value']), font=font, fill='black')
        draw.text((x, y - 1), "{0:0.2f}".format(poolItem['value']), font=font, fill='black')
        draw.text((x, y + 1), "{0:0.2f}".format(poolItem['value']), font=font, fill='black')
        draw.text((x, y), "{0:0.2f}".format(poolItem['value']), font=font, fill='white')
        poolItem['hero'].suggestionImage = ImageTk.PhotoImage(img)
    # clean suggestion frame
    cleanSuggestions()
    # add top 10 best heroes to frame
    label = Label(suggestionsFrameGeneral, text="General")
    label.grid(column=0, row=0)
    c = 0
    for item in pool[0:10]:
        Label(suggestionsFrameGeneral, image=item['hero'].suggestionImage).grid(column=c + 1, row=0)
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


# Generates suggestion row for role
def generateSuggestionGrid(pool, role: int, sFrame: Frame):
    count = 0  # counts how many heroes were added
    rolePool = []
    # get best heroes suitable for the role
    for poolitem in pool:
        if role in poolitem['hero'].roles:
            rolePool.append(poolitem)
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
    for poolItem in rolePool:
        Label(sFrame, image=poolItem['hero'].suggestionImage).grid(column=count, row=0)
        count += 1
    # add label with role name in first column
    label1 = Label(sFrame, text=rolename)
    label1.grid(column=0, row=0)


# Creates hero grid
# input : list of heroes (of same attribute), frame to place it
# output : array of dicts {Hero, add to team button, add to enemy button, bun button}
def drawHeroGrid(heroList, frame: Frame):
    rowC = 0
    colC = 0
    counter = 0
    grid = []
    # Creating buttons
    for hero in heroList:
        # Each hero consists of three buttons, two buttons in upper frame, one button in lower frame
        buttonFrame = Frame(frame, height=56, width=100, borderwidth=0, highlightthickness=0)
        heroButton = Button(buttonFrame, image=hero.image, borderwidth=0, highlightthickness=1)
        heroButton.grid(column=0, row=0)
        heroButton.bind("<Button-1>", lambda heroButton=heroButton, hero=hero: onHeroGridLeftClick(hero, heroButton))
        heroButton.bind("<Button-2>", lambda heroButton=heroButton, hero=hero: onHeroGridMiddleClick(hero, heroButton))
        heroButton.bind("<Button-3>", lambda heroButton=heroButton, hero=hero: onHeroGridRightClick(hero, heroButton))
        buttonFrame.grid(column=colC, row=rowC, sticky=NW, padx=0, pady=0)
        grid.append([hero, heroButton])
        # max 5 heroes in one row
        if colC == 4:
            colC = 0
            rowC += 1
        else:
            colC += 1
    return grid


strButtonsGrid = drawHeroGrid(strHeroes, strFrame)
agiButtonsGrid = drawHeroGrid(agiHeroes, agiFrame)
intButtonsGrid = drawHeroGrid(intHeroes, intFrame)
allButtonsGrid = drawHeroGrid(allHeroes, allFrame)
factorCheckbutton = Checkbutton(statusBarFrame, text="Use the number of games in a matchup as a factor", var=factorBool,
                                font=("Verdana", 10), activeforeground='white', selectcolor="black",
                                command=recalculatePicks)
factorCheckbutton.grid(row=0, column=0, sticky=W)
greedCheckbutton = Checkbutton(statusBarFrame, text="Use ally greed as a factor", var=greedBool,
                                font=("Verdana", 10), activeforeground='white', selectcolor="black",
                                command=recalculatePicks)
greedCheckbutton.grid(row=1, column=0, sticky=W)


# on a button click
def exportTable():
    # Creating hero name to column dict
    length = len(HeroList) + 1
    id_to_column = {}
    for i in range(len(HeroList)):
        id_to_column[HeroList[i].id] = i + 1
    _table = []
    _row = [None] * length
    # Header row
    _row[0] = ''
    for i in range(len(HeroList)):
        _row[i + 1] = HeroList[i].name
    _table.append(_row)
    # Content
    # Row
    for r in range(len(HeroList)):
        row = [None] * length
        row[0] = HeroList[r].name
        for matchup in HeroList[r].matchups:
            row[id_to_column[matchup.enemyId]] = "{:d} / {:d}".format(int(matchup.winrate * matchup.n), matchup.n)
        _table.append(row)
    import xlsxwriter
    workbook = xlsxwriter.Workbook('heromatchups.xlsx')
    worksheet = workbook.add_worksheet()

    for r in range(len(_table)):
        for c in range(len(_table[i])):
            worksheet.write(r, c, _table[r][c])
    workbook.close()


# a button widget which will open a
# new window on button click
tableViewButton = Button(statusBarFrame,
                         text="Export winrate table",
                         command=exportTable)
tableViewButton.grid(row=0, column=1)
try:
    mainloop()
except Exception as Argument:

    # creating/opening a file
    f = open("log.txt", "a")

    # writing in the file
    f.write(str(Argument))

    # closing the file
    f.close()
