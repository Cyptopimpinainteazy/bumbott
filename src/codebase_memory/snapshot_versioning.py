import os
import hashlib
import json
from datetime import datetime

class CodebaseSnapshot:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.snapshot = {}

    def _hash_file(self, filepath):
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def create_snapshot(self):
        self.snapshot = {}
        for dirpath, _, filenames in os.walk(self.root_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    file_hash = self._hash_file(filepath)
                    rel_path = os.path.relpath(filepath, self.root_dir)
                    self.snapshot[rel_path] = file_hash
                except Exception as e:
                    print(f"Error hashing file {filepath}: {e}")
        return self.snapshot

    def save_snapshot(self, output_path):
        snapshot_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "snapshot": self.snapshot
        }
        with open(output_path, 'w') as f:
            json.dump(snapshot_data, f, indent=2)

    def load_snapshot(self, input_path):
        with open(input_path, 'r') as f:
            data = json.load(f)
        self.snapshot = data.get("snapshot", {})
        return self.snapshot

    def compare_snapshots(self, other_snapshot):
        added = []
        removed = []
        modified = []

        current_files = set(self.snapshot.keys())
        other_files = set(other_snapshot.keys())

        added = list(current_files - other_files)
        removed = list(other_files - current_files)

        for file in current_files.intersection(other_files):
            if self.snapshot[file] != other_snapshot[file]:
                modified.append(file)

        return {
            "added": added,
            "removed": removed,
            "modified": modified
        }
