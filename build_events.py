#!/usr/bin/env python3
# Liest die rohe list_events-JSON (Argument 1) und schreibt:
#   - Argument 2: events.json  (Agenda fuer das Dashboard, mit Titeln)
#   - busy.json   (im selben Ordner; nur belegte Zeiten OHNE Titel, fuer die Teilen-Seite)
import json, os, sys

src = sys.argv[1]
dst = sys.argv[2]
busy_dst = os.path.join(os.path.dirname(dst), "busy.json")

with open(src, "r", encoding="utf-8") as f:
    data = json.load(f)

evs = []
busy = []
for e in data.get("events", []):
    if e.get("status") == "cancelled":
        continue
    title = e.get("summary", "(ohne Titel)")
    s = e.get("start", {})
    en = e.get("end", {})
    if "dateTime" in s:
        st = s["dateTime"]      # z.B. 2026-06-18T07:30:00+02:00
        et = en.get("dateTime", "")
        evs.append({
            "date": st[:10],
            "allDay": False,
            "start": st[11:16],
            "end": et[11:16] if et else "",
            "title": title,
        })
        # Fuer die Teilen-Seite: nur echte, blockierende Termine (keine "frei"-Eintraege), ohne Titel
        if e.get("transparency") != "transparent" and et:
            busy.append({
                "date": st[:10],
                "start": st[11:16],
                "end": et[11:16],
            })
    else:
        evs.append({
            "date": s.get("date", "")[:10],
            "allDay": True,
            "start": "",
            "end": "",
            "title": title,
        })

evs.sort(key=lambda x: (x["date"], x["start"] or ""))
busy.sort(key=lambda x: (x["date"], x["start"]))

with open(dst, "w", encoding="utf-8") as f:
    json.dump({"updated": data.get("updated", ""), "tz": data.get("timeZone", "Europe/Berlin"), "events": evs},
              f, ensure_ascii=False, separators=(",", ":"))

with open(busy_dst, "w", encoding="utf-8") as f:
    json.dump({"updated": data.get("updated", ""), "tz": data.get("timeZone", "Europe/Berlin"), "busy": busy},
              f, ensure_ascii=False, separators=(",", ":"))

print(len(evs), "Termine,", len(busy), "belegte Slots")
