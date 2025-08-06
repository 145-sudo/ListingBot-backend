import logging

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials


# Define the scope
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Load credentials from service account file
creds = Credentials.from_service_account_file(
    "./opportune-study-409222-b5a62c0d49fd.json", scopes=scope
)

gc = gspread.authorize(creds)

# Create a new spreadsheet (optional, if you don't have one already)
# spreadsheet = gc.create('Product Data from Colab')
# print(f"Spreadsheet created: {spreadsheet.url}")


# Get spreadsheet by id
def get_spreadsheet(spreadsheet_id):
    try:
        return gc.open_by_key(spreadsheet_id)
    except Exception as e:
        logging.error(f"Error getting spreadsheet: {e}")
        raise


# List available spreadsheets
def list_available_spreadsheets():
    """List all spreadsheets accessible to the service account"""
    try:
        spreadsheets = gc.openall()
        logging.info("Available spreadsheets:")
        for i, spreadsheet in enumerate(spreadsheets):
            logging.info(f"{i + 1}. {spreadsheet.title} (ID: {spreadsheet.id})")
        return spreadsheets
    except Exception as e:
        logging.error(f"Error listing spreadsheets: {e}")
        return []


# Update sheet by sheet name
def update_sheet(spreadsheet, df: pd.DataFrame, sheet_name: str = "Sheet1"):
    # Select worksheet by name
    worksheet = spreadsheet.worksheet(sheet_name)
    logging.info(f"Worksheet selected: {worksheet}")
    
    # Add headers if they are not already present in the sheet
    columns_list = df.columns.values.tolist()
    # logging.info(f"products df columns: {columns_list}")
    values = df.values.tolist()
    # logging.info(f"products df values line 1: {values[0]}")
    # logging.info(f"products df values line 2: {values[1]}")
    # logging.info(f"products df values line last: {values[-1]}")
    worksheet.update([columns_list] + values)

    logging.info("Data successfully uploaded to Google Sheets!")


# Update sheet by spreadsheet id
def update_sheet_by_id(df, spreadsheet_id, sheet_name="Sheet1"):
    """Update sheet using spreadsheet ID"""
    # try:
    spreadsheet = gc.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.worksheet(sheet_name)
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    logging.info("Data successfully uploaded to Google Sheets!")
    # except Exception as e:
    # print(f"Error: {e}")


