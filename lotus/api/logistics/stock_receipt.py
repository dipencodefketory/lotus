# -*- coding: utf-8 -*-

from lotus import db, csrf
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import StockReceipt, PSR_Attributes, Supplier, Product, ProductPicture
from functions import str_to_float, money_to_float

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime

stock_receipt = Blueprint('stock_receipt', __name__, url_prefix='/stock_receipt')


@stock_receipt.route('/post', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def post():
    """
    receives a dictionary via request.get_json() of the form
    {
        'external_id': external_id,
        'supplier_id': supplier_id,
        'units': units,
        'products':
            [
                {
                    ean: ean,
                    quantity: quantity,
                    weights: weights,
                    lengths: lengths,
                    widths: widths,
                    heights: heights
                },
                ...
            ]
        'name': name,                           <- optional
        'comment': comment,                     <- optional
        'tracking_number': tracking_number,     <- optional
    .
    :return:
    """
    data = request.get_json()
    print(data)
    if type(data) != dict:
        return make_response(jsonify({'message': 'Please provide dictionary as described in the docstring.', 'results': ''}), 422)
    else:
        if 'external_id' not in data or 'supplier_id' not in data or 'units' not in data or 'products' not in data:
            return make_response(jsonify({'message': 'external_id, supplier_id, units and products required.'}), 422)
        else:
            try:
                srs = StockReceipt.query.filter_by(external_id=data['external_id']).count()
                count = srs + 1
                supplier = Supplier.query.filter_by(id=data['supplier_id']).first()
                print(f'Wareneingang_{supplier.get_name()}_{count}')
                data['external_id'] = data['external_id'] if data['external_id'] else f'{supplier.get_name()[:3]}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                sr = StockReceipt(f'Wareneingang_{supplier.get_name()}_{data["external_id"]}_{count}', datetime.now(), None, None, None, 1, supplier.id,
                                  external_id=data['external_id'], tracking_number=data['tracking_number'], units=data['units'])
                db.session.add(sr)
                db.session.commit()
                result = {'supplier_id': data['supplier_id'], 'tracking_number': data['tracking_number'], 'external_id': data['external_id'], 'products': []}
                for p_data in data['products']:
                    try:
                        p = Product.query.filter_by(hsp_id=p_data['ean']).first()
                        if not p:
                            p = Product('EAN', p_data['ean'], name='neues Produkt', mpn='nicht zutreffend')
                            p.weight = str_to_float(money_to_float(p_data['weight']))
                            p.length = str_to_float(money_to_float(p_data['length']))
                            p.width = str_to_float(money_to_float(p_data['width']))
                            p.height = str_to_float(money_to_float(p_data['height']))
                            db.session.add(p)
                            db.session.commit()
                            p.add_basic_product_data(1)
                            j = 0
                            while j <= 1:
                                file_name = 'generic_pic.jpg'
                                db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                                j += 1
                        else:
                            p.weight = str_to_float(money_to_float(p_data['weight']))
                            p.length = str_to_float(money_to_float(p_data['length']))
                            p.width = str_to_float(money_to_float(p_data['width']))
                            p.height = str_to_float(money_to_float(p_data['height']))
                        db.session.add(PSR_Attributes(p_data['quantity'], None, None, sr.id, p.id))
                        db.session.commit()
                        result['products'].append({'id': p.id, 'quantity': p_data['quantity']})
                    except Exception as e:
                        print(e)
                db.session.commit()
                print(result)
                return make_response(jsonify({'message': '', 'result': result}), 200)
            except Exception as e:
                print(e)
                return make_response(jsonify({'message': str(e), 'result': result}), 400)
