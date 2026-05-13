from __future__ import annotations

from pathlib import Path
import pandas as pd
import tomllib


def load_single_thermo(dat_path: Path) -> pd.DataFrame:
    """
    Load one thermo table and merge metadata into dataframe columns.
    """

    toml_path = dat_path.with_suffix(".toml")

    # -----------------------------
    # Read metadata
    # -----------------------------
    with open(toml_path, "rb") as f:
        metadata = tomllib.load(f)

    delimiter = metadata.get("data", {}).get("delimiter", r"\s+")

    # -----------------------------
    # Read table
    # -----------------------------
    df = pd.read_csv(
        dat_path,
        comment="#",
        sep=delimiter,
        engine="python",
    )

    # -----------------------------
    # Add metadata as dataframe columns
    # -----------------------------

    for section_name, section in metadata.items():

        # skip non-dictionaries
        if not isinstance(section, dict):
            continue

        for key, value in section.items():

            column_name = f"{section_name}_{key}"

            df[column_name] = value

            # useful provenance fields
            # df["table_path"] = str(dat_path)
            # df["table_name"] = dat_path.stem

    return df


def scan_thermo_tables(data_dir: str | Path) -> pd.DataFrame:
    """
    Scan all folders recursively and merge thermo tables.
    """

    data_dir = Path(data_dir)

    dfs = []

    for dat_path in data_dir.rglob("*_thermo.dat"):

        try:
            df = load_single_thermo(dat_path)
            dfs.append(df)

            print(f"Loaded: {dat_path}")

        except Exception as e:
            print(f"Failed loading {dat_path}")
            print(e)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)