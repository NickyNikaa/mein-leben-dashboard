#!/usr/bin/env python3
"""Hilfsskript, damit Agents ihren Status ins Dashboard melden.

Beispiele:
  python3 agent_status.py agent clero-ig-outreach --status running --task "Schreibt Creator 7 von 20" --done 7 --total 20 --label "Creator"
  python3 agent_status.py agent clero-ig-outreach --status idle --result "20 DMs verschickt" --next 2026-10-05T07:00:00Z
  python3 agent_status.py dm --id t123 --handle pilates.muc --name "Anna" --category creator --message "Hallo!" --unread --draft "Hi Anna ..."
Danach committen und pushen, dann aktualisiert sich die Seite.
"""
import argparse, json, datetime

def now(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def load(p):
    with open(p, encoding="utf-8") as f: return json.load(f)
def save(p, d):
    d["updated"] = now()
    with open(p, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1)

ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
a = sub.add_parser("agent"); a.add_argument("id"); a.add_argument("--status", choices=["running","idle","paused","error"])
a.add_argument("--task"); a.add_argument("--result"); a.add_argument("--note"); a.add_argument("--next")
a.add_argument("--done", type=int); a.add_argument("--total", type=int); a.add_argument("--label"); a.add_argument("--name"); a.add_argument("--area")
d = sub.add_parser("dm"); d.add_argument("--id", required=True); d.add_argument("--handle"); d.add_argument("--name")
d.add_argument("--category", choices=["host","creator","partner","sonstiges"]); d.add_argument("--message"); d.add_argument("--at")
d.add_argument("--unread", action="store_true"); d.add_argument("--status"); d.add_argument("--draft"); d.add_argument("--url"); d.add_argument("--ablage")
x = ap.parse_args()

if x.cmd == "agent":
    db = load("agents.json"); ag = next((i for i in db["agents"] if i["id"] == x.id), None)
    if not ag: ag = {"id": x.id, "name": x.name or x.id, "area": x.area or "", "status": "idle"}; db["agents"].append(ag)
    if x.name: ag["name"] = x.name
    if x.area: ag["area"] = x.area
    if x.status:
        if x.status == "running" and ag.get("status") != "running": ag["started"] = now()
        if ag.get("status") == "running" and x.status != "running":
            ag["last_run"] = now(); ag["runs_today"] = (ag.get("runs_today", 0) + 1) if (ag.get("runs_day") == now()[:10]) else 1; ag["runs_day"] = now()[:10]
        ag["status"] = x.status
    if x.task is not None: ag["task_now"] = x.task
    if x.status in ("idle", "paused", "error"): ag["task_now"] = x.task or ""; ag.pop("progress_done", None); ag.pop("progress_total", None)
    if x.note is not None: ag["note"] = x.note
    if x.result is not None:
        ag["last_result"] = x.result; ag["last_run"] = now(); db.setdefault("log", []).append({"at": now(), "agent": ag["name"], "text": x.result})
        db["log"] = db["log"][-60:]
    if x.next: ag["next_run"] = x.next
    if x.done is not None: ag["progress_done"] = x.done
    if x.total is not None: ag["progress_total"] = x.total
    if x.label: ag["progress_label"] = x.label
    if ag.get("status") == "running": ag["heartbeat"] = now()
    save("agents.json", db)
else:
    db = load("dms.json"); th = next((i for i in db["threads"] if i["id"] == x.id), None)
    if not th: th = {"id": x.id, "status": "neu"}; db["threads"].append(th)
    for k, v in [("handle", x.handle), ("name", x.name), ("category", x.category), ("last_message", x.message), ("last_at", x.at or now()),
                 ("status", x.status), ("draft", x.draft), ("url", x.url), ("ablage", x.ablage)]:
        if v is not None: th[k] = v
    if x.unread: th["unread"] = True
    if x.draft and not x.status: th["status"] = "entwurf"
    save("dms.json", db)
