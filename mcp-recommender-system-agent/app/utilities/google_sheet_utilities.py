import json
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetUtils:
    def __init__(self, service_account_file, spreadsheet_id, sheet_name, scopes=None):
        self.service_account_file = service_account_file
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.scopes = scopes or ["https://www.googleapis.com/auth/spreadsheets"]
        self.service = self._authenticate()

    def _authenticate(self):
        try:
            creds = Credentials.from_service_account_file(
                self.service_account_file, scopes=self.scopes
            )
            return build("sheets", "v4", credentials=creds)
        except Exception as e:
            print(f"Authentication failed: {e}")
            raise

    def add_column(self, column_name, default_value=""):
        """
        Add a new column with the given column_name to the sheet.
        The new column cells are filled with default_value (empty string by default).
        """
        # Read the entire sheet data
        data = self.read_range(self.sheet_name)  # You might want to make sheet name or range configurable
        
        # If data is empty (no rows), just create a new header row with the column name
        if not data:
            # Write header only with the new column name
            self.write_range(f"{self.sheet_name}!A1", [[column_name]])
            return
        
        # data is a list of dicts (column_name -> value)
        # Add new column with default values to each row dict
        for row in data:
            row[column_name] = default_value
        
        # Convert list of dicts back to list of lists (including headers)
        headers = list(data[0].keys())
        rows = [[row.get(h, "") for h in headers] for row in data]
        new_data = [headers] + rows
        
        # Write back to sheet, starting at A1
        self.write_range(f"{self.sheet_name}!A1", new_data)

    def append_row(self, row_data):
        """
        Append a new row at the end of the records in the specified sheet.

        Args:
            row_data (list): List of values matching the columns order.
        """
        try:
            # The range for append can be just the sheet name
            sheet_name = self.sheet_name
            range_name = f"'{sheet_name}'"

            body = {"values": [row_data]}
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()

            return result
        except HttpError as err:
            print(f"API error during append: {err}")
            return {}
    
    def read_range(self, range_name, as_dataframe=False):
        """Read data from sheet; return list of dicts or DataFrame."""
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            values = result.get("values", [])

            if not values:
                return pd.DataFrame() if as_dataframe else []

            headers = values[0]
            data_rows = values[1:]

            if as_dataframe:
                return pd.DataFrame(data_rows, columns=headers)
            else:
                return [dict(zip(headers, row)) for row in data_rows]
        except HttpError as err:
            print(f"API error during read: {err}")
            return pd.DataFrame() if as_dataframe else []

    def write_range(self, range_name, data):
        """Write data (DataFrame or list of lists) to sheet."""
        if isinstance(data, pd.DataFrame):
            data = [list(data.columns)] + data.astype(str).values.tolist()

        body = {"values": data}
        try:
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body
            ).execute()
            return result
        except HttpError as err:
            print(f"API error during write: {err}")
            return {}

    def update_range(self, range_name, data):
        """Update data (same as write, separate for API clarity)."""
        return self.write_range(range_name, data)


    def update_cell_by_id(self, id_value, target_column, new_value, id_column="ID"):
        """
        Update the cell at the intersection of the row with given ID and target column.

        Args:
            id_value (str): The ID to match in the ID column.
            target_column (str): The column to update.
            new_value: The new value to set (will be converted to string).
            id_column (str): The name of the column containing unique IDs.
        """
        try:
            # Read all data as list of dicts
            data = self.read_range(self.sheet_name)
            if not data:
                print("Sheet is empty.")
                return False

            # Get headers and validate columns exist
            headers = list(data[0].keys())
            if id_column not in headers:
                print(f"ID column '{id_column}' not found. Available columns: {headers}")
                return False
            if target_column not in headers:
                print(f"Target column '{target_column}' not found. Available columns: {headers}")
                return False

            # Find the row index with better ID matching
            row_index = None
            for i, row in enumerate(data):
                if str(row.get(id_column, '')).strip() == str(id_value).strip():
                    row_index = i + 2  # +2 for 1-indexed sheets + header row
                    break

            if row_index is None:
                print(f"ID '{id_value}' not found in column '{id_column}'.")
                # Debug: print available IDs
                available_ids = [str(row.get(id_column, '')) for row in data[:5]]
                print(f"Available IDs (first 5): {available_ids}")
                return False

            # Get column index and convert to letter
            col_index = headers.index(target_column) + 1
            col_letter = self.col_index_to_letter(col_index)

            # Construct cell range
            cell_range = f"{self.sheet_name}!{col_letter}{row_index}"
            
            # Convert new_value to a simple string/number format
            # Handle different data types properly
            if isinstance(new_value, (list, dict, tuple)):
                # Convert complex data structures to string representation
                processed_value = str(new_value)
            elif isinstance(new_value, bool):
                processed_value = str(new_value).upper()  # TRUE/FALSE for sheets
            elif new_value is None:
                processed_value = ""
            else:
                processed_value = str(new_value)
            
            print(f"Updating cell: {cell_range} with value: '{processed_value}'")
            
            # Update the cell - note the double array structure [[value]]
            result = self.write_range(cell_range, [[processed_value]])
            
            # Check if update was successful
            if result and 'updatedCells' in result:
                print(f"Successfully updated {cell_range} ({result.get('updatedCells', 0)} cells)")
                return True
            elif result:
                print(f"Update completed for {cell_range}")
                return True
            else:
                print(f"Failed to update {cell_range}")
                return False

        except Exception as e:
            print(f"Error in update_cell_by_id: {e}")
            print(f"ID: {id_value}, Column: {target_column}, Value type: {type(new_value)}, Value: {new_value}")
            return False

    def col_index_to_letter(self, col_index):
        """Convert column index (1-based) to Excel column letter(s)"""
        result = ""
        while col_index > 0:
            col_index -= 1
            result = chr(65 + col_index % 26) + result
            col_index //= 26
        return result

#  uv run mcp install main.py 