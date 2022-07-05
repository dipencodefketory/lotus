from lotus import db
from basismodels import Product, WSRProduct, Sale, PricingLog, Product_Stock_Attributes, WSRParcel, WSReceipt
from sqlalchemy import case, or_, func
from datetime import datetime, timedelta
import xml.etree.ElementTree as ETree

import afterbuy_api


apr_1st = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


p_ids = []
for dt in [apr_1st]:
    sq_1 = db.session.query(
        PricingLog.product_id.label('p_id'), func.sum(Sale.quantity).label('quant')
    ).filter(
        PricingLog.id == Sale.pricinglog_id,
        Sale.timestamp < dt
    ).group_by(
        PricingLog.product_id
    ).subquery()

    sq_2 = db.session.query(
        WSRProduct.product_id.label('p_id'), func.sum(WSRProduct.quantity).label('quant')
    ).filter(
        WSRProduct.complete == True,
        WSRProduct.completed_at == dt
    ).group_by(
        WSRProduct.product_id
    ).subquery()

    sq_3 = db.session.query(
        WSRProduct.product_id.label('p_id'), func.sum(WSRProduct.quantity).label('quant')
    ).filter(
        WSRProduct.complete == True,
        WSRProduct.completed_at >= dt
    ).group_by(
        WSRProduct.product_id
    ).subquery()

    query = db.session.query(
        Product.internal_id
    ).join(
        sq_1, Product.id == sq_1.c.p_id
    ).outerjoin(
        sq_2, Product.id == sq_2.c.p_id
    ).join(
        sq_3, Product.id == sq_3.c.p_id
    ).add_columns(
        func.coalesce(sq_2.c.p_id)
    ).filter(
        func.coalesce(sq_2.c.p_id) == None,
        Product.release_date >= dt
    ).all()

    p_ids += [p_id for p_id, _ in query]

p_ids = list(set(p_ids))

found_ids = []
diff_dict = {}
for i in range((len(p_ids) - 1)//250 + 1):
    r = afterbuy_api.get_shop_products({'ProductID': p_ids[i * 250: (i + 1) * 250]})
    tree = ETree.fromstring(r.text)
    p_tree = [item for item in tree.iter() if item.tag == 'Product']
    stock_update = {}
    tag_dict = {}
    for p in p_tree:
        afterbuy_id = p.find('ProductID').text
        auction_quant = p.find('AuctionQuantity').text
        quant = p.find('Quantity').text
        psa, p = db.session.query(
            Product_Stock_Attributes, Product
        ).filter(
            Product.id == Product_Stock_Attributes.product_id
        ).filter(
            Product.internal_id == afterbuy_id,
            Product_Stock_Attributes.stock_id == 1
        ).first()
        if int(auction_quant) + int(quant) != psa.quantity - 100 * int(p.short_sell is True):
            diff_dict[p.id] = psa.quantity - 100 * int(p.short_sell is True) - int(auction_quant) - int(quant)
            found_ids.append(p.id)
            print(psa.product_id)
            print(psa.quantity)
            print(int(auction_quant) + int(quant))
            print('-----------------------------------')
print(diff_dict)

query = db.session.query(
    WSRProduct, WSRParcel.id, Product_Stock_Attributes
).join(
    WSRParcel, WSRParcel.id == WSRProduct.wsr_parcel_id
).join(
    WSReceipt, WSReceipt.id == WSRParcel.ws_receipt_id
).join(
    Product_Stock_Attributes, Product_Stock_Attributes.product_id == WSRProduct.product_id
).filter(
    Product_Stock_Attributes.stock_id == 1,
    WSReceipt.completed_at == apr_1st,
    WSRProduct.product_id.in_(found_ids)
).all()

wsr_parcel_id = None

for wsr_p, parcel_id, psa in query:
    wsr_parcel_id = parcel_id
    wsr_p.quantity -= diff_dict[wsr_p.product_id]
    psa.quantity -= diff_dict[wsr_p.product_id]
    db.session.commit()
    del diff_dict[wsr_p.product_id]

for p_id in diff_dict:
    _, price = db.session.query(
        PricingLog.product_id.label('p_id'), func.avg(Sale.chp_buying_price)
    ).filter(
        PricingLog.id == Sale.pricinglog_id,
        Sale.timestamp < apr_1st,
        PricingLog.product_id == p_id
    ).group_by(
        PricingLog.product_id
    ).first()
    db.session.add(WSRProduct(-diff_dict[p_id], price, 0, wsr_parcel_id, p_id, complete=True, completed_at=apr_1st))
    db.session.commit()
    psa = Product_Stock_Attributes.query.filter_by(product_id=p_id, stock_id=1).first()
    psa.quantity -= diff_dict[p_id]
    db.session.commit()
