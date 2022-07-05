# -*- coding: utf-8 -*-

from flask import Blueprint
from .ws_order import ws_order
from .stock_receipt import stock_receipt
from .ws_receipt import ws_receipt
from .ws_invoice import ws_invoice

logistics = Blueprint('logistics', __name__)
logistics.register_blueprint(ws_order, url_prefix='/ws_order')
logistics.register_blueprint(stock_receipt, url_prefix='/stock_receipt')
logistics.register_blueprint(ws_receipt, url_prefix='/ws_receipt')
logistics.register_blueprint(ws_invoice, url_prefix='/ws_invoice')
