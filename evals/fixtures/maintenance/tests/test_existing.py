"""One ordinary baseline case; not the complete acceptance suite."""

import unittest

from labels import export_labels


class ExistingBehavior(unittest.TestCase):
    def test_sorted_unique_catalog(self):
        rows = [
            {"accession": "MS-208", "title": "Amber prism", "collection": "minerals"},
            {"accession": "MS-103", "title": "Silver frond", "collection": "botany"},
        ]
        self.assertEqual(export_labels(rows), [
            {"accession": "MS-103", "caption": "Silver frond"},
            {"accession": "MS-208", "caption": "Amber prism"},
        ])


if __name__ == "__main__":
    unittest.main()
