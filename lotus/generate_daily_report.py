# -*- coding: utf-8 -*-

from lotus import db
from basismodels import DailyReport, Stock, Product, Product_Stock_Attributes, Product_CurrProcStat
from datetime import datetime
from sqlalchemy import Integer, or_, and_

stock_ids = db.session.query(Stock.id).filter_by(owned=True).all()

sellable = db.session.query(
    Product_Stock_Attributes, Product.id
).filter(
    Product_Stock_Attributes.quantity > 0
).filter(
    Product_Stock_Attributes.stock_id.in_(stock_ids)
).filter(
    Product_Stock_Attributes.product_id == Product.id
).count()

pos_stock = db.session.query(
    Product_Stock_Attributes, Product.id
).filter(
    Product_Stock_Attributes.quantity > Product.short_sell.cast(Integer)*100
).filter(
    Product_Stock_Attributes.stock_id.in_(stock_ids)
).filter(
    Product_Stock_Attributes.product_id == Product.id
).count()

short_sell = Product.query.filter_by(short_sell=True).count()
pre_order = Product.query.filter(Product.release_date > datetime.now()).count()
proc_prods = Product_CurrProcStat.query.filter(
    or_(
        and_(Product_CurrProcStat.proc_user_id == None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.product_id != None),
        and_(Product_CurrProcStat.product_id != None, Product_CurrProcStat.review == True)
    )
).count()

to_conf_prods = Product_CurrProcStat.query.filter(
    and_(Product_CurrProcStat.proc_user_id != None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.product_id != None)
).count()

conf_prods = Product_CurrProcStat.query.filter(
    and_(Product_CurrProcStat.proc_user_id != None, Product_CurrProcStat.conf_user_id != None, Product_CurrProcStat.product_id != None)
).count()

db.session.add(DailyReport(sellable, pos_stock, short_sell-pre_order, pre_order, proc_prods, to_conf_prods, conf_prods))
db.session.commit()
