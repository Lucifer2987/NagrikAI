"""
Adds the three image/OCR columns to an existing complaints table.
Safe to run multiple times — skips columns that already exist.

Run: uv run python -m backend.data.migrate_add_image_ocr
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
load_dotenv()

from backend.database import engine

NEW_COLUMNS = [
    ("image_path",    "VARCHAR(512)"),
    ("ocr_text",      "TEXT"),
    ("ocr_confidence","REAL"),
]


def migrate():
    with engine.connect() as conn:
        existing = {
            row[1]
            for row in conn.execute(
                __import__("sqlalchemy").text("PRAGMA table_info(complaints)")
            )
        }

        for col_name, col_type in NEW_COLUMNS:
            if col_name in existing:
                print(f"  Column '{col_name}' already exists — skipping.")
            else:
                conn.execute(
                    __import__("sqlalchemy").text(
                        f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"
                    )
                )
                print(f"  Added column '{col_name} {col_type}'.")

        conn.commit()

    print("Migration complete.")


if __name__ == "__main__":
    migrate()
