import logging
import requests


class ApiManager:
    """
    A class for managing API requests.
    """

    def __init__(self, logger: logging.Logger, base_url: str):
        """
        Initializes the ApiManager class with a logger and base URL for API requests.

        :param logger: A logger instance for logging messages.
        :param base_url: The base URL for API requests.
        """
        self._base_url = base_url
        self._logger = logger

    def get_laureates_data(self, url_params: dict = None) -> list[dict]:
        """
        Fetches laureates data from the API.

        :param url_params: Dictionary containing URL parameters for the API request. (default None)
        :return: List of dictionaries containing Nobel laureates data fetched from the API.
        """
        try:
            if url_params:
                url_params_str = "&".join([f"{key}={value}" for key, value in url_params.items()])
                full_url = f"{self._base_url}?{url_params_str}"
            else:
                full_url = self._base_url

            self._logger.debug(f"GET API REQUEST URL: {full_url}")

            response = requests.get(full_url)
            response.raise_for_status()

            json_laureates_data = response.json()
            return json_laureates_data['laureates']
        except requests.exceptions.RequestException as error:
            self._logger.error(f"An error occurred during attempt to fetch data from API: {error}")
            raise
