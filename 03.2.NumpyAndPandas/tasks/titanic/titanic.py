import typing as tp
import polars as pl


def male_age(df: pl.DataFrame) -> float:
    """
    Return mean age of survived men, embarked in Southampton with fare > 30
    :param df: dataframe
    :return: mean age
    """
    filtered = df.filter(
        (pl.col("Sex") == "male") &
        (pl.col("Survived") == 1) &
        (pl.col("Embarked") == "S") &
        (pl.col("Fare") > 30) &
        (pl.col("Age").is_not_null())
    )
    return filtered.select(pl.col("Age").mean()).item()


def nan_columns(df: pl.DataFrame) -> tp.Iterable[str]:
    """
    Return list of columns containing nans
    :param df: dataframe
    :return: series of columns
    """
    cols = []
    for col in df.columns:
        if df.select(pl.col(col).is_null().any()).item():
            cols.append(col)
    return cols


def class_distribution(df: pl.DataFrame) -> pl.Series:
    """
    Return Pclass distrubution
    :param df: dataframe
    :return: series with ratios
    """
    total = len(df)
    return df.group_by("Pclass").len().sort("Pclass").select(
        (pl.col("len") / total).alias("ratio")
    )["ratio"]


def families_count(df: pl.DataFrame, k: int) -> int:
    """
    Compute number of families with more than k members
    :param df: dataframe,
    :param k: number of members,
    :return: number of families
    """
    surnames = df.select(
        pl.col("Name").str.split(",").list.first().alias("surname")
    )
    counts = surnames.group_by("surname").len()
    return len(counts.filter(pl.col("len") > k))


def mean_price(df: pl.DataFrame, tickets: tp.Iterable[str]) -> float:
    """
    Return mean price for specific tickets list
    :param df: dataframe,
    :param tickets: list of tickets,
    :return: mean fare for this tickets
    """
    tickets_list = list(tickets)
    return df.filter(pl.col("Ticket").is_in(tickets_list)).select(
        pl.col("Fare").mean()
    ).item()


def max_size_group(df: pl.DataFrame, columns: list[str]) -> tp.Iterable[tp.Any]:
    """
    For given set of columns compute most common combination of values of these columns
    :param df: dataframe,
    :param columns: columns for grouping,
    :return: list of most common combination
    """
    filtered_df = df.filter(pl.all_horizontal([pl.col(col).is_not_null() for col in columns]))
    grouped = filtered_df.group_by(columns).len().sort("len", descending=True)
    first_row = grouped.head(1)
    return tuple(first_row[col].item() for col in columns)


def dead_lucky(df: pl.DataFrame) -> float:
    """
    Compute dead ratio of passengers with lucky tickets.
    A ticket is considered lucky when it contains an even number of digits in it
    and the sum of the first half of digits equals the sum of the second part of digits
    ex:
    lucky: 123222, 2671, 935755
    not lucky: 123456, 62869, 568290
    :param df: dataframe,
    :return: ratio of dead lucky passengers
    """
    def is_lucky(ticket: str) -> bool:
        if not isinstance(ticket, str):
            ticket = str(ticket)
        if not ticket.isdigit():
            return False
        if len(ticket) % 2 != 0:
            return False
        half = len(ticket) // 2
        return sum(int(d) for d in ticket[:half]) == sum(int(d) for d in ticket[half:])

    df_with_lucky = df.with_columns(
        pl.col("Ticket").map_elements(is_lucky, return_dtype=pl.Boolean).alias("is_lucky")
    )

    lucky_df = df_with_lucky.filter(pl.col("is_lucky"))

    if len(lucky_df) == 0:
        return 0.0

    dead = lucky_df.filter(pl.col("Survived") == 0)
    return len(dead) / len(lucky_df)
