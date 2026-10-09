# ------------------------------------------------------------
# services/work_session.py
# Tractor Board Computer
# Arbeitsgangsteuerung und Flächenaufzeichnung
# ------------------------------------------------------------

import json
import math
from datetime import datetime, timezone

from config import (
    MAX_COVERAGE_GAP_SECONDS,
    MAX_COVERAGE_STEP_M,
    MIN_COVERAGE_POLYGON_AREA_M2,
    MAX_COVERAGE_POLYGON_AREA_M2,
    MIN_WORK_SPEED_KMH,
)


def utc_now():
    """Aktuelle UTC-Zeit als ISO-8601-String."""
    return datetime.now(timezone.utc).isoformat()


class WorkSessionService:
    """
    Verwaltet Arbeitsgänge und bearbeitete Flächen.

    Status:
        idle   = kein offener Arbeitsgang
        active = Arbeitsgang aktiv
        paused = Arbeitsgang pausiert

    heading_deg:
        0° = Norden
        90° = Osten
        180° = Süden
        270° = Westen
    """

    def __init__(self, database):
        self.connection = database.connection

        self.active_session_id = None
        self.status = "idle"

        self.previous_edge = None
        self.previous_fix_time = None
        self.previous_gps = None

        self.origin_lat = None
        self.origin_lon = None

        self._create_tables()
        self._recover_sessions()

    # --------------------------------------------------------
    # DATENBANK
    # --------------------------------------------------------

    def _create_tables(self):
        """Legt fehlende Tabellen und Indizes an."""

        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS work_sessions (
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

            CREATE TABLE IF NOT EXISTS gps_track_points (
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

            CREATE TABLE IF NOT EXISTS coverage_polygons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                coordinates_json TEXT NOT NULL,
                area_m2 REAL NOT NULL,
                FOREIGN KEY (session_id)
                    REFERENCES work_sessions(id)
            );

            CREATE INDEX IF NOT EXISTS idx_gps_track_session
                ON gps_track_points(session_id, timestamp);

            CREATE INDEX IF NOT EXISTS idx_coverage_session
                ON coverage_polygons(session_id, timestamp);
        """)

        self.connection.commit()

    def _recover_sessions(self):
        """
        Pausiert aktive Arbeitsgänge nach einem Neustart.
        Ein Arbeitsgang wird nicht automatisch fortgesetzt.
        """

        self.connection.execute("""
            UPDATE work_sessions
            SET status = 'paused',
                paused_at = ?
            WHERE status = 'active'
        """, (utc_now(),))

        self.connection.commit()

        row = self.connection.execute("""
            SELECT id
            FROM work_sessions
            WHERE status = 'paused'
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()

        if row is not None:
            self.active_session_id = row["id"]
            self.status = "paused"

    # --------------------------------------------------------
    # ARBEITSGANG STARTEN
    # --------------------------------------------------------

    def start(
        self,
        implement_name,
        gps_to_hitch_m,
        hitch_to_edge_m,
        mount_position,
        working_width_m,
        name="Arbeitsgang",
    ):
        if self.status in ("active", "paused"):
            raise RuntimeError(
                "Es gibt bereits einen offenen Arbeitsgang."
            )

        if mount_position not in ("front", "rear"):
            raise ValueError(
                "Montageposition muss 'front' oder 'rear' sein."
            )

        if gps_to_hitch_m is None or gps_to_hitch_m < 0:
            raise ValueError(
                "GPS-Abstand zur Dreipunktaufnahme ungültig."
            )

        if hitch_to_edge_m is None or hitch_to_edge_m <= 0:
            raise ValueError(
                "Abstand zur wirksamen Arbeitskante ungültig."
            )

        if working_width_m is None or working_width_m <= 0:
            raise ValueError(
                "Die Arbeitsbreite muss größer als null sein."
            )

        cursor = self.connection.execute("""
            INSERT INTO work_sessions (
                name,
                implement_name,
                status,
                started_at,
                gps_to_hitch_m,
                hitch_to_edge_m,
                mount_position,
                working_width_m
            )
            VALUES (?, ?, 'active', ?, ?, ?, ?, ?)
        """, (
            name,
            implement_name,
            utc_now(),
            float(gps_to_hitch_m),
            float(hitch_to_edge_m),
            mount_position,
            float(working_width_m),
        ))

        self.connection.commit()

        self.active_session_id = cursor.lastrowid
        self.status = "active"

        self._reset_segment()
        self.origin_lat = None
        self.origin_lon = None

        return self.active_session_id

    # --------------------------------------------------------
    # ARBEITSGANG PAUSIEREN
    # --------------------------------------------------------

    def pause(self):
        if self.status != "active":
            return

        self.connection.execute("""
            UPDATE work_sessions
            SET status = 'paused',
                paused_at = ?
            WHERE id = ?
        """, (
            utc_now(),
            self.active_session_id,
        ))

        self.connection.commit()

        self.status = "paused"
        self._reset_segment()

    # --------------------------------------------------------
    # ARBEITSGANG FORTSETZEN
    # --------------------------------------------------------

    def resume(self):
        if (
            self.status != "paused"
            or self.active_session_id is None
        ):
            raise RuntimeError(
                "Es gibt keinen pausierten Arbeitsgang."
            )

        self.connection.execute("""
            UPDATE work_sessions
            SET status = 'active',
                paused_at = NULL
            WHERE id = ?
        """, (self.active_session_id,))

        self.connection.commit()

        self.status = "active"
        self._reset_segment()

    # --------------------------------------------------------
    # ARBEITSGANG BEENDEN
    # --------------------------------------------------------

    def finish(self):
        if self.status not in ("active", "paused"):
            return

        self.connection.execute("""
            UPDATE work_sessions
            SET status = 'finished',
                finished_at = ?
            WHERE id = ?
        """, (
            utc_now(),
            self.active_session_id,
        ))

        self.connection.commit()

        self.active_session_id = None
        self.status = "idle"

        self._reset_segment()
        self.origin_lat = None
        self.origin_lon = None

    # --------------------------------------------------------
    # INTERNEN ZUSTAND ZURÜCKSETZEN
    # --------------------------------------------------------

    def _reset_segment(self):
        self.previous_edge = None
        self.previous_fix_time = None
        self.previous_gps = None

    # --------------------------------------------------------
    # KOORDINATENTRANSFORMATION
    # --------------------------------------------------------

    @staticmethod
    def _local_xy(lat, lon, origin_lat, origin_lon):
        """
        Lokale Koordinaten in Metern:
        x = Osten, y = Norden.
        Geeignet als Näherung für kleine Felder.
        """

        radius = 6371000.0
        lat0 = math.radians(origin_lat)

        x = (
            radius
            * math.radians(lon - origin_lon)
            * math.cos(lat0)
        )

        y = radius * math.radians(lat - origin_lat)

        return x, y

    @staticmethod
    def _latlon(x, y, origin_lat, origin_lon):
        """Wandelt lokale Meterkoordinaten zurück in GPS."""

        radius = 6371000.0

        lat = origin_lat + math.degrees(y / radius)
        cos_lat = math.cos(math.radians(origin_lat))

        if abs(cos_lat) < 1e-8:
            raise ValueError(
                "Lokale Koordinatentransformation ungeeignet."
            )

        lon = origin_lon + math.degrees(
            x / (radius * cos_lat)
        )

        return [lat, lon]

    @staticmethod
    def _polygon_area(points):
        """Berechnet die Polygonfläche in Quadratmetern."""

        area = 0.0

        for index, (x1, y1) in enumerate(points):
            x2, y2 = points[(index + 1) % len(points)]
            area += x1 * y2 - x2 * y1

        return abs(area) / 2.0

    @staticmethod
    def _distance(a, b):
        """Euklidischer Abstand zweier lokaler Punkte."""

        return math.hypot(
            a[0] - b[0],
            a[1] - b[1],
        )

    # --------------------------------------------------------
    # GPS-FIX VERARBEITEN
    # --------------------------------------------------------
    def process_fix(
        self,
        latitude,
        longitude,
        speed_kmh,
        heading_deg,
    ):
        """
        Speichert GPS-Punkte und berechnet bei aktiver Arbeit
        Abdeckungspolygone zwischen gültigen GPS-Fixes.

        Rückgabe:
            {
                "track_segment": [[lat, lon], [lat, lon]] oder None,
                "coverage_polygon": [[lat, lon], ...] oder None
            }
        """

        result = {
            "track_segment": None,
            "coverage_polygon": None,
        }

        if latitude is None or longitude is None:
            self._reset_segment()
            return result

        latitude = float(latitude)
        longitude = float(longitude)

        if not (
            -90.0 <= latitude <= 90.0
            and -180.0 <= longitude <= 180.0
        ):
            self._reset_segment()
            return result

        if latitude == 0.0 and longitude == 0.0:
            self._reset_segment()
            return result

        now = datetime.now(timezone.utc)

        session_id = self.active_session_id
        is_working = self.status == "active"

        # GPS-Spur des offenen Arbeitsgangs speichern.
        if session_id is not None:
            self.connection.execute("""
                INSERT INTO gps_track_points (
                    session_id,
                    timestamp,
                    latitude,
                    longitude,
                    speed_kmh,
                    heading_deg,
                    is_working
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                now.isoformat(),
                latitude,
                longitude,
                speed_kmh,
                heading_deg,
                int(is_working),
            ))

        # Während einer Pause keine Arbeitsfläche erzeugen.
        if not is_working or session_id is None:
            self.connection.commit()
            self._reset_segment()
            return result

        row = self.connection.execute("""
            SELECT gps_to_hitch_m,
                   hitch_to_edge_m,
                   mount_position,
                   working_width_m
            FROM work_sessions
            WHERE id = ?
        """, (session_id,)).fetchone()

        if row is None or heading_deg is None:
            self.connection.commit()
            self._reset_segment()
            return result

        if speed_kmh is None or speed_kmh < MIN_WORK_SPEED_KMH:
            self.connection.commit()
            self._reset_segment()
            return result

        heading_deg = float(heading_deg) % 360.0

        if self.origin_lat is None:
            self.origin_lat = latitude
            self.origin_lon = longitude

        x, y = self._local_xy(
            latitude,
            longitude,
            self.origin_lat,
            self.origin_lon,
        )

        # 0° = Norden, 90° = Osten.
        heading = math.radians(heading_deg)

        forward_x = math.sin(heading)
        forward_y = math.cos(heading)

        # Linker Vektor relativ zur Fahrtrichtung.
        left_x = -forward_y
        left_y = forward_x

        # Position der Arbeitskante relativ zum GPS-Empfänger.
        mount_sign = (
            1.0
            if row["mount_position"] == "front"
            else -1.0
        )

        longitudinal_offset = (
            row["gps_to_hitch_m"]
            + mount_sign * row["hitch_to_edge_m"]
        )

        edge_x = x + longitudinal_offset * forward_x
        edge_y = y + longitudinal_offset * forward_y

        half_width = row["working_width_m"] / 2.0

        left_edge = (
            edge_x + half_width * left_x,
            edge_y + half_width * left_y,
        )

        right_edge = (
            edge_x - half_width * left_x,
            edge_y - half_width * left_y,
        )

        current_edge = (left_edge, right_edge)

        # GPS-Spursegment erzeugen.
        if self.previous_gps is not None:
            result["track_segment"] = [
                self.previous_gps,
                [latitude, longitude],
            ]

        # Fläche zwischen zwei Arbeitskanten berechnen.
        if (
            self.previous_edge is not None
            and self.previous_fix_time is not None
        ):
            elapsed = (
                now - self.previous_fix_time
            ).total_seconds()

            old_left, old_right = self.previous_edge

            old_center = (
                (old_left[0] + old_right[0]) / 2.0,
                (old_left[1] + old_right[1]) / 2.0,
            )

            new_center = (
                (left_edge[0] + right_edge[0]) / 2.0,
                (left_edge[1] + right_edge[1]) / 2.0,
            )

            step = self._distance(old_center, new_center)

            polygon_xy = [
                old_left,
                old_right,
                right_edge,
                left_edge,
            ]

            area_m2 = self._polygon_area(polygon_xy)

            valid_segment = (
                0 < elapsed <= MAX_COVERAGE_GAP_SECONDS
                and 0 < step <= MAX_COVERAGE_STEP_M
                and MIN_COVERAGE_POLYGON_AREA_M2
                < area_m2
                < MAX_COVERAGE_POLYGON_AREA_M2
            )

            if valid_segment:
                polygon_latlon = [
                    self._latlon(
                        px,
                        py,
                        self.origin_lat,
                        self.origin_lon,
                    )
                    for px, py in polygon_xy
                ]

                self.connection.execute("""
                    INSERT INTO coverage_polygons (
                        session_id,
                        timestamp,
                        coordinates_json,
                        area_m2
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    session_id,
                    now.isoformat(),
                    json.dumps(polygon_latlon),
                    area_m2,
                ))

                result["coverage_polygon"] = polygon_latlon

        self.previous_edge = current_edge
        self.previous_fix_time = now
        self.previous_gps = [latitude, longitude]

        self.connection.commit()

        return result

    # --------------------------------------------------------
    # GESPEICHERTE FLÄCHEN LADEN
    # --------------------------------------------------------

    def get_session_polygons(self, session_id):
        """Lädt alle gespeicherten Polygone eines Arbeitsgangs."""

        rows = self.connection.execute("""
            SELECT coordinates_json
            FROM coverage_polygons
            WHERE session_id = ?
            ORDER BY id
        """, (session_id,)).fetchall()

        return [
            json.loads(row["coordinates_json"])
            for row in rows
        ]

    # --------------------------------------------------------
    # ID DES OFFENEN ARBEITSGANGS
    # --------------------------------------------------------

    def get_open_session_id(self):
        """Gibt die ID des offenen Arbeitsgangs zurück."""
        return self.active_session_id
