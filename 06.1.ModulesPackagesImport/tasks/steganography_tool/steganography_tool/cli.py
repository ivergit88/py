from pathlib import Path

import click

from .decode import decode_message
from .encode import encode_message
from .utils import get_base_file, read_file, write_file


@click.group()
def main() -> None:
    pass


@main.command()
@click.argument("output_filename", type=click.Path())
@click.argument("secret_message", type=str)
def encode(output_filename: str, secret_message: str) -> None:
    data = get_base_file()
    encoded = encode_message(data, secret_message)
    write_file(encoded, Path(output_filename))


@main.command()
@click.argument("input_filename", type=click.Path(exists=True))
def decode(input_filename: str) -> None:
    data = read_file(Path(input_filename))
    click.echo(decode_message(data))


if __name__ == "__main__":
    main()
