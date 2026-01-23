import json
import logging
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import httpx
import urllib3
from rich import print
from tqdm import tqdm

from config import HEADERS, PORTALE_URL, CODICI_ISTAT, MAX_WORKERS, MINIFIED_FILEPATH, LATEST_DB, AB_LAYER, CERT_PATH
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
        if os.path.exists(CERT_PATH):
            logging.info(f"Using certificate at {CERT_PATH}")
            return httpx.Client(verify=CERT_PATH, headers=HEADERS, timeout=60.0)
        logging.warning("Certificate not found. Using system certificates.")
        raise FileNotFoundError(f"Certificate not found at {CERT_PATH}. Please provide a valid certificate.")

    def get_features(self, codice_istat):
        """Download Feaatures for a given ISTAT code."""
        try:
            response = self.session.get(f"{PORTALE_URL}/{AB_LAYER}/{codice_istat}")
            response.raise_for_status()
            data = response.json()
            if "features" in data:
                return data["features"]
            else:
                tqdm.write(f"No features found for {codice_istat}")
                return []
        except httpx.RequestError as e:
            print(f"{codice_istat}: {e}")
            return []

    def process_area(self, feature):
        endpoint = "datiArea.do?codiceArea"
        codice_area = str(feature["properties"]["CODICE"])
        params = "tipoArea=undefined&isFuoriNorma=undefined"
        response = self.session.get(f"{PORTALE_URL}/{endpoint}={codice_area}&{params}", timeout=60.0)
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
        """Save areas and new database."""
        with open(f"./data/json/{timestamp}.json", "w+", encoding="utf-8") as file:
            json.dump(areas, file)
        with open("./data/json/latest.json", "w+", encoding="utf-8") as file:
            json.dump(areas, file)
        os.rename(LATEST_DB, f"./data/db/{timestamp}.db")

    def download_features(self):
        """Download features for all regions."""
        all_features = []
        with tqdm(CODICI_ISTAT.values(), desc=f"Downloading {len(CODICI_ISTAT.values())} Regions",
                  unit="Regione") as pbar:
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

    @staticmethod
    def load_minified():
        assert os.path.exists(MINIFIED_FILEPATH), "Minified file does not exist."
        with open(MINIFIED_FILEPATH, "r", encoding="utf-8") as minified_file:
            features = json.load(minified_file)
            return features["features"]

    def get_feature_collection(self):
        features = self.download_features()
        feature_collection = list({feature["properties"]["CODICE"]: feature for feature in reversed(features)}.values())
        for feature in feature_collection:
            feature.pop("id", None)
            feature["properties"].pop("TYPE", None)
        output = {"type": "FeatureCollection", "features": feature_collection}
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=False) as temp_file:
            json.dump(output, temp_file)
            temp_file_path = temp_file.name
        try:
            subprocess.run(["mapshaper", "-i", temp_file_path, "-snap", "-simplify", "weighted 12% keep-shapes", "-o",
                            MINIFIED_FILEPATH], check=True)
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while processing the file: {e}")
            raise
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        return self.load_minified()

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

        if len(areas) == 0:
            logging.error("Nessun'area disponibile - il Portale Acque potrebbe essere offline. Aggiornamento annullato!")
            self.db_manager.close()
            if os.path.exists(LATEST_DB):
                os.remove(LATEST_DB)
            sys.exit(1)

        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.db_manager.update_version(timestamp)
        self.db_manager.commit()
        self.save(areas, timestamp)
        if len(errors) > 0:
            tqdm.write(f"Errors occurred for {len(errors)} areas:")
            for e in errors:
                tqdm.write(f"{e['properties']['CODICE']}")

    def run(self):
        if self.has_minified():
            feature_collection = self.load_minified()
        else:
            feature_collection = self.get_feature_collection()
        self.insert_features(feature_collection)
        self.db_manager.close()

    @staticmethod
    def has_minified():
        return os.path.exists(MINIFIED_FILEPATH)


if __name__ == "__main__":
    try:
        Update(LATEST_DB).run()
    except Exception as error:
        logging.exception(f"An error occurred: {error}")
    finally:
        logging.info("Done!")
