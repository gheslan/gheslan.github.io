"""Build the land outline used by the conference map.

Downloads Natural Earth country shapes (world-atlas, 1:50m, public domain),
projects them for the Europe–Mediterranean window of the map and writes a
single simplified SVG path to src/data/basemap.json.

Only needs to be re-run if the map window changes:  python src/basemap.py
"""
import json
import math
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "basemap.json")
URL = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json"

# Map window (degrees) and output size (SVG user units)
LON0, LON1 = -13.0, 33.0
LAT0, LAT1 = 30.5, 63.5
WIDTH = 600.0
LAT_REF = 47.0  # standard parallel of the equirectangular projection
KX = math.cos(math.radians(LAT_REF))
HEIGHT = WIDTH * (LAT1 - LAT0) / ((LON1 - LON0) * KX)


def project(lon, lat):
    x = (lon - LON0) * KX / ((LON1 - LON0) * KX) * WIDTH
    y = (LAT1 - lat) / (LAT1 - LAT0) * HEIGHT
    return x, y


def decode_arcs(topo):
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def ring_coords(ring, arcs):
    pts = []
    for i in ring:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "gheslan.github.io site builder"})
    topo = json.load(urllib.request.urlopen(req))
    arcs = decode_arcs(topo)
    margin = 4.0
    parts = []
    for geom in topo["objects"]["countries"]["geometries"]:
        polys = geom.get("arcs", [])
        if geom["type"] == "Polygon":
            polys = [polys]
        elif geom["type"] != "MultiPolygon":
            continue
        for poly in polys:
            for ring in poly:
                pts = ring_coords(ring, arcs)
                lons = [p[0] for p in pts]
                lats = [p[1] for p in pts]
                if max(lons) < LON0 - margin or min(lons) > LON1 + margin or max(lats) < LAT0 - margin or min(lats) > LAT1 + margin:
                    continue
                proj = [project(lo, la) for lo, la in pts]
                # clamp far-away points to just outside the window (they are clipped anyway)
                proj = [(min(max(x, -20), WIDTH + 20), min(max(y, -20), HEIGHT + 20)) for x, y in proj]
                # simplification: drop points closer than 1.6 units to the previous kept point
                kept = [proj[0]]
                for p in proj[1:]:
                    if math.hypot(p[0] - kept[-1][0], p[1] - kept[-1][1]) >= 1.6:
                        kept.append(p)
                xs = [p[0] for p in kept]
                ys = [p[1] for p in kept]
                if len(kept) < 4 or (max(xs) - min(xs)) * (max(ys) - min(ys)) < 6:
                    continue
                parts.append("M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in kept) + "Z")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"width": WIDTH, "height": round(HEIGHT, 1), "lon0": LON0, "lon1": LON1, "lat0": LAT0, "lat1": LAT1,
                   "lat_ref": LAT_REF, "d": "".join(parts)}, f)
    print(f"basemap: {len(parts)} rings, {os.path.getsize(OUT) // 1024} KB, {WIDTH:.0f}x{HEIGHT:.0f}")  # noqa


if __name__ == "__main__":
    main()
