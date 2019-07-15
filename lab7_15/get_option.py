import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

def get_options(ticker, option_type):
    url = 'https://finance.yahoo.com/quote/' + ticker + '/options?p=' + ticker
    source_code = requests.get(url)
    plaintext = source_code.text
    soup = BeautifulSoup(plaintext, 'html.parser')
    if option_type == 'call':
        calls = soup.findAll('table', {'class':'calls'})
    else: 
        calls = soup.findAll('table', {'class':'puts'})
    columns = calls[0].findAll('thead')
    columns = columns[0].findAll('span')
    n = len(columns)
    column_names = [0] * n
    for idx, val in enumerate(columns):
        column_names[idx] = val.getText()
    data = calls[0].findAll('tbody')
    row_data = data[0].findAll('tr')
    row_num = len(row_data)
    call_df = pd.DataFrame(columns = column_names)
    for row_val in row_data:
        row = [0] * n
        for col_idx, col_val in enumerate(row_val.findAll('td')):
            row[col_idx] = col_val.getText()
        temp = pd.DataFrame([row], columns = column_names)
        call_df = call_df.append(temp, ignore_index = True)
    return call_df

ticker = input('Enter the company ticker: ')
option_type = input('Enter the option type: ')
out = get_options(ticker, option_type)
print(out.head())