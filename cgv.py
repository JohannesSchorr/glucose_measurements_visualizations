"""
cgv.py

continuous glucose measurement

.. versionadded:: 0.1.0

visualize your glucose data measured by hand or 
by a glucose measurement system (CGM)
"""

from pathlib import Path
import pandas as pd
import matplotlib as mpl
import subprocess

# Use the pgf backend (must be set before pyplot imported)
mpl.use("pgf")
mpl.rcParams.update(
    {
        "pgf.texsystem": "pdflatex",
        "font.family": "serif",
        "text.usetex": True,
        "pgf.rcfonts": False,
    }
)
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter


from datetime import timedelta, date
from dataclasses import dataclass


@dataclass
class Week:

    """
    Representation of a week

    .. versionadded:: 0.1.0
    """

    first_day: date
    week_number: int

    @property
    def last_day(self) -> date:
        """last day of the week"""
        return self.first_day + timedelta(days=6)

    def calender_week(self) -> int:
        return self.first_day.isocalendar().week

    def year(self) -> int:
        return self.first_day.isocalendar().year

    def inside_week(self, day: date) -> bool:
        """check if given ``day`` is inside week"""
        if self.first_day <= day <= self.last_day:
            return True
        else:
            return False

    def time_span(self) -> str:
        """print the time-span of the week"""
        return (
            self.first_day.strftime(self.dateformat())
            + " - "
            + self.last_day.strftime(self.dateformat())
        )

    def dateformat(self) -> str:
        return "%d.%m.%Y"


class CGV:

    """
    Continous Glucose Visualization

    .. versionadded:: 0.1.0
    """

    def __init__(
        self,
        csv_path: str,
        date_column: str = "Gerätezeitstempel",
        glucose_column: str = "Glukosewert-Verlauf mmol/L",
    ):
        self.csv_path = Path(csv_path)
        self.data = pd.read_csv(self.csv_path, sep=",", header=1)
        if date_column in self.data.columns:
            self.date_column = date_column
        else:
            ValueError(
                f"Column-Name {date_column} is not given in the provided csv-file"
            )
        if glucose_column in self.data.columns:
            self.glucose_column = glucose_column
        else:
            ValueError(
                f"Column-Name {glucose_column} is not given in the provided csv-file"
            )
        self.data = self.data[
            self.data[self.date_column].notna() & self.data[self.glucose_column].notna()
        ]
        self.data[self.date_column] = pd.to_datetime(
            self.data[self.date_column], format="%m-%d-%Y %H:%M"
        )
        self.data.sort_values(by=self.date_column, inplace=True)
        self.weeks = self.segmenting_time_period()
        self.data[self.glucose_column] = self.convert_glucose_data()
        self._add_figure_folder()

    @property
    def dates(self) -> pd.Series:
        """dates in the data"""
        return self.data[self.date_column]

    @property
    def glucose(self) -> pd.Series:
        """glucose-values in the data"""
        return self.data[self.glucose_column]

    def _add_figure_folder(self) -> None:
        """adds figure-folder"""
        if not Path("./figures/").exists():
            Path("./figures/").mkdir()

    def segmenting_time_period(self, days_per_segment=7) -> list[Week]:
        """
        partitioning the full period into segements
        """
        first_day = self.dates.min().date()
        if first_day.weekday() > 0:
            first_day = first_day - timedelta(first_day.weekday())
        last_day = self.dates.max().date()
        first_week_day = first_day
        weeks = []
        week = 0
        while first_week_day < last_day:
            first_week_day = first_week_day + timedelta(days_per_segment)
            week += 1
            weeks.append(Week(first_week_day, week))
        return weeks

    def convert_glucose_data(self) -> pd.Series:
        """
        convert glucose-data saved as string with comma as decimal
        to numeric values
        """
        glucose_data = self.data[self.glucose_column]
        glucose_data = glucose_data.str.replace(pat=",", repl=".")
        return pd.to_numeric(glucose_data)

    def plot_week(self, week: int | Week) -> str:
        """plot the data within the given ``week_number``"""
        if isinstance(week, int):
            week = list(filter(lambda x: x.week_number == week, self.weeks))[0]
        filter_week = (week.first_day <= self.data[self.date_column].dt.date) & (
            self.data[self.date_column].dt.date <= week.last_day
        )
        week_data = self.data[filter_week]
        if len(week_data) == 0:
            print(f"In week {week} does no data exist")
            return
        fig, ax = plt.subplots(figsize=(18 * 0.39, 5.0 * 0.39))
        ax.plot(week_data[self.date_column], week_data[self.glucose_column])
        ax.set_ylabel("Glukose [mmol/L]")
        date_form = DateFormatter("%a")
        ax.xaxis.set_major_formatter(date_form)
        ax.grid("major")
        ax.set_title(
            f"Kalenderwoche {week.calender_week()}/{week.year()}: {week.time_span()}"
        )
        ax.set_xlim(week.first_day, week.last_day + timedelta(days=1))
        ax.set_ylim(0, 25)
        ax.fill_between(
            x=[week.first_day, week.last_day + timedelta(days=1)],
            y1=10.0,
            y2=3.9,
            color="lightgray",
        )
        path = self.plot_path(week)
        fig.savefig(path, format="pgf")
        return path

    def plot_path(self, week: Week):
        return f"./figures/Week{week.week_number}-{week.time_span()}.pgf"

    def plot_last_week(self) -> list[str]:
        last_week = max(self.weeks.keys())
        return [self.plot_week(last_week)]

    def plot_all_weeks(self) -> list[str]:
        first_week = min(self.weeks.keys())
        last_week = max(self.weeks.keys())
        return self.plot_week_range(first_week, last_week)

    def plot_week_range(self, first_week: int, last_week: int) -> list[str]:
        paths = []
        for week in range(first_week, last_week):
            paths.append(self.plot_week(week))
        return paths

    def plot_since_three_month(self) -> list[str]:
        starting_date = date.today() - timedelta(weeks=3 * 4)
        for week in self.weeks:
            if week.inside_week(starting_date):
                starting_week = week.week_number
        return self.plot_week_range(starting_week, len(self.weeks))

    def date_format(self) -> str:
        return "%d-%m-%Y"


