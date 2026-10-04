import sqlite3
from pathlib import Path


DATABASE_DIR = Path("/opt/tractor/data")
DATABASE_FILE = DATABASE_DIR / "tractor.db"


class Database:

    def __init__(self):

        DATABASE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.connection = sqlite3.connect(
            DATABASE_FILE
        )

        self.connection.row_factory = sqlite3.Row

        self.create_tables()


    def create_tables(self):

        cursor = self.connection.cursor()


        # ====================================================
        # TRAKTOREN
        # ====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tractors (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                manufacturer TEXT,
                model TEXT,
                year INTEGER,

                length REAL,
                width REAL,
                height REAL,

                wheelbase REAL,

                front_track REAL,
                rear_track REAL,

                weight REAL,

                notes TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


        # ====================================================
        # ANBAUGERÄTE
        # ====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS implements (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                manufacturer TEXT,
                model TEXT,

                type TEXT,

                length REAL,
                width REAL,
                height REAL,

                working_width REAL,

                distance_to_tractor REAL,

                weight REAL,

                notes TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


        self.connection.commit()


    # ========================================================
    # TRAKTOREN
    # ========================================================

    def add_tractor(
        self,
        name,
        manufacturer="",
        model="",
        year=None,
        length=None,
        width=None,
        height=None,
        wheelbase=None,
        front_track=None,
        rear_track=None,
        weight=None,
        notes=""
    ):

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO tractors (
                name,
                manufacturer,
                model,
                year,
                length,
                width,
                height,
                wheelbase,
                front_track,
                rear_track,
                weight,
                notes
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            manufacturer,
            model,
            year,
            length,
            width,
            height,
            wheelbase,
            front_track,
            rear_track,
            weight,
            notes
        ))

        self.connection.commit()

        return cursor.lastrowid


    def get_tractors(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT *
            FROM tractors
            ORDER BY name
        """)

        return cursor.fetchall()


    def get_tractor(self, tractor_id):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT *
            FROM tractors
            WHERE id = ?
        """, (tractor_id,))

        return cursor.fetchone()


    def delete_tractor(self, tractor_id):

        self.connection.execute("""
            DELETE FROM tractors
            WHERE id = ?
        """, (tractor_id,))

        self.connection.commit()


    # ========================================================
    # ANBAUGERÄTE
    # ========================================================

    def add_implement(
        self,
        name,
        manufacturer="",
        model="",
        type="",
        length=None,
        width=None,
        height=None,
        working_width=None,
        distance_to_tractor=None,
        weight=None,
        notes=""
    ):

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO implements (
                name,
                manufacturer,
                model,
                type,
                length,
                width,
                height,
                working_width,
                distance_to_tractor,
                weight,
                notes
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            manufacturer,
            model,
            type,
            length,
            width,
            height,
            working_width,
            distance_to_tractor,
            weight,
            notes
        ))

        self.connection.commit()

        return cursor.lastrowid


    def get_implements(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT *
            FROM implements
            ORDER BY name
        """)

        return cursor.fetchall()


    def get_implement(self, implement_id):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT *
            FROM implements
            WHERE id = ?
        """, (implement_id,))

        return cursor.fetchone()


    def delete_implement(self, implement_id):

        self.connection.execute("""
            DELETE FROM implements
            WHERE id = ?
        """, (implement_id,))

        self.connection.commit()


    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.connection.close()

