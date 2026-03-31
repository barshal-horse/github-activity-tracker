"""
Process real GH Archive JSON.gz data with pandas and export aggregated CSVs.
Handles the inconsistent schemas in GH Archive data that trip up Spark's inference.
"""
import gzip
import json
import os
from pathlib import Path
from collections import Counter, defaultdict
import csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "gharchive"
DASHBOARD_DATA_DIR = PROJECT_ROOT / "dashboard" / "data"


def process_files():
    json_files = sorted(RAW_DIR.rglob("*.json.gz"))
    if not json_files:
        print("No JSON files found!")
        return

    print(f"Processing {len(json_files)} files...")

    event_type_counts = Counter()
    event_type_actors = defaultdict(set)
    event_type_repos = defaultdict(set)
    hourly_counts = defaultdict(lambda: Counter())  # (date, hour) -> event_type -> count
    hourly_actors = defaultdict(lambda: defaultdict(set))
    hourly_repos = defaultdict(lambda: defaultdict(set))
    repo_events = defaultdict(lambda: Counter())  # repo -> event_type -> count
    repo_actors = defaultdict(set)

    total = 0
    skipped_bots = 0

    for fpath in json_files:
        print(f"  Reading {fpath.name}...")
        with gzip.open(str(fpath), "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                actor_login = (event.get("actor") or {}).get("login", "")
                if not actor_login or "[bot]" in actor_login or actor_login.endswith("bot"):
                    skipped_bots += 1
                    continue

                event_type = event.get("type", "Unknown")
                repo_name = (event.get("repo") or {}).get("name", "unknown/unknown")
                created_at = event.get("created_at", "")

                # Parse date and hour
                event_date = created_at[:10] if created_at else "unknown"
                try:
                    event_hour = int(created_at[11:13]) if created_at else 0
                except (ValueError, IndexError):
                    event_hour = 0

                total += 1

                # Aggregate
                event_type_counts[event_type] += 1
                event_type_actors[event_type].add(actor_login)
                event_type_repos[event_type].add(repo_name)

                key = (event_date, event_hour)
                hourly_counts[key][event_type] += 1
                hourly_actors[key][event_type].add(actor_login)
                hourly_repos[key][event_type].add(repo_name)

                repo_events[repo_name][event_type] += 1
                repo_actors[repo_name].add(actor_login)

    print(f"\nTotal events processed: {total:,}")
    print(f"Bots skipped: {skipped_bots:,}")

    # ---- Write CSVs ----
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # CSV 1: Event distribution
    dist_path = DASHBOARD_DATA_DIR / "event_distribution.csv"
    with open(dist_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event_type", "event_count", "unique_actors", "unique_repos", "percentage"])
        for et, cnt in event_type_counts.most_common():
            w.writerow([
                et, cnt,
                len(event_type_actors[et]),
                len(event_type_repos[et]),
                round(cnt * 100.0 / total, 2)
            ])
    print(f"Saved event_distribution.csv ({len(event_type_counts)} event types)")

    # CSV 2: Hourly activity
    hourly_path = DASHBOARD_DATA_DIR / "hourly_activity.csv"
    with open(hourly_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event_date", "event_hour", "event_type", "event_count", "unique_actors", "unique_repos"])
        for (date, hr) in sorted(hourly_counts.keys()):
            for et, cnt in hourly_counts[(date, hr)].most_common():
                w.writerow([
                    date, hr, et, cnt,
                    len(hourly_actors[(date, hr)][et]),
                    len(hourly_repos[(date, hr)][et]),
                ])
    print(f"Saved hourly_activity.csv")

    # CSV 3: Top repos (top 50)
    top_repos = sorted(repo_events.keys(), key=lambda r: sum(repo_events[r].values()), reverse=True)[:50]
    repos_path = DASHBOARD_DATA_DIR / "top_repos.csv"
    with open(repos_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "repo_name", "repo_owner", "repo_short_name", "total_events",
            "total_contributors", "push_count", "star_count", "fork_count",
            "pr_count", "issue_count", "activity_rank"
        ])
        for i, repo in enumerate(top_repos):
            parts = repo.split("/", 1)
            evts = repo_events[repo]
            w.writerow([
                repo,
                parts[0] if len(parts) > 1 else repo,
                parts[1] if len(parts) > 1 else repo,
                sum(evts.values()),
                len(repo_actors[repo]),
                evts.get("PushEvent", 0),
                evts.get("WatchEvent", 0),
                evts.get("ForkEvent", 0),
                evts.get("PullRequestEvent", 0),
                evts.get("IssuesEvent", 0),
                i + 1
            ])
    print(f"Saved top_repos.csv ({len(top_repos)} repos)")

    print(f"\n✅ Done! Dashboard data is in {DASHBOARD_DATA_DIR}")


if __name__ == "__main__":
    process_files()
