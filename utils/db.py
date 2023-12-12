import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def begin_transaction(self):
        """Begin a new transaction."""
        self.cursor.execute('BEGIN;')

    def create_tables(self):
        """Create tables if they don't exist."""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS areas (
                CODICE INTEGER PRIMARY KEY NOT NULL,
                nome VARCHAR(50) NOT NULL,
                comune VARCHAR(50) NOT NULL,
                provincia VARCHAR(25) NOT NULL,
                siglaProvincia VARCHAR(2) NOT NULL,
                regione INTEGER NOT NULL,
                stato INTEGER NOT NULL,
                limiteEi INTEGER NOT NULL,
                limiteEc INTEGER NOT NULL,
                dataInizioStagioneBalneare VARCHAR(10) NOT NULL,
                dataFineStagioneBalneare VARCHAR(10) NOT NULL,
                statoDesc VARCHAR(50) NOT NULL,
                geometry TEXT NOT NULL,
                isFuoriNorma VARCHAR(1),
                ultimaAnalisi VARCHAR(10),
                valoreEi INTEGER,
                valoreEc INTEGER,
                flagOltreLimiti INTEGER,
                scheda INTEGER,
                interdizioni TEXT
            );
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS version (
                lastUpdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
            """
        )
        self.connection.commit()

    def insert_area(self, area_data):
        """Insert or replace a new area into the areas table."""
        try:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO areas VALUES (
                    :CODICE, :nome, :comune, :provincia, :siglaProvincia,
                    :regione, :stato, :limiteEi, :limiteEc, :dataInizioStagioneBalneare,
                    :dataFineStagioneBalneare, :statoDesc, :geometry, :isFuoriNorma,
                    :ultimaAnalisi, :valoreEi, :valoreEc, :flagOltreLimiti, :scheda, :interdizioni
                );
                """,
                area_data
            )
        except sqlite3.IntegrityError as e:
            print(f"Database insert error: {e}")

    def update_version(self, timestamp):
        """Update the version table with the current timestamp."""
        self.cursor.execute(
            "INSERT OR REPLACE INTO version (ROWID, lastUpdate) VALUES (1, ?)", [timestamp]
        )

    def commit(self):
        """Commit the current transaction."""
        self.connection.commit()

    def close(self):
        """Close the database connection."""
        self.connection.close()
