import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
import urllib3
from rich import print
from tqdm import tqdm

from config import HEADERS, PORTALE_URL, CODICI_ISTAT, MAX_WORKERS
from utils import Utilities, DatabaseManager

urllib3.disable_warnings()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Update:
    def __init__(self, database):
        self.db_manager = DatabaseManager(database)
        self.session = self.get_session()
        self.utils = Utilities()

    @staticmethod
    def get_session():
        session = requests.Session()
        session.headers.update(HEADERS)
        return session

    def get_features(self, codice_istat):
        """Download data for a given ISTAT code."""
        try:
            response = self.session.get(f"{PORTALE_URL}/rest/layer/AB/{codice_istat}", verify=False)
            response.raise_for_status()
            data = response.json()
            if "features" in data:
                return data["features"]
            else:
                tqdm.write(f"No features found for {codice_istat}")
                return []
        except requests.RequestException as e:
            print(f"{codice_istat}: {e}")
            return []

    def process_area(self, feature):
        """Process and insert area data into the database."""
        codice_area = feature["properties"]["CODICE"]
        response = self.session.get(f"{PORTALE_URL}/datiArea.do?codiceArea={str(codice_area)}&tipoArea=undefined&isFuoriNorma=undefined",
                                    verify=False, timeout=(20, 60))
        if response.status_code == 200:
            data = response.json()
            area = data.get("areaBalneazioneBean")
            if area is None:
                return None
            coordinates = feature["geometry"]["coordinates"]
            return self.utils.convert_area(area, coordinates, data)
        return None

    @staticmethod
    def save(areas, timestamp):
        """Save areas to a JSON file."""
        with open(f"./data/json/{timestamp}.json", "w+", encoding="utf-8") as file:
            json.dump(areas, file)

    def insert_features(self, features):
        """Insert features into the database."""
        areas, errors = [], []
        self.db_manager.begin_transaction()
        pbar = tqdm(total=len(features), desc=f"Processing {len(features)} Areas", unit="area")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_feature = {executor.submit(self.process_area, feature): feature for feature in features}
            for future in as_completed(future_to_feature):
                feature = future_to_feature[future]
                try:
                    area = future.result()
                    if area:
                        areas.append(area)
                        self.db_manager.insert_area(area)
                except Exception as exc:
                    errors.append(feature)
                    tqdm.write(f"Feature generated an exception: {feature}, {exc}")
                finally:
                    pbar.update(1)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.db_manager.update_version(timestamp)
        self.db_manager.commit()
        self.save(areas, timestamp)
        os.rename("./data/latest.db", f"./data/db/{timestamp}.db")
        if len(errors) > 0:
            tqdm.write(f"Errors occurred for {len(errors)} areas:")
            for e in errors:
                tqdm.write(f"{e['properties']['CODICE']}")

    def download_features(self):
        """Download features for all regions."""
        all_features = []
        with tqdm(CODICI_ISTAT.values(), desc=f"Downloading {len(CODICI_ISTAT.values())} Regions", unit="Regione") as pbar:
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_istat = {executor.submit(self.get_features, istat): istat for istat in CODICI_ISTAT.values()}
                for future in as_completed(future_to_istat):
                    codice_istat = future_to_istat[future]
                    try:
                        features = future.result()
                        all_features.extend(features)
                    except Exception as e:
                        tqdm.write(f"Error downloading features for {codice_istat}: {e}")
                    finally:
                        pbar.update(1)
        return all_features

    def run(self):
        temp_file = "./data/output.json"
        mini_file = "./data/minified.json"
        if os.path.exists(mini_file):
            minified = open(mini_file, encoding="utf-8")
            features = json.loads(minified.read())
            feature_collection = features["features"]
        else:
            features = self.download_features()
            feature_collection = list({feature["properties"]["CODICE"]: feature for feature in features}.values())
            output = {"type": "FeatureCollection", "features": feature_collection}
            with open(temp_file, "w+", encoding="utf-8") as file:
                json.dump(output, file)
            os.system(f"mapshaper -i {temp_file} -snap -simplify weighted 12% keep-shapes -o {mini_file}")
            os.remove(temp_file)

        self.insert_features(feature_collection)
        self.db_manager.close()


if __name__ == "__main__":
    try:
        Update("./data/latest.db").run()
    except Exception as error:
        logging.exception(f"An error occurred: {error}")
    finally:
        logging.info("Done!")
