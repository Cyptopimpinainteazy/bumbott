import difflib
from typing import List, Dict

class ChangeDetector:
    def __init__(self, old_snapshot: Dict[str, str], new_snapshot: Dict[str, str]):
        self.old_snapshot = old_snapshot
        self.new_snapshot = new_snapshot

    def detect_changes(self):
        added = []
        removed = []
        modified = []

        old_files = set(self.old_snapshot.keys())
        new_files = set(self.new_snapshot.keys())

        added = list(new_files - old_files)
        removed = list(old_files - new_files)

        for file in old_files.intersection(new_files):
            if self.old_snapshot[file] != self.new_snapshot[file]:
                modified.append(file)

        return {
            "added": added,
            "removed": removed,
            "modified": modified
        }

    def diff_file_content(self, old_content: str, new_content: str) -> List[str]:
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        diff = difflib.unified_diff(old_lines, new_lines, lineterm='')
        return list(diff)
