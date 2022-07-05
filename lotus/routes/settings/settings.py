# -*- coding: utf-8 -*-

from flask import Blueprint
from .product import product
from .marketplace import marketplace
from .shipping import shipping
from .pricing import pricing
from decorators import is_logged_in, new_pageload, roles_required

from flask import render_template


settings = Blueprint('settings', __name__, static_folder='static', template_folder='templates')
settings.register_blueprint(product, url_prefix='/product')
settings.register_blueprint(marketplace, url_prefix='/marketplace')
settings.register_blueprint(shipping, url_prefix='/shipping')
settings.register_blueprint(pricing, url_prefix='/pricing')


@settings.route('/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def index():
    return render_template('index.html')
