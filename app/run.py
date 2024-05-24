import copy
import requests

from api_manager import ApiManager
from file_manager import FileManager
from utils import (get_logger, parse_args, read_config, get_laureates_necessary_data, fetch_nobel_laureates,
                   add_emails_to_laureates_data)


def start_script() -> None:
    """
    Reads run script command arguments, creates logger, reads config and creates Api and File Managers instances.
    Fetch data from the API and writes it to .json and .excel ( if special flags were set in the script run command ).
    """
    args = parse_args()
    logger = get_logger("FETCHER", min(args.v * 10, 50))
    cfg = read_config("config.toml")

    api_mgr = ApiManager(logger, cfg['app']['base_api_url'])
    file_mgr = FileManager(logger, cfg)

    try:
        url_api_params = cfg['api_params'].copy()
        api_attempts = cfg['app']['max_api_attempts']
        fetched_laureates_data = fetch_nobel_laureates(logger, api_mgr, url_api_params, api_attempts)
    except requests.exceptions.RequestException:
        fetched_laureates_data = []

    if fetched_laureates_data:
        trimmed_laureates_data = get_laureates_necessary_data(logger, fetched_laureates_data)

        if args.json:
            laureates_data_copy = copy.deepcopy(trimmed_laureates_data)
            laureates_data_with_email = add_emails_to_laureates_data(laureates_data_copy, cfg['app']['email_suffix'])
            file_mgr.save_data_to_json_file(laureates_data_with_email)

        if args.excel:
            file_mgr.save_data_to_excel_file_and_generate_charts(trimmed_laureates_data)
    else:
        logger.error("No data was retrieved from the API!")

    logger.info("Fetcher finished his work.")


if __name__ == '__main__':
    start_script()
