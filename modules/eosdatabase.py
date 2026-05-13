from __future__ import annotations

import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from modules.thermo_loader import scan_thermo_tables


class EOSDatabase:

    def __init__(self, data_dir: str):

        self.data_dir = data_dir

        self.df = scan_thermo_tables(data_dir)

    # -------------------------------------------------
    # Basic filtering
    # -------------------------------------------------

    def filter_out(
        self,
        field: str,
        contains: str,
    ) -> "EOSDatabase":
        """
        Return filtered copy.
        """

        new_db = EOSDatabase.__new__(EOSDatabase)

        new_db.data_dir = self.data_dir

        mask = (
            self.df[field]
            .astype(str)
            .str.contains(contains, case=False, na=False)
        )

        new_db.df = self.df[mask].copy()

        return new_db

    # -------------------------------------------------
    # Convenience methods
    # -------------------------------------------------

    def columns(self):

        return list(self.df.columns)

    def unique(self, field: str):

        return sorted(self.df[field].dropna().unique())
    
    def print_species(self):

        print("Species in database")
        print("-------------------")

        required = ["science_material", "science_formula", "source_citation"]

        missing = [
            col for col in required
            if col not in self.df.columns
        ]

        if missing:
            print(f"Missing required columns: {missing}")
            return

        # Keep only relevant columns
        species = (
            self.df[
                ["science_material", "science_formula", "source_citation"]
            ]
            .drop_duplicates()
            .sort_values(["science_material", "science_formula", "source_citation"])
        )

        current_material = None

        for _, row in species.iterrows():

            material = row["science_material"]
            formula = row["science_formula"]
            citation = row["source_citation"]

            # print material header only once
            if material != current_material:

                print()
                print(material)

                current_material = material

            print(f"  - {formula} : {citation}")


    def summary(self):

        print("EOSDatabase summary")
        print("-------------------")
        print(f"Rows   : {len(self.df)}")
        print(f"Columns: {len(self.df.columns)}")
        print("-------------------")
        if "source_citation" not in self.df.columns:
            print("No citation column found")
            return

        # avoid duplicates
        cols = ["source_citation"]

        if "science_formula" in self.df.columns:
            cols.append("science_formula")

        citations = (
            self.df[cols]
            .drop_duplicates()
            .sort_values(cols)
        )

        for _, row in citations.iterrows():

            if "science_formula" in cols:
                print(f"{row['source_citation']} ({row['science_formula']})")
            else:
                print(row["source_citation"])

    def export_tsv(
        self,
        filename: str,
        output_dir: str = "./output",
    ):

        # ---------------------------------
        # Create output directory if needed
        # ---------------------------------

        output_dir = Path(output_dir)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ---------------------------------
        # Append export date
        # ---------------------------------

        today = datetime.now().strftime("%Y%m%d")

        output_filename = (
            f"{filename}_{today}.tsv"
        )

        output_path = output_dir / output_filename

        # ---------------------------------
        # Export dataframe
        # ---------------------------------

        self.df.to_csv(
            output_path,
            sep="\t",
            index=False,
        )

        print()
        print("Export complete")
        print(f"File: {output_path}")
        print(f"Rows exported: {len(self.df)}")

    def plot_rhopt(self,plt_show=True):

        # ---------------------------------
        # Required columns
        # ---------------------------------

        required = [
            "rho[g/cm^3]",
            "P[GPa]",
            "T[K]",
            "source_unique_id",
        ]

        missing = [
            col for col in required
            if col not in self.df.columns
        ]

        if missing:
            print(
                f"Missing required columns: {missing}"
            )
            return

        # ---------------------------------
        # Unique datasets
        # ---------------------------------

        unique_ids = sorted(
            self.df["source_unique_id"]
            .dropna()
            .unique()
        )

        n_ids = len(unique_ids)

        print(f"Found {n_ids} datasets")

        if n_ids > 10:

            print(
                "ERROR: More than 10 datasets.\n"
                "Aborting to avoid unreadable plot."
            )

            return

        # ---------------------------------
        # Marker styles
        # ---------------------------------

        markers = [
            "o",
            "s",
            "^",
            "D",
            "v",
            "P",
            "X",
            "*",
            "<",
            ">",
        ]

        # ---------------------------------
        # Create figure
        # ---------------------------------

        fig, ax = plt.subplots(
            figsize=(8, 6)
        )

        # ---------------------------------
        # Global temperature normalization
        # ---------------------------------

        Tmin = self.df["T[K]"].min()
        Tmax = self.df["T[K]"].max()

        norm = mcolors.Normalize(
            vmin=Tmin,
            vmax=Tmax,
        )


        # ---------------------------------
        # Plot each dataset separately
        # ---------------------------------

        for marker, uid in zip(markers, unique_ids):

            sub = self.df[
                self.df["source_unique_id"] == uid
            ]

            sc = ax.scatter(
                sub["rho[g/cm^3]"],
                sub["P[GPa]"],
                c=sub["T[K]"],
                norm=norm,
                marker=marker,
                s=40,
                alpha=0.8,
                label=uid,
            )

        # ---------------------------------
        # Axes
        # ---------------------------------

        ax.set_xlabel(r"$\rho$ [g/cm$^3$]")
        ax.set_ylabel(r"$P$ [GPa]")

        ax.set_xscale("log")
        ax.set_yscale("log")

        # ---------------------------------
        # Colorbar
        # ---------------------------------

        cbar = plt.colorbar(sc, ax=ax)

        cbar.set_label(r"$T$ [K]")

        # ---------------------------------
        # Legend
        # ---------------------------------

        ax.legend(
            title="Dataset",
            fontsize=8,
        )

        # ---------------------------------
        # Cosmetics
        # ---------------------------------

        ax.grid(
            alpha=0.3,
            which="both",
        )

        plt.tight_layout()

        if plt_show == True: plt.show()


    def __repr__(self):

        return (
            f"EOSDatabase(rows={len(self.df)}, "
            f"columns={len(self.df.columns)})"
        )