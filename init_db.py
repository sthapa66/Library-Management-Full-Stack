# uv run --env-file .env python init_db.py

from backend.app.core.db import engine
import pandas as pd
from pathlib import Path
from typing import List


DATA_DIR = Path("init_data")
BOOK_CSV = DATA_DIR / "book.csv"
AUTHORS_CSV = DATA_DIR / "authors.csv"
BOOK_AUTHORS_CSV = DATA_DIR / "book_authors.csv"


def load_table(
    csv_path: Path,
    table_name: str,
    transformations: dict | None = None,
    drop_columns: List[str] | None = None,
) -> None:
    """
    Load a CSV file into a SQLite table with column renaming and transformations.

    Args:
        conn: SQLite connection object
        csv_path: Path to the CSV file
        table_name: Name of the target database table
        column_mapping: Dictionary mapping CSV columns to database columns
        transformations: Optional dict of column transformations to apply
        drop_columns: Optional list of columns to drop before insertion
    """
    print(f"Loading {table_name}...")

    df = pd.read_csv(csv_path, sep="\t")
    # df = df.rename(columns=column_mapping)

    if transformations:
        for col, transform_func in transformations.items():
            df[col] = transform_func(df[col])

    if drop_columns:
        print(f"Dropping columns: {drop_columns}")
        df = df.drop(columns=drop_columns)

    if table_name == "BOOK_AUTHORS":
        # df["author_id"] = df["author_id"].astype(int).add(1).astype(str)
        df["author_id"] = df["author_id"].add(1)
        df = df.drop_duplicates(subset=["author_id", "isbn"])

    print(df.head(5))

    df.to_sql(table_name.lower(), engine, if_exists="append", index=False)

    print(f"{table_name} loaded successfully ({len(df)} rows).")


def populate_database() -> None:
    """
    Populate all database tables from CSV files.
    """
    # Define table loading specifications
    table_specs = [
        {
            "csv_path": AUTHORS_CSV,
            "table_name": "AUTHORS",
            "drop_columns": "author_id",
        },
        {
            "csv_path": BOOK_CSV,
            "table_name": "BOOK",
        },
        {
            "csv_path": BOOK_AUTHORS_CSV,
            "table_name": "BOOK_AUTHORS",
        }
    ]

    for spec in table_specs:
        load_table(
            spec["csv_path"],
            spec["table_name"],
            # spec.get("transformations"),
            drop_columns = spec.get("drop_columns"),
        )


def main() -> None:
    populate_database()


if __name__ == "__main__":
    main()
