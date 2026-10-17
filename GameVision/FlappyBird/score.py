import json
import os
from config import SCORES_PATH

MAX_SCORES = 5
NAME_MAX_LEN = 12

class HighScores:
    def __init__(self, path=SCORES_PATH):
        self.path = path
        self.entries = self._load()

    def _load(self):
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
            return sorted(data, key=lambda e: e["score"], reverse=True)[:MAX_SCORES]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return []

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.entries, f, indent=2)

    def qualifies(self, score):
        if score <= 0:
            return False
        return len(self.entries) < MAX_SCORES or score > self.entries[-1]["score"]

    def add(self, name, score):
        self.entries.append({"name": name[:NAME_MAX_LEN] or "ANON", "score": score})
        self.entries = sorted(self.entries, key=lambda e: e["score"], reverse=True)[:MAX_SCORES]
        self._save()