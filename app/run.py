import logging
import requests

from api_manager import ApiManager
from file_manager import FileManager
from utils import get_logger, parse_args, read_config

REQUIRED_LAUREATES_DATA = {
    "givenName": "en",
    "familyName": "en",
    "gender": None,
    "birth": "date",
    "wikipedia": "english",
    "nobelPrizes": {"awardYear", "category", "prizeStatus", "motivation"}
}


def get_laureates_necessary_data(logger: logging.Logger, laureates_data: list[dict]) -> list[dict]:
    """
    Extracts necessary data from the fetched Nobel laureates data.

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
        for key, value in laureate.items():
            if key == "nobelPrizes":
                necessary_laureates_data[key] = trim_nobel_prizes_data(value)
            elif key in REQUIRED_LAUREATES_DATA:
                if isinstance(value, dict) and REQUIRED_LAUREATES_DATA[key] in value:
                    necessary_laureates_data[key] = value[REQUIRED_LAUREATES_DATA[key]]
                else:
                    necessary_laureates_data[key] = value
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


if __name__ == '__main__':
    args = parse_args()
    logger = get_logger("FETCHER", min(args.v * 10, 50))
    cfg = read_config("config.toml")

    api_mgr = ApiManager(logger, cfg['app']['base_api_url'])
    file_mgr = FileManager(logger, cfg)

    try:
        url_api_params = cfg['api_params'].copy()
        api_attempts = cfg['app']['max_api_attempts']
        fetched_laureates_data = fetch_nobel_laureates(logger, api_mgr, url_api_params, api_attempts)
    except requests.exceptions.RequestException as error:
        fetched_laureates_data = []

    if fetched_laureates_data:
        trimmed_laureates_data = get_laureates_necessary_data(logger, fetched_laureates_data)

        if args.json:
            file_mgr.save_data_to_json_file(trimmed_laureates_data)

        if args.excel:
            file_mgr.save_data_to_excel_file(trimmed_laureates_data)
    else:
        logger.error("No data was retrieved from the API!")

    logger.info("Fetcher finished his work.")
