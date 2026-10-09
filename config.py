# ------------------------------------------------------------
# config.py
# Tractor Board Computer
# ------------------------------------------------------------

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Startposition der Karte
START_LATITUDE = 51.3127
START_LONGITUDE = 9.4797

# Kartenzoom
MAP_ZOOM = 16

# Aktualisierungsintervalle
GPS_UPDATE_INTERVAL = 1.0
CLOCK_UPDATE_INTERVAL = 1.0

# ------------------------------------------------------------
# ARBEITSGEOMETRIE
# ------------------------------------------------------------

# Vorzeichenbehafteter Abstand GPS-Referenzpunkt -> Dreipunktaufnahme.
#
# Positiv: Die Aufnahme liegt in Fahrtrichtung vor dem GPS-Punkt.
# Negativ: Die Aufnahme liegt hinter dem GPS-Punkt.
#
# Den tatsächlichen Wert in Metern eintragen.
GPS_TO_HITCH_M = None

# Abstand von der Dreipunktaufnahme bis zur wirksamen Arbeitskante.
# Diesen Wert misst du am Gerät. Er muss positiv sein.
IMPLEMENT_HITCH_TO_EDGE_M = None

# Montageposition:
# "rear"  = Heckanbaugerät
# "front" = Frontanbaugerät
IMPLEMENT_MOUNT_POSITION = "rear"

# Tatsächliche Arbeitsbreite in Metern.
IMPLEMENT_WORKING_WIDTH_M = None

# Bezeichnung des derzeit verwendeten Anbaugeräts.
IMPLEMENT_NAME = "Anbaugerät"

# ------------------------------------------------------------
# FILTER FÜR DIE FLÄCHENERFASSUNG
# ------------------------------------------------------------

# GPS-Punkte mit größerer Zeitlücke werden nicht verbunden.
MAX_COVERAGE_GAP_SECONDS = 3.0

# Maximale Distanz zwischen zwei aufeinanderfolgenden
# Arbeitskantenpositionen, um ein Polygon zu erzeugen.
MAX_COVERAGE_STEP_M = 5.0

# Sehr kleine Polygone werden als GPS-Rauschen verworfen.
MIN_COVERAGE_POLYGON_AREA_M2 = 0.05

# Große Polygone werden verworfen, da sie auf einen
# GPS-Sprung oder eine ungültige Messung hindeuten können.
MAX_COVERAGE_POLYGON_AREA_M2 = 100.0

# Unterhalb dieser Geschwindigkeit wird keine neue Fläche
# erfasst. Das verhindert Flächen durch GPS-Drift im Stand.
MIN_WORK_SPEED_KMH = 0.5
