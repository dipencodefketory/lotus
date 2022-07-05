# -*- coding: utf-8 -*-

from lotus import db, csrf, tax_group
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import Order, ShippingStatus_Log, Order_Product_Attributes, Supplier, Product

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime

ws_order = Blueprint('ws_order', __name__, url_prefix='/ws_order')


@ws_order.route('/shipped_products/post', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def post_shipped_products():
    """
    receives a dictionary via request.get_json() of the form
    {
        'external_id': external_id,
        'supplier_id': supplier_id,
        'tracking_number': tracking_number,
        'products':
            [
                {
                    id: id,
                    quantity: quantity
                },
                ...
            ]
    }
    .
    :return:
    """
    data = request.get_json()
    print(data)
    if type(data) != dict:
        return make_response(jsonify({'message': 'Please provide dictionary as described in the docstring.', 'results': ''}), 422)
    else:
        if 'external_id' not in data or 'supplier_id' not in data or 'tracking_number' not in data or 'products' not in data:
            return make_response(jsonify({'message': 'external_id, supplier_id, tracking_number and products required.'}), 422)
        else:
            try:
                orders = Order.query.filter(
                    Order.order_time >= datetime.strptime('01.09.2021', '%d.%m.%Y')
                ).join(ShippingStatus_Log).all()

                order_ids = [order.id for order in orders if order.get_current_shipping_stat().label == 'bestellt']
                p_dict = dict((p['id'], int(p['quantity'])) for p in data['products'])
                p_ids = list(p_dict.keys())

                query = db.session.query(
                    Supplier, Order, Order_Product_Attributes
                ).filter(
                    Supplier.id == Order.supplier_id
                ).filter(
                    Order_Product_Attributes.order_id == Order.id
                ).filter(
                    Order_Product_Attributes.product_id.in_(p_ids)
                ).filter(
                    Supplier.id == int(data['supplier_id'])
                ).filter(
                    Order.id.in_(order_ids)
                ).order_by(
                    Order.order_time
                ).all()
                try:
                    supplier = Supplier.query.filter_by(id=int(data['supplier_id'])).first()
                    now = datetime.now()
                    products = []
                    for sup, o, opa in query:
                        if opa.product_id in p_dict:
                            diff = opa.ordered - opa.shipped if opa.shipped is not None else opa.ordered
                            add = min(diff, p_dict[opa.product_id])
                            if add > 0:
                                opa.shipped += add
                                p_dict[opa.product_id] -= add
                                if p_dict[opa.product_id] == 0:
                                    del p_dict[opa.product_id]
                                products.append({'product_id': opa.product_id, 'quantity': add, 'price': opa.price, 'tax': opa.prc_tax/100})
                                db.session.commit()
                    if p_dict:
                        order = Order(f'Wareneingang_{supplier.get_name()}_{datetime.now().strftime("%Y_%m_%d-%H_%M")}', now, None, 0, 0, None, 1, 6, supplier.id)
                        db.session.add(order)
                        db.session.commit()
                        for key in p_dict:
                            p = Product.query.filter_by(id=key).first()
                            new_connection = Order_Product_Attributes(p_dict[key], p_dict[key], 0, tax_group[p.tax_group][supplier.std_tax], order.id, p.id)
                            db.session.add(new_connection)
                            db.session.commit()
                            products.append({'product_id': key, 'quantity': p_dict[key], 'price': 0, 'tax': tax_group[p.tax_group][supplier.std_tax]/100})
                        order.price = order.gross_price()
                        db.session.commit()
                    print(products)
                    return make_response(jsonify({'message': '', 'result': {'external_id': data['external_id'], 'supplier_id': data['supplier_id'], 'parcels': [{'tracking_number': data['tracking_number'], 'products': products}]}}), 200)
                except Exception as e:
                    print(e)
                    return make_response(jsonify({'message': str(e)}), 400)
            except Exception as e:
                print(e)
                return make_response(jsonify({'message': str(e)}), 400)
