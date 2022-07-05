# -*- coding: utf-8 -*-

from lotus import db
from flask import Blueprint, render_template
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import Marketplace, ProductLinkCategory, Product, Marketplace_Product_Attributes

from flask import request, flash, redirect, url_for

marketplace = Blueprint('marketplace', __name__, static_folder='static', template_folder='templates')


@marketplace.route('/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def index():
    mps = Marketplace.query.all()
    productlinkcategories = ProductLinkCategory.query.filter_by(active=True).all()
    if request.method == 'POST':
        if request.form['name'] != '':
            check_marketplace = Marketplace.query.filter_by(name=request.form['name']).first()
            if check_marketplace:
                flash('Eine Marketplace mit diesem Namen existiert bereits.', 'danger')
            else:
                new_marketplace = Marketplace(request.form['name'], request.form['link'])
                link_category_id = int(request.form['productlinkcategory'])
                if link_category_id != 0:
                    new_marketplace.productlinkcategory_id = link_category_id
                db.session.add(new_marketplace)
                db.session.commit()
                products = Product.query.all()
                for product in products:
                    db.session.add(Marketplace_Product_Attributes(new_marketplace.id, product.id))
                    db.session.commit()
                return redirect(url_for('center_settings_marketplaces'))
        else:
            flash('Bitte gib einen Namen an', 'danger')
    return render_template('marketplace/marketplace.html', marketplaces=mps, productlinkcategories=productlinkcategories)
