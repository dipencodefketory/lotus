# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Sale
import afterbuy_api
from datetime import datetime, timedelta
import xml.etree.ElementTree as ETree
from sqlalchemy import and_


sales = Sale.query.filter(and_(Sale.timestamp >= datetime.strptime('01.11.2021', '%d.%m.%Y'), Sale.quantity > 0, Sale.sent_by == None)).all()

le = len(sales)
for i in range((le+1)//250 + 1):
    print(f'{i+1}/{(le+1)//250 + 1}')
    order_ids = [sale.order_number for sale in sales[i*250: (i+1)*250]]
    r = afterbuy_api.get_sold_items({'OrderID': order_ids})
    tree = ETree.fromstring(r.text)
    orders = []
    for order in tree.findall('.//Order'):
        delivery_date = order.find('.//DeliveryDate')
        tracking_number = order.find('.//AdditionalInfo')
        tracking_number = tracking_number.text if tracking_number is not None else None
        shipping_method = order.find('.//ShippingMethod')
        shipping_method = shipping_method.text if shipping_method is not None else None
        if delivery_date is not None:
            f = '%d.%m.%Y' if len(delivery_date.text) == 10 else '%d.%m.%Y %H:%M:%S'
            delivery_date = datetime.strptime(delivery_date.text, f)
            order_id = order.find('.//OrderID').text
            check_sales = Sale.query.filter_by(order_number=order_id).all()
            for check_sale in check_sales:
                check_sale.sent_by = delivery_date
                check_sale.tracking_number = tracking_number if tracking_number is not None and check_sale.tracking_number is None else check_sale.tracking_number
                check_sale.shipping_method = shipping_method if shipping_method is not None else check_sale.shipping_method
                db.session.commit()

sales = Sale.query.filter(and_(Sale.tracking_number == None, Sale.timestamp >= datetime.strptime('01.11.2021', '%d.%m.%Y'), Sale.quantity > 0, Sale.sent_by == None)).all()
