import json

import pandas as pd

from config import COMUNI_URL


class Utilities:
    def __init__(self):
        self.comuni = self.load_comuni()

    @staticmethod
    def load_comuni():
        try:
            return pd.read_csv(COMUNI_URL)
        except Exception as e:
            print(f"Failed to load comuni data: {e}")
            return None

    def get_regione(self, provincia):
        """Get region code from provincia"""
        sardegna = ["CI", "OT", "VS", "OG"]
        if provincia in sardegna:
            return 20
        elif provincia == "NA":
            return 15
        codice = self.comuni.loc[self.comuni.sigla == provincia, "cod_reg"].values[0]
        return int(codice)

    @staticmethod
    def get_analisi(data, key):
        value = None
        if data.get("analisi"):
            value = data["analisi"][0].get(key)
        elif data.get("analisiStorico"):
            value = data["analisiStorico"][0].get(key)
        return str(value) if value is not None else None

    def convert_area(self, area, coordinates, data):
        """Converts area"""
        dettaglioProfiliBean = data.get("dettaglioProfiliBean", [{}])
        codice = dettaglioProfiliBean[0].get("codice") if dettaglioProfiliBean else None
        interdizioni = data.get("interdizioni")
        interdizioni_str = json.dumps(interdizioni[0]) if interdizioni and interdizioni[0] else ""

        return {
            "CODICE": area.get("codice"),
            "nome": area.get("nome"),
            "comune": area.get("comune"),
            "provincia": area.get("provincia"),
            "siglaProvincia": area.get("siglaProvincia"),
            "regione": self.get_regione(area.get("siglaProvincia")),
            "stato": area.get("stato"),
            "limiteEi": area.get("limiteEi"),
            "limiteEc": area.get("limiteEc"),
            "dataInizioStagioneBalneare": area.get("dataInizioStagioneBalneare", ""),
            "dataFineStagioneBalneare": area.get("dataFineStagioneBalneare", ""),
            "statoDesc": area.get("statoDesc"),
            "isFuoriNorma": area.get("isFuoriNorma"),
            "geometry": str(coordinates),
            "ultimaAnalisi": self.get_analisi(data, "dataAnalisi"),
            "valoreEi": self.get_analisi(data, "valoreEnterococchi"),
            "valoreEc": self.get_analisi(data, "valoreEscherichiaColi"),
            "flagOltreLimiti": self.get_analisi(data, "flagOltreLimiti"),
            "scheda": codice,
            "interdizioni": interdizioni_str
        }
