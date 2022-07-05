# -*- coding: utf-8 -*-

from lotus import db
from basismodels import WSRProduct, WSRParcel, WSReceipt, Supplier, PricingLog, Sale
from routines import ab_product_update

from datetime import datetime, timedelta
from sqlalchemy import func, case, and_


dt = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
start_dt = (dt - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
end_dt = dt - timedelta(microseconds=1)

sq = db.session.query(
    PricingLog.product_id.label('p_id'), func.sum(Sale.quantity).label('sale_quant')
).filter(
    PricingLog.id == Sale.pricinglog_id
).filter(
    Sale.timestamp >= start_dt
).filter(
    Sale.timestamp <= end_dt
).group_by(
    PricingLog.product_id
).subquery()

query = db.session.query(
    WSRProduct.product_id, func.sum(WSRProduct.quantity), case([(func.sum(WSRProduct.quantity) == 0, 0)], else_=(func.sum(WSRProduct.price * WSRProduct.quantity) / func.sum(WSRProduct.quantity)))
).outerjoin(
    sq, sq.c.p_id == WSRProduct.product_id
).add_column(
    func.max(func.coalesce(sq.c.sale_quant, 0))
).filter(
    and_(
        WSRProduct.complete == True,
        WSRProduct.completed_at >= start_dt,
        WSRProduct.completed_at <= end_dt
    )
).group_by(
    WSRProduct.product_id
).all()

p_ids = []
supplier = Supplier.query.filter_by(firmname='Lager').first()
wsr = WSReceipt(f'Nullbestellung_{datetime.now().strftime("%Y-%m-%d")}', supplier.id, units=1, completed_at=dt)
db.session.add(wsr)
db.session.commit()
wsr_parcel = WSRParcel('NO_TRACKING_NUMBER', wsr.id)
db.session.add(wsr_parcel)
db.session.commit()
for p_id, quant, price, sale_quant in query:
    if quant-sale_quant != 0:
        p_ids.append(p_id)
        db.session.add(WSRProduct(quant-sale_quant, price, 0, wsr_parcel.id, p_id, complete=True, completed_at=dt))
        db.session.commit()
wsr.gross_price = wsr.calc_gross_price()
wsr.net_price = wsr.calc_net_price()
wsr.positions = wsr.get_product_positions()
wsr.num_products = wsr.get_product_quantity()
db.session.commit()

for i in range((len(p_ids) + 1) // 250):
    r = ab_product_update(product_ids=p_ids[i*250: (i+1)*250], buying_price=True)
