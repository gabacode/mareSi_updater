import os
import json
import subprocess


def diff():
    files = []
    for file in os.listdir('./data'):
        if file.endswith('.db') and not file.startswith('latest'):
            files.append(file)
    sort = sorted(files, reverse=True)
    dbs = sort[:2]
    print(dbs)
    diff = subprocess.Popen(['sqldiff ./data/' + dbs[1] + ' ./data/' + dbs[0]],
                            shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
    diffList = diff.read().splitlines()

    lastDB = dbs[0].rpartition('.db')[0]
    print('Last DB:', lastDB)

    with open('./data/updates.json', "r") as file:
        data = json.load(file)

    lastUpdate = data[-1]['date']
    needsUpdate = lastDB > lastUpdate

    print('Last update:', lastUpdate)
    print('New update:', needsUpdate)

    if needsUpdate:
        print('UPDATE')
        data.append({'date': lastDB, 'diff': diffList})
        with open('./data/updates.json', "w") as file:
            json.dump(data, file)


diff()
