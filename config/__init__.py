PORTALE_URL = "https://www.portaleacque.salute.gov.it/PortaleAcquePubblico"
COMUNI_URL = "https://raw.githubusercontent.com/opendatasicilia/comuni-italiani/main/dati/comuni.csv"
HEADERS = {
    "Connection": "keep-alive",
    "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    "Accept": "",
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
CODICI_ISTAT = {
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
MAX_WORKERS = 15
LATEST_DB = "./data/latest.db"
MINIFIED_FILEPATH = "./data/minified.json"
AB_LAYER = "rest/layer/AB"
CERT_PATH = "./config/certs/chain.pem"
