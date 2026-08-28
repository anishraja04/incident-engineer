# LegacyImporter

Daily importer that reads order records exported from a legacy mainframe
system and loads them into the warehouse database.

- `importer/loader.py` — CSV reading + record conversion.
- `importer/data/` — the exported files.
- `tests/` — unit tests.

Run tests with:

```bash
python -m pytest -q
```