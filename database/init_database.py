# database/init_database.py
#
# Initialisiert die komplette pytrac-SQLite-Datenbank neu.
#
# ACHTUNG:
# ALLE vorhandenen Tabellen und Daten werden gelöscht!
#
# Aufruf:
#   python3 -m database.init_database
#
# Ohne Rückfrage (z.B. für einen bewusst geplanten Neuaufbau):
#   python3 -m database.init_database --yes

import argparse
import sqlite3
import sys
from pathlib import Path

from database.database import DATABASE_DIR, DATABASE_FILE


def create_schema(connection):
    """Erstellt das vollständige Datenbankschema."""

    connection.executescript("""
        CREATE TABLE tractors (
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
        );

        CREATE TABLE implements (
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
        );

        CREATE TABLE work_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            implement_name TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            paused_at TEXT,
            finished_at TEXT,
            gps_to_hitch_m REAL NOT NULL,
            hitch_to_edge_m REAL NOT NULL,
            mount_position TEXT NOT NULL,
            working_width_m REAL NOT NULL
        );

        CREATE TABLE gps_track_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            timestamp TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            speed_kmh REAL,
            heading_deg REAL,
            is_working INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY (session_id)
                REFERENCES work_sessions(id)
        );

        CREATE TABLE coverage_polygons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            coordinates_json TEXT NOT NULL,
            area_m2 REAL NOT NULL,

            FOREIGN KEY (session_id)
                REFERENCES work_sessions(id)
        );

        CREATE INDEX idx_gps_track_session
            ON gps_track_points(session_id, timestamp);

        CREATE INDEX idx_coverage_session
            ON coverage_polygons(session_id, timestamp);
    """)


def list_tables(connection):
    """Liefert alle normalen Tabellen außer SQLite-internen Tabellen."""

    rows = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    return [row[0] for row in rows]


def initialize_database(force=False):
    """Löscht die bisherigen Tabellen und legt das Schema neu an."""

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 60)
    print(" PYTRAC - DATENBANK-INITIALISIERUNG")
    print("=" * 60)
    print(f"Datenbank: {DATABASE_FILE}")
    print()
    print("WARNUNG: ALLE vorhandenen Tabellen und Daten")
    print("werden unwiderruflich gelöscht.")
    print()

    if not force:
        confirmation = input(
            "Zum Fortfahren exakt RESET eingeben: "
        ).strip()

        if confirmation != "RESET":
            print("Abgebrochen. Es wurden keine Daten gelöscht.")
            return False

    connection = None

    try:
        connection = sqlite3.connect(DATABASE_FILE)

        # Fremdschlüsselprüfung vor dem Löschen deaktivieren.
        connection.execute("PRAGMA foreign_keys = OFF")

        # Schemaänderungen werden gemeinsam ausgeführt.
        connection.execute("BEGIN IMMEDIATE")

        existing_tables = list_tables(connection)

        for table in existing_tables:
            # Tabellennamen stammen ausschließlich aus sqlite_master.
            quoted_name = '"' + table.replace('"', '""') + '"'
            connection.execute(
                f"DROP TABLE IF EXISTS {quoted_name}"
            )

        # Alte Views entfernen, sofern vorhanden.
        views = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'view'
        """).fetchall()

        for (view_name,) in views:
            quoted_name = (
                '"' + view_name.replace('"', '""') + '"'
            )
            connection.execute(
                f"DROP VIEW IF EXISTS {quoted_name}"
            )

        # Nach dem DROP-Teil beginnt der Aufbau des neuen Schemas.
        # executescript führt selbst COMMIT aus; deshalb wird hier
        # vor dem Schemaaufbau explizit committed.
        connection.commit()

        create_schema(connection)
        connection.commit()

        connection.execute("PRAGMA foreign_keys = ON")

        # Kontrolle: alle erwarteten Tabellen müssen existieren.
        expected = {
            "tractors",
            "implements",
            "work_sessions",
            "gps_track_points",
            "coverage_polygons",
        }

        actual = set(list_tables(connection))
        missing = expected - actual

        if missing:
            raise RuntimeError(
                "Tabellen fehlen nach Initialisierung: "
                + ", ".join(sorted(missing))
            )

        print()
        print("Datenbank erfolgreich neu erstellt.")
        print()
        print("Vorhandene Tabellen:")

        for table in sorted(actual):
            print(f"  - {table}")

        print()
        print("Alle bisherigen Daten wurden gelöscht.")
        print("Die Datenbank ist bereit.")
        return True

    except Exception as error:
        if connection is not None:
            connection.rollback()

        print(
            f"FEHLER bei der Initialisierung: {error}",
            file=sys.stderr,
        )
        return False

    finally:
        if connection is not None:
            connection.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Setzt die pytrac-Datenbank zurück und erstellt "
            "alle Tabellen neu."
        )
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Bestätigung überspringen; alle Daten werden gelöscht.",
    )

    args = parser.parse_args()

    success = initialize_database(force=args.yes)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
