# -*- coding: utf-8 -*-

from lotus import db, csrf
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import WSReceipt, WSIProduct, WSInvoice, Product, ProductPicture
from functions import str_to_float, money_to_float, str_to_int

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime

ws_invoice = Blueprint('ws_invoice', __name__, url_prefix='/ws_invoice')


@ws_invoice.route('/post', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def post():
    """
    receives a dictionary via request.get_json() of the form
    {
        'name: name,
        'invoice_number: invoice_number,
        'invoice_dt': invoice_dt,
        'target_dt': target_dt,
        'paid_at': paid_at,
        'paid': paid,
        'net_price: net_price,
        'gross_price: gross_price,
        'positions: positions,
        'num_products: num_products,
        'add_cost: add_cost,
        'comment: comment,
        'afterbuy_id: afterbuy_id,
        'completed_at: completed_at,
        'supplier_id: supplier_id,
        'ws_receipt_id: ws_receipt_id,
        'products:
            [
                {
                    product_id: product_id,
                    quantity: quantity,
                    price: price,
                    tax: tax
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
        try:
            wsi = WSInvoice(name=data['name'] if 'name' in data else None, invoice_number=data['invoice_number'] if 'invoice_number' in data else None, invoice_dt=data['invoice_dt'] if 'invoice_dt' in data else None,
                            target_dt=data['target_dt'] if 'target_dt' in data else None, paid_at=data['paid_at'] if 'paid_at' in data else None, paid=data['paid'] if 'paid' in data else None,
                            net_price=str_to_float(money_to_float(data['net_price'])) if 'net_price' in data else None, gross_price=str_to_float(money_to_float(data['gross_price'])) if 'gross_price' in data else None,
                            positions=str_to_int(data['positions']) if 'positions' in data else None,  num_products=str_to_int(data['num_products']) if 'num_products' in data else None,
                            add_cost=data['add_cost'] if 'add_cost' in data else None, comment=data['comment'] if 'comment' in data else None,
                            afterbuy_id=data['afterbuy_id'] if 'afterbuy_id' in data else None, completed_at=data['completed_at'] if 'completed_at' in data else None,
                            supplier_id=str_to_int(data['supplier_id']) if 'supplier_id' in data else None, ws_receipt_id=data['ws_receipt_id'] if 'ws_receipt_id' in data else None)
            if 'ws_receipt_id' in data:
                if data['ws_receipt_id']:
                    wsr = WSReceipt.query.filter_by(id=int(data['ws_receipt_id'])).first()
                    wsr.ws_invoice_id = wsi.id
                    wsr.inv_status = wsr.check_invoice()
            db.session.add(wsi)
            db.session.commit()
            for p in data['products']:
                try:
                    db.session.add(WSIProduct(p['quantity'], p['price'], p['tax'], wsi.id, p['product_id']))
                    db.session.commit()
                except Exception as e:
                    print(e)
            if wsi.products:
                wsi.gross_price = wsi.calc_gross_price()
                wsi.net_price = wsi.calc_net_price()
                wsi.positions = wsi.get_product_positions()
                wsi.num_products = wsi.get_product_quantity()
            else:
                wsi.gross_price = str_to_float(money_to_float(data['gross_price'])) if 'gross_price' in data else wsi.gross_price
                wsi.net_price = str_to_float(money_to_float(data['net_price'])) if 'net_price' in data else wsi.net_price
                wsi.positions = str_to_int(data['positions']) if 'positions' in data else wsi.positions
                wsi.num_products = str_to_int(data['num_products']) if 'num_products' in data else wsi.num_products
            db.session.commit()
            return make_response(jsonify({'message': ''}), 200)
        except Exception as e:
            return make_response(jsonify({'message': str(e)}), 400)


@ws_invoice.route('/patch', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def patch():
    """
    receives a dictionary via request.get_json() of the form
    {
        'id': id,
        'name: name,
        'invoice_number: invoice_number,
        'net_price: net_price,
        'gross_price: gross_price,
        'positions: positions,
        'num_products: num_products,
        'add_cost: add_cost,
        'comment: comment,
        'afterbuy_id: afterbuy_id,
        'completed_at: completed_at,
        'supplier_id: supplier_id,
        'ws_receipt_id: ws_receipt_id,
        'products:
            [
                {
                    id: id,
                    quantity: quantity,
                    price: price,
                    tax: tax
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
        return make_response(jsonify({'msg': 'Please provide dictionary as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            wsi = WSInvoice.query.filter_by(id=int(data['id'])).first()
            if wsi:
                result = {'products': []}
                wsi = WSInvoice.query.filter_by(id=int(data['id'])).first()
                wsi.name = data['name'] if 'name' in data else wsi.name
                wsi.invoice_number = data['invoice_number'] if 'invoice_number' in data else wsi.invoice_number
                if 'invoice_dt' in data:
                    wsi.invoice_dt = data['invoice_dt'] if data['invoice_dt'] else wsi.invoice_dt
                if 'target_dt' in data:
                    wsi.target_dt = data['target_dt'] if data['target_dt'] else wsi.target_dt
                if 'paid_at' in data:
                    wsi.paid_at = data['paid_at'] if data['paid_at'] else wsi.paid_at
                    try:
                        print(data['paid_at'])
                        datetime.strptime(data['paid_at'], '%Y-%m-%d')
                        wsi.paid = True
                    except:
                        wsi.paid = False
                wsi.add_cost = str_to_float(money_to_float(data['add_cost'])) if 'add_cost' in data else wsi.add_cost
                wsi.comment = data['comment'] if 'comment' in data else wsi.comment
                wsi.afterbuy_id = data['afterbuy_id'] if 'afterbuy_id' in data else wsi.afterbuy_id
                wsi.completed_at = data['completed_at'] if 'completed_at' in data else wsi.completed_at
                wsi.supplier_id = str_to_int(data['supplier_id']) if 'supplier_id' in data else wsi.supplier_id
                db.session.commit()
                for p in data['products']:
                    try:
                        wsi_p = WSIProduct.query.filter_by(id=p['id']).first()
                        wsi_p.quantity = p['quantity'] if 'quantity' in p else wsi_p.quantity
                        wsi_p.price = p['price'] if 'price' in p else wsi_p.price
                        tax = str_to_float(money_to_float(p['tax']))
                        wsi_p.tax = tax/100 if tax else tax
                        db.session.commit()
                        result['products'].append({'id': wsi_p.id, 'gross_price': '%0.2f' % (wsi_p.gross_price()), 'full_price': '%0.2f' % (wsi_p.quantity * wsi_p.gross_price())})
                    except Exception as e:
                        print(e)
                if wsi.products:
                    wsi.gross_price = wsi.calc_gross_price()
                    wsi.net_price = wsi.calc_net_price()
                    wsi.positions = wsi.get_product_positions()
                    wsi.num_products = wsi.get_product_quantity()
                else:
                    wsi.gross_price = str_to_float(money_to_float(data['gross_price'])) if 'gross_price' in data else wsi.gross_price
                    wsi.net_price = str_to_float(money_to_float(data['net_price'])) if 'net_price' in data else wsi.net_price
                    wsi.positions = str_to_int(data['positions']) if 'positions' in data else wsi.positions
                    wsi.num_products = str_to_int(data['num_products']) if 'num_products' in data else wsi.num_products
                db.session.commit()
                if 'ws_receipt_id' in data:
                    if data['ws_receipt_id']:
                        wsr = WSReceipt.query.filter_by(id=int(data['ws_receipt_id'])).first()
                        wsi.receipt = wsr
                        wsr.inv_status = wsr.check_invoice()
                result['net_price'] = '%0.2f' % wsi.net_price if wsi.net_price else ''
                result['gross_price'] = '%0.2f' % wsi.gross_price if wsi.gross_price else ''
                result['product_positions'] = wsi.positions
                result['product_quantity'] = wsi.num_products
                print(result)
                return make_response(jsonify({'message': '', 'result': result}), 200)
            else:
                return make_response(jsonify({'message': 'WSInvoice not found'}), 422)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)


@ws_invoice.route('/delete', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def delete():
    """
    receives a list via request.get_json() of the form
    [wsi_id_1, wsi_id_2, ...]
    .
    :return:
    """
    data = request.get_json()
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide list as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            result = []
            wsi_ids = [int(wsi_id) for wsi_id in data]
            ws_invoices = WSInvoice.query.filter(WSInvoice.id.in_(wsi_ids)).all()
            for wsi in ws_invoices:
                if wsi.receipt:
                    wsi.receipt.invoice_id = None
                    db.session.commit()
                result.append(wsi.id)
                WSIProduct.query.filter_by(ws_invoice_id=wsi.id).delete(synchronize_session='fetch')
                db.session.commit()
                db.session.delete(wsi)
                db.session.commit()
            return make_response(jsonify({'message': '', 'result': result}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)


@ws_invoice.route('/products/add', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def add_products():
    """
    receives a list via request.get_json() of the form
    {
        'id': id,
        'products:
            [
                {
                    'id': product_id,
                    'quantity': quantity,
                    'price': price,
                    'tax': tax
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
        if 'id' not in data or 'products' not in data:
            return make_response(jsonify({'message': 'id and products required.'}), 422)
        else:
            try:
                wsi = WSInvoice.query.filter_by(id=int(data['id'])).first()
                if wsi:
                    products = []
                    for p_data in data['products']:
                        p = Product.query.filter_by(id=int(p_data['id'])).first()
                        if p is None:
                            p = Product('EAN', p_data['ean'], name=p_data['name'], mpn='nicht zutreffend')
                            db.session.add(p)
                            db.session.commit()
                            p.add_basic_product_data(1)
                            j = 0
                            while j <= 1:
                                file_name = 'generic_pic.jpg'
                                db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                                j += 1
                        tax = str_to_float(money_to_float(p_data['tax']))
                        try:
                            wsi_p = WSIProduct(p_data['quantity'], p_data['price'], tax/100 if tax else tax, wsi.id, p.id)
                            db.session.add(wsi_p)
                            db.session.commit()
                            products.append({'id': wsi_p.id, 'p_id': p.id, 'p_hsp_id': p.hsp_id, 'p_internal_id': p.internal_id, 'p_name': p.name, 'quantity': wsi_p.quantity,
                                             'tax': '%0.2f' % (wsi_p.tax * 100), 'net_price': '%0.2f' % wsi_p.price, 'gross_price': '%0.2f' % (wsi_p.price * (1 + wsi_p.tax)),
                                             'full_price': '%0.2f' % (wsi_p.price * (1 + wsi_p.tax) * wsi_p.quantity)})
                        except Exception as e:
                            print(e)
                    if wsi.products:
                        wsi.gross_price = wsi.calc_gross_price()
                        wsi.net_price = wsi.calc_net_price()
                        wsi.positions = wsi.get_product_positions()
                        wsi.num_products = wsi.get_product_quantity()
                    db.session.commit()
                    result = {'net_price': '%0.2f' % wsi.net_price, 'gross_price': '%0.2f' % wsi.gross_price, 'product_positions': wsi.positions, 'product_quantity': wsi.num_products,
                              'products': products}
                    print(result)
                    return make_response(jsonify({'message': '', 'result': result}), 200)
                else:
                    return make_response(jsonify({'message': 'WSInvoice not found'}), 422)
            except Exception as e:
                print(e)
                return make_response(jsonify({'message': str(e)}), 400)


@ws_invoice.route('/products/delete', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def delete_products():
    """
    receives a list via request.get_json() of the form
    [wsi_p_id_1, wsi_p_id_2, ...]
    .
    :return:
    """
    data = request.get_json()
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide list as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            result = []
            wsi_p_ids = [int(wsi_p_id) for wsi_p_id in data]
            ws_invoices = WSInvoice.query.join(
                WSIProduct, WSIProduct.ws_invoice_id == WSInvoice.id
            ).filter(
                WSIProduct.id.in_(wsi_p_ids)
            ).order_by(
                WSInvoice.id
            ).all()
            WSIProduct.query.filter(
                WSIProduct.id.in_(wsi_p_ids)
            ).delete(synchronize_session='fetch')
            db.session.commit()
            for wsi in ws_invoices:
                wsi.net_price = wsi.calc_net_price()
                wsi.gross_price = wsi.calc_gross_price()
                wsi.positions = wsi.get_product_positions()
                wsi.num_products = wsi.get_product_quantity()
                db.session.commit()
                result.append({'net_price': '%0.2f' % wsi.net_price if wsi.net_price else '', 'gross_price': '%0.2f' % wsi.gross_price if wsi.gross_price else '', 'product_positions': wsi.positions,
                               'product_quantity': wsi.num_products, 'read_only_off': False if wsi.products else True})
            print(result)
            return make_response(jsonify({'message': '', 'result': result}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)
