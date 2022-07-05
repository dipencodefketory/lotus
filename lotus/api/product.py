# -*- coding: utf-8 -*-

from lotus import db, csrf
from basismodels import (Product, Product_ProductFeatureValue, ProductFeatureValue, ProductFeature, Marketplace_Product_Attributes, Marketplace_Product_Attributes_Description, Marketplace,
                         PPrRule, PricingRule)
from decorators import is_logged_in, new_pageload, roles_required
import routines
from lookup import version_normalizer_dict
from functions import split_string

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime

product = Blueprint('product', __name__, url_prefix='/product')


@product.route('/get', methods=['GET'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def get():
    query = db.session.query(
        Product, Product_ProductFeatureValue, ProductFeatureValue, ProductFeature
    ).filter(
        Product.id == Product_ProductFeatureValue.product_id
    ).filter(
        Product_ProductFeatureValue.productfeaturevalue_id == ProductFeatureValue.id
    ).filter(
        ProductFeatureValue.productfeature_id == ProductFeature.id
    ).filter(
        ProductFeature.sourcve == 'lotus'
    ).order_by(
        Product.id, ProductFeature.id
    ).all()
    data = []
    seen_p_ids = []
    p_data = {}
    seen_pf_ids = []
    pf_data = {}
    for p, _, pfv, pf in query + [(None, None, None, None)]:
        if p is not None:
            if p.id not in seen_p_ids:
                if seen_p_ids:
                    data.append(p_data)
                seen_p_ids.append(p.id)
                p_data = {'p_id': p.id, 'p_internal_id': p.internal_id, 'p_hsp_id': p.hsp_id, 'p_name': p.name, 'features': []}
                seen_pf_ids = [pf.id]
                pf_data = {'pf_id': pf.id, 'pf_name': pf.name, 'values': [pfv.value]}
            else:
                if pf.name in seen_pf_ids:
                    pf_data['values'].append(pfv.value)
                else:
                    p_data['features'].append(pf_data)
                    seen_pf_ids = [pf.id]
                    pf_data = {'pf_id': pf.id, 'pf_name': pf.name, 'values': [pfv.value]}
        else:
            p_data['features'].append(pf_data)
    return jsonify({})


@product.route('/patch', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def patch():
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
    data = request.get_json()
    ps = Product.query.filter(Product.id.in_([int(key) for key in data])).all()
    proc_ids = []
    for p in ps:
        p_data = data[str(p.id)]
        try:
            p.name = p_data['name'] if p_data['name'] is not None else p.name if 'name' in p_data else p.name
            p.mpn = p_data['mpn'] if p_data['mpn'] is not None else p.mpn
            p.brand = p_data['brand'] if p_data['brand'] is not None else p.brand
            p.spec_trait_0 = p_data['spec_trait_0'] if p_data['spec_trait_0'] is not None else p.spec_trait_0
            p.spec_trait_1 = p_data['spec_trait_1'] if p_data['spec_trait_1'] is not None else p.spec_trait_1
            p.spec_trait_2 = p_data['spec_trait_2'] if p_data['spec_trait_2'] is not None else p.spec_trait_2
            p.spec_trait_3 = p_data['spec_trait_3'] if p_data['spec_trait_3'] is not None else p.spec_trait_3
            p.length = p_data['length'] if p_data['length'] else p.length
            p.width = p_data['width'] if p_data['width'] else p.width
            p.height = p_data['height'] if p_data['height'] else p.height
            p.weight = p_data['weight'] if p_data['weight'] else p.weight
            p.release_date = p_data['release_date'] if p_data['release_date'] is not None else p.release_date
            p.main_group_id = p_data['main_group_id'] if p_data['main_group_id'] is not None else p.main_group_id
            p.category_id = p_data['category_id'] if p_data['category_id'] is not None else p.category_id
            if 'pricing_bundle_id' in p_data:
                p.pricing_bundle_id = p_data['pricing_bundle_id'] if p_data['pricing_bundle_id'] not in ['', None] else p.pricing_bundle_id
            db.session.commit()
            if p_data['features']:
                pf_ids = [int(pf_id) for pf_id in p_data['features'] ]
                pfs = ProductFeature.query.filter(ProductFeature.id.in_(pf_ids)).all()
                for pf in pfs:
                    vals = p_data['features'][str(pf.id)]
                    checkvalues = pf.get_value_product(p.id)
                    if checkvalues:
                        for checkvalue in checkvalues:
                            connection = Product_ProductFeatureValue.query.filter_by(product_id=p.id, productfeaturevalue_id=checkvalue.id).first()
                            if connection:
                                db.session.delete(connection)
                                db.session.commit()
                    if vals != '':
                        vals = split_string(vals, [',', ';']).replace(',', ';').split(';')
                        for featurevalue in vals:
                            checkfeaturevalue = ProductFeatureValue.query.filter_by(productfeature_id=pf.id, value=featurevalue).first()
                            if checkfeaturevalue:
                                new_connection = Product_ProductFeatureValue(p.id, checkfeaturevalue.id)
                                db.session.add(new_connection)
                                db.session.commit()
                            else:
                                new_pfv = ProductFeatureValue(featurevalue, pf.id)
                                db.session.add(new_pfv)
                                db.session.commit()
                                new_connection = Product_ProductFeatureValue(p.id, new_pfv.id)
                                db.session.add(new_connection)
                                db.session.commit()
            if p_data['descriptions']:
                ebay = Marketplace.query.filter_by(name='Ebay').first()
                mpa = Marketplace_Product_Attributes.query.filter_by(product_id=p.id, marketplace_id=ebay.id).first()
                descrs = list(sorted(mpa.descriptions, key=lambda descr: descr.position))
                while len(descrs) < 4:
                    d = Marketplace_Product_Attributes_Description(len(descrs), '', mpa.id)
                    descrs.insert(-1, d)
                    descrs[-1].position = 4
                    db.session.add(d)
                    db.session.commit()
                update_pos = [int(pos) for pos in p_data['descriptions']]
                max_pos = max(update_pos)
                if len(descrs) < max_pos:
                    for i in range(max_pos):
                        if len(descrs) < i + 1:
                            db.session.add(Marketplace_Product_Attributes_Description(i + 1, p_data['descriptions'][str(i + 1)] if str(i + 1) in p_data['descriptions'] else '', mpa.id))
                        elif str(i + 1) in p_data['descriptions']:
                            descrs[i].text = p_data['descriptions'][str(i + 1)]
                else:
                    for pos in update_pos:
                        descrs[pos - 1].text = p_data['descriptions'][str(pos)]
                db.session.commit()
            proc_ids.append(p.id)
        except Exception as e:
            print(e)
    return make_response(jsonify({'proc': proc_ids}), 200)


@product.route('/complete_basic_data', methods=['PATCH'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management', 'Produkt-Marketing')
def complete_basic_data():
    """
    receives a list of product-ids via request.get_json(), which should be processed.
    :return:
    """
    p_ids = request.get_json()
    ps = Product.query.filter(Product.id.in_([int(p_id) for p_id in p_ids])).all()
    proc_ids = []
    for p in ps:
        try:
            if p.spec_trait_0:
                p.name = p.spec_trait_0
                p.name += f' - {p.spec_trait_1}' if p.spec_trait_1 else ''
                p.name += f' - {p.spec_trait_2}' if p.spec_trait_2 else ''
                p.name += f' - {p.spec_trait_3}' if p.spec_trait_3 else ''
            for mpa in p.marketplace_attributes:
                mpa.name = p.spec_trait_0 if p.spec_trait_0 else p.name
                mpa.name += f' - {p.spec_trait_1}' if p.spec_trait_1 else ''
                mpa.name += f' - {p.spec_trait_2}' if p.spec_trait_2 else ''
                mpa.name += ' - Neu & OVP'
                mpa.name += f' - {version_normalizer_dict[p.spec_trait_3]}' if p.spec_trait_3 in version_normalizer_dict else ''
                if mpa.marketplace.id == 1:
                    if p.spec_trait_3 in ['AT', 'EU', 'UK', 'Nordic', 'PEGI', 'AUS'] and p.category_id == 1:
                        if p.spec_trait_3 in ['UK', 'AUS']:
                            mpa.name += f' - Englisches Cover'
                        else:
                            mpa.name += f' - {p.spec_trait_3} Cover'
                    if p.release_date:
                        if p.release_date > datetime.now():
                            mpa.name += ' - Release: ' + datetime.strftime(p.release_date, '%d.%m.%Y')
            db.session.commit()
            usk = False
            usk_val = ''
            insert_list = []
            for value in p.get_ext_featurevalues():
                if value.int_value_id:
                    insert_list.append(value.int_value_id)
            for key in insert_list:
                featurevalue = ProductFeatureValue.query.filter_by(id=key).first()
                if featurevalue.productfeature.name == 'USK-Einstufung':
                    usk = True
                    usk_val = featurevalue.value.split(' ')[-1]
            routines.ebay_description_generator(p, '', usk, usk_val, suppress_mid=True)
            proc_ids.append(p.id)
        except Exception as e:
            print(e)
    return make_response(jsonify({'proc': proc_ids}), 200)
