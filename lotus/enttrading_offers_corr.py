# -*- coding: utf-8 -*-

from lotus import *
import requests
from requests.auth import HTTPBasicAuth
import csv
from dotenv import load_dotenv


load_dotenv(env_vars_path)

username = 'lotusicafe-de'
password = 'GWle==-**^lX'

r = requests.get('https://feeds.entertainment-trading.com/3728900-lotusicafe.csv', auth=HTTPBasicAuth(username, password))
r.encoding = 'utf-8'
csv_reader = csv.DictReader(r.text.strip().split('\n'), delimiter=';', dialect=csv.excel)

sku_dict = {}

for row in csv_reader:
    if row['location'] in sku_dict:
        sku_dict[row['location']].append(row['sku'])
    else:
        sku_dict[row['location']] = [row['sku']]

print(sku_dict)
for key in sku_dict:
    psas = Product_Stock_Attributes.query.filter(Product_Stock_Attributes.sku.in_(sku_dict[key])).update({'loc': key}, synchronize_session='fetch')
    db.session.commit()



