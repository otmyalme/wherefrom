"""
Run the application.

This has been added in a rush so that the application can actually be used from
the command line and can thus reasonably be mentioned on an résumé.
"""

from argparse import ArgumentParser
from dataclasses import dataclass
import json
from pathlib import Path
import sys

from wherefrom.walk import walk_directory_trees


type Args = list[str] | None


def run(args: Args = None) -> None:
    """Run the application."""
    arguments = parse_command_line_arguments(args)
    results, exceptions = walk_directory_trees(*arguments.base_paths)
    for exception in exceptions:
        sys.stderr.write(str(exception))
        sys.stderr.write("\n")
    result_dict = {str(path): value for path, value in results}
    sys.stdout.write(json.dumps(result_dict, indent=2))
    sys.stdout.write("\n")


# COMMAND-LINE ARGUMENTS #################################################################

@dataclass
class Arguments:
    """Encapsulates the command-line arguments passed to the application."""
    base_paths: list[Path]


APPLICATION_DESCRIPTION = """
    Read the “where from” extended file attributes of the specified files and print the
    gathered values as a JSON object. If a directory is specified, recursively descend
    into it and read the “where from” attribute of all regular files it contains.
"""
BASE_PATHS_HELP = """
    Zero or more paths to process. Directories are processed recursively, and other files
    have their “where from” value read.
"""
HELP_HELP = "Show this help message."


def create_command_line_argument_parser() -> ArgumentParser:
    """Create a parser for the application’s command-line arguments."""
    parser = ArgumentParser(description=APPLICATION_DESCRIPTION, add_help=False)
    parser.add_argument(
        "base_paths", metavar="PATH", nargs="*", type=Path, help=BASE_PATHS_HELP,
    )
    parser.add_argument("-h", "--help", action="help", help=HELP_HELP)
    return parser


def parse_command_line_arguments(args: Args = None) -> Arguments:
    """Parse the command-line arguments provided by the user."""
    parser = create_command_line_argument_parser()
    return Arguments(**vars(parser.parse_args(args)))
