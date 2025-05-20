import unittest

from src.codebase_memory.change_detection import ChangeDetector

class TestChangeDetector(unittest.TestCase):
    def setUp(self):
        self.old_snapshot = {
            "file1.txt": "hash1",
            "file2.txt": "hash2",
            "file3.txt": "hash3"
        }
        self.new_snapshot = {
            "file2.txt": "hash2",
            "file3.txt": "hash3_modified",
            "file4.txt": "hash4"
        }

    def test_detect_changes(self):
        detector = ChangeDetector(self.old_snapshot, self.new_snapshot)
        changes = detector.detect_changes()
        self.assertIn("file4.txt", changes["added"])
        self.assertIn("file1.txt", changes["removed"])
        self.assertIn("file3.txt", changes["modified"])

    def test_diff_file_content(self):
        old_content = "line1\nline2\nline3"
        new_content = "line1\nline2 modified\nline3"
        detector = ChangeDetector(self.old_snapshot, self.new_snapshot)
        diff = detector.diff_file_content(old_content, new_content)
        self.assertTrue(any("-line2" in line or "+line2 modified" in line for line in diff))

if __name__ == "__main__":
    unittest.main()
