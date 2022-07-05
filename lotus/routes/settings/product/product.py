# -*- coding: utf-8 -*-

from lotus import db, csrf
from flask import Blueprint, render_template
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import Marketplace, Marketplace_ProductCategory, Stock, PrCatStock_Attr, ProductCategory, ProductCategory_ProductFeature, ProductLinkCategory, Product_ProductFeatureValue, ProductFeatureValue, ProductFeature, MPCategory, MPCat_PrCat

from flask import request, flash, redirect, url_for, jsonify
from sqlalchemy import func

product = Blueprint('product_', __name__, static_folder='static', template_folder='templates')


@product.route('/categories', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def categories():
    stock_lags = PrCatStock_Attr.query.order_by(
        PrCatStock_Attr.cat_id
    ).all()
    sl_dict = {}
    for sl in stock_lags:
        if sl.cat_id not in sl_dict:
            sl_dict[sl.cat_id] = {sl.stock_id: {'sl_id': sl.id, 'ship_days': sl.ship_days}}
        else:
            sl_dict[sl.cat_id][sl.stock_id] = {'sl_id': sl.id, 'ship_days': sl.ship_days}
    stocks = db.session.query(
        Stock
    ).order_by(
        Stock.id
    ).all()
    product_categories = ProductCategory.query.order_by(ProductCategory.name).all()
    if request.method == 'POST' and request.form['btn'] == 'add_category':
        if request.form['name'] != '' and request.form['ID'] != '':
            checkcategory = ProductCategory.query.filter_by(name=request.form['name']).first()
            if checkcategory:
                flash('Eine Kategorie mit diesem Namen existiert bereits.', 'danger')
            else:
                new_category = ProductCategory(request.form['ID'], request.form['name'])
                db.session.add(new_category)
                db.session.commit()
                return redirect(url_for('center_settings_products'))
        else:
            flash('Bitte fülle beide Felder aus.', 'danger')
    return render_template('product/categories.html', product_categories=product_categories, stocks=stocks, sl_dict=sl_dict)


@product.route('/category/<category_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def category(category_id):
    cat = ProductCategory.query.filter_by(id=int(category_id)).first()
    orphans = ProductCategory.query.filter(ProductCategory.parent_id == None).filter(ProductCategory.id!=category_id).all()
    successor_ids = [successor.id for successor in cat.get_successors()]
    adopt_parents = ProductCategory.query.filter(ProductCategory.id.notin_(successor_ids)).all()
    family_ids = [member.id for member in cat.get_family()]
    other_cats = ProductCategory.query.filter(ProductCategory.id.notin_(family_ids)).all()
    subquery = db.session.query(ProductCategory_ProductFeature.productfeature_id).filter(
        ProductCategory_ProductFeature.productcategory_id==int(category_id)
    ).all()
    poss_features = ProductFeature.query.filter(ProductFeature.id.notin_(subquery)).filter_by(source='lotus').order_by(ProductFeature.name).all()
    main_cats = ProductCategory.query.filter(ProductCategory.parent_id == None).order_by(ProductCategory.name).all()
    mps = Marketplace.query.all()
    mp_cats = {}
    mp_cat_pre_ids = {}
    mp_conn_ids = {}
    for mp in mps:
        mp_cats[mp.id] = MPCategory.query.filter(MPCategory.parent_id == None).filter(MPCategory.mp_id == mp.id).order_by(MPCategory.name).all()
        mp_cat_pre_ids[mp.id] = []
        mp_conn_ids[mp.id] = []
    query = db.session.query(
        ProductCategory, MPCat_PrCat, MPCategory
    ).filter(
        ProductCategory.id == MPCat_PrCat.pr_cat_id
    ).filter(
        MPCategory.id == MPCat_PrCat.mp_cat_id
    ).filter(
        ProductCategory.id == int(category_id)
    ).all()
    for _, _, mp_cat in query:
        mp_cat_pre_ids[mp_cat.mp_id] += [pre.id for pre in mp_cat.get_predecessors()]
        mp_conn_ids[mp_cat.mp_id].append(mp_cat.id)
    return render_template('product/category.html', category=cat, orphans=orphans, adopt_parents=adopt_parents, other_cats=other_cats, poss_features=poss_features, main_cats=main_cats, mps=mps, mp_cats=mp_cats,
                           mp_cat_pre_ids=mp_cat_pre_ids, mp_conn_ids=mp_conn_ids)


@product.route('/category/update_mp_codes/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@csrf.exempt
@new_pageload
@roles_required('Admin')
def category_update_mp_codes(category_id):
    cat = ProductCategory.query.filter_by(id=int(category_id)).first()
    mps = Marketplace.query.all()
    try:
        for mp in mps:
            mpc = Marketplace_ProductCategory.query.filter_by(marketplace_id=mp.id, productcategory_id=cat.id).first()
            if mpc is None:
                db.session.add(Marketplace_ProductCategory(request.form[f'mp_code_{ mp.id }'], mp.id, cat.id))
            else:
                mpc.marketplace_system_id = request.form[f'mp_code_{ mp.id }']
            db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': str(e)})


@product.route('/category/change_category/<category_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def category_change_category(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    subquery = db.session.query(ProductCategory_ProductFeature.productfeature_id).filter(
        ProductCategory_ProductFeature.productcategory_id==int(category_id)
    ).all()
    other_features = ProductFeature.query.filter(ProductFeature.id.notin_(subquery)).filter_by(source='lotus').all()
    own_feature_html = ''''''
    for feature in category.get_productfeatures():
        own_feature_html += f'''<div class="whitebutton" style="width: 100%; transition: 200ms">
        { feature.name }
        </div>'''
    own_feature_html += '''<div style="height: 25px; width: 100%"></div>'''
    other_feature_html = ''''''
    for feature in other_features:
        other_feature_html += f'''<div class="whitebutton" style="width: 100%; transition: 200ms">
        { feature.name }
        </div>'''
    other_feature_html += '''<div style="height: 25px; width: 100%"></div>'''
    return jsonify({'own_feature_html': own_feature_html, 'other_feature_html': other_feature_html})


@product.route('/category/edit_name/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def edit_category_name(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    category.name = request.form['name'].strip() if request.form['name'] else category.name
    db.session.commit()
    return redirect(url_for('category', category_id=category_id))


@product.route('/category/detach/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def detach_category(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    redirect_id = category.parent_id
    category.parent_id = None
    db.session.commit()
    return redirect(url_for('category', category_id=redirect_id))


@product.route('/category/detach_successors/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def detach_successors(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    redirect_id = category.parent_id
    for successor in category.get_successors():
        successor.parent_id = None
        db.session.commit()
    category.parent_id = None
    db.session.commit()
    return redirect(url_for('category', category_id=redirect_id))


@product.route('/category/adopt_child/<category_id>,<child_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def category_adopt_child(category_id, child_id):
    child = ProductCategory.query.filter_by(id=int(child_id)).first()
    child.parent_id = category_id
    db.session.commit()
    return redirect(url_for('category', category_id=category_id))


@product.route('/category/edit_parent/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def edit_category_parent(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    category.parent_id = int(request.form['category']) if request.form['category'] else category.parent_id
    db.session.commit()
    return redirect(url_for('category', category_id=category_id))


@product.route('/category/transfer_features/<category_id>,<transfer_cat_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def category_transfer_features(category_id, transfer_cat_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    for feat in category.productfeatures:
        db.session.delete(feat)
        db.session.commit()
    cfs = ProductCategory_ProductFeature.query.filter_by(productcategory_id=int(transfer_cat_id)).all()
    for cf in cfs:
        db.session.add(ProductCategory_ProductFeature(category.id, cf.productfeature_id))
        db.session.commit()
    return redirect(url_for('settings.product_.category', category_id=category_id))


@product.route('/category/detach_feature/<category_id>,<feature_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def category_detach_feature(category_id, feature_id):
    feature = ProductFeature.query.filter_by(id=int(feature_id)).first()
    check_cf = ProductCategory_ProductFeature.query.filter_by(productcategory_id=int(category_id), productfeature_id=int(feature_id)).first()
    if check_cf:
        db.session.delete(check_cf)
        db.session.commit()
    return jsonify({
        'status_code': 200,
        'feature_name': feature.name,
        'add_url': url_for('settings.product_.category_add_feature', category_id=category_id, feature_id=feature_id)
    })


@product.route('/category/add_feature/<category_id>,<feature_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def category_add_feature(category_id, feature_id):
    new_cf = ProductCategory_ProductFeature.query.filter_by(productcategory_id=int(category_id), productfeature_id=int(feature_id)).first()
    if not new_cf:
        new_cf = ProductCategory_ProductFeature(category_id, feature_id)
        db.session.add(new_cf)
        db.session.commit()
    return jsonify({
        'status_code': 200,
        'feature_name': new_cf.productfeature.name,
        'detach_url': url_for('settings.product_.category_detach_feature', category_id=category_id, feature_id=feature_id)
    })


@product.route('/features', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def features():
    product_features = ProductFeature.query.filter_by(source='lotus').order_by(ProductFeature.name).all()
    if request.method == 'POST' and request.form['btn'] == 'add_feature':
        if request.form['name'] != '' and request.form['ID'] != '':
            checkfeature = ProductFeature.query.filter_by(name=request.form['name'], source='lotus').first()
            if checkfeature:
                flash('Ein Attribut mit diesem Namen existiert bereits.', 'danger')
            else:
                new_feature = ProductFeature(request.form['ID'], request.form['name'], False)
                new_feature.source = 'lotus'
                db.session.add(new_feature)
                db.session.commit()
                return redirect(url_for('center_settings_products'))
        else:
            flash('Bitte fülle beide Felder aus.', 'danger')
    return render_template('product/features.html', product_features=product_features)


@product.route('/links', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def links():
    product_link_categories = ProductLinkCategory.query.order_by(ProductLinkCategory.name).all()
    if request.method == 'POST' and request.form['btn'] == 'add_link_category':
        if request.form['name'] != '':
            checkcategory = ProductLinkCategory.query.filter_by(name=request.form['name']).first()
            if checkcategory:
                flash('Eine Linkkategorie mit diesem Namen existiert bereits.', 'danger')
            else:
                new_category = ProductLinkCategory(request.form['name'])
                db.session.add(new_category)
                db.session.commit()
                return redirect(url_for('center_settings_products'))
        else:
            flash('Bitte fülle beide Felder aus.', 'danger')
    return render_template('product/links.html', product_link_categories=product_link_categories)


@product.route('/change_cat_feature/<cat_id>,<feature_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def change_cat_feature(cat_id, feature_id):
    cat_feature = ProductCategory_ProductFeature.query.filter_by(productcategory_id=int(cat_id), productfeature_id=int(feature_id)).first()
    if cat_feature:
        db.session.delete(cat_feature)
    else:
        db.session.add(ProductCategory_ProductFeature(cat_id, feature_id))
    db.session.commit()
    return jsonify({})


@product.route('/change_feature_active/<feature_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def change_settings_products_change_feature_active(feature_id):
    feature = ProductFeature.query.filter_by(id=int(feature_id)).first()
    if feature.active:
        feature.active = False
    else:
        feature.active = True
    db.session.commit()
    return jsonify({})


@product.route('/change_feature_fixed/<feature_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def change_settings_products_change_feature_fixed(feature_id):
    feature = ProductFeature.query.filter_by(id=int(feature_id)).first()
    if feature.fixed_values:
        feature.fixed_values = False
    else:
        feature.fixed_values = True
    db.session.commit()
    return jsonify({})


@product.route('/delete_feature/<feature_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def delete_feature(feature_id):
    feature = ProductFeature.query.filter_by(id=int(feature_id)).first()
    for entry in feature.values:
        db.session.delete(entry)
    db.session.delete(feature)
    db.session.commit()
    return redirect(url_for('center_product_settings'))


@product.route('/delete_linkcategory/<linkcategory_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def delete_linkcategory(linkcategory_id):
    cat = ProductLinkCategory.query.filter_by(id=int(linkcategory_id)).first()
    for link in cat.links:
        db.session.delete(link)
        db.session.commit()
    db.session.delete(cat)
    db.session.commit()
    return redirect(url_for('center_product_settings'))


@product.route('/activate_category/<productcategory_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def activate_category(productcategory_id):
    ProductCategory.query.filter_by(id=int(productcategory_id)).first().active = True
    db.session.commit()
    return redirect(url_for('center_product_settings'))


@product.route('/deactivate_category/<productcategory_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def deactivate_category(productcategory_id):
    ProductCategory.query.filter_by(id=int(productcategory_id)).first().active = False
    db.session.commit()
    return redirect(url_for('center_product_settings'))


@product.route('/featurevalues/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def featurevalues(id):
    feature = ProductFeature.query.filter_by(id=int(id)).first()
    values = feature.values
    values.sort(key=lambda x: x.value)
    if request.method == 'POST' and request.form['btn']=='value':
        if request.form['name'] != '':
            checkvalue = ProductFeatureValue.query.filter_by(value=request.form['name'], productfeature_id=feature.id).first()
            if checkvalue:
                flash('Ein Feature-Wert mit diesem Namen existiert bereits.', 'danger')
            else:
                new_value = ProductFeatureValue(request.form['name'], feature.id)
                db.session.add(new_value)
                db.session.commit()
                return redirect(url_for('featurevalues', id=id))
        else:
            flash('Bitte gib einen Namen an.', 'danger')
    return render_template('product/featurevalues.html', feature=feature, values=values)


@product.route('/edit_featurename/<id>', methods=['POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def edit_featurename(id):
    feature = ProductFeature.query.filter_by(id=int(id)).first()
    feature.name = request.form['name']
    db.session.commit()
    return redirect(url_for('featurevalues', id=id))


@product.route('/activate_featurevalue/<id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def activate_featurevalue(id):
    ProductFeatureValue.query.filter_by(id=int(id)).first().active = True
    db.session.commit()
    return redirect(url_for('featurevalues', id=ProductFeatureValue.query.filter_by(id=int(id)).first().productfeature_id))


@product.route('/deactivate_featurevalue/<id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def deactivate_featurevalue(id):
    ProductFeatureValue.query.filter_by(id=int(id)).first().active = False
    db.session.commit()
    return redirect(url_for('featurevalues', id=ProductFeatureValue.query.filter_by(id=int(id)).first().productfeature_id))


@product.route('/delete_featurevalue/<id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def delete_featurevalue(id):
    value = ProductFeatureValue.query.filter_by(id=int(id)).first()
    back_id = value.productfeature_id
    db.session.delete(value)
    db.session.commit()
    return redirect(url_for('featurevalues', id=back_id))


@product.route('/featurevalue/<value_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def featurevalue(value_id):
    value = ProductFeatureValue.query.filter_by(id=int(value_id)).first()
    ext_features = db.session.query(
        ProductFeature, ProductFeatureValue
    ).outerjoin(
        Product_ProductFeatureValue
    ).filter(
        ProductFeature.id==ProductFeatureValue.productfeature_id
    ).filter(
        ProductFeature.source!='lotus'
    ).filter(
        ProductFeatureValue.int_value_id==None
    ).having(
        func.count(Product_ProductFeatureValue.id) >= 5
    ).group_by(
        ProductFeature.id, ProductFeatureValue.id
    ).order_by(
        ProductFeature.source
    ).all()
    return render_template('product/featurevalue.html', value=value, ext_features=ext_features, first_id=ext_features[0][0].id)


@product.route('/edit_featurevalue/<value_id>', methods=['POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def edit_featurevalue(value_id):
    feature = ProductFeatureValue.query.filter_by(id=int(value_id)).first()
    feature.value = request.form['value']
    db.session.commit()
    return redirect(url_for('featurevalue', value_id=value_id))


@product.route('/connect_ext_featurevalues/<value_id>,<ext_value_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_connect_ext_featurevalues(value_id, ext_value_id):
    ext_value = ProductFeatureValue.query.filter_by(id=int(ext_value_id)).first()
    ext_value.int_value_id = int(value_id)
    db.session.commit()
    return jsonify({'featurevalue': ext_value.value, 'feature': ext_value.productfeature.name})


@product.route('/disconnect_ext_featurevalues/<ext_value_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_disconnect_ext_featurevalues(ext_value_id):
    ext_value = ProductFeatureValue.query.filter_by(id=int(ext_value_id)).first()
    ext_value.int_value_id = None
    db.session.commit()
    return jsonify({'featurevalue': ext_value.value, 'feature': ext_value.productfeature.name})
