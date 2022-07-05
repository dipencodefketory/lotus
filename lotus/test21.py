# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Order, Order_Product_Attributes, ShippingStatus_Log, Supplier, WSReceipt, WSRParcel, WSRProduct
from datetime import datetime
import csv
import ftplib
import requests
import re
from functions import deumlaut
import os


WSRProduct.query.delete()
db.session.commit()
WSRParcel.query.delete()
db.session.commit()
WSReceipt.query.delete()
db.session.commit()

orders = Order.query.filter(
    Order.order_time >= datetime.strptime('01.01.2022', '%d.%m.%Y')
).join(
    ShippingStatus_Log
).all()

order_ids = [order.id for order in orders if order.get_current_shipping_stat().label == 'abgeschlossen']

orders = Order.query.filter(Order.id.in_(order_ids)).order_by(Order.order_time).all()
le = len(orders)
for i, order in enumerate(orders):
    print(f'{i}/{le}')
    c_dt = order.get_current_shipping_stat().init_date
    supplier = Supplier.query.filter_by(id=order.supplier_id).first()
    wsr = WSReceipt(order.name, supplier.id, external_id=None, units=1, completed_at=c_dt)
    wsr.init_dt = order.order_time
    db.session.add(wsr)
    db.session.commit()
    wsr_parcel = WSRParcel('-', wsr.id)
    db.session.add(wsr_parcel)
    db.session.commit()
    for p in order.products:
        db.session.add(WSRProduct(p.shipped, p.price, p.prc_tax/100, wsr_parcel.id, p.product_id, complete=True, completed_at=c_dt))
        db.session.commit()
    wsr.gross_price = wsr.calc_gross_price()
    wsr.net_price = wsr.calc_net_price()
    db.session.commit()
