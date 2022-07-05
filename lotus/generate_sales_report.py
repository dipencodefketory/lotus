# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Sale, SalesReport, Marketplace
import afterbuy_api
from datetime import datetime, timedelta
import xml.etree.ElementTree as ETree
from sqlalchemy import func


mps = Marketplace.query.all()
d = (datetime.now()-timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
for mp in mps:
    num_sales = db.session.query(Sale.id).filter(Sale.timestamp >= d).filter(Sale.timestamp < d + timedelta(days=1)).filter_by(marketplace_id=mp.id).count()
    num_own = db.session.query(Sale.id).filter(Sale.timestamp >= d).filter(Sale.timestamp < d + timedelta(days=1)).filter_by(own_stock=True, marketplace_id=mp.id).count()
    num_short_sell = db.session.query(Sale.id).filter(Sale.timestamp >= d).filter(Sale.timestamp < d + timedelta(days=1)).filter_by(short_sell=True, marketplace_id=mp.id).count()
    num_pre_order = db.session.query(Sale.id).filter(Sale.timestamp >= d).filter(Sale.timestamp < d + timedelta(days=1)).filter_by(pre_order=True, marketplace_id=mp.id).count()
    print('-------------------------------')
    print(d)
    print(num_sales)
    print(num_own)
    print(num_short_sell)
    print(num_pre_order)
    db.session.add(SalesReport(num_sales, num_own, num_short_sell, num_pre_order, mp.id, init_date=d))
    db.session.commit()
