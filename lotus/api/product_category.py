# -*- coding: utf-8 -*-

from lotus import csrf
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import ProductCategory

from flask import Blueprint, request, jsonify, make_response

product_category = Blueprint('product_category', __name__, url_prefix='/product_category')


@product_category.route('/patch', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def patch():
    data = request.get_json()
    print(data)
    p_cats = ProductCategory.query.filter(ProductCategory.id.in_([int(key) for key in data])).all()
    proc_ids = []
    for p_cat in p_cats:
        p_cat_data = data[str(p_cat.id)]
        try:
            r = p_cat.self_update(ship_days=p_cat_data['ship_days'] if 'ship_days' in p_cat_data else None, mp_data=p_cat_data['mp_data'] if 'mp_data' in p_cat_data else None)
            if r is True:
                proc_ids.append(p_cat.id)
        except Exception as e:
            print(e)
    return make_response(jsonify({'msg': 'success'}), 200)
