from fastapi import FastAPI, HTTPException, Body
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from decouple import config
from typing import List, Dict
import re

app = FastAPI()

SPREADSHEET_ID = config('SPREADSHEET_ID')
SERVICE_ACCOUNT_FILE = config('SERVICE_ACCOUNT_FILE')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)


def normalize_value(value: str) -> str:
    """Normalize the value by trimming whitespace, removing brackets, and converting to lowercase"""
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', value)).strip().lower()


@app.post("/get-data")
async def get_data(filters: Dict[str, List[str]] = Body(...)):
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=config('SHEET_NAME')).execute()
        rows = result.get('values', [])

        if not rows:
            raise HTTPException(status_code=404, detail="No data found")

        header = rows[0]
        filtered_data = rows[1:]  # Exclude the header

        # Normalize the filters
        normalized_filters = {col: [normalize_value(
            val) for val in vals] for col, vals in filters.items()}

        # Apply filtering based on each column and its normalized values
        for column, values in normalized_filters.items():
            if column not in header:
                raise HTTPException(status_code=404, detail=f"Column '{
                                    column}' not found")
            col_index = header.index(column)
            filtered_data = [
                row for row in filtered_data
                if len(row) > col_index and normalize_value(row[col_index]) in values
            ]

        if not filtered_data:
            raise HTTPException(
                status_code=404, detail="No matching data found")

        return {"data": filtered_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
