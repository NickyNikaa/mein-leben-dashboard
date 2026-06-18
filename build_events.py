#!/usr/bin/env python3
# Liest die rohe list_events-JSON (Argument 1) und schreibt eine kompakte events.json (Argument 2).
import json, sys

src = sys.argv[1]
dst = sys.argv[2]

with open(src, "r", encoding="utf-8") as f:
    data = json.load(f)

evs = []
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
    else:
        evs.append({
            "date": s.get("date", "")[:10],
            "allDay": True,
            "start": "",
            "end": "",
            "title": title,
        })

evs.sort(key=lambda x: (x["date"], x["start"] or ""))

out = {
    "updated": data.get("updated", ""),
    "tz": data.get("timeZone", "Europe/Berlin"),
    "events": evs,
}
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

print(len(evs), "Termine")
for e in evs[:10]:
    print(e["date"], e["start"] or "ganztägig", "-", e["title"])
