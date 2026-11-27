"""Summarize three observed tasks per participant in the project evaluation."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median
from math import isfinite


def summarize(records):
    people = defaultdict(dict)
    for row in records:
        person, task = row["participant"].strip(), row["task"].strip()
        seconds = float(row["seconds"])
        completed = row["completed"].strip().lower()
        if (not person or task not in ("filter", "listen", "projection")
                or task in people[person] or completed not in ("yes", "no")
                or not isfinite(seconds) or seconds < 0):
            raise ValueError("Invalid or duplicate session task")
        people[person][task] = (completed == "yes", seconds)
    if not 4 <= len(people) <= 6 or any(len(tasks) != 3 for tasks in people.values()):
        raise ValueError("Final summary needs three task records for each of 4–6 classmates")
    for task in ("filter", "listen", "projection"):
        observations = [tasks[task] for tasks in people.values()]
        times = [seconds for done, seconds in observations if done]
        yield (task, len(observations), len(times), median(times) if times else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.sessions.open(newline="") as source:
        rows = list(summarize(csv.DictReader(source)))
    with args.output.open("x", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(("task", "attempts", "completed", "median_completed_seconds"))
        writer.writerows(rows)


if __name__ == "__main__":
    main()
