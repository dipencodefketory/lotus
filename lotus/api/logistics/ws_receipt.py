# -*- coding: utf-8 -*-

from lotus import db, csrf
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import WSReceipt, WSRParcel, WSRProduct, Supplier, Product_Stock_Attributes, Product, PricingLog, Sale, PSAUpdateQueue, ProductPicture, WSInvoice, StockUpdateQueue
import routines
from functions import str_to_float, money_to_float

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
from sqlalchemy import or_, and_, func

ws_receipt = Blueprint('ws_receipt', __name__, url_prefix='/ws_receipt')


@ws_receipt.route('/post', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def post():
    """
    receives a dictionary via request.get_json() of the form
    {
        'name': name,
        'comment': comment,
        'units': units,
        'external_id': external_id,
        'afterbuy_id': afterbuy_id,
        'completed_at': completed_at,
        'supplier_id': supplier_id,
        'parcels':
            [
                {
                    'tracking_number': tracking_number,
                    'products':
                        [
                            {
                                product_id: product_id,
                                quantity: quantity,
                                price: price,
                                tax: tax
                            },
                            ...
                        ]
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
        if 'external_id' not in data or 'supplier_id' not in data or 'parcels' not in data:
            return make_response(jsonify({'message': 'external_id, supplier_id and parcels required.'}), 422)
        else:
            try:
                parcel_ids = []
                wsr = WSReceipt.query.filter_by(external_id=data['external_id'], supplier_id=data['supplier_id']).first() if data['external_id'] and data['supplier_id'] else None
                if wsr is None:
                    supplier = Supplier.query.filter_by(id=data['supplier_id']).first()
                    wsr = WSReceipt(f'Wareneingang_{supplier.get_name()}_{datetime.now().strftime("%Y_%m_%d-%H_%M")}', supplier.id, external_id=data['external_id'], units=data['units'])
                    db.session.add(wsr)
                    db.session.commit()
                for parcel in data['parcels']:
                    try:
                        wsr_parcel = WSRParcel(parcel['tracking_number'], wsr.id)
                        db.session.add(wsr_parcel)
                        db.session.commit()
                        parcel_ids.append(wsr_parcel)
                        for p in parcel['products']:
                            try:
                                db.session.add(WSRProduct(p['quantity'], p['price'], p['tax'], wsr_parcel.id, p['product_id']))
                                db.session.commit()
                            except Exception as e:
                                print(e)
                    except Exception as e:
                        print(e)
                wsr.gross_price = wsr.calc_gross_price()
                wsr.net_price = wsr.calc_net_price()
                wsr.positions = wsr.get_product_positions()
                wsr.num_products = wsr.get_product_quantity()
                wsr.inv_status = wsr.check_invoice()
                db.session.commit()
                return make_response(jsonify({'message': '', 'result': {'wsr_id': wsr.id, 'parcel_ids': parcel_ids}}), 200)
            except Exception as e:
                return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/patch', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def patch():
    """
    receives a dictionary via request.get_json() of the form
    {
        'id': id,
        'name': name,
        'units': units,
        'add_cost': add_cost,
        'external_id': external_id,
        'afterbuy_id': afterbuy_id,
        'completed_at': completed_at,
        'supplier_id': supplier_id,
        'invoice_id': invoice_id,
        'comment': comment,
        'parcels':
            [
                {
                    'id': id,
                    'tracking_number': tracking_number,
                    'products':
                        [
                            {
                                id: id,
                                quantity: quantity,
                                price: price,
                                tax: tax
                            },
                            ...
                        ]
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
        if 'id' not in data:
            return make_response(jsonify({'message': 'id required.'}), 422)
        else:
            result = {'parcels': []}
            try:
                wsr = WSReceipt.query.filter_by(id=data['id']).first()
                if wsr:
                    wsr.name = data['name'] if 'name' in data else wsr.name
                    wsr.units = int(data['units']) if 'units' in data else wsr.units
                    wsr.external_id = data['external_id'] if 'external_id' in data else wsr.external_id
                    wsr.afterbuy_id = data['afterbuy_id'] if 'afterbuy_id' in data else wsr.afterbuy_id
                    wsr.completed_at = datetime.strptime(data['completed_at'], '%Y-%m-%d') if 'completed_at' in data else wsr.completed_at
                    wsr.supplier_id = data['supplier_id'] if 'supplier_id' in data else wsr.supplier_id
                    wsr.add_cost = str_to_float(money_to_float(data['add_cost'])) if 'add_cost' in data else wsr.add_cost
                    if wsr.invoice and 'invoice_id' in data:
                        wsr.invoice.ws_receipt_id = None
                    wsr.invoice_id = data['invoice_id'] if 'invoice_id' in data else wsr.invoice_id
                    wsr.comment = data['comment'] if 'comment' in data else wsr.comment
                    for parcel_data in data['parcels']:
                        parcel = WSRParcel.query.filter_by(id=parcel_data['id']).first()
                        parcel_response = {'id': parcel.id, 'products': []}
                        parcel.tracking_number = parcel_data['tracking_number'] if 'tracking_number' in parcel_data else parcel.tracking_number
                        for wsr_p_data in parcel_data['products']:
                            wsr_p = WSRProduct.query.filter_by(id=wsr_p_data['id']).first()
                            wsr_p.quantity = int(wsr_p_data['quantity'])
                            wsr_p.price = float(wsr_p_data['price'])
                            wsr_p.tax = float(wsr_p_data['tax'])/100
                            parcel_response['products'].append({'id': wsr_p.id, 'gross_price': '%0.2f' % (wsr_p.price * (1 + wsr_p.tax)), 'full_price': '%0.2f' % (wsr_p.price * (1 + wsr_p.tax) * wsr_p.quantity)})
                        parcel_response['p_num'] = parcel.get_quantity()
                        result['parcels'].append(parcel_response)
                    wsr.net_price = wsr.calc_net_price()
                    wsr.gross_price = wsr.calc_gross_price()
                    wsr.positions = wsr.get_product_positions()
                    wsr.num_products = wsr.get_product_quantity()
                    wsr.inv_status = wsr.check_invoice()
                    db.session.commit()
                    result['net_price'] = '%0.2f' % wsr.net_price
                    result['gross_price'] = '%0.2f' % wsr.gross_price
                    result['product_positions'] = wsr.positions
                    result['product_quantity'] = wsr.num_products
                    result['invoice'] = False
                    if wsr.invoice:
                        result['invoice'] = True
                        result['inv_net_price'] = '%0.2f' % wsr.invoice.net_price if wsr.invoice.net_price else ''
                        result['inv_gross_price'] = '%0.2f' % wsr.invoice.gross_price if wsr.invoice.gross_price else ''
                        result['inv_product_positions'] = wsr.invoice.positions
                        result['inv_product_quantity'] = wsr.invoice.num_products
                    return make_response(jsonify({'message': '', 'result': result}), 200)
                else:
                    return make_response(jsonify({'message': 'WSReceipt not found'}), 422)
            except Exception as e:
                print(e)
                return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/absorb', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def absorb():
    """
    receives a dict via request.get_json() of the form
    {
        'id': id,
        'absorb_id': absorb_id
    }
    .
    :return:
    """
    data = request.get_json()
    if type(data) != dict:
        return make_response(jsonify({'message': 'Please provide dict as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            if data['id'] == data['absorb_id']:
                return make_response(jsonify({'message': 'Absorber = Absorbed.'}), 422)
            wsr = WSReceipt.query.filter_by(id=int(data['id'])).first()
            absorb_wsr = WSReceipt.query.filter_by(id=int(data['absorb_id'])).first()
            if wsr and absorb_wsr:
                for parcel in absorb_wsr.parcels:
                    parcel.ws_receipt_id = wsr.id
                    db.session.commit()
                wsr.net_price = wsr.calc_net_price()
                wsr.gross_price = wsr.calc_gross_price()
                wsr.positions = wsr.get_product_positions()
                wsr.num_products = wsr.get_product_quantity()
                wsr.units += absorb_wsr.units
                wsr.inv_status = wsr.check_invoice()
                db.session.commit()
                result = {
                    'net_price': '%0.2f' % wsr.net_price + ' €',
                    'gross_price': '%0.2f' % wsr.gross_price + ' €',
                    'parcel_num': len(wsr.parcels),
                    'units': wsr.units
                }
                if absorb_wsr.invoice is not None:
                    absorb_wsr.invoice.receipt_id = None
                    db.session.commit()
                db.session.delete(absorb_wsr)
                db.session.commit()
                return make_response(jsonify({'message': '', 'result': result}), 200)
            else:
                return make_response(jsonify({'message': 'WSReceipt not found'}), 422)
        except Exception as e:
            return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/delete', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def delete():
    """
    receives a list via request.get_json() of the form
    [wsr_id_1, wsr_id_2, ...]
    .
    :return:
    """
    data = request.get_json()
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide list as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            check_completed = False
            result = []
            wsr_ids = [int(wsr_id) for wsr_id in data]
            ws_receipts = WSReceipt.query.filter(WSReceipt.id.in_(wsr_ids)).all()
            for wsr in ws_receipts:
                del_wsr = True
                for parcel in wsr.parcels:
                    for product in parcel.products:
                        if product.complete is True:
                            del_wsr = False
                            break
                    if del_wsr is False:
                        break
                if del_wsr is True:
                    if wsr.invoice:
                        wsr.invoice.ws_receipt_id = None
                        db.session.commit()
                    result.append(wsr.id)
                    for parcel in wsr.parcels:
                        WSRProduct.query.filter_by(wsr_parcel_id=parcel.id).delete(synchronize_session='fetch')
                        db.session.commit()
                        db.session.delete(parcel)
                        db.session.commit()
                    db.session.delete(wsr)
                    db.session.commit()
                else:
                    check_completed = True
            return make_response(jsonify({'message': '' if check_completed is False else 'Some receipts had completed positions. Make sure all position are open before delete.', 'result': result}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/<ws_receipt_id>/get_pick_list', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def get_pick_list(ws_receipt_id):
    try:
        query = db.session.query(
            WSRProduct, Product, PricingLog, Sale
        ).join(
            WSRParcel, WSRParcel.id == WSRProduct.wsr_parcel_id
        ).filter(
            WSRProduct.product_id == Product.id
        ).filter(
            Product.id == PricingLog.product_id
        ).filter(
            PricingLog.id == Sale.pricinglog_id
        ).filter(
            WSRParcel.ws_receipt_id == ws_receipt_id
        ).filter(
            Sale.timestamp >= datetime.strptime('01.12.2021', '%d.%m.%Y')
        ).filter(
            Sale.quantity > 0
        ).filter(
            Sale.sent_by == None
        ).order_by(
            WSRProduct.product_id, Sale.timestamp
        ).all()
        avail_dict = {}
        pick_dict = {'product_ids': []}
        for wsr_p, p, log, s in query:
            avail_dict[wsr_p.product_id] = avail_dict[wsr_p.product_id] + wsr_p.quantity if wsr_p.product_id in avail_dict else wsr_p.quantity
            if avail_dict[wsr_p.product_id] >= s.quantity:
                if wsr_p.product_id in pick_dict:
                    pick_dict[wsr_p.product_id]['quantity'] += s.quantity
                else:
                    pick_dict[wsr_p.product_id] = {'ean': p.hsp_id, 'name': p.name, 'quantity': s.quantity}
                pick_dict['product_ids'].append(wsr_p.product_id)
                avail_dict[wsr_p.product_id] -= s.quantity
        del pick_dict['product_ids']
        pick_list = [pick_dict[key] for key in pick_dict]
        return make_response(jsonify({'message': '', 'result': pick_list}), 200)
    except Exception as e:
        print(e)
        return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/<wsr_id>/match_invoice', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def match_invoice(wsr_id):
    try:
        wsr = WSReceipt.query.filter_by(id=wsr_id).first()
        if wsr:
            wsi = WSInvoice.query.filter(
                or_(
                    and_(
                        WSInvoice.net_price == wsr.net_price,
                        WSInvoice.net_price == wsr.gross_price,
                        WSInvoice.num_products == wsr.num_products
                    ),
                    and_(
                        WSInvoice.net_price == wsr.net_price,
                        WSInvoice.net_price == wsr.gross_price,
                        WSInvoice.num_products == wsr.positions
                    ),
                    and_(
                        WSInvoice.net_price == wsr.net_price,
                        WSInvoice.net_price == wsr.num_products,
                        WSInvoice.num_products == wsr.positions
                    ),
                    and_(
                        WSInvoice.net_price == wsr.gross_price,
                        WSInvoice.net_price == wsr.num_products,
                        WSInvoice.num_products == wsr.positions
                    ),
                )

            ).filter(
                WSInvoice.supplier_id == wsr.supplier_id
            ).filter(
                WSInvoice.receipt == None
            ).order_by(
                WSInvoice.invoice_dt.desc()
            ).first()
            if wsi:
                wsr.invoice_id = wsi.id
                wsi.receipt = wsr
                wsr.inv_status = wsr.check_invoice()
                db.session.commit()
                return make_response(jsonify({'message': '', 'result':
                    {
                        'type': 'matched',
                        'invoice_id': wsi.id,
                        'gross_price': wsr.gross_price,
                        'net_price': wsr.net_price,
                        'product_positions': wsr.positions,
                        'product_quantity': wsr.num_products,
                        'inv_gross_price': wsi.gross_price,
                        'inv_net_price': wsi.net_price,
                        'inv_product_positions': wsi.positions,
                        'inv_product_quantity': wsi.num_products
                    }}), 200)
            else:
                wsi = WSInvoice.query.filter(
                    or_(
                        WSInvoice.net_price == wsr.net_price,
                        WSInvoice.net_price == wsr.gross_price,
                        WSInvoice.num_products == wsr.num_products,
                        WSInvoice.positions == wsr.positions
                    )
                ).filter(
                    WSInvoice.supplier_id == wsr.supplier_id
                ).filter(
                    WSInvoice.receipt == None
                ).order_by(
                    WSInvoice.invoice_dt.desc()
                ).first()
                if wsi:
                    return make_response(jsonify({'message': '', 'result': {'type': 'candidate', 'invoice_id': wsi.id}}), 200)
                else:
                    return make_response(jsonify({'message': '', 'result': {'type': 'no matching invoice found.'}}), 200)
        else:
            return make_response(jsonify({'message': 'WSReceipt not found'}), 422)
    except Exception as e:
        print(e)
        return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/parcels/add', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def add_parcels():
    """
    receives a list via request.get_json() of the form
    {
        'wsr_id': wsr_id,
        'parcels:
            [
                {
                    'tracking_number': tracking_number,
                    'products':
                        [
                            {
                                'product_id': product_id,
                                'quantity': quantity,
                                'price': price,
                                'tax': tax
                            },
                            ...
                        ]
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
        return make_response(jsonify({'message': 'Please provide dict as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            wsr = WSReceipt.query.filter_by(id=int(data['wsr_id'])).first()
            result = {'parcels': []}
            for parcel_data in data['parcels']:
                parcel = WSRParcel(parcel_data['tracking_number'] if 'tracking_number' in parcel_data else '', wsr.id)
                db.session.add(parcel)
                db.session.commit()
                parcel_response = {'id': parcel.id, 'tracking_number': parcel.tracking_number, 'products': []}
                for p_data in parcel_data['products']:
                    try:
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
                        wsr_p = WSRProduct(p_data['quantity'], p_data['price'], tax / 100 if tax else tax, parcel.id, p_data['id'])
                        db.session.add(wsr_p)
                        db.session.commit()
                        parcel_response['products'].append({'id': wsr_p.id, 'p_id': p.id, 'p_hsp_id': p.hsp_id, 'p_internal_id': p.internal_id, 'p_name': p.name, 'quantity': wsr_p.quantity,
                                                            'tax': '%0.2f' % (wsr_p.tax * 100), 'net_price': '%0.2f' % wsr_p.price, 'gross_price': '%0.2f' % (wsr_p.price * (1 + wsr_p.tax)),
                                                            'full_price': '%0.2f' % (wsr_p.price * (1 + wsr_p.tax) * wsr_p.quantity)})
                    except Exception as e:
                        print(e)
                parcel_response['p_num'] = parcel.get_quantity()
                result['parcels'].append(parcel_response)
            wsr.gross_price = wsr.calc_gross_price()
            wsr.net_price = wsr.calc_net_price()
            wsr.positions = wsr.get_product_positions()
            wsr.num_products = wsr.get_product_quantity()
            wsr.inv_status = wsr.check_invoice()
            db.session.commit()
            result['net_price'] = '%0.2f' % wsr.net_price
            result['gross_price'] = '%0.2f' % wsr.gross_price
            result['product_positions'] = wsr.positions
            result['product_quantity'] = wsr.num_products
            result['invoice'] = False
            if wsr.invoice:
                result['invoice'] = True
                result['inv_net_price'] = '%0.2f' % wsr.invoice.net_price if wsr.invoice.net_price else ''
                result['inv_gross_price'] = '%0.2f' % wsr.invoice.gross_price if wsr.invoice.gross_price else ''
                result['inv_product_positions'] = wsr.invoice.positions
                result['inv_product_quantity'] = wsr.invoice.num_products
            print(result)
            return make_response(jsonify({'message': '', 'result': result}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/delete_parcels', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def delete_parcels():
    """
    receives a list via request.get_json() of the form
    [parcel_id_1, parcel_id_2, ...]
    .
    :return:
    """
    data = request.get_json()
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide list as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            check_completed = False
            result = []
            parcel_ids = [int(parcel_id) for parcel_id in data]
            parcels = WSRParcel.query.filter(WSRParcel.id.in_(parcel_ids)).all()
            wsr_ids = []
            removed = []
            for parcel in parcels:
                del_parcel = True
                for product in parcel.products:
                    if product.complete is True:
                        del_parcel = False
                        break
                if del_parcel is True:
                    removed.append(parcel.id)
                    wsr_ids.append(parcel.ws_receipt_id)
                    WSRProduct.query.filter_by(wsr_parcel_id=parcel.id).delete(synchronize_session='fetch')
                    db.session.commit()
                    db.session.delete(parcel)
                    db.session.commit()
            ws_receipts = WSReceipt.query.filter(WSReceipt.id.in_(wsr_ids)).all()
            for wsr in ws_receipts:
                wsr_res = {'parcels': []}
                for parcel in wsr.parcels:
                    wsr_res['parcels'].append({'id': parcel.id, 'p_num': parcel.get_quantity()})
                wsr.net_price = wsr.calc_net_price()
                wsr.gross_price = wsr.calc_gross_price()
                wsr.positions = wsr.get_product_positions()
                wsr.num_products = wsr.get_product_quantity()
                wsr.inv_status = wsr.check_invoice()
                db.session.commit()
                wsr_res['net_price'] = '%0.2f' % wsr.net_price
                wsr_res['gross_price'] = '%0.2f' % wsr.gross_price
                wsr_res['product_positions'] = wsr.positions
                wsr_res['product_quantity'] = wsr.num_products
                wsr_res['invoice'] = False
                if wsr.invoice:
                    wsr_res['invoice'] = True
                    wsr_res['inv_net_price'] = '%0.2f' % wsr.invoice.net_price if wsr.invoice.net_price else ''
                    wsr_res['inv_gross_price'] = '%0.2f' % wsr.invoice.gross_price if wsr.invoice.gross_price else ''
                    wsr_res['inv_product_positions'] = wsr.invoice.positions
                    wsr_res['inv_product_quantity'] = wsr.invoice.num_products
                result.append(wsr_res)
            return make_response(jsonify({'message': '' if check_completed is False else 'Some positions were completed. Make sure to open before delete.', 'result': result, 'removed': removed}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/parcel/<parcel_id>/separate', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def separate_parcel(parcel_id):
    """
    :param parcel_id:
    :return:
    """
    try:
        parcel = WSRParcel.query.filter_by(id=int(parcel_id)).first()
        curr_wsr = parcel.ws_receipt
        supplier = curr_wsr.supplier
        wsr = WSReceipt(f'Wareneingang_{supplier.get_name()}_{datetime.now().strftime("%Y_%m_%d-%H_%M")}', supplier.id,
                        external_id=f'{supplier.get_name()[:3]}_{datetime.now().strftime("%Y%m%d%H%M%S")}', units=1)
        db.session.add(wsr)
        db.session.commit()
        parcel.ws_receipt_id = wsr.id
        wsr.net_price = wsr.calc_net_price()
        wsr.gross_price = wsr.calc_gross_price()
        wsr.positions = wsr.get_product_positions()
        wsr.num_products = wsr.get_product_quantity()
        wsr.inv_status = wsr.check_invoice()
        curr_wsr.net_price = curr_wsr.calc_net_price()
        curr_wsr.gross_price = curr_wsr.calc_gross_price()
        curr_wsr.positions = wsr.get_product_positions()
        curr_wsr.num_products = wsr.get_product_quantity()
        curr_wsr.inv_status = wsr.check_invoice()
        db.session.commit()
        result = {
            'net_price': '%0.2f' % curr_wsr.net_price,
            'gross_price': '%0.2f' % curr_wsr.gross_price,
            'product_positions': curr_wsr.positions,
            'product_quantity': curr_wsr.num_products,
            'invoice': False
        }
        if wsr.invoice:
            result['invoice'] = True
            result['inv_net_price'] = '%0.2f' % wsr.invoice.net_price if wsr.invoice.net_price else ''
            result['inv_gross_price'] = '%0.2f' % wsr.invoice.gross_price if wsr.invoice.gross_price else ''
            result['inv_product_positions'] = wsr.invoice.positions
            result['inv_product_quantity'] = wsr.invoice.num_products
        return make_response(jsonify({'message': '', 'result': result}), 200)
    except Exception as e:
        print(e)
        return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/parcel/<parcel_id>/paste_wsr_product/<inp_value>', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def parcel_paste_wsr_product(parcel_id, inp_value):
    """
    :param parcel_id:
    :param inp_value:
    :return:
    """
    try:
        result = {'parcels': []}
        wsr_p = WSRProduct.query.filter_by(id=inp_value).first()
        print(wsr_p.product.name)
        wsr_p.wsr_parcel_id = int(parcel_id)
        db.session.commit()
        wsr = wsr_p.wsr_parcel.ws_receipt
        for parcel in wsr.parcels:
            result['parcels'].append({'id': parcel.id, 'p_num': parcel.get_quantity()})
        print(result)
        return make_response(jsonify({'message': '', 'result': result}), 200)
    except Exception as e:
        print(e)
        return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/parcel/<parcel_id>/get_pick_list', methods=['GET'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def get_parcel_pick_list(parcel_id):
    try:
        query = db.session.query(
            WSRProduct, Product, PricingLog, Sale
        ).filter(
            WSRProduct.product_id == Product.id
        ).filter(
            Product.id == PricingLog.product_id
        ).filter(
            PricingLog.id == Sale.pricinglog_id
        ).filter(
            WSRProduct.wsr_parcel_id == parcel_id
        ).filter(
            Sale.timestamp >= datetime.strptime('01.12.2021', '%d.%m.%Y')
        ).filter(
            Sale.quantity > 0
        ).filter(
            Sale.sent_by == None
        ).order_by(
            WSRProduct.product_id, Sale.timestamp
        ).all()
        avail_dict = {}
        pick_dict = {'product_ids': []}
        for wsr_p, p, log, s in query:
            avail_dict[wsr_p.product_id] = avail_dict[wsr_p.product_id] + wsr_p.quantity if wsr_p.product_id in avail_dict else wsr_p.quantity
            if avail_dict[wsr_p.product_id] >= s.quantity:
                if wsr_p.product_id in pick_dict:
                    pick_dict[wsr_p.product_id]['quantity'] += s.quantity
                else:
                    pick_dict[wsr_p.product_id] = {'ean': p.hsp_id, 'name': p.name, 'quantity': s.quantity}
                pick_dict['product_ids'].append(wsr_p.product_id)
                avail_dict[wsr_p.product_id] -= s.quantity
        del pick_dict['product_ids']
        pick_list = [pick_dict[key] for key in pick_dict]
        return make_response(jsonify({'message': '', 'result': pick_list}), 200)
    except Exception as e:
        print(e)
        return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/products/add', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def add_products():
    """
    receives a list via request.get_json() of the form
    {
        'parcel_id': parcel_id,
        'products:
            [
                {
                    id: id,
                    ean: ean,
                    name: name,
                    quantity: quantity,
                    tax: tax,
                    net_price: net_price,
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
        if 'parcel_id' not in data or 'products' not in data:
            return make_response(jsonify({'message': 'parcel_id and products required.'}), 422)
        else:
            try:
                parcel = WSRParcel.query.filter_by(id=int(data['parcel_id'])).first()
                if parcel:
                    result = {'parcels': []}
                    parcel_response = {'id': parcel.id, 'products': []}
                    wsr = parcel.ws_receipt
                    for p_data in data['products']:
                        try:
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
                            wsr_p = WSRProduct(p_data['quantity'], p_data['price'], tax/100 if tax else tax, parcel.id, p_data['id'])
                            db.session.add(wsr_p)
                            db.session.commit()
                            parcel_response['products'].append({'id': wsr_p.id, 'p_id': p.id, 'p_hsp_id': p.hsp_id, 'p_internal_id': p.internal_id, 'p_name': p.name, 'quantity': wsr_p.quantity,
                                                                'tax': '%0.2f' % (wsr_p.tax * 100), 'net_price': '%0.2f' % wsr_p.price,  'gross_price': '%0.2f' % (wsr_p.price * (1 + wsr_p.tax)),
                                                                'full_price': '%0.2f' % (wsr_p.price * (1 + wsr_p.tax) * wsr_p.quantity)})
                            parcel_response['p_num'] = parcel.get_quantity()
                            result['parcels'].append(parcel_response)
                        except Exception as e:
                            print(e)
                    wsr.gross_price = wsr.calc_gross_price()
                    wsr.net_price = wsr.calc_net_price()
                    wsr.positions = wsr.get_product_positions()
                    wsr.num_products = wsr.get_product_quantity()
                    wsr.inv_status = wsr.check_invoice()
                    db.session.commit()
                    result['net_price'] = '%0.2f' % wsr.net_price
                    result['gross_price'] = '%0.2f' % wsr.gross_price
                    result['product_positions'] = wsr.positions
                    result['product_quantity'] = wsr.num_products
                    result['invoice'] = False
                    if wsr.invoice:
                        result['invoice'] = True
                        result['inv_net_price'] = '%0.2f' % wsr.invoice.net_price if wsr.invoice.net_price else ''
                        result['inv_gross_price'] = '%0.2f' % wsr.invoice.gross_price if wsr.invoice.gross_price else ''
                        result['inv_product_positions'] = wsr.invoice.positions
                        result['inv_product_quantity'] = wsr.invoice.num_products
                    print(result)
                    return make_response(jsonify({'message': '', 'result': result}), 200)
                else:
                    return make_response(jsonify({'message': 'WSParcel not found'}), 422)
            except Exception as e:
                print(e)
                return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/products/delete', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def delete_products():
    """
    receives a list via request.get_json() of the form
    [wsr_p_id_1, wsr_p_id_2, ...]
    .
    :return:
    """
    data = request.get_json()
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide list as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            result = []
            wsr_p_ids = [int(wsr_p_id) for wsr_p_id in data]
            ws_receipts = WSReceipt.query.join(
                WSRParcel, WSRParcel.ws_receipt_id == WSReceipt.id
            ).join(
                WSRProduct, WSRProduct.wsr_parcel_id == WSRParcel.id
            ).filter(
                WSRProduct.id.in_(wsr_p_ids)
            ).order_by(
                WSReceipt.id
            ).all()
            delete_wsr_ps = WSRProduct.query.filter(
                WSRProduct.complete == False
            ).filter(
                WSRProduct.id.in_(wsr_p_ids)
            ).delete(synchronize_session='fetch')
            check_completed = False
            if len(wsr_p_ids) > delete_wsr_ps:
                check_completed = True
            db.session.commit()
            print(ws_receipts)
            for wsr in ws_receipts:
                wsr_res = {'parcels': []}
                for parcel in wsr.parcels:
                    wsr_res['parcels'].append({'id': parcel.id, 'p_num': parcel.get_quantity()})
                wsr.net_price = wsr.calc_net_price()
                wsr.gross_price = wsr.calc_gross_price()
                wsr.positions = wsr.get_product_positions()
                wsr.num_products = wsr.get_product_quantity()
                wsr.inv_status = wsr.check_invoice()
                db.session.commit()
                wsr_res['net_price'] = '%0.2f' % wsr.net_price
                wsr_res['gross_price'] = '%0.2f' % wsr.gross_price
                wsr_res['product_positions'] = wsr.positions
                wsr_res['product_quantity'] = wsr.num_products
                wsr_res['invoice'] = False
                if wsr.invoice:
                    wsr_res['invoice'] = True
                    wsr_res['inv_net_price'] = '%0.2f' % wsr.invoice.net_price if wsr.invoice.net_price else ''
                    wsr_res['inv_gross_price'] = '%0.2f' % wsr.invoice.gross_price if wsr.invoice.gross_price else ''
                    wsr_res['inv_product_positions'] = wsr.invoice.positions
                    wsr_res['inv_product_quantity'] = wsr.invoice.num_products
                result.append(wsr_res)
            print(result)
            return make_response(jsonify({'message': '' if check_completed is False else 'Some positions were completed. Make sure to open before delete.', 'result': result}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)



@ws_receipt.route('/products/complete', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def complete_products():
    """
    receives a list via request.get_json() of the form
    [wsr_p_id_1, wsr_p_id_2, ...]
    .
    :return:
    """
    data = request.get_json()
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide list as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            product_ids = []
            receipt_ids = []
            wsr_p_ids = [int(wsr_p_id) for wsr_p_id in data]
            wsr_ps = WSRProduct.query.filter(WSRProduct.id.in_(wsr_p_ids)).all()
            for wsr_p in wsr_ps:
                if wsr_p.complete == False or wsr_p.completed_at == None:
                    receipt_ids += [wsr_p.wsr_parcel.ws_receipt_id] if wsr_p.wsr_parcel.ws_receipt_id not in receipt_ids else []
                    psa = Product_Stock_Attributes.query.filter_by(product_id=wsr_p.product_id, stock_id=1).first()
                    print(psa.product.name)
                    if wsr_p.quantity > 0 and (psa.quantity < 100 and wsr_p.product.short_sell == True or psa.quantity < 0 and wsr_p.product.short_sell == False):
                        sale_query = db.session.query(
                            Product, PricingLog, Sale
                        ).filter(
                            Product.id == PricingLog.product_id
                        ).filter(
                            PricingLog.id == Sale.pricinglog_id
                        ).filter(
                            Product.id == wsr_p.product_id
                        ).filter(
                            Sale.sendable_by == None
                        ).filter(
                            Sale.cancelled == False
                        ).filter(
                            Sale.sent_by == None
                        ).filter(
                            Sale.quantity > 0
                        ).filter(
                            Sale.timestamp >= datetime.strptime('01.12.2021', '%d.%m.%Y')
                        ).order_by(
                            Sale.timestamp
                        ).all()
                        to_ship = int(wsr_p.quantity)
                        for p, log, sale in sale_query:
                            if sale.quantity <= to_ship:
                                to_ship -= sale.quantity
                                sale.sendable_by = datetime.now()
                                if to_ship == 0:
                                    break
                        db.session.commit()
                    db.session.add(StockUpdateQueue(wsr_p.quantity, psa.id, curr_stock=psa.quantity))
                    db.session.commit()
                    db.session.add(PSAUpdateQueue(wsr_p.product_id))
                    wsr_p.complete = True
                    wsr_p.completed_at = datetime.now()
                    db.session.commit()
                    try:
                        psa.buying_price = wsr_p.product.get_own_buying_price()
                        wsr_p.product.buying_price = psa.buying_price
                        db.session.commit()
                    except Exception as e:
                        print(e)
                        continue
                    product_ids.append(wsr_p.product_id)
            if product_ids:
                r = routines.ab_product_update(product_ids=product_ids, buying_price=True)
                print(r.text)
            if receipt_ids:
                subquery = db.session.query(
                    WSReceipt.id.label('ws_receipt_id'), func.count(WSRParcel.id), func.count(WSRProduct.id).label('complete_count')
                ).filter(
                    WSReceipt.id.in_(receipt_ids)
                ).filter(
                    WSReceipt.completed_at == None
                ).filter(
                    WSRParcel.ws_receipt_id == WSReceipt.id
                ).filter(
                    WSRParcel.id == WSRProduct.wsr_parcel_id
                ).group_by(
                    WSReceipt.id
                ).subquery()

                query = db.session.query(
                    WSReceipt, func.count(WSRParcel.id.distinct()), func.count(WSRProduct.id), func.max(WSRProduct.completed_at)
                ).join(
                    subquery, subquery.c.ws_receipt_id == WSReceipt.id
                ).add_column(
                    func.max(subquery.c.complete_count).label('count')
                ).filter(
                    WSReceipt.id.in_(receipt_ids)
                ).filter(
                    WSReceipt.completed_at == None
                ).filter(
                    WSRParcel.ws_receipt_id == WSReceipt.id
                ).filter(
                    WSRParcel.id == WSRProduct.wsr_parcel_id
                ).group_by(
                    WSReceipt.id
                ).having(
                    func.count(WSRParcel.id.distinct()) == WSReceipt.units
                ).having(
                    func.count(WSRProduct.id) == func.max(subquery.c.complete_count)
                ).all()

                for wsr, _, _, dt, _ in query:
                    wsr.completed_at = dt
                    db.session.commit()
            return make_response(jsonify({'message': ''}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)


@ws_receipt.route('/products/open', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def open_products():
    """
    receives a list via request.get_json() of the form
    [wsr_p_id_1, wsr_p_id_2, ...]
    .
    :return:
    """
    data = request.get_json()
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide list as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            product_ids = []
            wsr_p_ids = [int(wsr_p_id) for wsr_p_id in data]
            wsr_ps = WSRProduct.query.filter(WSRProduct.id.in_(wsr_p_ids)).all()
            for wsr_p in wsr_ps:
                if wsr_p.complete is True:
                    psa = Product_Stock_Attributes.query.filter_by(product_id=wsr_p.product_id, stock_id=1).first()
                    print(psa.product.name)
                    if wsr_p.quantity > 0 and (psa.quantity - wsr_p.quantity < 100 and wsr_p.product.short_sell == True or psa.quantity - wsr_p.quantity < 0 and wsr_p.product.short_sell == False):
                        sale_query = db.session.query(
                            Product, PricingLog, Sale
                        ).filter(
                            Product.id == PricingLog.product_id
                        ).filter(
                            PricingLog.id == Sale.pricinglog_id
                        ).filter(
                            Product.id == wsr_p.product.id
                        ).filter(
                            Sale.sendable_by != None
                        ).filter(
                            Sale.cancelled == False
                        ).filter(
                            Sale.sent_by == None
                        ).filter(
                            Sale.quantity > 0
                        ).filter(
                            Sale.timestamp >= datetime.strptime('01.12.2021', '%d.%m.%Y')
                        ).order_by(
                            Sale.timestamp.desc()
                        ).all()
                        not_to_ship = int(wsr_p.quantity)
                        for p, log, sale in sale_query:
                            if sale.quantity <= not_to_ship:
                                not_to_ship -= sale.quantity
                                sale.sendable_by = None
                                if not_to_ship == 0:
                                    break
                        db.session.commit()
                    db.session.add(StockUpdateQueue(-1 * wsr_p.quantity, psa.id, curr_stock=psa.quantity))
                    db.session.commit()
                    db.session.add(PSAUpdateQueue(wsr_p.product_id))
                    wsr_p.complete = False
                    wsr_p.opened_at = datetime.now()
                    db.session.commit()
                    try:
                        psa.buying_price = wsr_p.product.get_own_buying_price()
                        wsr_p.product.buying_price = psa.buying_price
                        db.session.commit()
                    except Exception as e:
                        print(e)
                        continue
                    product_ids.append(wsr_p.product_id)
            if product_ids:
                r = routines.ab_product_update(product_ids=product_ids, buying_price=True)
                print(r.text)
            return make_response(jsonify({'message': ''}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'message': str(e)}), 400)
