"""High-score table stored as JSON next to the game."""
import json
import os

from config import SCORES_PATH

MAX_SCORES = 5
NAME_MAX_LEN = 12


class HighScores:
    def __init__(self, path=SCORES_PATH):
        self.path = path
        self.entries = self._load()

    # --- storage -----------------------------------------------------------
    @staticmethod
    def _clean(entry):
        """Return a valid entry dict, or None if the stored row is garbage."""
        try:
            score = int(entry["score"])
            name = str(entry.get("name", "ANON"))[:NAME_MAX_LEN] or "ANON"
            mode = str(entry.get("mode", ""))
        except (KeyError, TypeError, ValueError, AttributeError):
            return None
        return {"name": name, "score": score, "mode": mode}

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(data, list):
            return []
        rows = [r for r in (self._clean(e) for e in data) if r]
        return sorted(rows, key=lambda e: e["score"], reverse=True)[:MAX_SCORES]

    def _save(self):
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2)
            os.replace(tmp, self.path)          # atomic: never leaves a half-written file
        except OSError:
            pass                                 # read-only folder: keep playing anyway

    # --- API ---------------------------------------------------------------
    @property
    def best(self):
        return self.entries[0]["score"] if self.entries else 0

    def qualifies(self, score):
        if score <= 0:
            return False
        return len(self.entries) < MAX_SCORES or score > self.entries[-1]["score"]

    def add(self, name, score, mode=""):
        name = name.strip()[:NAME_MAX_LEN] or "ANON"
        self.entries.append({"name": name, "score": int(score), "mode": mode})
        self.entries = sorted(self.entries, key=lambda e: e["score"], reverse=True)[:MAX_SCORES]
        self._save()
