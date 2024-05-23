import argparse
import logging
import os
import tomllib


def get_logger(name: str, verbosity_level: int) -> logging.Logger:
    """
    Creates logger with specified verbosity level, name and configures stream handler for console output.

    :param name: New logger name
    :param verbosity_level: New logger verbosity level
    :return: New logger
    """
    new_logger = logging.getLogger(name)
    new_logger.setLevel(verbosity_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    new_logger.addHandler(console_handler)

    return new_logger


def read_config(config_path: str) -> dict:
    """
    Reads .toml config file.

    :param config_path: Path to .toml config file
    :return: Config data
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Missing {config_path} file!")

    try:
        with open(config_path, 'rb') as cfg_file:
            return tomllib.load(cfg_file)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"Error during parsing the {config_path} file: {error}")


def parse_args():
    """Parse args from command line."""
    parser = argparse.ArgumentParser(description="Script for fetching data about nobel prizes and their owners")
    parser.add_argument("-v", action='count', default=0, help="Increase output verbosity")
    parser.add_argument("--json", action='store_true', help="Save fetched data to a .json file")
    parser.add_argument("--excel", action='store_true', help="Save fetched data to an .xlsx file")
    return parser.parse_args()