# Add dropdown for List/Delist
def add_dropdown(sheet_name, column_name="status", default_value=None):
    try:
        # Define dropdown values
        dropdown_values = ["List", "Delist"]

        spreadsheet = gc.open("AutoProductList")
        sheet = spreadsheet.worksheet(sheet_name)

        # Get headers
        headers = sheet.row_values(1)
        if column_name in headers:
            col_idx = headers.index(column_name)  # zero-based
        else:
            # Add a new column with the given column_name
            sheet.add_cols(1)
            headers = sheet.row_values(1)
            col_idx = len(headers) - 1
            # Set the header value for the new column
            sheet.update_cell(1, col_idx + 1, column_name)  # gspread is 1-based

        # Optionally fill all cells in the column (except header) with default_value
        if default_value is not None:
            num_rows = sheet.row_count
            # Prepare the range for the column (excluding header)
            cell_range = (
                gspread.utils.rowcol_to_a1(2, col_idx + 1)
                + ":"
                + gspread.utils.rowcol_to_a1(num_rows, col_idx + 1)
            )
            values = [[default_value] for _ in range(num_rows - 1)]
            sheet.update(cell_range, values)  # type: ignore

        # Check if dropdown already exists in the target column
        meta = sheet.spreadsheet.fetch_sheet_metadata()
        sheet_meta = next(
            s for s in meta["sheets"] if s["properties"]["sheetId"] == sheet.id
        )
        validations = sheet_meta.get("dataValidations", [])
        for dv in validations:
            rng = dv.get("range", {})
            if (
                rng.get("startColumnIndex") == col_idx
                and dv.get("rule", {}).get("condition", {}).get("type") == "ONE_OF_LIST"
            ):
                logging.info(f"Dropdown already exists in column '{column_name}'.")
                return

        # Set data validation for List/Delist column
        sheet.spreadsheet.batch_update(
            {
                "requests": [
                    {
                        "setDataValidation": {
                            "range": {
                                "sheetId": sheet.id,
                                "startRowIndex": 1,  # Start after header
                                "endRowIndex": sheet.row_count,
                                "startColumnIndex": col_idx,
                                "endColumnIndex": col_idx + 1,
                            },
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_LIST",
                                    "values": [
                                        {"userEnteredValue": val}
                                        for val in dropdown_values
                                    ],
                                },
                                "showCustomUi": True,
                                "strict": True,
                            },
                        }
                    }
                ]
            }
        )

        # Add conditional formatting for "List" (green) and "Delist" (red)
        sheet.spreadsheet.batch_update(
            {
                "requests": [
                    {
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [
                                    {
                                        "sheetId": sheet.id,
                                        "startRowIndex": 1,  # after header
                                        "endRowIndex": sheet.row_count,
                                        "startColumnIndex": col_idx,
                                        "endColumnIndex": col_idx + 1,
                                    }
                                ],
                                "booleanRule": {
                                    "condition": {
                                        "type": "TEXT_EQ",
                                        "values": [{"userEnteredValue": "List"}],
                                    },
                                    "format": {
                                        "backgroundColor": {
                                            "red": 0.8,
                                            "green": 1,
                                            "blue": 0.8,
                                        }
                                    },
                                },
                            },
                            "index": 0,
                        }
                    },
                    {
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [
                                    {
                                        "sheetId": sheet.id,
                                        "startRowIndex": 1,
                                        "endRowIndex": sheet.row_count,
                                        "startColumnIndex": col_idx,
                                        "endColumnIndex": col_idx + 1,
                                    }
                                ],
                                "booleanRule": {
                                    "condition": {
                                        "type": "TEXT_EQ",
                                        "values": [{"userEnteredValue": "Delist"}],
                                    },
                                    "format": {
                                        "backgroundColor": {
                                            "red": 1,
                                            "green": 0.8,
                                            "blue": 0.8,
                                        }
                                    },
                                },
                            },
                            "index": 0,
                        }
                    },
                ]
            }
        )
        logging.info(f"Added dropdown to {sheet.title} in column '{column_name}'")
    except Exception as e:
        logging.error(f"Error adding dropdown to {sheet.title}: {e}")
        raise


# Get sheet data
def get_sheet_data(spreadsheet_id, sheet_name="Sheet1", df=False):
    try:
        spreadsheet = gc.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        if df:
            logging.info(
                f"Getting data from {sheet_name} in {spreadsheet_id} as DataFrame"
            )
            data = worksheet.get_all_values()
            if not data:
                return pd.DataFrame()
            df_p = pd.DataFrame(data[1:], columns=data[0])  # type: ignore
            return df_p
        else:
            logging.info(f"Getting data from {sheet_name} in {spreadsheet_id} as list")
            return worksheet.get_all_values()
    except Exception as e:
        logging.error(f"Error getting data from {sheet_name} in {spreadsheet_id}: {e}")


# for right now this feature
def update_supplier_sheet(sheet, products, dropdown_col="Status"):
    # Fetch all data
    data = sheet.get_all_records()
    sku_to_row = {
        row["SKU"]: idx + 2 for idx, row in enumerate(data)
    }  # +2 for header and 1-indexing

    # Get header row (first row)
    header = sheet.row_values(1)
    stock_col_idx = header.index("Stock") + 1
    price_col_idx = header.index("Price") + 1

    for product in products:
        sku = product["SKU"]
        if sku in sku_to_row:
            row_idx = sku_to_row[sku]
            sheet.update_cell(row_idx, stock_col_idx, product["Stock"])
            sheet.update_cell(row_idx, price_col_idx, product["Price"])
            # Do NOT update dropdown_col
        else:
            # Append new row with all fields (including dropdown default)
            new_row = [
                product["SKU"],
                product["Name"],
                product["Stock"],
                product["Price"],
                "Active",
            ]  # or whatever default
            sheet.append_row(new_row)
