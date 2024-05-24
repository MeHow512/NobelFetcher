import json
import logging
import pandas as pd
from xlsxwriter import Workbook

from charts import Charts


class FileManager:
    """
    Class responsible for managing file operations ( saving data to .json or .xlsx file ).
    """
    def __init__(self, logger: logging.Logger, cfg: dict):
        """
        Initializes the FileManager class with a logger and configuration settings.

        :param logger: A logger instance for logging messages.
        :param cfg: Configuration settings.
        """
        self._logger = logger
        self._cfg = cfg

    def save_data_to_json_file(self, laureates_data: list[dict], file_name: str = "laureates_data.json") -> None:
        """
        Saves the laureates data to .json file.

        :param laureates_data: A list of dictionaries with laureates data.
        :param file_name: Output .json file name.
        """
        try:
            with open(file_name, "w", encoding="utf-8") as json_file:
                json.dump(laureates_data, json_file, indent=4, ensure_ascii=False)
            self._logger.info(f"Data saved to {file_name}.")
        except FileNotFoundError:
            self._logger.error(f"Failed to save data to {file_name}: File not found.")
        except IOError:
            self._logger.error(f"Failed to save data to {file_name}: IO error occurred.")
        except Exception as e:
            self._logger.error(f"Failed to save data to {file_name}: {e}")

    def save_data_to_excel_file_and_generate_charts(self, laureates_data: list[dict],
                                                    file_name: str = "laureates_data.xlsx") -> None:
        """
        Formats data headers and converts lists to strings, which allows them to be saved to a cell in .xlsx file.
        Generates statistics charts for specified data. It then saves the data in an .xlsx format file using specific
        formatting for headers and rows.

        :param laureates_data: A list of dictionaries with laureates data.
        :param file_name: Output .xlsx file name.
        """
        laureates_data = self._make_headers_pretty_version(laureates_data)

        try:
            nobel_prizes_df = pd.DataFrame([prize for entry in laureates_data for prize in entry["NOBEL PRIZES"]])
            converted_laureates_data = self._convert_each_list_to_string(laureates_data)
            laureates_df = pd.DataFrame(converted_laureates_data)

            workbook = Workbook(file_name)
            main_worksheet = workbook.add_worksheet(f"Nobel laureates in {self._cfg['api_params']['nobelPrizeYear']} - "
                                                    f"{self._cfg['api_params']['yearTo']}")

            header_format = workbook.add_format({
                'valign': 'center',
                'fg_color': self._cfg['xlsx_formatting']['headers_color'],
                'border': 1,
                'font_color': 'white',
                'bold': True
            })
            base_format_settings = {'valign': 'top', 'text_wrap': True}
            cell_format = workbook.add_format(base_format_settings)
            odd_cell_format = workbook.add_format(base_format_settings | {
                'fg_color': self._cfg['xlsx_formatting']['odd_rows_color']
            })

            for col_num, header in enumerate(laureates_df.columns):
                main_worksheet.write(0, col_num, header, header_format)

            row_num = 1
            for laureate in converted_laureates_data:
                for col_num, cell_data in enumerate(laureate.values()):
                    if row_num % 2 == 0:
                        main_worksheet.write(row_num, col_num, cell_data, cell_format)
                    else:
                        main_worksheet.write(row_num, col_num, cell_data, odd_cell_format)
                row_num += 1

            # adjusting columns width to content size
            for i, width in enumerate(laureates_df.map(lambda x: len(str(x))).max()):
                main_worksheet.set_column(i, i, width + 2)

            charts_mgr = Charts(self._logger, workbook)
            charts_mgr.draw_statistics_charts(laureates_df, nobel_prizes_df, main_worksheet)

            workbook.close()
            self._logger.info(f"Data saved to {file_name}.")
        except Exception as e:
            self._logger.error(f"Failed to save data to {file_name}: {e}")

    @staticmethod
    def _make_headers_pretty_version(laureates_data: list[dict]) -> list[dict]:
        """
        Changes all headers of the input data - the header from the exampleHeader version is changed to EXAMPLE HEADER.

        :param laureates_data: A list of dictionaries with laureates data.
        :return: Laureates data with processed headers.
        """
        processed_laureates_data = []
        known_keys = {}

        def process_key_name(processing_key: str) -> str:
            """
            Processes the input string to the SAMPLE INPUT STRING version and, after the process, saves the input key
            and its processed version to the known_keys dictionary to speed up the function in subsequent use cases.

            :param processing_key: The key name to process.
            :return: Processed key name.
            """
            if processing_key in known_keys.keys():
                return known_keys[processing_key]
            else:
                new_key = "".join(char if char.islower() else f" {char}" for char in processing_key)
                new_key = new_key.strip().upper()
                known_keys[processing_key] = new_key
                return new_key

        for laureate in laureates_data:
            new_laureate_data = {}
            for key, value in laureate.items():
                if isinstance(value, list):
                    new_items = []
                    for inner_item in value:
                        processed_value = {}
                        for inner_key, inner_value in inner_item.items():
                            processed_value[process_key_name(inner_key)] = inner_value
                        new_items.append(processed_value)
                    new_laureate_data[process_key_name(key)] = new_items
                else:
                    new_laureate_data[process_key_name(key)] = value
            processed_laureates_data.append(new_laureate_data)

        return processed_laureates_data

    @staticmethod
    def _convert_each_list_to_string(laureates_data: list[dict]) -> list[dict]:
        """
        Convert each list value in the laureates data into formatted string that can be entered into Excel cell.

        :param laureates_data: A list of dictionaries with laureates data.
        :return: Converted laureates data
        """
        for laureate in laureates_data:
            for key, value in laureate.items():
                if isinstance(value, list):
                    laureate[key] = "\n".join([f"{inner_key}: {inner_value}" for inner_dict in value
                                               for inner_key, inner_value in inner_dict.items()])
        return laureates_data
