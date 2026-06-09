import json
import os
import time

HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".ls-imagecomm", "history.json")
MAX_ENTRIES = 15


class HistoryManager:
    def __init__(self):
        self._entries = []
        self._load()

    def _load(self):
        try:
            if os.path.isfile(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
        except Exception:
            self._entries = []

    def _save(self):
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2, ensure_ascii=False)

    def add_entry(self, pasta, arquivos_originais, ok, total):
        nomes = [os.path.basename(p) for p in arquivos_originais[:5]]
        entry = {
            "timestamp": time.time(),
            "pasta": pasta,
            "arquivos": nomes,
            "ok": ok,
            "total": total,
        }
        self._entries.insert(0, entry)
        self._entries = self._entries[:MAX_ENTRIES]
        self._save()

    @property
    def entries(self):
        return list(self._entries)
