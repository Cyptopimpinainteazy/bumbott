import unittest
import os
import json

from src.codebase_memory.snapshot_versioning import CodebaseSnapshot

class TestCodebaseSnapshot(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        with open(os.path.join(self.test_dir, "file1.txt"), "w") as f:
            f.write("Hello World")
        with open(os.path.join(self.test_dir, "file2.txt"), "w") as f:
            f.write("Another file")

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_create_and_save_snapshot(self):
        snapshotter = CodebaseSnapshot(self.test_dir)
        snapshot = snapshotter.create_snapshot()
        self.assertIn("file1.txt", snapshot)
        self.assertIn("file2.txt", snapshot)
        snapshotter.save_snapshot("snapshot.json")
        self.assertTrue(os.path.exists("snapshot.json"))
        with open("snapshot.json", "r") as f:
            data = json.load(f)
        self.assertIn("timestamp", data)
        self.assertIn("snapshot", data)
        os.remove("snapshot.json")

    def test_load_and_compare_snapshots(self):
        snapshotter1 = CodebaseSnapshot(self.test_dir)
        snapshot1 = snapshotter1.create_snapshot()
        snapshotter1.save_snapshot("snapshot1.json")

        with open(os.path.join(self.test_dir, "file2.txt"), "w") as f:
            f.write("Modified content")

        snapshotter2 = CodebaseSnapshot(self.test_dir)
        snapshot2 = snapshotter2.create_snapshot()
        snapshotter2.save_snapshot("snapshot2.json")

        changes = snapshotter2.compare_snapshots(snapshot1)
        self.assertIn("file2.txt", changes["modified"])
        self.assertEqual(len(changes["added"]), 0)
        self.assertEqual(len(changes["removed"]), 0)

        os.remove("snapshot1.json")
        os.remove("snapshot2.json")

if __name__ == "__main__":
    unittest.main()
