# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product_Stock_Attributes, PSAUpdateQueue

from datetime import datetime, timedelta

dt = datetime.now().replace(second=0, microsecond=0)
p_ids = db.session.query(Product_Stock_Attributes.product_id).filter(
    dt-timedelta(minutes=225) >= Product_Stock_Attributes.termination_date
).filter(
    dt-timedelta(minutes=255) <= Product_Stock_Attributes.termination_date
).all()
for p_id in p_ids:
    db.session.add(PSAUpdateQueue(p_id))
    db.session.commit()
