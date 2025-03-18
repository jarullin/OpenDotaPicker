from Loaders import load_hero_data
import requests
import json
import os, time


def parse(herotable: []):
    output = []
    output = ''
    counter = 0
    for hero in herotable:
        counter += 1
        params = {'hero_id': hero.id}
        responce = requests.get("https://api.opendota.com/api/benchmarks/", params=params)
        if responce.status_code != 200:
            raise RuntimeError
        benchmarks = responce.json()
        hero.gpm = benchmarks['result']['gold_per_min'][4]['value']
        hero.dpm = benchmarks['result']['hero_damage_per_min'][4]['value']
        hero.tdmg = benchmarks['result']['tower_damage'][4]['value']
        time.sleep(1)
        print("\rParsing data "+str(counter) + " of 126", end = "")
    return herotable
