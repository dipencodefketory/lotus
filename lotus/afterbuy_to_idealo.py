# -*- coding: utf-8 -*-

from lotus import *
from datetime import datetime
import idealo_order


check_dates = []
access_dict = idealo_order.get_access_token()
r = idealo_order.get_orders(access_dict=access_dict, from_time=datetime.strptime('01.01.2021', '%d.%m.%Y').strftime('%Y-%m-%dT%H:%MZ'))
idealo_orders = r.json()
not_found = []
for order in idealo_orders['content']:
    sale = Sale.query.filter_by(mp_order_id=order['idealoOrderId']).first()
    if sale:
        if sale.cancelled is True:
            r = idealo_order.revoke_order(access_dict, sale.mp_order_id, sale.pricinglog.product.internal_id, 'CUSTOMER_REVOKE')
            print('REVOKE')
            print(order['idealoOrderId'])
            print(r.text)
            print('---------------------')
        elif sale.tracking_number is not None:
            r = idealo_order.set_fulfil_info(access_dict, sale.mp_order_id, 'DHL', sale.tracking_number)
            print('SET_TRACKING')
            print(order['idealoOrderId'])
            print(r.text)
            print('---------------------')
    else:
        not_found.append(order['idealoOrderId'])
        check_dates.append(order['created'][:10])
print('NOT FOUND:')
print(not_found)
print('CHECK DATES:')
print(list(set(check_dates)))
