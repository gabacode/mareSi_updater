"""Calculates diffs between two databases and saves them to a file."""
import os
import json
import subprocess


def diff():
    """The Main Function"""
    files = []
    for file in os.listdir("./data"):
        if file.endswith(".db") and not file.startswith("latest"):
            files.append(file)
    sort = sorted(files, reverse=True)
    dbs = sort[:2]
    print(dbs)
    differences = subprocess.Popen(
        [f"sqldiff ./data/{dbs[1]} ./data/{dbs[0]}"],
        shell=True,
        stdout=subprocess.PIPE,
        universal_newlines=True,
    ).stdout
    diff_list = differences.read().splitlines()

    last_db = dbs[0].rpartition(".db")[0]
    print("Last DB:", last_db)

    with open("./data/updates.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    last_update = data[-1]["date"]
    needs_update = last_db > last_update

    print("Last update:", last_update)
    print("New update:", needs_update)

    if needs_update:
        if len(diff_list) > 1:
            print("UPDATE")
            data.append({"date": last_db, "diff": diff_list})
            with open("./data/updates.json", "w", encoding="utf-8") as file:
                json.dump(data, file)


diff()
