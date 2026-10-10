import json
import math
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("PYTRAC_WEB_DB", BASE_DIR / "pytrac_web.db"))

app = FastAPI(title="PyTrac Web", version="0.1.0")


@contextmanager
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS tractors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            length_m REAL NOT NULL,
            width_m REAL NOT NULL,
            height_m REAL NOT NULL,
            gps_x_m REAL NOT NULL DEFAULT 0,
            gps_y_m REAL NOT NULL DEFAULT 0,
            gps_z_m REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS implements (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            length_m REAL NOT NULL,
            width_m REAL NOT NULL,
            height_m REAL NOT NULL,
            working_width_m REAL NOT NULL,
            mount_position TEXT NOT NULL DEFAULT 'rear',
            hitch_offset_m REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            boundary TEXT NOT NULL,
            area_m2 REAL NOT NULL DEFAULT 0
        );
        """)


init_db()


class Tractor(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    length_m: float = Field(gt=0, le=50)
    width_m: float = Field(gt=0, le=15)
    height_m: float = Field(gt=0, le=15)
    gps_x_m: float = 0
    gps_y_m: float = 0
    gps_z_m: float = 0


class Implement(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    length_m: float = Field(gt=0, le=30)
    width_m: float = Field(gt=0, le=15)
    height_m: float = Field(gt=0, le=15)
    working_width_m: float = Field(gt=0, le=30)
    mount_position: str = "rear"
    hitch_offset_m: float = 0


class FieldInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    boundary: dict


def polygon_area_m2(geojson: dict) -> float:
    """Näherungsfläche in einem lokalen Meter-Koordinatensystem."""
    if geojson.get("type") != "Polygon":
        raise ValueError("Erwartet wird ein GeoJSON-Polygon.")

    rings = geojson.get("coordinates", [])
    if not rings or len(rings[0]) < 4:
        raise ValueError("Die Feldgrenze benötigt mindestens 3 Eckpunkte.")

    points = rings[0]
    lat0 = math.radians(sum(p[1] for p in points) / len(points))
    lon0 = points[0][0]

    xy = [
        (
            (lon - lon0) * 111320 * math.cos(lat0),
            (lat - sum(p[1] for p in points) / len(points)) * 110540,
        )
        for lon, lat, *_ in points
    ]

    area = abs(sum(
        xy[i][0] * xy[(i + 1) % len(xy)][1]
        - xy[(i + 1) % len(xy)][0] * xy[i][1]
        for i in range(len(xy))
    )) / 2

    return area


@app.get("/api/tractors")
def list_tractors():
    with db() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM tractors ORDER BY name"
        )]


@app.post("/api/tractors")
def create_tractor(item: Tractor):
    with db() as con:
        cur = con.execute("""
            INSERT INTO tractors
            (name, length_m, width_m, height_m,
             gps_x_m, gps_y_m, gps_z_m)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tuple(item.model_dump().values()))
        return {"id": cur.lastrowid, **item.model_dump()}


@app.delete("/api/tractors/{item_id}")
def delete_tractor(item_id: int):
    with db() as con:
        cur = con.execute("DELETE FROM tractors WHERE id=?", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Traktor nicht gefunden")
    return {"ok": True}


@app.get("/api/implements")
def list_implements():
    with db() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM implements ORDER BY name"
        )]


