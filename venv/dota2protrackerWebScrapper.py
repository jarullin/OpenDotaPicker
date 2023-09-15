import bs4.element
import requests
import json
from bs4 import BeautifulSoup
import re

HeroList = []
rawData = []
with open('herotable.json') as f:
    rawData = json.load(f)
    # Create and fill hero instances
output = '['
for item in rawData:
    heroItem = dict(id = item['id'], name = item['localized_name'])
    HeroList.append(heroItem)
    response = requests.get('https://dota2protracker.com/hero/'+item['localized_name']+'#')
    if response.status_code != 200:
        raise RuntimeError
    soup = BeautifulSoup(response.text, 'html.parser')
    heroStats = soup.find('div',class_='role-tabs')
    roles = []
    if not isinstance(heroStats.find(lambda tag:'Carry' in tag.text), type(None)) and heroStats.find_all(lambda tag:'Carry' in tag.text).__len__() > 0:
        roles.append(1)
    if not isinstance(heroStats.find(lambda tag:'Mid' in tag.text), type(None)) and heroStats.find(lambda tag:'Mid' in tag.text).__len__() > 0:
        roles.append(2)
    if not isinstance(heroStats.find(lambda tag:'Offlane' in tag.text), type(None)) and heroStats.find(lambda tag:'Offlane' in tag.text).__len__() > 0:
        roles.append(3)
    if not isinstance(heroStats.find(lambda tag:'Support (4)' in tag.text), type(None)) and heroStats.find(lambda tag:'Support (4)' in tag.text).__len__() > 0:
        roles.append(4)
    if not isinstance(heroStats.find(lambda tag:'Support (5)' in tag.text), type(None)) and heroStats.find(lambda tag:'Support (5)' in tag.text).__len__() > 0:
        roles.append(5)
    item['roles']=roles
    output += json.dumps(item, indent = 4) + ',\n'
output = output[:-2]+ ']'
with open('herotable.json', 'w') as f:
    f.write(output)