class PDF:

    """create a pdf from the given pgf's using LaTeX"""

    def __init__(self, pgf_paths: list[str], file_name: str, name: str = None):
        self.pgf_paths = [Path(pgf) for pgf in pgf_paths if Path(pgf).exists()]
        self._name = name
        self._file_name = file_name
        self.build_tex_file()
        self.compile_latex()

    def preamble(self) -> list[str]:
        """get the preamble of the LaTeX-document"""
        lines = [
            "\\documentclass[DIV=15]{scrreprt}",
            "\\usepackage[T1]{fontenc}",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage[ngerman]{babel}",
            "\\usepackage{txfonts}%",
            "\\usepackage{pgfplots}",
            "\\usepackage{scrlayer-scrpage}",
            f"\\ihead{{{self._name}}}",
            "\\ohead{Glukose-Werte}",
        ]
        return lines

    def document(self) -> list[str]:
        """build the document"""
        lines = ["\\begin{document}", ""]
        for path in self.pgf_paths:
            lines.append("\\begin{center}")
            lines.append(f"\t\\input{{{str(path)}}}")
            lines.append("\\end{center}")
            lines.append("")
        lines.append("\\end{document}")
        return lines

    def build_tex_file(self) -> None:
        """buils the tex-file"""
        lines = self.preamble() + self.document()
        with open(self._file_name + ".tex", "w") as tex:
            tex.write("\n".join(lines))

    def compile_latex(self) -> None:
        """compiles the LaTeX-document"""
        subprocess.call(["pdflatex", self._file_name + ".tex"])


if __name__ == "__main__":
    c_g_v = CGV(csv_path="./data/20230725.csv")
    PDF(c_g_v.plot_since_three_month(), name="Johannes Schorr")
