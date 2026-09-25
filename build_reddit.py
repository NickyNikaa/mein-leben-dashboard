#!/usr/bin/env python3
# Holt aktuelle Reddit-Posts aus ausgewaehlten Subreddits ueber Reddits oeffentliche
# JSON-Feeds (keine Reddit-API-App / kein OAuth noetig, kein GPT-Scoring, keine laufenden Kosten).
# Schreibt reddit.json im selben schlanken Format-Stil wie build_events.py -> events.json.
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
import sys
import time
import urllib.request
import urllib.error
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
MIN_SCORE = 3                # Rauschen raus: Posts unter dieser Punktzahl ignorieren
MAX_TOTAL_POSTS = 60         # Obergrenze fuer die gespeicherte Liste
USER_AGENT = "python:mein-leben-dashboard-reddit-feed:v1.0 (personal dashboard, low volume)"

OUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "reddit.json"


def fetch_subreddit(name):
    url = "https://www.reddit.com/r/{}/hot.json?limit={}".format(name, POSTS_PER_SUBREDDIT)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
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


def main():
    all_posts = []
    seen_ids = set()
    errors = []
    for sub in SUBREDDITS:
        try:
            for p in fetch_subreddit(sub):
                if p["id"] in seen_ids:
                    continue
                seen_ids.add(p["id"])
                all_posts.append(p)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            errors.append("{}: {}".format(sub, e))
        time.sleep(1)  # freundlich zu Reddits Servern

    all_posts.sort(key=lambda p: p["score"], reverse=True)
    all_posts = all_posts[:MAX_TOTAL_POSTS]

    for p in all_posts:
        p["created"] = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc).isoformat()
        del p["created_utc"]

    out = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "subreddits": SUBREDDITS,
        "posts": all_posts,
    }
    if errors:
        out["errors"] = errors

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    print(len(all_posts), "Posts gespeichert.", ("Fehler: " + "; ".join(errors)) if errors else "")


if __name__ == "__main__":
    main()
