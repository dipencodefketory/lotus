# -*- coding: utf-8 -*-

"""Everything regarding orders from wholesalers."""

# Internal Library
from lotus import db
from basismodels import Order, Order_Product_Attributes, Product_Stock_Attributes, Stock, Product
from entertainment_trading import create_order

# External Library
from datetime import datetime


def send_order(order_id: int):
    order = Order.query.filter_by(id=order_id).first()
    if order.sent:
        res = {'status_code': 403, 'reason': 'Already sent.', 'add_info': []}
    else:
        sup_name = order.supplier.firmname
        impl_suppliers = ['Entertainment-Trading']
        if sup_name in impl_suppliers:
            low_stock = []
            stock = db.session.query(
                Order_Product_Attributes, Product_Stock_Attributes, Stock, Product
            ).filter(
                Order_Product_Attributes.product_id == Product.id
            ).filter(
                Order_Product_Attributes.order_id == order_id
            ).filter(
                Product_Stock_Attributes.product_id == Order_Product_Attributes.product_id
            ).filter(
                Product_Stock_Attributes.avail_date <= datetime.now()
            ).filter(
                Product_Stock_Attributes.termination_date >= datetime.now()
            ).filter(
                Product_Stock_Attributes.stock_id == Stock.id
            ).filter(
                Stock.supplier_id == order.supplier_id
            ).all()
            for s in stock:
                print(s[1].quantity)
                if s[0].ordered > s[1].quantity and s[3].release_date <= datetime.now():
                    low_stock.append((s[0].product.id, s[0].product.name))
            if not low_stock:
                if sup_name == 'Entertainment-Trading':
                    lines = []
                    for s in stock:
                        if s[1].sku:
                            lines.append({'sku': s[1].sku, 'title': s[0].product.name, 'qty': s[0].ordered, "price_ex_vat": s[0].price})
                    r = create_order(order.id, 'EUR', '03035306768', 'service@lotusicafe.de', 'Faruk Önal', 'lotusicafe', 'Proskauer Str. 32', '10247', 'Berlin', 'DE', lines, 'S1')
                    if r.ok:
                        data = r.json()
                        res = {'status_code': r.status_code, 'reason': r.reason, 'order_id': str(data['id'])}
                    elif r.status_code == 400:
                        error_lines = []
                        for i, line in enumerate(r.json()['lines']):
                            if line:
                                for key in line:
                                    error_lines.append((stock[i][0].product.hsp_id, line[key]))
                        res = {'status_code': r.status_code, 'reason': r.reason, 'add_info': error_lines}
                    else:
                        res = {'status_code': r.status_code, 'reason': r.reason}
                else:
                    res = {'status_code': 401, 'reason': 'Supplier not implemented.', 'impl_suppliers': impl_suppliers}
            else:
                res = {'status_code': 402, 'reason': 'Insufficient stock.', 'add_info': low_stock}
        else:
            res = {'status_code': 401, 'reason': 'Supplier not implemented.', 'add_info': impl_suppliers}
    return res
