import argparse
import logging
import os
import requests
import tomllib

from api_manager import ApiManager

REQUIRED_LAUREATES_DATA = {
    "givenName": "en",
    "familyName": "en",
    "gender": None,
    "birth": "date",
    "wikipedia": "english",
    "nobelPrizes": {"awardYear", "category", "prizeStatus", "motivation"}
}


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


def get_laureates_necessary_data(logger: logging.Logger, laureates_data: list[dict]) -> list[dict]:
    """
    Extracts necessary data from the fetched Nobel laureates data. If any of the required data is missing for a given
    laureate data, it is added as 'Unknown'.

    :param logger: A logger instance for printing output messages.
    :param laureates_data: Laureates data fetched from API.
    :return: List of dictionaries containing trimmed laureates data only with necessary fields.
    """
    new_laureates_data = []
    for laureate in laureates_data:
        # Skip organizations
        if "orgName" in laureate:
            logger.debug(f"Skipping organization data: {laureate['orgName']['en']}")
            continue

        necessary_laureates_data = {}
        for key, value in REQUIRED_LAUREATES_DATA.items():
            if key in laureate:
                if key == "nobelPrizes":
                    necessary_laureates_data[key] = trim_nobel_prizes_data(laureate['nobelPrizes'])
                else:
                    if isinstance(laureate[key], dict) and value in laureate[key]:
                        necessary_laureates_data[key] = laureate[key][value]
                    else:
                        necessary_laureates_data[key] = laureate[key]
            else:
                necessary_laureates_data[key] = "Unknown"

        new_laureates_data.append(necessary_laureates_data)

    return new_laureates_data


def trim_nobel_prizes_data(laureate_prizes: list[dict]) -> list[dict]:
    """
    Trims laureate prizes data to include only required fields.

    :param laureate_prizes: List of dictionaries containing laureate prizes data.
    :return: Trimmed laureate prizes data.
    """
    trimmed_nobel_prizes_data = []
    for nobel_prize in laureate_prizes:
        trimmed_nobel_prize_data = {}
        for prize_data in REQUIRED_LAUREATES_DATA['nobelPrizes']:
            if prize_data in nobel_prize:
                if isinstance(nobel_prize[prize_data], dict) and "en" in nobel_prize[prize_data]:
                    trimmed_nobel_prize_data[prize_data] = nobel_prize[prize_data]['en']
                else:
                    trimmed_nobel_prize_data[prize_data] = nobel_prize[prize_data]
        trimmed_nobel_prizes_data.append(trimmed_nobel_prize_data)

    return trimmed_nobel_prizes_data


def fetch_nobel_laureates(logger: logging.Logger, api_mgr: ApiManager, url_api_params: dict,
                          max_api_attempts: int) -> list:
    """
    Fetches Nobel laureates data from the specified API and given parameters.

    :param logger: A logger instance for printing output messages.
    :param api_mgr: Instance of the ApiManager class responsible for making API requests.
    :param url_api_params: Url parameters for the API request.
    :param max_api_attempts: Max API request attempts
    :return: List of dictionaries containing data about Nobel laureates.
    """
    fetched_data = []
    attempts = 0
    logger.info(f"Fetching nobel laureates from year {url_api_params['nobelPrizeYear']} to {url_api_params['yearTo']}")
    while attempts < max_api_attempts:
        attempts += 1
        logger.debug(f"Attempt {attempts}/{max_api_attempts}:")
        try:
            laureates_data = api_mgr.get_laureates_data(url_api_params)
            if not laureates_data:
                logger.debug("All data for the set parameters has been fetched. Skipping other attempts.")
                break

            fetched_data.extend(laureates_data)
            url_api_params['offset'] += 50
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred during attempt {attempts} to fetch data from API: {e}")
            if attempts == max_api_attempts:
                logger.error(f"Max number of attempts ({max_api_attempts}) reached. Cannot fetch data from API.")
                break

    return fetched_data
