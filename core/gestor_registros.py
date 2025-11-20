"""Gestor sencillo de records: guarda y carga JSON en data/records.json"""
import json
from datetime import datetime
from pathlib import Path


RUTA = Path(__file__).resolve().parents[1] / 'data' / 'records.json'


def cargar_registros():
    RUTA.parent.mkdir(parents=True, exist_ok=True)
    if not RUTA.exists():
        RUTA.write_text('[]', encoding='utf-8')
        return []
    try:
        with open(RUTA, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def guardar_registro(nombre, tiempo, avatar=None):
    registros = cargar_registros()
    entry = {
        'name': nombre,
        'time': round(float(tiempo), 2),
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    if avatar:
        try:
            entry['avatar'] = str(avatar)
        except Exception:
            entry['avatar'] = None
    # append and keep unique entries (avoid exact duplicates)
    registros.append(entry)
    # sort by time (ascending)
    registros.sort(key=lambda r: r.get('time', 999999))
    # remove exact duplicates (same name, time, date, avatar)
    unique = []
    seen = set()
    for r in registros:
        key = (r.get('name'), float(r.get('time', 0.0)), r.get('date'), r.get('avatar'))
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    # keep only top 5 fastest records
    limited = unique[:5]
    with open(RUTA, 'w', encoding='utf-8') as f:
        json.dump(limited, f, ensure_ascii=False, indent=4)
