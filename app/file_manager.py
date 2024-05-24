import json
import logging
import pandas as pd
from xlsxwriter import Workbook
from xlsxwriter.workbook import Worksheet
from xlsxwriter.utility import xl_rowcol_to_cell_fast


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
        self._chart_data_sheet_name = "Charts Data"

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
            cell_format = workbook.add_format({
                'valign': 'top',
                'text_wrap': True
            })
            odd_cell_format = workbook.add_format({
                'valign': 'top',
                'fg_color': self._cfg['xlsx_formatting']['odd_rows_color'],
                'text_wrap': True
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

            self._draw_statistics_charts(laureates_df, nobel_prizes_df, workbook, main_worksheet)

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

    def _draw_statistics_charts(self, laureates_df: pd.DataFrame, nobel_prizes_df: pd.DataFrame,
                                workbook: Workbook, main_worksheet: Worksheet) -> None:
        """
        Creates additional Worksheet in the workbook and adds specially prepared data there that will be used
        in the charts. Draws statistics charts based on the provided data. Generates a pie charts representing
        various statistics i.e.
            - the gender distribution of people who received the Nobel Prize,
            - the distribution of the number of Nobel Prizes in a given year,
            - the distribution of the science fields in which the Nobel Prize was awarded.

        :param laureates_df: DataFrame containing information about Nobel Prize Laureates.
        :param nobel_prizes_df: DataFrame containing information only about Nobel Prizes.
        :param workbook: Workbook instance where the charts will be added.
        :param main_worksheet: Worksheet where the charts will be added.
        """
        col_names_with_chart_data = {
            "GENDER": {"title": "Gender distribution of Nobel Prize winners", "excel_coords": None,
                       "excel_data_rows_amount": None},
            "AWARD YEAR": {"title": "Nobel Prizes won in given years", "excel_coords": None,
                           "excel_data_rows_amount": None},
            "CATEGORY": {"title": "Nobel Prizes won for a given categories", "excel_coords": None,
                         "excel_data_rows_amount": None}
        }
        chart_data_worksheet = workbook.add_worksheet(self._chart_data_sheet_name)

        # Move GENDER column for making easier data calculations for charts
        nobel_prizes_df.insert(len(nobel_prizes_df.columns), 'GENDER', laureates_df.pop('GENDER'))

        column_index = 0
        for column_name in col_names_with_chart_data.keys():
            count_data = nobel_prizes_df[column_name].value_counts().sort_index()
            chart_data_worksheet.write_column(xl_rowcol_to_cell_fast(0, column_index),
                                              count_data.index)
            chart_data_worksheet.write_column(xl_rowcol_to_cell_fast(0, column_index + 1), count_data.values)
            col_names_with_chart_data[column_name]['excel_coords'] = (column_index, column_index + 1)
            col_names_with_chart_data[column_name]['excel_data_rows_amount'] = (len(count_data.index),
                                                                                len(count_data.values))
            column_index += 3

        # Drawing charts based on data in chart data worksheet next to the all data in main worksheet
        cell_number_next_to_all_excel_data = laureates_df.shape[1] + 3
        for chart_data in col_names_with_chart_data.values():
            chart_start_cell = xl_rowcol_to_cell_fast(0, cell_number_next_to_all_excel_data)
            self._generate_pie_chart(workbook, chart_data_worksheet, main_worksheet, chart_data, chart_start_cell)
            cell_number_next_to_all_excel_data += 10

    @staticmethod
    def _generate_pie_chart(workbook: Workbook, chart_data_worksheet: Worksheet, main_worksheet: Worksheet,
                            chart_data: dict, chart_start_cell: str) -> None:
        """
        Generates a pie chart in the Excel workbook, more precisely in the main worksheet which contains a table with
        data from the API. The chart is placed in the cell provided in the params (chart_start_cell).

        :param workbook: The Excel workbook to which the chart will be added.
        :param chart_data_worksheet: THe worksheet containing the data for the chart.
        :param main_worksheet: The main worksheet where the chart will be added.
        :param chart_data: A dictionary containing information for the chart. It should include title of the chart,
        excel coordinates where category and values for the chart are defined and data rows amount in Excel to determine
        the range of cells from which data should be collected and used in chart.
        :param chart_start_cell: Cell number symbolizing the starting point of the chart ( top left corner of the chart)
        """
        chart = workbook.add_chart({'type': 'pie'})
        chart.set_title({'name': chart_data['title']})
        chart.add_series({
            'categories': [chart_data_worksheet.name, 0, chart_data['excel_coords'][0],
                           chart_data['excel_data_rows_amount'][0] - 1, chart_data['excel_coords'][0]],
            'values': [chart_data_worksheet.name, 0, chart_data['excel_coords'][1],
                       chart_data['excel_data_rows_amount'][1] - 1, chart_data['excel_coords'][1]],
            'data_labels': {'value': True}
        })
        chart.set_size({'width': 500, 'height': 300})

        main_worksheet.insert_chart(chart_start_cell, chart)
