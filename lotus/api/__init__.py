# -*- coding: utf-8 -*-

from flask import Blueprint
from .product import product
from .product_category import product_category
from .product_group import product_group
from .pricing import pricing
from .logistics import logistics


api = Blueprint('api', __name__)
api.register_blueprint(product, url_prefix='/product')
api.register_blueprint(product_category, url_prefix='/product_category')
api.register_blueprint(product_group, url_prefix='/product_group')
api.register_blueprint(pricing, url_prefix='/pricing')
api.register_blueprint(logistics, url_prefix='/logistics')

