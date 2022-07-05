# -*- coding: utf-8 -*-

from lotus import db, csrf
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import PricingBundle, PricingRule, Product

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
from sqlalchemy import func

pricing = Blueprint('pricing', __name__, url_prefix='/pricing')


@pricing.route('/bundle', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def post_bundle():
    """
    receives a list of dictionaries via request.get_json() of the form
    [
        {
            'name: name_1
            'rules':
                [
                    {
                        'name': name_1,
                        'if_strategy': if_strategy_1,
                        'if_sale_suc_h': if_sale_suc_h_1,
                        'if_sale_fail_h': if_sale_fail_h_1,
                        'if_sale_num': if_sale_num_1,
                        'if_sale_rev': if_sale_rev_1,
                        'then_strategy': then_strategy_1,
                    },
                    OR
                    {
                        'id': id_1,
                    }
                    ...
                ]
            'product_ids':
                [
                    product_id_1,
                    product_id_2,
                    ...
                ]
        }
    ]
    .
    :return:
    """

    data = request.get_json()
    print(data)
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide a list of dictionaries as described in the docstring.', 'results': ''}), 422)
    else:
        errs = False
        results = []
        for bundle in data:
            if 'name' not in bundle or 'rules' not in bundle or 'products' not in bundle:
                errs = True
                results.append({'status_code': 422, 'message': 'name required.'})
            else:
                try:
                    bundle = PricingBundle(init_dt=datetime.now(), name=bundle['name'])
                    db.session.add(bundle)
                    db.session.commit()
                    for rule in bundle['rule']:
                        if 'id' in rule:
                            pb = PricingBundle.query.filter_by(id=int(rule['id'])).first()
                            pb.pricing_bundle_id = bundle.id
                            db.session.commit()
                        else:
                            if_sale_suc_h = rule['if_sale_suc_h'] if rule['if_sale_suc_h'] != '' else None
                            if_sale_fail_h = rule['if_sale_fail_h'] if rule['if_sale_fail_h'] != '' else None
                            if_sale_num = rule['if_sale_num'] if rule['if_sale_num'] != '' else None
                            if_sale_rev = rule['if_sale_rev'] if rule['if_sale_rev'] != '' else None
                            db.session.add(PricingRule(init_dt=datetime.now(), name=rule['name'], if_strategy=rule['if_strategy'], then_strategy=rule['then_strategy'], if_sale_suc_h=if_sale_suc_h,
                                                       if_sale_fail_h=if_sale_fail_h, if_sale_num=if_sale_num, if_sale_rev=if_sale_rev, pricing_bundle_id=bundle.id))
                            db.session.commit()
                        results.append({'name': rule['name'], 'status_code': 200, 'message': ''})
                    for product_id in bundle['product_ids']:
                        p = Product.query.filter_by(id=int(product_id)).first()
                        p.pricing_bundle_id = bundle.id
                        db.session.commit()
                except Exception as e:
                    print(e)
                    errs = True
                    results.append({'status_code': 400, 'message': str(e)})
        return make_response(jsonify({'message': '', 'results': results}), 200 if errs is False else 400)


@pricing.route('/bundle/<bundle_id>', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def patch_bundle(bundle_id):
    data = request.get_json()
    print(data)
    if type(data) != dict:
        return make_response(jsonify({'message': 'Please provide a list of dictionaries as described in the docstring.', 'results': ''}), 422)
    else:
        try:
            bundle = PricingBundle.query.filter_by(id=int(bundle_id)).first()
            bundle.name = data['name'] if 'name' in data else bundle.name
            db.session.commit()
            return make_response(jsonify({'message': ''}), 200)
        except Exception as e:
            return make_response(jsonify({'message': str(e)}), 400)


@pricing.route('/rule', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def post_rule():
    """
    receives a list of dictionaries via request.get_json() of the form
    [
        {
            'name': name_1,
            'if_strategy': if_strategy_1,
            'if_sale_suc_h': if_sale_suc_h_1,
            'if_sale_fail_h': if_sale_fail_h_1,
            'if_sale_num': if_sale_num_1,
            'if_sale_rev': if_sale_rev_1,
            'pricing_bundle_id': pricing_bundle_id,
            'then_strategy': then_strategy_1,
        },
        {
            'name': name_2,
            ...
        }
    ]
    .
    :return:
    """

    data = request.get_json()
    print(data)
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide a list of dictionaries as described in the docstring.', 'results': ''}), 422)
    else:
        errs = False
        results = []
        for rule in data:
            if 'name' not in rule or 'if_strategy' not in rule or 'then_strategy' not in rule:
                errs = True
                results.append({'name': rule['name'], 'status_code': 422, 'message': 'name, if_strategy and then_strategy required.'})
            else:
                try:
                    if_sale_suc_h = rule['if_sale_suc_h'] if rule['if_sale_suc_h'] != '' else None
                    if_sale_fail_h = rule['if_sale_fail_h'] if rule['if_sale_fail_h'] != '' else None
                    if_sale_num = rule['if_sale_num'] if rule['if_sale_num'] != '' else None
                    if_sale_rev = rule['if_sale_rev'] if rule['if_sale_rev'] != '' else None
                    pricing_bundle_id = rule['pricing_bundle_id'] if rule['pricing_bundle_id'] != '' else None
                    pr_rule = PricingRule(init_dt=datetime.now(), name=rule['name'], if_strategy=rule['if_strategy'], then_strategy=rule['then_strategy'], if_sale_suc_h=if_sale_suc_h,
                                       if_sale_fail_h=if_sale_fail_h, if_sale_num=if_sale_num, if_sale_rev=if_sale_rev, pricing_bundle_id=pricing_bundle_id)
                    db.session.add(pr_rule)
                    db.session.commit()
                    results.append({'name': rule['name'], 'id': pr_rule.id,  'status_code': 200, 'message': ''})
                except Exception as e:
                    print(e)
                    errs = True
                    results.append({'name': rule['name'], 'status_code': 400, 'message': str(e)})
        return make_response(jsonify({'message': '', 'results': results}), 200 if errs is False else 400)


@pricing.route('/rule', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def patch_rule():
    """
    receives a list of dictionaries via request.get_json() of the form
    [
        {
            'name': name_1,
            'if_strategy': if_strategy_1,
            'if_sale_suc_h': if_sale_suc_h_1,
            'if_sale_fail_h': if_sale_fail_h_1,
            'if_sale_num': if_sale_num_1,
            'if_sale_rev': if_sale_rev_1,
            'pricing_bundle_id': pricing_bundle_id,
            'then_strategy': then_strategy_1,
        },
        {
            'name': name_2,
            ...
        }
    ]
    .
    :return:
    """

    data = request.get_json()
    print(data)
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide a list of dictionaries as described in the docstring.', 'results': ''}), 422)
    else:
        errs = False
        results = []
        for rule in data:
            if 'name' not in rule or 'if_strategy' not in rule or 'then_strategy' not in rule:
                errs = True
                results.append({'name': rule['name'], 'status_code': 422, 'message': 'name, if_strategy and then_strategy required.'})
            else:
                try:
                    pr_rule = PricingRule.query.filter_by(id=int(rule['id'])).first()
                    if rule:
                        pr_rule.if_sale_suc_h = rule['if_sale_suc_h'] if rule['if_sale_suc_h'] != '' else None
                        pr_rule.if_sale_fail_h = rule['if_sale_fail_h'] if rule['if_sale_fail_h'] != '' else None
                        pr_rule.if_sale_num = rule['if_sale_num'] if rule['if_sale_num'] != '' else None
                        pr_rule.if_sale_rev = rule['if_sale_rev'] if rule['if_sale_rev'] != '' else None
                        pr_rule.pricing_bundle_id = rule['pricing_bundle_id'] if rule['pricing_bundle_id'] != '' else None
                        db.session.commit()
                        results.append({'name': rule['name'], 'id': pr_rule.id,  'status_code': 200, 'message': ''})
                    else:
                        results.append({'name': rule['name'], 'status_code': 402, 'message': 'not found.'})
                except Exception as e:
                    print(e)
                    errs = True
                    results.append({'name': rule['name'], 'status_code': 400, 'message': str(e)})
        return make_response(jsonify({'message': '', 'results': results}), 200 if errs is False else 400)


@pricing.route('/rule/<pr_rule_id>', methods=['DELETE'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def delete_rule(pr_rule_id):
    PricingRule.query.filter_by(id=int(pr_rule_id)).delete()
    db.session.commit()
    return make_response(jsonify({'msg': ''}), 200)


@pricing.route('/rule/<pr_rule_id>', methods=['GET'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def get_rule(pr_rule_id):
    pr_rule = PricingRule.query.filter_by(id=int(pr_rule_id)).first()
    return make_response(jsonify({
        'if_strategy': pr_rule.if_strategy,
        'then_strategy': pr_rule.then_strategy,
        'if_sale_suc_h': pr_rule.if_sale_suc_h,
        'if_sale_fail_h': pr_rule.if_sale_fail_h,
        'if_sale_num': pr_rule.if_sale_num,
        'if_sale_rev': pr_rule.if_sale_rev
    }), 200)


@pricing.route('/rules', methods=['GET'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def get_rules():
    """
    receives a list of dictionaries via request.get_json() of the form
    [
        {
            'name': name_1,
            'if_strategy': if_strategy_1,
            'if_sale_suc_h': if_sale_suc_h_1,
            'if_sale_fail_h': if_sale_fail_h_1,
            'if_sale_num': if_sale_num_1,
            'if_sale_rev': if_sale_rev_1,
            'then_strategy': then_strategy_1,
        },
        {
            'name': name_2,
            ...
        }
    ]
    .
    :return:
    """
    p_ids = request.args.get('product_ids').split(',')
    print(p_ids)
    query = db.session.query(
        PricingRule, func.count(PPrRule.id)
    ).filter(
        PricingRule.id == PPrRule.pricing_rule_id
    ).filter(
        PPrRule.product_id.in_([int(p_id) for p_id in p_ids]) if p_ids else True
    ).order_by(
        PricingRule.id
    ).group_by(
        PricingRule.id
    ).all()
    data = [{
        'id': prr.id,
        'name': prr.name,
        'if_strategy': prr.if_strategy,
        'if_sale_suc_h': prr.if_sale_suc_h,
        'if_sale_fail_h': prr.if_sale_fail_h,
        'if_sale_num': prr.if_sale_num,
        'if_sale_rev': prr.if_sale_rev,
        'then_strategy': prr.then_strategy,
        'products': [
            {
                'p_id': p_pr_rule.product_id, 'p_name': p_pr_rule.product.name, 'start': p_pr_rule.start.strftime('%d.%m.%Y'), 'end': p_pr_rule.end.strftime('%d.%m.%Y'),
                'priority': p_pr_rule.priority
            } for p_pr_rule in prr.products
        ]
    } for prr, _ in query]
    return make_response(jsonify({'results': len(data), 'data': data}), 200)
