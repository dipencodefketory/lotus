# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product_Stock_Attributes, StockUpdateQueue, PSAUpdateQueue

from datetime import datetime
from sqlalchemy import func


dt = datetime.now()

db.session.query(
    StockUpdateQueue
).filter(
    StockUpdateQueue.proc_dt == None
).update(
    {'proc_dt': dt}, synchronize_session='fetch'
)
db.session.commit()

query = db.session.query(
    Product_Stock_Attributes, Product_Stock_Attributes.quantity + func.sum(StockUpdateQueue.update_amount)
).filter(
    Product_Stock_Attributes.id == StockUpdateQueue.psa_id
).filter(
    StockUpdateQueue.proc_dt == dt
).group_by(
    Product_Stock_Attributes.id
).all()

err_psa = []
for psa, quantity in query:
    try:
        psa.quantity = quantity
        db.session.commit()
        psa.product.update_psa = True
        db.session.add(PSAUpdateQueue(psa.product.id))
        db.session.commit()
    except Exception as e:
        print(e)
        err_psa.append(psa.id)

db.session.query(
    StockUpdateQueue
).filter(
    StockUpdateQueue.psa_id.in_(err_psa)
).filter(
    StockUpdateQueue.proc_dt == dt
).update(
    {'proc_dt': None}, synchronize_session='fetch'
)
db.session.commit()
