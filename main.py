from fastapi import FastAPI, HTTPException
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from decouple import config


app = FastAPI()

# Path to your credentials JSON file

SERVICE_ACCOUNT_FILE = config('SERVICE_ACCOUNT_FILE')

# Scopes for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Spreadsheet ID and Range
SPREADSHEET_ID = config('SPREADSHEET_ID')
# Adjust the range as per your sheet
RANGE_NAME = f"{config('SHEET_NAME')}!A:Z"

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)


@app.get("/get-data/{column}/{value}")
async def get_data(column: str, value: str):
    try:
        # Call the Sheets API to get the data
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        rows = result.get('values', [])

        if not rows:
            raise HTTPException(status_code=404, detail="No data found")

        # Find the index of the specified column
        header = rows[0]
        if column not in header:
            raise HTTPException(status_code=404, detail="Column not found")

        col_index = header.index(column)
        filtered_data = [row for row in rows if len(
            row) > col_index and row[col_index] == value]

        if not filtered_data:
            raise HTTPException(
                status_code=404, detail="No matching data found")

        return {"data": filtered_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
