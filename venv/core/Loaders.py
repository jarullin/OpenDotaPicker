import json
import os
import re
import threading
import time

import Model
import Utility
import requests
from PIL import Image, ImageTk, ImageDraw

Status = 0


# Loads roles from Dota2ProTracker
def update_roles(HeroList):
    print("Updating roles, thread=" + str(threading.get_ident()))
    counter = 0
    print("    ", end="")
    for hero in HeroList:
        counter += 1
        print("\rReceiving data " + str(counter) + " of " + str(len(HeroList)), end="")
        Status = counter / len(HeroList)
        try:
            response = requests.get('https://dota2protracker.com/hero/' + hero.name)
        except:
            print(response.status_code)
        if response.status_code != 200:
            raise RuntimeError

        text = response.text
        if "heroStats" in text:
            index = text.index("heroStats") + 10
            text = text[index:]
            matches_key = 'matches'
            index2 = text.index("buildData")
            text = text[0:index2 - 1]
        else:
            index = text.index("hero_stats") + 11
            text = text[index:]
            matches_key = 'num_matches'
            index2 = text.index("]")+2
            text = text[0:index2 - 1]

        fixed_json = (re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
                      .replace("'", '"')).replace(":.",":0.")
        print(fixed_json)
        res = json.loads(fixed_json)
        total_matches = 0
        roles = []
        for x in res:
            if x['position'] == "all":
                total_matches = x[matches_key]
        for x in res:
            if x['position'] == 'pos 1':
                if x[matches_key] >= total_matches * 0.2:
                    roles.append(1)
                continue

            if x['position'] == 'pos 2':
                if x[matches_key] >= total_matches * 0.2:
                    roles.append(2)
                continue

            if x['position'] == 'pos 3':
                if x[matches_key] >= total_matches * 0.2:
                    roles.append(3)
                continue

            if x['position'] == 'pos 4':
                if x[matches_key] >= total_matches * 0.2:
                    roles.append(4)
                continue

            if x['position'] == 'pos 5':
                if x[matches_key] >= total_matches * 0.2:
                    roles.append(5)
                continue
        hero.roles = roles
    Utility.saveHeroTable(HeroList, "data/herotable.json")
    return HeroList
    # print("Role update finished, reloading HeroList from file")
    # HeroList[:] = load_hero_data()
    # print("Reloading pictures")
    # HeroList[:] = getHeroPictures(HeroList)


# Loads hero data from file:
def load_hero_data(path: str) -> []:
    HeroList = []
    # Load hero data from file
    with open(path, "r") as f:
        rawData = json.load(f)
        # Create and fill hero instances
        for item in rawData:
            heroInstance = Model.Hero()
            heroInstance.id = item['id']
            heroInstance.dotaName = item['name']
            heroInstance.name = item['localized_name']
            heroInstance.attackType = item['attack_type']
            heroInstance.roles = item['roles']
            heroInstance.attribute = item['primary_attr']
            heroInstance.aliases = item['aliases']
            heroInstance.gpm = item['gpm']
            heroInstance.dpm = item['dpm']
            heroInstance.tdmg = item['tdmg']
            HeroList.append(heroInstance)
    return HeroList


# Loads matchup data from OpenDotaAPI:
Status = 0


def update_matchup_data(HeroList):
    print("Updating matchups, thread=" + str(threading.get_ident()))
    output = ''
    counter = 0
    print("    ", end="")
    for hero in HeroList:
        counter += 1
        print("\rReceiving data " + str(counter) + " of " + str(len(HeroList)), end="")
        # Status += 100/len(_heroList)
        responce = requests.get("https://api.opendota.com/api/heroes/" + str(hero.id) + "/matchups")
        if responce.status_code != 200:
            raise RuntimeError
        matchups = responce.json()
        time.sleep(1)
        output += "[\"id\" : " + str(hero.id) + " , \"matchups\" : " + str(matchups) + ']\n'
    print("")
    # Saving data
    output = output.replace("\'", "\"")
    with open('data/heromatchups.json', 'w') as f:
        f.write(output)
    # reload matchups
    print("Matchup update finished, reloading matchups from file")
    HeroList[:] = load_matchup_data(HeroList)


# Loads matchup data from file:
def load_matchup_data(heroList: []):
    # Check if there is a matchups file
    stats = [0, 10000]
    # Loading matchup data from file
    with open('data/heromatchups.json', 'r') as f:
        for line in f:
            line = "{" + line[1:-2].replace('id ', 'id') + "}"
            matchupData = json.loads(line)
            hero = Utility.getHeroById(matchupData['id'], heroList)
            matchups = matchupData['matchups']
            # Getting minimal und maximal number of games played in matchup. Is needed to estimate
            # how good matchup data is
            # stats[0] - minimal games played, stats[1] - maximal
            for matchup in matchups:
                hero.maxMatchupN = matchup['games_played'] if hero.maxMatchupN < matchup[
                    'games_played'] else hero.maxMatchupN
                hero.minMatchupN = matchup['games_played'] if hero.minMatchupN > matchup[
                    'games_played'] else hero.minMatchupN
            # Free OpenDota API limits the number of requests to 60 per minute
            newMatchupList = []
            for matchup in matchups:
                newMatchupList.append(
                    Model.Winrate(_enemyId=matchup['hero_id'], _winrate=matchup['wins'] / matchup['games_played'],
                                  _n=matchup['games_played']))
            hero.matchups = newMatchupList
    Status = 100
    return heroList


# Loads hero pictures
def getHeroPictures(heroList: []) -> []:
    for hero in heroList:
        source = Image.open('img\\' + hero.attribute + "\\" + hero.name + "_icon.gif").resize((100, 56))
        hero.image = ImageTk.PhotoImage(source)
        # Creating button pictures
        hero.banImageSmall = ImageTk.PhotoImage(ImageTk.getimage(hero.image).resize((50, 28)))
        source = source.convert("RGB")
        draw = ImageDraw.Draw(source)
        draw.rectangle([(0, 0), (100, 56)], outline='#49fc03', width=5)
        hero.suggestionImage = hero.image
        hero.highlightedImage = ImageTk.PhotoImage(source)
    return heroList
