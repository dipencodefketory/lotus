# -*- coding: utf-8 -*-

from lotus import db
from basismodels import WSRProduct, WSRParcel, WSReceipt, PricingLog, Sale, Product_Stock_Attributes, Product
from routines import ab_product_update

from datetime import datetime, timedelta
from sqlalchemy import func, case, and_, or_, Integer


start_dt = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#start_dt = (dt - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


sq_1 = db.session.query(
    WSRProduct.product_id.label('p_id'), func.sum(WSRProduct.quantity).label('wsr_quant')
).filter(
    and_(
        WSRProduct.complete == True,
        WSRProduct.completed_at >= start_dt
    )
).group_by(
    WSRProduct.product_id
).subquery()

sq_2 = db.session.query(
    PricingLog.product_id.label('p_id'), func.sum(Sale.quantity).label('sale_quant')
).filter(
    PricingLog.id == Sale.pricinglog_id
).filter(
    Sale.timestamp >= start_dt
).group_by(
    PricingLog.product_id
).subquery()

query = db.session.query(
    Product, Product_Stock_Attributes
).outerjoin(
    sq_1, sq_1.c.p_id == Product_Stock_Attributes.product_id
).outerjoin(
    sq_2, sq_2.c.p_id == Product_Stock_Attributes.product_id
).add_column(
    func.coalesce(sq_1.c.wsr_quant, 0) - func.coalesce(sq_2.c.sale_quant, 0) + Product.short_sell.cast(Integer) * 100
).filter(
    Product.id == Product_Stock_Attributes.product_id
).filter(
    Product_Stock_Attributes.stock_id == 1
).filter(
    func.coalesce(sq_1.c.wsr_quant, 0) - func.coalesce(sq_2.c.sale_quant, 0) + Product.short_sell.cast(Integer) * 100 != Product_Stock_Attributes.quantity
).order_by(
    Product.id.desc()
).all()
le=len(query)
for i, (p, psa, quantity) in enumerate(query):
    print(f'{i+1}/{le}\t{p.id}\t{p.internal_id} - {quantity}')
    psa.quantity = quantity
    db.session.commit()
