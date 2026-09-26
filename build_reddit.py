#!/usr/bin/env python3
# Holt aktuelle Reddit-Posts aus ausgewaehlten Subreddits.
#
# Stand 2026: Reddit hat den self-serve API-App-Zugang (reddit.com/prefs/apps)
# faktisch eingestellt ("Responsible Builder Policy" - manuelle Pruefung noetig,
# hohe Ablehnungsquote fuer Einzelpersonen). Deshalb kein OAuth/API-App hier.
# Stattdessen zwei Ebenen, die (Stand heute) ohne Anmeldung funktionieren:
#   1. old.reddit.com/*.json  - inhaltlich identisch zu www.reddit.com/*.json,
#      aber von Reddits Bot-Abwehr spuerbar seltener blockiert.
#   2. Fallback pro Subreddit, falls alt trotzdem blockt: RSS-Feed (*.rss).
#      Liefert Titel/Link/Autor/Datum, aber KEIN Score/Kommentarzahl (dann 0).
# Kein GPT-Scoring, keine laufenden Kosten. Schreibt reddit.json im selben
# schlanken Format-Stil wie build_events.py -> events.json.
#
# Subreddit-Liste unten frei anpassbar. Aktuelle Zuordnung zu Nickys Themen:
#   AI Agents / Agentic AI / Usecases    -> AI_Agents
#   KI allgemein                         -> artificial
#   KI Usecases & Erfahrungen            -> ChatGPT
#   Automatisierungen                    -> automation
#   Business / Selbststaendigkeit        -> Entrepreneur, SaaS
#   Moneymaking with AI / Side Projects  -> SideProject, SaaS
#   Tipps & Github Repos                 -> SideProject, opensource
#   Jobs (Freelance/Remote)              -> forhire

import json
import random
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SUBREDDITS = [
    "AI_Agents",
    "artificial",
    "ChatGPT",
    "automation",
    "Entrepreneur",
    "SaaS",
    "SideProject",
    "forhire",
    "opensource",
]

POSTS_PER_SUBREDDIT = 15     # wie viele Hot-Posts pro Subreddit geholt werden
MIN_SCORE = 3                # Rauschen raus (gilt nur fuer den JSON-Pfad, RSS hat keinen Score)
MAX_TOTAL_POSTS = 60         # Obergrenze fuer die gespeicherte Liste
OUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "reddit.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

RSS_NS = {"atom": "http://www.w3.org/2005/Atom"}


def sleep_jitter(base=2.5, spread=1.5):
    time.sleep(base + random.uniform(0, spread))


def _get(url, retry_on_429=True):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 429 and retry_on_429:
            time.sleep(8)
            return _get(url, retry_on_429=False)
        raise


def fetch_json(sub):
    url = "https://old.reddit.com/r/{}/hot.json?limit={}".format(sub, POSTS_PER_SUBREDDIT)
    data = json.loads(_get(url).decode("utf-8"))
    posts = []
    for child in data.get("data", {}).get("children", []):
        p = child.get("data", {})
        if p.get("stickied") or p.get("over_18"):
            continue
        if (p.get("score") or 0) < MIN_SCORE:
            continue
        posts.append({
            "id": p.get("id"),
            "subreddit": p.get("subreddit"),
            "title": p.get("title", ""),
            "author": p.get("author", ""),
            "permalink": "https://www.reddit.com" + p.get("permalink", ""),
            "url": p.get("url", ""),
            "score": p.get("score", 0),
            "num_comments": p.get("num_comments", 0),
            "created_utc": p.get("created_utc", 0),
        })
    return posts


def fetch_rss(sub):
    url = "https://www.reddit.com/r/{}/new.rss?limit={}".format(sub, POSTS_PER_SUBREDDIT)
    root = ET.fromstring(_get(url))
    posts = []
    for entry in root.findall("atom:entry", RSS_NS):
        link_el = entry.find("atom:link", RSS_NS)
        id_el = entry.find("atom:id", RSS_NS)
        title_el = entry.find("atom:title", RSS_NS)
        author_el = entry.find("atom:author/atom:name", RSS_NS)
        updated_el = entry.find("atom:updated", RSS_NS)
        permalink = link_el.get("href") if link_el is not None else ""
        post_id = (id_el.text or "").rsplit("_", 1)[-1] if id_el is not None else permalink
        created_utc = 0
        if updated_el is not None and updated_el.text:
            try:
                created_utc = datetime.fromisoformat(updated_el.text.replace("Z", "+00:00")).timestamp()
            except ValueError:
                created_utc = 0
        author = ""
        if author_el is not None and author_el.text:
            author = author_el.text.replace("/u/", "")
        posts.append({
            "id": post_id,
            "subreddit": sub,
            "title": title_el.text if title_el is not None else "",
            "author": author,
            "permalink": permalink,
            "url": permalink,
            "score": 0,
            "num_comments": 0,
            "created_utc": created_utc,
        })
    return posts


def fetch_subreddit(sub):
    try:
        return fetch_json(sub), None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        json_error = str(e)
    try:
        posts = fetch_rss(sub)
        return posts, "old.reddit.com blockiert ({}), RSS-Fallback genutzt (ohne Score/Kommentare)".format(json_error)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ET.ParseError) as e:
        return [], "old.reddit.com: {} / RSS ebenfalls fehlgeschlagen: {}".format(json_error, e)


def main():
    all_posts = []
    seen_ids = set()
    notes = []
    for i, sub in enumerate(SUBREDDITS):
        if i > 0:
            sleep_jitter()
        posts, note = fetch_subreddit(sub)
        if note:
            notes.append("{}: {}".format(sub, note))
        for p in posts:
            if p["id"] in seen_ids:
                continue
            seen_ids.add(p["id"])
            all_posts.append(p)

    all_posts.sort(key=lambda p: (p["score"], p["created_utc"]), reverse=True)
    all_posts = all_posts[:MAX_TOTAL_POSTS]

    for p in all_posts:
        p["created"] = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc).isoformat()
        del p["created_utc"]

    out = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "subreddits": SUBREDDITS,
        "posts": all_posts,
    }
    if notes:
        out["notes"] = notes

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    print(len(all_posts), "Posts gespeichert.")
    if notes:
        print("Hinweise:", "; ".join(notes))


if __name__ == "__main__":
    main()
