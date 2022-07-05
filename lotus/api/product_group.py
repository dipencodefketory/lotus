# -*- coding: utf-8 -*-

from lotus import db, csrf
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import ProductGroup

from flask import Blueprint, request, jsonify, make_response
from sqlalchemy import func, and_, or_
import re
import json

product_group = Blueprint('product_group', __name__, url_prefix='/product_group')


@product_group.route('/post', methods=['POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def post():
    """
    receives a list of dictionaries via request.get_json() of the form
    [
        {
            'name': pgr_name_1,             <- Name of the group
            'product_ids':
                [
                    p_id_1,
                    p_id_2,
                    ...
                ]
        },
        {
            'name': pgr_name_2,             <- Name of the group
            ...
        }
    ].
    :return:
    """
    data = request.get_json()
    if type(data) != list:
        return make_response(jsonify({'message': 'Please provide a list of dictionaries as described in the docstring.', 'results': ''}), 422)
    else:
        errs = False
        results = []
        for pgr in data:
            try:
                db.session.add(ProductGroup(pgr['name'], [int(p_id) for p_id in pgr['product_ids']]))
                db.session.commit()
                results.append({'name': pgr['name'], 'status_code': 200, 'message': ''})
            except Exception as e:
                print(e)
                errs = True
                results.append({'name': pgr['name'], 'status_code': 400, 'message': str(e)})
        return make_response(jsonify({'message': '', 'results': results}), 200 if errs is False else 400)


@product_group.route('/patch', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def patch():
    """
    receives a dictionary of dictionaries via request.get_json() of the form
    {
        pgr_id_1:
            {
                'name': pgr_name,             <- Name of the product-group
                ...
            },
        pgr_id_2:
            {
                'name': pgr_name,             <- Name of the product-group
                ...
            }
    }.
    :return:
    """
    data = request.get_json()
    results = []
    errs = False
    pgrs = ProductGroup.query.filter(ProductGroup.id.in_([int(key) for key in data])).all()
    for pgr in pgrs:
        pgr_data = data[str(pgr.id)]
        try:
            print(pgr_data)
            pgr.self_update(name=pgr_data['name'] if 'name' in pgr_data else None)
            results.append({'name': pgr_data['name'], 'status_code': 200, 'message': ''})
        except Exception as e:
            print(e)
            errs = True
            results.append({'name': pgr_data['name'], 'status_code': 400, 'message': str(e)})
    return make_response(jsonify({'message': '', 'results': results}), 200 if errs is False else 400)


@product_group.route('/search/<keywords>', methods=['GET'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def search(keywords):
    kw_dq = re.findall(r'\"(.+?)\"', keywords)
    for el in kw_dq:
        keywords = keywords.replace(f'"{el}"', '')
    kws = [kw.strip().lower() for kw in keywords.split(' ') + kw_dq]
    query = ProductGroup.query
    num_entries = list(filter(lambda el: el.isnumeric(), kws))
    if num_entries:
        num_query = query.filter(or_(ProductGroup.id == int(num_entry) for num_entry in num_entries)).all()
        print(num_query)
        if num_query:
            return jsonify([{'gr_id': gr.id, 'gr_name': gr.name} for gr in num_query])
    and_query = query.filter(and_(func.lower(ProductGroup.name).like(f'%{kw}%') for kw in kws if kw)).all()
    if and_query:
        return jsonify([{'gr_id': gr.id, 'gr_name': gr.name} for gr in and_query])
    query = query.filter(or_(func.lower(ProductGroup.name).like(f'%{kw}%') for kw in kws if kw))
    if query:
        return jsonify([{'gr_id': gr.id, 'gr_name': gr.name} for gr in query])


@product_group.route('/merge/<pgr_id>', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def merge(pgr_id):
    """
    receives a dictionary of dictionaries via request.get_json() of the form
    {
        p_id_1:
            {
                'name': p_name,             <- Name of the product
                ...
            },
        p_id_2:
            {
                'name': p_name,             <- Name of the product
                ...
            }
    }.
    All entries are optional and will only be updated if provided.
    :return:
    """
    pgr = ProductGroup.query.filter_by(id=int(pgr_id)).first()
    #try:
    pgr.merge(int(request.form['mgr_id']))
    return make_response(jsonify({'msg': 'success'}), 200)
    #except Exception as e:
    #    return make_response(jsonify({'msg': str(e)}), 400)