@app.post("/api/implements")
def create_implement(item: Implement):
    if item.mount_position not in ("front", "rear", "trailed"):
        raise HTTPException(400, "Ungültige Montageposition")

    with db() as con:
        cur = con.execute("""
            INSERT INTO implements
            (name, length_m, width_m, height_m,
             working_width_m, mount_position, hitch_offset_m)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tuple(item.model_dump().values()))
        return {"id": cur.lastrowid, **item.model_dump()}


@app.delete("/api/implements/{item_id}")
def delete_implement(item_id: int):
    with db() as con:
        cur = con.execute("DELETE FROM implements WHERE id=?", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Anbaugerät nicht gefunden")
    return {"ok": True}


@app.get("/api/fields")
def list_fields():
    with db() as con:
        return [
            {
                **dict(r),
                "boundary": json.loads(r["boundary"]),
            }
            for r in con.execute("SELECT * FROM fields ORDER BY name")
        ]


@app.post("/api/fields")
def create_field(item: FieldInput):
    try:
        area = polygon_area_m2(item.boundary)
    except (ValueError, TypeError, IndexError) as exc:
        raise HTTPException(400, str(exc)) from exc

    with db() as con:
        cur = con.execute("""
            INSERT INTO fields (name, boundary, area_m2)
            VALUES (?, ?, ?)
        """, (item.name, json.dumps(item.boundary), area))
        return {
            "id": cur.lastrowid,
            "name": item.name,
            "boundary": item.boundary,
            "area_m2": area,
        }


@app.put("/api/fields/{item_id}")
def update_field(item_id: int, item: FieldInput):
    try:
        area = polygon_area_m2(item.boundary)
    except (ValueError, TypeError, IndexError) as exc:
        raise HTTPException(400, str(exc)) from exc

    with db() as con:
        cur = con.execute("""
            UPDATE fields SET name=?, boundary=?, area_m2=? WHERE id=?
        """, (item.name, json.dumps(item.boundary), area, item_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Feld nicht gefunden")
    return {"ok": True, "area_m2": area}


@app.delete("/api/fields/{item_id}")
def delete_field(item_id: int):
    with db() as con:
        cur = con.execute("DELETE FROM fields WHERE id=?", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Feld nicht gefunden")
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(PAGE)


PAGE = r"""
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PyTrac – Verwaltung</title>
<link rel="stylesheet"
 href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet"
 href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css">
<style>
body {margin:0;font:15px system-ui;background:#f3f5f2;color:#202820}
header {background:#203b2a;color:white;padding:18px 24px}
main {display:grid;grid-template-columns:340px 1fr;gap:16px;padding:16px}
section {background:white;padding:16px;border-radius:12px}
input,select,button {box-sizing:border-box;width:100%;padding:9px;margin:4px 0 10px}
button {background:#285c38;color:white;border:0;border-radius:6px;cursor:pointer}
#map {height:65vh;min-height:420px;border-radius:8px}
small {color:#687268}
@media(max-width:800px){main{grid-template-columns:1fr}#map{height:50vh}}
</style>
</head>
<body>
<header><h2>PyTrac</h2>Maschinen · Felder · Fahrtsimulation</header>
<main>
<section>
<h3>Traktor erfassen</h3>
<form id="tractor">
<input name="name" placeholder="Name" required>
<input name="length_m" type="number" step=".01" placeholder="Länge (m)" required>
<input name="width_m" type="number" step=".01" placeholder="Breite (m)" required>
<input name="height_m" type="number" step=".01" placeholder="Höhe (m)" required>
<label>GPS-Position relativ zur Fahrzeugmitte (m)</label>
<input name="gps_x_m" type="number" step=".01" value="0" placeholder="X: nach vorn">
<input name="gps_y_m" type="number" step=".01" value="0" placeholder="Y: nach links">
<input name="gps_z_m" type="number" step=".01" value="0" placeholder="Z: nach oben">
<button>Traktor speichern</button>
</form>
<div id="tractors"></div>
<hr>
<h3>Anbaugerät erfassen</h3>
<form id="implement">
<input name="name" placeholder="Name" required>
<input name="length_m" type="number" step=".01" placeholder="Länge (m)" required>
<input name="width_m" type="number" step=".01" placeholder="Breite (m)" required>
<input name="height_m" type="number" step=".01" placeholder="Höhe (m)" required>
<input name="working_width_m" type="number" step=".01" placeholder="Arbeitsbreite (m)" required>
<select name="mount_position">
<option value="rear">Heck</option>
<option value="front">Front</option>
<option value="trailed">Gezogen</option>
</select>
<input name="hitch_offset_m" type="number" step=".01" value="0" placeholder="Aufnahme bis Arbeitskante (m)">
<button>Anbaugerät speichern</button>
</form>
<div id="implements"></div>
<hr>
<h3>Feld speichern</h3>
<p>Zeichne rechts mit dem Polygon-Werkzeug eine Feldgrenze.</p>
<form id="field">
<input name="name" placeholder="Feldname" required>
<button>Gezeichnetes Feld speichern</button>
</form>
<div id="fields"></div>
<hr>
<h3>Fahrt simulieren</h3>
<p>Klicke auf der Karte mehrere Wegpunkte. Dann starte die Animation.</p>
<button id="clearRoute">Fahrtpunkte löschen</button>
<button id="playRoute">Simulation starten</button>
<p id="status"><small>Noch keine Fahrt definiert.</small></p>
</section>
<section>
<h3>Karte</h3>
<div id="map"></div>
<p><small>Für die Karte ist eine Internetverbindung erforderlich.
Die Daten werden lokal in SQLite gespeichert.</small></p>
</section>
</main>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<script>
const map = L.map('map').setView([51.3127,9.4797],15);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
 attribution:'&copy; OpenStreetMap-Mitwirkende'
}).addTo(map);

const drawn = new L.FeatureGroup().addTo(map);
map.addControl(new L.Control.Draw({
 draw:{polygon:true,polyline:false,rectangle:false,circle:false,
       circlemarker:false,marker:false},
 edit:{featureGroup:drawn}
}));

let route=[], routeLine=null, vehicle=null, fieldsLayer=L.layerGroup().addTo(map);
let currentFieldId=null;

map.on(L.Draw.Event.CREATED, e => {
 drawn.clearLayers();
 drawn.addLayer(e.layer);
});
map.on('click', e => {
 route.push([e.latlng.lat,e.latlng.lng]);
 if(routeLine) map.removeLayer(routeLine);
 routeLine=L.polyline(route,{color:'#e58b22',weight:4}).addTo(map);
 document.getElementById('status').textContent =
   route.length+' Wegpunkte gesetzt.';
});

async function api(url, options={}) {
 const r=await fetch(url,{headers:{'Content-Type':'application/json'},
                            ...options});
 if(!r.ok) throw Error(await r.text());
 return r.json();
}
function values(form) {
 const obj=Object.fromEntries(new FormData(form));
 for(const k in obj) if(k!=='name' && k!=='mount_position')
   obj[k]=Number(obj[k]||0);
 return obj;
}
function addForm(id,url,refresh) {
 document.getElementById(id).addEventListener('submit',async e=>{
  e.preventDefault();
  try {
   await api(url,{method:'POST',body:JSON.stringify(values(e.target))});
   e.target.reset(); await refresh();
  } catch(err) { alert('Fehler: '+err.message); }
 });
}
async function loadTractors(){
 const items=await api('/api/tractors');
 document.getElementById('tractors').innerHTML='<b>Traktoren</b>'+
  items.map(x=>`<p>${x.name} · ${x.width_m} × ${x.length_m} m
   <button onclick="removeItem('/api/tractors/${x.id}',loadTractors)">Löschen</button></p>`).join('');
}
async function loadImplements(){
 const items=await api('/api/implements');
 document.getElementById('implements').innerHTML='<b>Anbaugeräte</b>'+
  items.map(x=>`<p>${x.name} · Arbeitsbreite ${x.working_width_m} m
   <button onclick="removeItem('/api/implements/${x.id}',loadImplements)">Löschen</button></p>`).join('');
}
async function loadFields(){
 const items=await api('/api/fields');
 fieldsLayer.clearLayers();
 document.getElementById('fields').innerHTML='<b>Felder</b>'+
  items.map(x=>`<p>${x.name} · ${(x.area_m2/10000).toFixed(3)} ha
   <button onclick="editField(${x.id})">Bearbeiten</button>
   <button onclick="removeItem('/api/fields/${x.id}',loadFields)">Löschen</button></p>`).join('');
 items.forEach(x=>{
  const layer=L.geoJSON(x.boundary).addTo(fieldsLayer);
  layer.bindPopup(`${x.name}: ${(x.area_m2/10000).toFixed(3)} ha`);
 });
}
async function removeItem(url,refresh){
 if(confirm('Diesen Eintrag löschen?')) {
  try { await api(url,{method:'DELETE'}); await refresh(); }
  catch(e){alert(e.message);}
 }
}
async function editField(id){
 const item=(await api('/api/fields')).find(x=>x.id===id);
 if(!item) return;
 currentFieldId=id;
 document.querySelector('#field [name=name]').value=item.name;
 drawn.clearLayers();
 const layer=L.geoJSON(item.boundary).getLayers()[0];
 drawn.addLayer(layer);
 map.fitBounds(layer.getBounds());
 document.getElementById('status').textContent=
  'Feld zum Bearbeiten geladen. Grenze ändern und speichern.';
}
addForm('tractor','/api/tractors',loadTractors);
addForm('implement','/api/implements',loadImplements);
document.getElementById('field').addEventListener('submit',async e=>{
 e.preventDefault();
 const layer=drawn.getLayers()[0];
 if(!layer){alert('Bitte zuerst ein Polygon zeichnen.');return;}
 const boundary=layer.toGeoJSON().geometry;
 const name=e.target.name.value;
 try{
  const edit=currentFieldId!==null;
  await api(edit?'/api/fields/'+currentFieldId:'/api/fields',{
   method:edit?'PUT':'POST',
   body:JSON.stringify({name,boundary})
  });
  currentFieldId=null; e.target.reset(); drawn.clearLayers();
  await loadFields();
 }catch(err){alert('Fehler: '+err.message);}
});
document.getElementById('clearRoute').onclick=()=>{
 route=[]; if(routeLine) map.removeLayer(routeLine);
 if(vehicle) map.removeLayer(vehicle);
 routeLine=null; vehicle=null;
 document.getElementById('status').textContent='Fahrtpunkte gelöscht.';
};
document.getElementById('playRoute').onclick=()=>{
 if(route.length<2){alert('Bitte mindestens zwei Wegpunkte setzen.');return;}
 if(vehicle) map.removeLayer(vehicle);
 let i=0;
 vehicle=L.circleMarker(route[0],{radius:8,color:'#d34b36'}).addTo(map);
 document.getElementById('status').textContent='Simulation läuft …';
 const step=()=>{
  if(i>=route.length){document.getElementById('status').textContent='Simulation beendet.';return;}
  vehicle.setLatLng(route[i++]);
  setTimeout(step,500);
 };
 step();
};
Promise.all([loadTractors(),loadImplements(),loadFields()])
 .catch(e=>console.error(e));
</script>
</body>
</html>
"""
