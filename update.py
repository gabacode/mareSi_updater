"""Update Areas"""

import json
import sqlite3
import os
from datetime import datetime
import time
import pandas as pd
import requests


PORTALE_URL = "https://www.portaleacque.salute.gov.it/PortaleAcquePubblico"
COMUNI = "https://raw.githubusercontent.com/opendatasicilia/comuni-italiani/main/dati/comuni.csv"
connection = sqlite3.connect("./data/latest.db")
cursor = connection.cursor()
request = requests.Session()

headers = {
    "Connection": "keep-alive",
    "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    "Accept": "application/json",
    "Content-Type": "application/json",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
    "sec-ch-ua-platform": '"Windows"',
    "Origin": "https://www.portaleacque.salute.gov.it/",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.portaleacque.salute.gov.it/PortaleAcquePubblico/",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Cookie": "cookies_consent=true",
}

request.headers.update(headers)

cursor.execute(
    """
create table if not exists areas (
    CODICE integer primary key not null,
    nome varchar(50) not null,
    comune varchar(50) not null,
    provincia varchar(25) not null,
    siglaProvincia varchar(2) not null,
    regione integer not null,
    stato integer not null,
    limiteEi integer not null,
    limiteEc integer not null,
    dataInizioStagioneBalneare varchar(10) not null,
    dataFineStagioneBalneare varchar(10) not null,
    statoDesc varchar(50) not null,
    geometry text not null,
    isFuoriNorma varchar(1),
    ultimaAnalisi varchar(10),
    valoreEi integer,
    valoreEc integer,
    flagOltreLimiti integer,
    scheda integer,
    interdizioni text
    );
"""
)
cursor.execute(
    """
create table if not exists version (
    lastUpdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    );
"""
)

codici_istat = {
    "Piemonte": "001272",
    "Liguria": "010025",
    "Lombardia": "015146",
    "Veneto": "027042",
    "Friuli Venezia Giulia": "032006",
    "Emilia Romagna": "037006",
    "Toscana": "048017",
    "Marche": "042002",
    "Umbria": "054039",
    "Lazio": "058091",
    "Abruzzo": "066049",
    "Molise": "070006",
    "Campania": "063049",
    "Puglia": "072006",
    "Basilicata": "076063",
    "Calabria": "079023",
    "Sicilia": "082053",
    "Sardegna": "092009",
}

comuni = pd.read_csv(COMUNI)
output = []


def down_join(codice_istat):
    """Gets features for codice ISTAT"""
    global output
    try:
        data = request.get(f"{PORTALE_URL}/rest/layer/AB/{codice_istat}", verify=False)
    except ConnectionError as error:
        print(error)
    if data.status_code != 200:
        print(data.status_code)
        return
    data = data.json()
    for i in range(len(data["features"])):
        codice = data["features"][i]["properties"]["CODICE"]
        geometry = data["features"][i]["geometry"]
        converted = {
            "type": "Feature",
            "properties": {"CODICE": codice},
            "geometry": geometry,
        }
        output.append(converted)


def get_regione(provincia):
    """Get region code from provincia"""
    # print(provincia)
    if (
        (provincia == "CI")
        or (provincia == "OT")
        or (provincia == "VS")
        or (provincia == "OG")
    ):
        return 20
    elif provincia == "NA":
        return 15
    codice = comuni.loc[comuni.sigla == provincia, "cod_reg"].values[0]
    return int(codice)


