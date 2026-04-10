import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# Approach 1. from csv file

banks_banckruptcy = pd.read_csv('failed_banks.csv', encoding='cp1252')

# Strip whitespace from column names to remove non-breaking spaces
banks_banckruptcy.columns = banks_banckruptcy.columns.str.strip()
print(banks_banckruptcy.head())

# tast is to count how many banks failed in each year

dates = pd.to_datetime(banks_banckruptcy['Closing Date'])
print(dates.dt.year.value_counts())

# Approach 2. from website

url = 'https://www.fdic.gov/bank-failures/failed-bank-list?pg=1'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

pagination_span = soup.find('span', class_='usa-pagination__link-text')
total_pages = int(pagination_span.text.strip())
print(f'Всего страниц: {total_pages}')

# Собираем все таблицы
all_dfs = []
for page in range(1, total_pages + 1):
    url = f'https://www.fdic.gov/bank-failures/failed-bank-list?pg={page}'
    response = requests.get(url)
    dfs = pd.read_html(response.text)
    df = dfs[0]
    df.columns = df.columns.str.strip()
    all_dfs.append(df)
    print(f'Забрали страницу {page}')
    # time.sleep(1)  # Пауза, чтоб не банили

full_table = pd.concat(all_dfs, ignore_index=True)
# full_table.to_csv('failed_banks_full.csv', index=False)
# print('Файл сохранён: failed_banks_full.csv')

dates = pd.to_datetime(full_table['Closing Date'])
print(dates.dt.year.value_counts().sort_index())

# Approach 3. from XML

df = pd.read_xml('http://www.cbr.ru/scripts/XML_daily.asp', encoding='cp1252')
# print(df.head())

print(df.loc[:, ['CharCode', 'Value']])
print(df[df['CharCode'] == 'USD'])