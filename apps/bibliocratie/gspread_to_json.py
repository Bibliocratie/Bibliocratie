import getopt
import logging
import json
import sys

import gspread
from oauth2client.client import SignedJwtAssertionCredentials


def GetGoogleSheetAsDict(**kwargs):
    key_file = None
    username = None
    password = None
    sheet_key = None
    worksheet_key = None
    data = {}

    for opt, arg in kwargs.iteritems():
        if opt in ("k", "key"):
            key_file = arg
        elif opt in ("u", "user"):
            username = arg
        elif opt in ("p", "password"):
            password = arg
        elif opt in ("s", "sheet"):
            sheet_key = arg
        elif opt in ("w", "worksheet"):
            worksheet_key = arg

    if (username == None and (key_file == None or password == None)) or sheet_key == None:
        return {'error': True, 'message': "invalid argument", "data": ""}

    if key_file:
        try:

            f = file(key_file, 'rb')
            key = f.read()
            f.close()

            scope = ['https://spreadsheets.google.com/feeds', 'https://docs.google.com/feeds']
            credentials = SignedJwtAssertionCredentials(username, key, scope)
            gc = gspread.authorize(credentials)

        except Exception as e:
            return {'error': True, 'message': "invalid keyfile", "data": ""}

    elif username and password:
        gc = gspread.login(username, password)

    try:
        sheet = gc.open_by_key(sheet_key)
    except gspread.exceptions.SpreadsheetNotFound:
        return {'error': True, 'message': "Unable to find spreadsheet \"%s\" -- unable to continue." % sheet_key,
                "data": ""}

    worksheets = sheet.worksheets()

    for worksheet in worksheets:
        data[worksheet.title] = worksheet.get_all_records()

    if worksheet_key == None:
        return {'error': False, 'message': "", "data": data}
    else:
        return {'error': False, 'message': "", "data": data[worksheet_key]}
