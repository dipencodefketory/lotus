from lotus import db
from basismodels import PSR_Attributes, StockReceipt, WSReceipt, WSRParcel, WSRProduct, Order, Order_Product_Attributes


psr_attributes = PSR_Attributes.query.filter(PSR_Attributes.stock_receipt_id == 1057).all()
psr_dict = {}
no_order = []

for psr_attr in psr_attributes:
    opa_ids = []
    opa = Order_Product_Attributes.query.filter(
        Order_Product_Attributes.product_id == psr_attr.product_id
    ).filter(
        Order_Product_Attributes.shipped > 0
    ).order_by(
        Order_Product_Attributes.ordered.desc()
    ).first()
    opa.shipped -= psr_attr.quantity
    db.session.commit()
    psr_dict[psr_attr.id] = opa_ids

print(psr_dict)
print(no_order)