def insert(feature_collection):
    """Insert data into DB"""
    # https://www.portaleacque.salute.gov.it/PortaleAcquePubblico/datiArea.do?codiceArea={codice}&tipoArea=undefined&isFuoriNorma=undefined
    timeout = 0
    areas = []
    missing = []
    cursor.execute("BEGIN TRANSACTION;")
    for index, record in enumerate(feature_collection["features"]):
        time.sleep(timeout)
        area = record["properties"]["CODICE"]
        data = request.get(
            f"{PORTALE_URL}/datiArea.do?codiceArea={str(area)}&tipoArea=undefined&isFuoriNorma=undefined",
            verify=False,
        )
        if data.status_code == 200:
            data = data.json()
            converted = {
                "CODICE": data["areaBalneazioneBean"]["codice"],
                "nome": data["areaBalneazioneBean"]["nome"],
                "comune": data["areaBalneazioneBean"]["comune"],
                "provincia": data["areaBalneazioneBean"]["provincia"],
                "siglaProvincia": data["areaBalneazioneBean"]["siglaProvincia"],
                "regione": get_regione(data["areaBalneazioneBean"]["siglaProvincia"]),
                "stato": data["areaBalneazioneBean"]["stato"],
                "limiteEi": data["areaBalneazioneBean"]["limiteEi"],
                "limiteEc": data["areaBalneazioneBean"]["limiteEc"],
                "dataInizioStagioneBalneare": data["areaBalneazioneBean"][
                    "dataInizioStagioneBalneare"
                ]
                if "dataInizioStagioneBalneare" in data["areaBalneazioneBean"]
                else "",
                "dataFineStagioneBalneare": data["areaBalneazioneBean"][
                    "dataFineStagioneBalneare"
                ]
                if "dataFineStagioneBalneare" in data["areaBalneazioneBean"]
                else "",
                "statoDesc": data["areaBalneazioneBean"]["statoDesc"],
                "isFuoriNorma": data["areaBalneazioneBean"]["isFuoriNorma"],
                "geometry": str(record["geometry"]["coordinates"]),
                "ultimaAnalisi": str(data["analisi"][0]["dataAnalisi"])
                if len(data["analisi"]) > 0
                else str(data["analisiStorico"][0]["dataAnalisi"])
                if len(data["analisiStorico"]) > 0
                else None,
                "valoreEi": str(data["analisi"][0]["valoreEnterococchi"])
                if len(data["analisi"]) > 0
                else str(data["analisiStorico"][0]["valoreEnterococchi"])
                if len(data["analisiStorico"]) > 0
                else None,
                "valoreEc": str(data["analisi"][0]["valoreEscherichiaColi"])
                if len(data["analisi"]) > 0
                else str(data["analisiStorico"][0]["valoreEscherichiaColi"])
                if len(data["analisiStorico"]) > 0
                else None,
                "flagOltreLimiti": str(data["analisi"][0]["flagOltreLimiti"])
                if len(data["analisi"]) > 0
                else str(data["analisiStorico"][0]["flagOltreLimiti"])
                if len(data["analisiStorico"]) > 0
                else None,
                "scheda": data["dettaglioProfiliBean"][0]["codice"]
                if data["dettaglioProfiliBean"] is not None
                else None,
                "interdizioni": str(data["interdizioni"])
                if data["interdizioni"] is not None
                else None,
            }
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO areas VALUES (:CODICE, :nome, :comune, :provincia, :siglaProvincia, :regione, :stato, :limiteEi, :limiteEc, :dataInizioStagioneBalneare, :dataFineStagioneBalneare, :statoDesc, :geometry, :isFuoriNorma, :ultimaAnalisi, :valoreEi, :valoreEc, :flagOltreLimiti, :scheda, :interdizioni);",
                    converted,
                )
                print(
                    f"[{str(index)}/{str(len(feature_collection['features']))}]",
                    converted["CODICE"],
                    converted["nome"],
                    converted["comune"],
                    converted["provincia"],
                    converted["regione"],
                )
                areas.append(converted)
            except InterruptedError as error:
                print(error)
        else:
            missing.append(area)
            continue
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    cursor.execute(
        "INSERT OR REPLACE INTO version (ROWID, lastUpdate) VALUES (1, ?)", [timestamp]
    )
    cursor.execute("COMMIT;")
    with open(f"./data/json/{timestamp}.json", "w+", encoding="utf-8") as file:
        json.dump(areas, file)
    os.rename("./data/latest.db", f"./data/{timestamp}.db")
    print("missing: ", missing)
    print("Done!")


def execute():
    """The Main Function"""
    if not os.path.exists("./data/minified.json"):
        global output
        for codice_istat in codici_istat.values():
            down_join(codice_istat)
        print("Looking for duplicates...")
        nodups = {i["properties"]["CODICE"]: i for i in reversed(output)}.values()
        features = list(nodups)
        output = {"type": "FeatureCollection", "features": features}
        print("Saving file...")
        with open("./data/output.json", "w+", encoding="utf-8") as file:
            json.dump(output, file)
        os.system(
            "mapshaper -i ./data/output.json -snap -simplify weighted 12% keep-shapes -o ./data/minified.json"
        )
        os.remove("./data/output.json")
    minified = open("./data/minified.json", encoding="utf-8")
    feature_collection = json.loads(minified.read())
    print("Inserting features into db...")
    insert(feature_collection)


execute()
connection.close()
