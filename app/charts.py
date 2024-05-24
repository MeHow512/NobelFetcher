import logging
import pandas as pd
from xlsxwriter import Workbook
from xlsxwriter.workbook import Worksheet
from xlsxwriter.utility import xl_rowcol_to_cell_fast


class Charts:
    """
    Class responsible for creating charts in Excel file.
    """

    def __init__(self, logger: logging.Logger, workbook: Workbook):
        """
        Initializes the Charts class with a logger and Excel workbook.

        :param logger: A logger instance for logging messages.
        :param workbook: The Excel workbook to which the chart will be added.
        """
        self._logger = logger
        self._workbook = workbook
        self._chart_data_sheet_name = "Charts Data"

    def draw_statistics_charts(self, laureates_df: pd.DataFrame, nobel_prizes_df: pd.DataFrame,
                               main_worksheet: Worksheet) -> None:
        """
        Creates additional Worksheet in the workbook and adds specially prepared data there that will be used
        in the charts. Draws statistics charts based on the provided data. Generates a pie charts representing
        various statistics i.e.
            - the gender distribution of people who received the Nobel Prize,
            - the distribution of the number of Nobel Prizes in a given year,
            - the distribution of the science fields in which the Nobel Prize was awarded.

        :param laureates_df: DataFrame containing information about Nobel Prize Laureates.
        :param nobel_prizes_df: DataFrame containing information only about Nobel Prizes.
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
        chart_data_worksheet = self._workbook.add_worksheet(self._chart_data_sheet_name)

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
            self._generate_pie_chart(chart_data_worksheet, main_worksheet, chart_data, chart_start_cell)
            cell_number_next_to_all_excel_data += 10

    def _generate_pie_chart(self, chart_data_worksheet: Worksheet, main_worksheet: Worksheet, chart_data: dict,
                            chart_start_cell: str) -> None:
        """
        Generates a pie chart in the Excel workbook, more precisely in the main worksheet which contains a table with
        data from the API. The chart is placed in the cell provided in the params (chart_start_cell).

        :param chart_data_worksheet: THe worksheet containing the data for the chart.
        :param main_worksheet: The main worksheet where the chart will be added.
        :param chart_data: A dictionary containing information for the chart. It should include title of the chart,
        excel coordinates where category and values for the chart are defined and data rows amount in Excel to determine
        the range of cells from which data should be collected and used in chart.
        :param chart_start_cell: Cell number symbolizing the starting point of the chart ( top left corner of the chart)
        """
        chart = self._workbook.add_chart({'type': 'pie'})
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
