# -*- coding: utf-8 -*-

from lotus import db
from flask import redirect, url_for
from basismodels import PricingBundle, PricingAction
from decorators import is_logged_in, new_pageload, roles_required

from flask import Blueprint, render_template
from datetime import datetime

pricing = Blueprint('pricing_', __name__, static_folder='static', template_folder='templates')


@pricing.route('/')
@is_logged_in
@new_pageload
@roles_required('Admin')
def index():
    pr_bundles = PricingBundle.query.all()
    return render_template('pricing/pricing.html', pr_bundles=pr_bundles)


@pricing.route('/bundle/<pr_bundle_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def bundle(pr_bundle_id):
    if int(pr_bundle_id) == 0:
        pr_bundle = PricingBundle(init_dt=datetime.now(), name='')
        db.session.add(pr_bundle)
        db.session.commit()
        return redirect(url_for('settings.pricing_.bundle', pr_bundle_id=pr_bundle.id))
    pas = db.session.query(
        PricingAction.name
    ).filter(
        PricingAction.archived == False
    ).group_by(
        PricingAction.name
    ).all()
    pr_bundle = PricingBundle.query.filter_by(id=int(pr_bundle_id)).first()
    return render_template('pricing/pricing_bundle.html', pr_bundle=pr_bundle, pa_names=[pa_name for pa_name, in pas])
