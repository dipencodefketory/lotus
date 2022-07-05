#-*- coding: utf-8 -*-

import afterbuy_api
import idealo_order
import xml.etree.ElementTree as ETree
from datetime import datetime, timedelta


access_dict = idealo_order.get_access_token()
r = idealo_order.get_orders(access_dict, status=['REVOKING'])
data = r.json()
orders = data['content']
i = 1
while i < data['totalPages']:
    r = idealo_order.get_orders(access_dict, status=['REVOKING'], page_number=i-1)
    data = r.json()
    orders += data['content']

min_date = datetime.now()
for order in orders:
    min_date = datetime.strptime(order['created'][:19], '%Y-%m-%dT%H:%M:%S') if datetime.strptime(order['created'][:19], '%Y-%m-%dT%H:%M:%S') < min_date else min_date
day_delta = (datetime.now()-min_date).days+1

id_dict = {}
for i in range(day_delta):
    start = (datetime.now()-timedelta(days=i+1)).strftime('%d.%m.%Y')
    end = (datetime.now()-timedelta(days=i)).strftime('%d.%m.%Y')
    r = afterbuy_api.get_sold_items({'Tag': ['Idealo'], 'DateFilter': ['AuctionEndDate', start, end]})
    tree = ETree.fromstring(r.text)
    order_query = [item for item in tree.iter() if item.tag == 'Order']
    for item in tree.iter():
        if item.tag == 'Order':
            order_id = item.findtext('OrderID')
            alt_id = item.findtext('OrderIDAlt')
            id_dict[alt_id] = order_id

for order in orders:
    print(order)
    if order['idealoOrderId'] in id_dict:
        r = afterbuy_api.update_sold_items([{'order_id': id_dict[order['idealoOrderId']], 'tags': ['Idealo', 'STORNO']}])
        print(r.text)
    else:
        print(f'Could not translate IdealoOrderId "{order["idealoOrderId"]}".')
