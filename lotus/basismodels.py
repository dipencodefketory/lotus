from lotus import db, tax_group, env_vars_path
from datetime import *
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from functions import *
from lookup import ebay_ff_policy_ids
from sqlalchemy import func, case, or_, and_
from sqlalchemy.orm import backref
import math
from ebaysdk.finding import Connection as Finding_Connection
from ebaysdk.trading import Connection as Trading_Connection
from requests.auth import HTTPBasicAuth
import requests
import xml.etree.ElementTree as ETree
from ext.marketplace import shopify
import idealo_offer
import ebay_api
import afterbuy_api
# from mpAPIs.magento import post_product, post_category
import base64
import os
from os import environ
from dotenv import load_dotenv, set_key
from typing import Union
import lookup
import re

load_dotenv(env_vars_path)


class Region(db.Model):
    __tablename__ = "region"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(60))
    abbr = db.Column(db.String(8))

    countries = db.relationship("Country", backref="region", lazy="select")

    def __init__(self, name: str, abbr: str):
        if type(name) != str:
            raise TypeError('Variable name must be of type str.')
        if type(abbr) != str:
            raise TypeError('Variable abbr must be of type str.')
        if len(name) > 60:
            raise ValueError('Variable name can not have more than 60 characters.')
        if len(abbr) > 8:
            raise ValueError('Variable abbr can not have more than 8 characters.')
        self.init_dt = datetime.now()
        self.name = name
        self.abbr = abbr


class Country(db.Model):
    __tablename__ = "country"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(60))
    iso_2 = db.Column(db.String(2))
    iso_3 = db.Column(db.String(3))
    iso_num = db.Column(db.String(3))
    domain = db.Column(db.String(3))

    region_id = db.Column(db.Integer, db.ForeignKey("region.id"))

    def __init__(self, name: str, iso_2: str, iso_3: str, iso_num: str, domain: str, region_id: int = None):
        if type(name) != str:
            raise TypeError('Variable name must be of type str.')
        if type(iso_2) != str:
            raise TypeError('Variable iso_2 must be of type str.')
        if type(iso_3) != str:
            raise TypeError('Variable iso_3 must be of type str.')
        if type(iso_num) != str:
            raise TypeError('Variable iso_num must be of type str.')
        if type(domain) != str:
            raise TypeError('Variable domain must be of type str.')
        if region_id is not None and type(region_id) != int:
            raise TypeError('Optional variable region_id must be of type int.')
        if len(name) > 60:
            raise ValueError('Variable name can not have more than 60 characters.')
        if len(iso_2) > 2:
            raise ValueError('Variable iso_2 can not have more than 2 characters.')
        if len(iso_3) > 3:
            raise ValueError('Variable iso_3 can not have more than 3 characters.')
        if len(iso_num) > 3:
            raise ValueError('Variable iso_num can not have more than 3 characters.')
        if len(domain) > 3:
            raise ValueError('Variable domain can not have more than 3 characters.')
        if region_id is not None:
            region = Region.query.filter_by(id=region_id).first()
            if region is None:
                raise ValueError(f'No region with id {region_id} found.')
        self.init_dt = datetime.now()
        self.name = name
        self.iso_2 = iso_2
        self.iso_3 = iso_3
        self.iso_num = iso_num
        self.domain = domain
        self.region_id = region_id


class SSRAttr(db.Model):
    __tablename__ = "ssr_attr"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    ship_days = db.Column(db.Integer)
    add_cost = db.Column(db.Float)
    not_ = db.Column(db.Boolean)

    region_id = db.Column(db.Integer, db.ForeignKey("region.id"))
    shipping_service_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))

    def __init__(self, ship_days: int, add_cost: float, not_: bool, region_id: int, shipping_service_id: int):
        if type(ship_days) != int:
            raise TypeError('Variable ship_days must be of type int.')
        if type(add_cost) != float:
            raise TypeError('Variable add_cost must be of type float.')
        if type(not_) != bool:
            raise TypeError('Variable not_ must be of type bool.')
        if type(region_id) != int:
            raise TypeError('Variable region_id must be of type int.')
        if type(shipping_service_id) != int:
            raise TypeError('Variable shipping_service_id must be of type int.')
        region = Region.query.filter_by(id=region_id).first()
        if region is None:
            raise ValueError(f'No region with id {region_id} found.')
        shs = ShippingService.query.filter_by(id=shipping_service_id).first()
        if shs is None:
            raise ValueError(f'No shipping-service with id {shipping_service_id} found.')
        self.init_dt = datetime.now()
        self.ship_days = ship_days
        self.add_cost = add_cost
        self.not_ = not_
        self.region_id = region_id
        self.shipping_service_id = shipping_service_id


class SSCAttr(db.Model):
    __tablename__ = "ssc_attr"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    ship_days = db.Column(db.Integer)
    add_cost = db.Column(db.Float)
    not_ = db.Column(db.Boolean)

    country_id = db.Column(db.Integer, db.ForeignKey("country.id"))
    shipping_service_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))

    def __init__(self, ship_days: int, add_cost: float, not_: bool, country_id: int, shipping_service_id: int):
        if type(ship_days) != int:
            raise TypeError('Variable ship_days must be of type int.')
        if type(add_cost) != float:
            raise TypeError('Variable add_cost must be of type float.')
        if type(not_) != bool:
            raise TypeError('Variable not_ must be of type bool.')
        if type(country_id) != int:
            raise TypeError('Variable country_id must be of type int.')
        if type(shipping_service_id) != int:
            raise TypeError('Variable shipping_service_id must be of type int.')
        country = Country.query.filter_by(id=country_id).first()
        if country is None:
            raise ValueError(f'No country with id {country_id} found.')
        shs = ShippingService.query.filter_by(id=shipping_service_id).first()
        if shs is None:
            raise ValueError(f'No shipping-service with id {shipping_service_id} found.')
        self.init_dt = datetime.now()
        self.ship_days = ship_days
        self.add_cost = add_cost
        self.not_ = not_
        self.country_id = country_id
        self.shipping_service_id = shipping_service_id


class ImageProcJob(db.Model):
    __tablename__ = "image_proc_job"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)
    proc_dt = db.Column(db.DateTime)

    prefix = db.Column(db.String(50))
    digits = db.Column(db.Integer)
    min_int = db.Column(db.Integer)
    max_int = db.Column(db.Integer)
    suffix = db.Column(db.String(50))
    ok = db.Column(db.Boolean)

    results = db.relationship("IPJResults", backref="ipj", lazy="select")

    def __init__(self, prefix: str, digits: int, min_int: int, max_int: int, suffix: str):
        if type(prefix) != str:
            raise TypeError('Variable prefix must be of type str.')
        if type(digits) != int:
            raise TypeError('Variable digits must be of type int.')
        if type(min_int) != int:
            raise TypeError('Variable min_int must be of type int.')
        if type(max_int) != int:
            raise TypeError('Variable max_int must be of type int.')
        if type(suffix) != str:
            raise TypeError('Variable suffix must be of type str.')
        self.init_dt = datetime.now()
        self.prefix = prefix
        self.digits = digits
        self.min_int = min_int
        self.max_int = max_int
        self.suffix = suffix


class IPJResults(db.Model):
    __tablename__ = "ipj_results"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    filename = db.Column(db.String(200))
    msg = db.Column(db.String)
    ok = db.Column(db.Boolean)

    ipj_id = db.Column(db.Integer, db.ForeignKey("image_proc_job.id"))

    def __init__(self, filename: str, msg: str, ok: bool, ipj_id: int):
        if type(filename) != str:
            raise TypeError('Variable filename must be of type str.')
        if type(msg) != str:
            raise TypeError('Variable msg must be of type str.')
        if type(ok) != bool:
            raise TypeError('Variable ok must be of type bool.')
        if type(ipj_id) != int:
            raise TypeError('Variable ipj_id must be of type int.')
        self.init_dt = datetime.now()
        self.filename = filename
        self.msg = msg
        self.ok = ok
        self.ipj_id = ipj_id


class ProductUpdateLog(db.Model):
    __tablename__ = "product_update_log"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    url = db.Column(db.String)
    method = db.Column(db.String)
    data = db.Column(db.String)
    response = db.Column(db.String)
    status_code = db.Column(db.Integer)

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))

    def __init__(self, url: str, method: str, data: str, response: str, status_code: int, product_id: int = None, marketplace_id: int = None):
        if type(url) != str:
            raise TypeError('Variable url must be of type str.')
        if type(method) != str:
            raise TypeError('Variable method must be of type str.')
        if type(data) != str:
            raise TypeError('Variable data must be of type str.')
        if type(response) != str:
            raise TypeError('Variable response must be of type str.')
        if type(status_code) != int:
            raise TypeError('Variable status_code must be of type int.')
        if product_id is not None and type(product_id) != int:
            raise TypeError('Optional variable product_id must be of type int.')
        if marketplace_id is not None and type(marketplace_id) != int:
            raise TypeError('Optional variable marketplace_id must be of type int.')
        self.init_date = datetime.now()
        self.url = url
        self.method = method
        self.data = data
        self.response = response
        self.status_code = status_code
        self.product_id = product_id
        self.marketplace_id = marketplace_id


class DailyReport(db.Model):
    __tablename__ = "daily_report"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    sellable = db.Column(db.Integer)
    pos_stock = db.Column(db.Integer)
    short_sell = db.Column(db.Integer)
    pre_order = db.Column(db.Integer)
    proc_prods = db.Column(db.Integer)
    to_conf_prods = db.Column(db.Integer)
    conf_prods = db.Column(db.Integer)

    mp_reports = db.relationship("MPReport", backref="daily_report", lazy="select")
    ws_reports = db.relationship("WSReport", backref="daily_report", lazy="select")

    def __init__(self, sellable: int, pos_stock: int, short_sell: int, pre_order: int, proc_prods: int, to_conf_prods: int, conf_prods: int):
        if type(sellable) != int:
            raise TypeError('Variable sellable must be of type int.')
        if type(pos_stock) != int:
            raise TypeError('Variable pos_stock must be of type int.')
        if type(short_sell) != int:
            raise TypeError('Variable short_sell must be of type int.')
        if type(pre_order) != int:
            raise TypeError('Variable pre_order must be of type int.')
        if type(proc_prods) != int:
            raise TypeError('Variable proc_prods must be of type int.')
        if type(to_conf_prods) != int:
            raise TypeError('Variable to_conf_prods must be of type int.')
        if type(conf_prods) != int:
            raise TypeError('Variable conf_prods must be of type int.')
        self.sellable = sellable
        self.pos_stock = pos_stock
        self.short_sell = short_sell
        self.pre_order = pre_order
        self.proc_prods = proc_prods
        self.to_conf_prods = to_conf_prods
        self.conf_prods = conf_prods
        self.init_date = datetime.now()


class PrActionReport(db.Model):
    __tablename__ = "pr_action_report"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    name = db.Column(db.String(100))
    num_active = db.Column(db.Integer)
    num_sales = db.Column(db.Integer)

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))

    def __init__(self, name: str, num_active: int, num_sales: int, marketplace_id: int, init_date: datetime = None):
        if type(name) != str:
            raise TypeError('Variable name must be of type str.')
        if type(num_active) != int:
            raise TypeError('Variable num_active must be of type int.')
        if type(num_sales) != int:
            raise TypeError('Variable num_sales must be of type int.')
        if type(marketplace_id) != int:
            raise TypeError('Variable marketplace_id must be of type int.')
        if len(name) > 100:
            raise ValueError('Variable name can not have more than 100 characters.')
        self.init_date = init_date if init_date is not None else datetime.now()
        self.name = name
        self.num_active = num_active
        self.num_sales = num_sales
        self.marketplace_id = marketplace_id


class SalesReport(db.Model):
    __tablename__ = "sales_report"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    num_sales = db.Column(db.Integer)
    num_own = db.Column(db.Integer)
    num_short_sell = db.Column(db.Integer)
    num_pre_order = db.Column(db.Integer)

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))

    def __init__(self, num_sales: int, num_own: int, num_short_sell: int, num_pre_order: int, marketplace_id: int, init_date: datetime = None):
        if type(num_sales) != int:
            raise TypeError('Variable num_sales must be of type int.')
        if type(num_own) != int:
            raise TypeError('Variable num_own must be of type int.')
        if type(num_short_sell) != int:
            raise TypeError('Variable num_short_sell must be of type int.')
        if type(num_pre_order) != int:
            raise TypeError('Variable num_pre_order must be of type int.')
        if type(marketplace_id) != int:
            raise TypeError('Variable marketplace_id must be of type int.')
        self.init_date = init_date if init_date is not None else datetime.now()
        self.num_sales = num_sales
        self.num_own = num_own
        self.num_short_sell = num_short_sell
        self.num_pre_order = num_pre_order
        self.marketplace_id = marketplace_id


class MPReport(db.Model):
    __tablename__ = "mp_report"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    est_uploaded = db.Column(db.Integer)
    est_active = db.Column(db.Integer)
    est_active_short_sell = db.Column(db.Integer)
    est_active_pre_order = db.Column(db.Integer)
    est_inactive = db.Column(db.Integer)
    uploaded = db.Column(db.Integer)
    active = db.Column(db.Integer)
    active_short_sell = db.Column(db.Integer)
    active_pre_order = db.Column(db.Integer)
    inactive = db.Column(db.Integer)

    daily_report_id = db.Column(db.Integer, db.ForeignKey("daily_report.id"))
    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))

    def __init__(self, est_uploaded: int, est_active: int, est_active_short_sell: int, est_active_pre_order: int, est_inactive: int, uploaded: int, active: int, active_short_sell: int, active_pre_order: int, inactive: int,
                 marketplace_id: int, daily_report_id: int = None):
        if type(est_uploaded) != int:
            raise TypeError('Variable est_uploaded must be of type int.')
        if type(est_active) != int:
            raise TypeError('Variable est_active must be of type int.')
        if type(est_active_short_sell) != int:
            raise TypeError('Variable est_active_short_sell must be of type int.')
        if type(est_active_pre_order) != int:
            raise TypeError('Variable est_active_pre_order must be of type int.')
        if type(est_inactive) != int:
            raise TypeError('Variable est_inactive must be of type int.')
        if type(uploaded) != int:
            raise TypeError('Variable uploaded must be of type int.')
        if type(active) != int:
            raise TypeError('Variable active must be of type int.')
        if type(active_short_sell) != int:
            raise TypeError('Variable active_short_sell must be of type int.')
        if type(active_pre_order) != int:
            raise TypeError('Variable active_pre_order must be of type int.')
        if type(inactive) != int:
            raise TypeError('Variable inactive must be of type int.')
        if type(marketplace_id) != int:
            raise TypeError('Variable marketplace_id must be of type int.')
        if daily_report_id is not None and type(daily_report_id) != int:
            raise TypeError('Optional variable daily_report_id must be of type int.')
        if daily_report_id is not None:
            dr = DailyReport.query.filter_by(id=daily_report_id).first()
            if dr is None:
                raise SystemError(f'No daily report found with id {daily_report_id}.')
        self.init_date = datetime.now()
        self.est_uploaded = est_uploaded
        self.est_active = est_active
        self.est_active_short_sell = est_active_short_sell
        self.est_active_pre_order = est_active_pre_order
        self.est_inactive = est_inactive
        self.uploaded = uploaded
        self.active = active
        self.active_short_sell = active_short_sell
        self.active_pre_order = active_pre_order
        self.inactive = inactive
        self.marketplace_id = marketplace_id
        self.daily_report_id = daily_report_id


class WSReport(db.Model):
    __tablename__ = "ws_report"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    num_all = db.Column(db.Integer)
    num_pos_stock = db.Column(db.Integer)
    num_pre_order = db.Column(db.Integer)
    num_imp = db.Column(db.Integer)
    num_imp_pos_stock = db.Column(db.Integer)
    num_imp_pre_order = db.Column(db.Integer)

    daily_report_id = db.Column(db.Integer, db.ForeignKey("daily_report.id"))
    wholesaler_id = db.Column(db.Integer, db.ForeignKey("wholesaler.id"))

    def __init__(self, num_all: int, num_pos_stock: int, num_pre_order: int, num_imp: int, num_imp_pos_stock: int, num_imp_pre_order: int, wholesaler_id: int, daily_report_id: int = None):
        if type(num_all) != int:
            raise TypeError('Variable num_all must be of type int.')
        if type(num_pos_stock) != int:
            raise TypeError('Variable num_pos_stock must be of type int.')
        if type(num_pre_order) != int:
            raise TypeError('Variable num_pre_order must be of type int.')
        if type(num_imp) != int:
            raise TypeError('Variable num_imp must be of type int.')
        if type(num_imp_pos_stock) != int:
            raise TypeError('Variable num_imp_pos_stock must be of type int.')
        if type(num_imp_pre_order) != int:
            raise TypeError('Variable num_imp_pre_order must be of type int.')
        if type(wholesaler_id) != int:
            raise TypeError('Variable wholesaler_id must be of type int.')
        if wholesaler_id is not None:
            ws = Wholesaler.query.filter_by(id=wholesaler_id).first()
            if ws is None:
                raise SystemError(f'No wholesaler found with id {wholesaler_id}.')
        if daily_report_id is not None and type(daily_report_id) != int:
            raise TypeError('Optional variable daily_report_id must be of type int.')
        if daily_report_id is not None:
            dr = DailyReport.query.filter_by(id=daily_report_id).first()
            if dr is None:
                raise SystemError(f'No daily report found with id {daily_report_id}.')
        self.init_date = datetime.now()
        self.num_all = num_all
        self.num_pos_stock = num_pos_stock
        self.num_pre_order = num_pre_order
        self.num_imp = num_imp
        self.num_imp_pos_stock = num_imp_pos_stock
        self.num_imp_pre_order = num_imp_pre_order
        self.wholesaler_id = wholesaler_id
        self.daily_report_id = daily_report_id


class Wholesaler(db.Model):
    __tablename__ = "wholesaler"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    name = db.Column(db.String(80))

    reports = db.relationship("WSReport", backref="wholesaler", lazy="select")

    def __init__(self, name):
        if type(name) != str:
            raise TypeError('Variable name must be of type str.')
        if len(name) > 80:
            raise ValueError('Variable name can not have more than 80 characters.')
        self.init_date = datetime.now()
        self.name = name


class SystemAction(db.Model):
    __tablename__ = "systemaction"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    system_action = db.Column(db.Boolean)
    action = db.Column(db.String)
    vesiontable_name = db.Column(db.String)
    row_id = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, system_action, action):
        self.init_date = datetime.now()
        self.system_action = system_action
        self.action = action


class Workday(db.Model):
    __tablename__ = "workday"
    id = db.Column(db.Integer, primary_key=True)

    check_in_datetime = db.Column(db.DateTime)
    check_in_ip = db.Column(db.String(15))
    check_out_datetime = db.Column(db.DateTime)
    check_out_ip = db.Column(db.String(15))
    sick_leave = db.Column(db.Boolean)
    vaca_leave = db.Column(db.Boolean)
    holiday = db.Column(db.Boolean)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, check_in_ip: str, user_id: int, check_in_datetime: datetime = None, check_out_datetime: datetime = None, check_out_ip: str = None, sick_leave: bool = False, vaca_leave: bool = False, holiday: bool = False):
        if type(check_in_ip) != str:
            raise TypeError('Variable check_in_ip must be of type str.')
        elif type(user_id) != int:
            raise TypeError('Variable user_id must be of type int.')
        elif check_in_datetime != None and type(check_in_datetime) != datetime:
            raise TypeError('Variable check_in_datetime must be of type datetime.')
        elif check_out_datetime != None and type(check_out_datetime) != datetime:
            raise TypeError('Variable check_out_datetime must be of type datetime.')
        elif check_out_ip != None and type(check_out_ip) != str:
            raise TypeError('Variable check_out_ip must be of type str.')
        elif type(sick_leave) != bool:
            raise TypeError('Variable sick_leave must be of type bool.')
        elif type(vaca_leave) != bool:
            raise TypeError('Variable vaca_leave must be of type bool.')
        elif type(holiday) != bool:
            raise TypeError('Variable holiday must be of type bool.')
        else:
            check_user = User.query.filter_by(id=user_id).first()
            if not check_user:
                raise ValueError(f'No user found with id {user_id}')
            self.check_in_datetime = check_in_datetime if check_in_datetime is not None else datetime.now()
            self.check_out_datetime = check_out_datetime
            self.check_out_ip = check_out_ip
            self.check_in_ip = check_in_ip
            self.user_id = user_id
            self.sick_leave = sick_leave
            self.vaca_leave = vaca_leave
            self.holiday = holiday
            if check_out_datetime is not None:
                check_po = Payout.query.filter(Payout.start<=check_in_datetime).filter(Payout.end>=check_out_datetime).filter_by(user_id=user_id).first()
                if check_po:
                    check_po.time_balance += self.get_duration().total_seconds()
                    db.session.commit()
                    fol_pos = Payout.query.filter(Payout.start>check_po.end).filter_by(user_id=user_id).all()
                    for po in fol_pos:
                        po.time_balance += self.get_duration().total_seconds()
                        db.session.commit()

    def get_duration(self):
        if self.check_in_datetime is not None and self.check_out_datetime is not None:
            delta = self.check_out_datetime - self.check_in_datetime
            if delta.seconds <= 1800:
                return delta
            elif delta.seconds <= 21600:
                return delta - timedelta(hours=.5)
            else:
                return delta - timedelta(hours=1)
        else:
            return timedelta(hours=0)


class Payout(db.Model):
    __tablename__ = "payout"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    hours = db.Column(db.Float)
    time_balance = db.Column(db.Integer)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, hours: float, start: datetime, end: datetime, user_id: int):
        if type(hours) != float:
            raise TypeError('Variable hours must be of type float.')
        if type(start) != datetime:
            raise TypeError('Variable start must be of type datetime.')
        if type(end) != datetime:
            raise TypeError('Variable end must be of type datetime.')
        if type(user_id) != int:
            raise TypeError('Variable user_id must be of type int.')
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        if end <= start:
            raise ValueError('Start and end result in an empty time-intervall.')
        check_start_po = Payout.query.filter(Payout.start <= start).filter(Payout.end >= start).filter_by(user_id=user_id).first()
        check_end_po = Payout.query.filter(Payout.start <= end).filter(Payout.end >= end).filter_by(user_id=user_id).first()
        if check_end_po is not None or check_start_po is not None:
            raise SystemError("Found payout with overlapping time-intervalls. Make sure start and end are valid.")
        last_po = Payout.query.filter(Payout.end < start).order_by(Payout.end.desc()).filter_by(user_id=user_id).first()
        if last_po:
            balance = last_po.time_balance
        else:
            balance = 0
        wdays = Workday.query.filter(Workday.check_in_datetime >= start).filter(Workday.check_out_datetime <= end).filter_by(user_id=user_id).all()
        dur = sum([wd.get_duration() for wd in wdays], timedelta()).total_seconds()
        self.init_date = datetime.now()
        self.start = start
        self.end = end
        self.hours = hours
        self.user_id = user_id
        self.time_balance = balance - hours*3600 + dur
        fol_pos = Payout.query.filter(Payout.start > start).filter_by(user_id=user_id).all()
        for fol_po in fol_pos:
            fol_po.time_balance += dur - hours*3600
            db.session.commit()


class UserPageload(db.Model):
    __tablename__ = "user_pageload"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    url = db.Column(db.String)
    ip = db.Column(db.String(15))

    session_id = db.Column(db.Integer, db.ForeignKey("user_session.id"))

    def __init__(self, url: str, ip: str, session_id: int):
        if type(url) != str:
            raise TypeError('Variable url must be of type str.')
        if type(ip) != str:
            raise TypeError('Variable ip must be of type str.')
        if type(session_id) != int:
            raise TypeError('Variable session_id must be of type int.')
        self.init_dt = datetime.now()
        self.url = url
        self.ip = ip
        self.session_id = session_id


class UserSession(db.Model):
    __tablename__ = "user_session"
    id = db.Column(db.Integer, primary_key=True)

    check_in_dt = db.Column(db.DateTime)
    check_in_ip = db.Column(db.String(15))
    check_out_dt = db.Column(db.DateTime)
    check_out_ip = db.Column(db.String(15))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    pageloads = db.relationship("UserPageload", backref="session", lazy="select")

    def __init__(self, check_in_dt: datetime, check_in_ip: str, user_id: int):
        if type(check_in_dt) != datetime:
            raise TypeError('Variable check_in_dt must be of type datetime.')
        if type(check_in_ip) != str:
            raise TypeError('Variable check_in_ip must be of type str.')
        if type(user_id) != int:
            raise TypeError('Variable user_id must be of type int.')
        self.check_in_dt = check_in_dt
        self.check_in_ip = check_in_ip
        self.check_out_dt = None
        self.check_out_ip = None
        self.user_id = user_id


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)

    active = db.Column(db.Boolean)
    confirmed = db.Column(db.Boolean)
    wait_for_pricingaction_thread = db.Column(db.Boolean)
    wait_for_product_thread = db.Column(db.Boolean)
    confirmation_code = db.Column(db.String(255))
    username = db.Column(db.String(50))
    password = db.Column(db.String(255))
    name = db.Column(db.String(100))
    firstname = db.Column(db.String(100))
    birthday = db.Column(db.DateTime)
    fon = db.Column(db.String(50))
    email = db.Column(db.String(100))
    address = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    profilepic = db.Column(db.String(10))
    lastpageload = db.Column(db.DateTime)

    actions = db.relationship("SystemAction", backref="user", lazy="select")
    products = db.relationship("Product_User_Attributes", backref="user", lazy="select")
    pricingactions = db.relationship("PricingAction_User_Attributes", backref="user", lazy="select")
    roles = db.relationship("Role_User_Attributes", backref="user", lazy="select")
    sessions = db.relationship("UserSession", backref="user", lazy="select")

    def __init__(self, username, password, confirmation_code, name, firstname, email):
        self.init_date = datetime.now()
        self.active = False
        self.confirmed = False
        self.confirmation_code = confirmation_code
        self.username = username
        self.password = password
        self.name = name
        self.firstname = firstname
        self.email = email

    def get_pricingactions(self):
        ids = PricingAction_User_Attributes.query.filter_by(user_id=self.id).all()
        return PricingAction.query.filter(PricingAction.id.in_([item.pricingaction_id for item in ids])).all()

    def get_products(self):
        ids = Product_User_Attributes.query.filter_by(user_id=self.id).all()
        return Product.query.filter(Product.id.in_([item.product_id for item in ids])).all()

    def get_roles(self):
        ids = Role_User_Attributes.query.filter_by(user_id=self.id).all()
        return Role.query.filter(Role.id.in_([item.role_id for item in ids])).all()


class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(50), unique=True)

    users = db.relationship("Role_User_Attributes", backref="role", lazy="select")

    def __init__(self, name):
        self.name = name

    def get_users(self):
        ids = Role_User_Attributes.query.filter_by(role_id=self.id).all()
        return User.query.filter(User.id.in_([item.user_id for item in ids])).all()


class Role_User_Attributes(db.Model):
    __tablename__ = "role_user_attributes"
    id = db.Column(db.Integer(), primary_key=True)

    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, role_id, user_id):
        self.role_id = role_id
        self.user_id = user_id


class Product_User_Attributes(db.Model):
    __tablename__ = "product_user_attributes"
    id = db.Column(db.Integer(), primary_key=True)

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    checked = db.Column(db.Boolean)

    def __init__(self, product_id, user_id):
        self.product_id = product_id
        self.user_id = user_id


class Product_CurrProcStat(db.Model):
    __tablename__ = "product_currprocstat"
    id = db.Column(db.Integer(), primary_key=True)

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    proc_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    proc_timestamp = db.Column(db.DateTime)
    conf_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    conf_timestamp = db.Column(db.DateTime)
    review = db.Column(db.Boolean)

    proc_user = db.relationship("User", foreign_keys=[proc_user_id])
    conf_user = db.relationship("User", foreign_keys=[conf_user_id])

    def __init__(self, product_id):
        self.product_id = product_id
        self.review = False


class PSAUpdateQueue(db.Model):
    __tablename__ = "psa_update_queue"
    id = db.Column(db.Integer(), primary_key=True)
    init_datetime = db.Column(db.DateTime)

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    def __init__(self, product_id):
        self.init_datetime = datetime.now()
        self.product_id = product_id


class StockUpdateQueue(db.Model):
    __tablename__ = "stock_update_queue"
    id = db.Column(db.Integer(), primary_key=True)
    init_datetime = db.Column(db.DateTime)

    update_amount = db.Column(db.Integer)
    curr_stock = db.Column(db.Integer)
    proc_dt = db.Column(db.DateTime)

    psa_id = db.Column(db.Integer, db.ForeignKey("product_stock_attributes.id"), nullable=False)

    def __init__(self, update_amount: int, psa_id: int, curr_stock: int = None, proc_dt: datetime = None):
        self.init_datetime = datetime.now()
        self.curr_stock = curr_stock
        self.update_amount = update_amount
        self.psa_id = psa_id
        self.proc_dt = proc_dt


class ProductNotification(db.Model):
    __tablename__ = "product_notification"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)
    seen_datetime = db.Column(db.DateTime)
    done_datetime = db.Column(db.DateTime)

    title = db.Column(db.String(255))
    text = db.Column(db.String())

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, product_id: int, title: str, text: str):
        if type(product_id) != int:
            raise TypeError('Variable product_id must be of type int.')
        if type(title) != str:
            raise TypeError('Variable title must be of type str.')
        if type(text) != str:
            raise TypeError('Variable text must be of type str.')
        if len(title) > 255:
            raise TypeError('Variable title can have 255 characters at most.')
        check_p = Product.query.filter_by(id=product_id).first()
        if check_p is None:
            raise SystemError(f'Not product found for product_id {product_id}.')
        self.init_datetime = datetime.now()
        self.product_id = product_id
        self.title = title
        self.text = text


class ProductTag(db.Model):
    __tablename__ = "product_tag"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)

    name = db.Column(db.String(30))
    description = db.Column(db.String(1000))

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))

    products = db.relationship("PrTagRelation", backref="tag", lazy="select")

    def __init__(self, name: str, description: str, marketplace_id: int = None):
        if type(name) != str:
            raise TypeError('Variable name must be of type str.')
        if type(description) != str:
            raise TypeError('Variable description must be of type str.')
        if len(name) > 30:
            raise TypeError('Variable name can have 30 characters at most.')
        if len(description) > 1000:
            raise TypeError('Variable description can have 1000 characters at most.')
        check_tag = ProductTag.query.filter_by(name=name, marketplace_id=marketplace_id).first()
        if check_tag is not None:
            raise SystemError('This tag already exists.')
        self.init_datetime = datetime.now()
        self.name = name
        self.description = description
        self.marketplace_id = marketplace_id


class PrTagRelation(db.Model):
    __tablename__ = "pr_tag_relation"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    tag_id = db.Column(db.Integer, db.ForeignKey("product_tag.id"))

    def __init__(self, product_id: int, tag_id: int):
        if type(product_id) != int:
            raise TypeError('Variable product_id must be of type int.')
        if type(tag_id) != int:
            raise TypeError('Variable tag_id must be of type int.')
        check_p = Product.query.filter_by(id=product_id).first()
        if check_p is None:
            raise SystemError(f'Not product found for product_id {product_id}.')
        check_pt = ProductTag.query.filter_by(id=tag_id).first()
        if check_pt is None:
            raise SystemError(f'Not tag found for tag_id {tag_id}.')
        self.init_datetime = datetime.now()
        self.product_id = product_id
        self.tag_id = tag_id


class PrGrToken(db.Model):
    __tablename__ = "pr_gr_token"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(100))

    def __init__(self, name):
        if type(name) != str:
            raise TypeError(f'Variable name must be of type str. {type(name)} given.')
        if len(name) > 100:
            raise ValueError(f'Variable name can have at most 100 characters. {len(name)} given.')
        self.init_dt = datetime.now()
        self.name = name


class PrGrTokens(db.Model):
    __tablename__ = "pr_gr_tokens"
    id = db.Column(db.Integer, primary_key=True)

    group_id = db.Column(db.Integer, db.ForeignKey("product_group.id"))
    token_id = db.Column(db.Integer, db.ForeignKey("pr_gr_token.id"))

    def __init__(self, group_id, token_id):
        if type(group_id) != int:
            raise TypeError(f'Variable name must be of type int. {type(group_id)} given.')
        if type(token_id) != int:
            raise TypeError(f'Variable group_type must be of type int. {type(token_id)} given.')
        pgr = ProductGroup.query.filter_by(id=group_id).first()
        if pgr is None:
            raise ValueError(f'Could not find a product-group with id {group_id}.')
        t = PrGrToken.query.filter_by(id=token_id).first()
        if t is None:
            raise ValueError(f'Could not find a product with id {token_id}.')
        self.init_dt = datetime.now()
        self.group_id = group_id
        self.token_id = token_id


class ProductGroup(db.Model):
    __tablename__ = "product_group"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(255))
    group_type = db.Column(db.String(50))
    description = db.Column(db.String(1000))
    leaf = db.Column(db.Boolean)
    main_group = db.Column(db.Boolean)

    parent_id = db.Column(db.Integer, db.ForeignKey("product_group.id"))

    children = db.relationship("ProductGroup", backref=backref('parent', remote_side=[id]))
    products = db.relationship("PPGroup", backref="product_group", lazy="select")
    main_ps = db.relationship("Product", backref="main_group", lazy="select")
    tokens = db.relationship("PrGrTokens", backref="product_group", lazy="select")

    def __init__(self, name: str, main_p_ids: list, group_type: str = 'BASIC', description: str = '', leaf: bool = False, main_group: bool = True):
        if type(name) != str:
            raise TypeError(f'Variable name must be of type str. {type(name)} given.')
        if type(group_type) != str:
            raise TypeError(f'Variable group_type must be of type str. {type(group_type)} given.')
        if type(description) != str:
            raise TypeError(f'Variable description must be of type str. {type(description)} given.')
        if type(leaf) != bool:
            raise TypeError(f'Variable leaf must be of type bool. {type(leaf)} given.')
        if type(main_group) != bool:
            raise TypeError(f'Variable main_group must be of type bool. {type(main_group)} given.')
        if type(main_p_ids) != list:
            raise TypeError(f'Variable main_p_ids must be of type list. {type(main_p_ids)} given.')
        else:
            for main_p_id in main_p_ids:
                if type(main_p_id) != int:
                    raise TypeError(f'Elements of main_p_ids must be of type int. {type(main_p_id)} given.')
        if len(name) > 255:
            raise ValueError(f'Variable name can have at most 255 characters. {len(name)} given.')
        if len(group_type) > 50:
            raise ValueError(f'Variable name can have at most 50 characters. {len(group_type)} given.')
        if len(description) > 1000:
            raise ValueError(f'Variable name can have at most 1000 characters. {len(description)} given.')
        main_ps = Product.query.filter(Product.id.in_(main_p_ids)).all()
        if not main_ps:
            raise ValueError(f'Not products found given the ids {main_p_ids}. Provide at least one valid product-id.')
        self.init_dt = datetime.now()
        self.name = name
        self.group_type = group_type
        self.description = description
        self.leaf = leaf
        self.main_group = main_group
        self.main_ps = main_ps

    def self_update(self, name: str = None):
        self.name = name if name is not None else self.name
        db.session.commit()

    def merge(self, mgr_id):
        Product.query.filter_by(main_group_id=mgr_id).update({'main_group_id': self.id}, synchronize_session='fetch')
        db.session.commit()
        PPGroup.query.filter_by(product_group_id=mgr_id).update({'product_group_id': self.id}, synchronize_session='fetch')
        db.session.commit()
        PrGrTokens.query.filter_by(group_id=mgr_id).update({'group_id': self.id}, synchronize_session='fetch')
        db.session.commit()

    def find_matches(self, num: int = 5):
        own_tokens = PrGrTokens.query.filter_by(group_id=self.id).all()
        token_ids = [el.token_id for el in own_tokens]
        return db.session.query(
            ProductGroup, func.count(PrGrTokens.id)
        ).filter(
            ProductGroup.id == PrGrTokens.group_id
        ).filter(
            PrGrTokens.token_id.in_(token_ids)
        ).filter(
            ProductGroup.id != self.id
        ).group_by(
            ProductGroup.id
        ).order_by(
            func.count(PrGrTokens.id).desc()
        ).limit(
            num
        ).all()


class PPGroup(db.Model):
    __tablename__ = "ppgroup"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    product_group_id = db.Column(db.Integer, db.ForeignKey("product_group.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, product_group_id, product_id):
        if type(product_group_id) != int:
            raise TypeError(f'Variable name must be of type int. {type(product_group_id)} given.')
        if type(product_id) != int:
            raise TypeError(f'Variable group_type must be of type int. {type(product_id)} given.')
        pgr = ProductGroup.query.filter_by(id=product_group_id).first()
        if pgr is None:
            raise ValueError(f'Could not find a product-group with id {product_group_id}.')
        p = Product.query.filter_by(id=product_id).first()
        if p is None:
            raise ValueError(f'Could not find a product with id {product_id}.')
        self.init_dt = datetime.now()
        self.product_group_id = product_group_id
        self.product_id = product_id


class PrdGlobalID(db.Model):
    __tablename__ = "prd_global_id"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    global_id_type = db.Column(db.String(10))
    global_id = db.Column(db.String(20))

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, global_id_type: str, global_id: str, product_id: int):
        if type(global_id_type) != str:
            raise TypeError(f'Variable global_id_type must be of type str. {type(global_id_type)} given.')
        if type(global_id) != str:
            raise TypeError(f'Variable global_id must be of type str. {type(global_id)} given.')
        if type(product_id) != int:
            raise TypeError(f'Variable name product_id be of type int. {type(product_id)} given.')
        p = Product.query.filter_by(id=product_id).first()
        if p is None:
            raise ValueError(f'Could not find a product with id {product_id}.')
        self.init_dt = datetime.now()
        self.global_id_type = global_id_type
        self.global_id = global_id
        self.product_id = product_id


class ProductSD(db.Model):
    __tablename__ = "product_sd"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)
    rep_dt = db.Column(db.DateTime)

    buying_price = db.Column(db.Float)
    cheapest_buying_price = db.Column(db.Float)
    cheapest_stock_id = db.Column(db.Integer, db.ForeignKey("stock.id"))
    shipping_profile_id = db.Column(db.Integer, db.ForeignKey("shipping_profile.id"))
    nat_shipping_1_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    nat_shipping_2_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    nat_shipping_3_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    nat_shipping_4_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    int_shipping_1_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    int_shipping_2_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    int_shipping_3_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    int_shipping_4_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))


    def __init__(self, product_id: int, buying_price: float = None, cheapest_buying_price: float = None, cheapest_stock_id: int = None, shipping_profile_id: int = None, nat_shipping_1_id: int = None,
                 nat_shipping_2_id: int = None, nat_shipping_3_id: int = None, nat_shipping_4_id: int = None, int_shipping_1_id: int = None, int_shipping_2_id: int = None, int_shipping_3_id: int = None,
                 int_shipping_4_id: int = None):
        if type(product_id) != int:
            raise TypeError(f'Variable product_id must be of type int. {type(product_id)} given.')
        if buying_price is not None and type(buying_price) != float:
            raise TypeError(f'Variable buying_price must be of type float. {type(buying_price)} given.')
        if cheapest_buying_price is not None and type(cheapest_buying_price) != float:
            raise TypeError(f'Variable cheapest_buying_price must be of type float. {type(cheapest_buying_price)} given.')
        if cheapest_stock_id is not None and type(cheapest_stock_id) != int:
            raise TypeError(f'Variable name cheapest_stock_id be of type int. {type(cheapest_stock_id)} given.')
        if shipping_profile_id is not None and type(shipping_profile_id) != int:
            raise TypeError(f'Variable name shipping_profile_id be of type int. {type(shipping_profile_id)} given.')
        if nat_shipping_1_id is not None and type(nat_shipping_1_id) != int:
            raise TypeError(f'Variable name nat_shipping_1_id be of type int. {type(nat_shipping_1_id)} given.')
        if nat_shipping_2_id is not None and type(nat_shipping_2_id) != int:
            raise TypeError(f'Variable name nat_shipping_2_id be of type int. {type(nat_shipping_2_id)} given.')
        if nat_shipping_3_id is not None and type(nat_shipping_3_id) != int:
            raise TypeError(f'Variable name nat_shipping_3_id be of type int. {type(nat_shipping_3_id)} given.')
        if nat_shipping_4_id is not None and type(nat_shipping_4_id) != int:
            raise TypeError(f'Variable name nat_shipping_4_id be of type int. {type(nat_shipping_4_id)} given.')
        if int_shipping_1_id is not None and type(int_shipping_1_id) != int:
            raise TypeError(f'Variable name int_shipping_1_id be of type int. {type(int_shipping_1_id)} given.')
        if int_shipping_2_id is not None and type(int_shipping_2_id) != int:
            raise TypeError(f'Variable name int_shipping_2_id be of type int. {type(int_shipping_2_id)} given.')
        if int_shipping_3_id is not None and type(int_shipping_3_id) != int:
            raise TypeError(f'Variable name int_shipping_3_id be of type int. {type(int_shipping_3_id)} given.')
        if int_shipping_4_id is not None and type(int_shipping_4_id) != int:
            raise TypeError(f'Variable name int_shipping_4_id be of type int. {type(int_shipping_4_id)} given.')
        self.init_dt = datetime.now()
        self.rep_dt = None
        self.product_id = product_id
        last_psd = ProductSD.query.filter_by(product_id=product_id).order_by(ProductSD.init_dt.desc()).first()
        if last_psd:
            last_psd.rep_dt = self.init_dt
            self.buying_price = buying_price if buying_price is not None else last_psd.buying_price
            self.cheapest_buying_price = cheapest_buying_price if cheapest_buying_price is not None else last_psd.cheapest_buying_price
            self.cheapest_stock_id = cheapest_stock_id if cheapest_stock_id is not None else last_psd.cheapest_stock_id
            self.shipping_profile_id = shipping_profile_id if shipping_profile_id is not None else last_psd.shipping_profile_id
            self.nat_shipping_1_id = nat_shipping_1_id if nat_shipping_1_id is not None else last_psd.nat_shipping_1_id
            self.nat_shipping_2_id = nat_shipping_2_id if nat_shipping_2_id is not None else last_psd.nat_shipping_2_id
            self.nat_shipping_3_id = nat_shipping_3_id if nat_shipping_3_id is not None else last_psd.nat_shipping_3_id
            self.nat_shipping_4_id = nat_shipping_4_id if nat_shipping_4_id is not None else last_psd.nat_shipping_4_id
            self.int_shipping_1_id = int_shipping_1_id if int_shipping_1_id is not None else last_psd.int_shipping_1_id
            self.int_shipping_2_id = int_shipping_2_id if int_shipping_2_id is not None else last_psd.int_shipping_2_id
            self.int_shipping_3_id = int_shipping_3_id if int_shipping_3_id is not None else last_psd.int_shipping_3_id
            self.int_shipping_4_id = int_shipping_4_id if int_shipping_4_id is not None else last_psd.int_shipping_4_id
        else:
            product = Product.query.filter_by(id=product_id).first()
            self.buying_price = buying_price if buying_price is not None else product.buying_price
            self.cheapest_buying_price = cheapest_buying_price if cheapest_buying_price is not None else product.cheapest_buying_price
            self.cheapest_stock_id = cheapest_stock_id if cheapest_stock_id is not None else product.cheapest_stock_id
            self.shipping_profile_id = shipping_profile_id if shipping_profile_id is not None else product.shipping_profile_id
            self.nat_shipping_1_id = nat_shipping_1_id if nat_shipping_1_id is not None else product.nat_shipping_1_id
            self.nat_shipping_2_id = nat_shipping_2_id if nat_shipping_2_id is not None else product.nat_shipping_2_id
            self.nat_shipping_3_id = nat_shipping_3_id if nat_shipping_3_id is not None else product.nat_shipping_3_id
            self.nat_shipping_4_id = nat_shipping_4_id if nat_shipping_4_id is not None else product.nat_shipping_4_id
            self.int_shipping_1_id = int_shipping_1_id if int_shipping_1_id is not None else product.int_shipping_1_id
            self.int_shipping_2_id = int_shipping_2_id if int_shipping_2_id is not None else product.int_shipping_2_id
            self.int_shipping_3_id = int_shipping_3_id if int_shipping_3_id is not None else product.int_shipping_3_id
            self.int_shipping_4_id = int_shipping_4_id if int_shipping_4_id is not None else product.int_shipping_4_id


class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)

    block_release_date = db.Column(db.Boolean)
    internal_id = db.Column(db.String(20), unique=True)
    hsp_id_type = db.Column(db.String(50))
    hsp_id = db.Column(db.String(20))
    mpn = db.Column(db.String(20))
    name = db.Column(db.String(255))
    spec_trait_0 = db.Column(db.String(200))
    spec_trait_1 = db.Column(db.String(200))
    spec_trait_2 = db.Column(db.String(200))
    spec_trait_3 = db.Column(db.String(200))
    brand = db.Column(db.String)
    measurements = db.Column(db.String(20))
    length = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    packagenr = db.Column(db.String(20))
    shipping_dhl = db.Column(db.Float)
    shipping_dp = db.Column(db.Float)
    shipping_dpd = db.Column(db.Float)
    shipping_hermes = db.Column(db.Float)

    images_taken = db.Column(db.Boolean)
    update_psa = db.Column(db.DateTime)
    update_mp = db.Column(db.Boolean)
    release_date = db.Column(db.DateTime)
    tax_group = db.Column(db.Integer)
    state = db.Column(db.Integer)
    short_sell = db.Column(db.Boolean)
    buying_price = db.Column(db.Float)
    cheapest_buying_price = db.Column(db.Float)
    mp_stock = db.Column(db.Integer)

    pricing_bundle_id = db.Column(db.Integer, db.ForeignKey("pricing_bundle.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))
    main_group_id = db.Column(db.Integer, db.ForeignKey("product_group.id"))
    cheapest_stock_id = db.Column(db.Integer)
    shipping_profile_id = db.Column(db.Integer, db.ForeignKey("shipping_profile.id"))
    nat_shipping_1_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    nat_shipping_2_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    nat_shipping_3_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    nat_shipping_4_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    int_shipping_1_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    int_shipping_2_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    int_shipping_3_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))
    int_shipping_4_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))

    nat_shipping_1 = db.relationship("ShippingService", foreign_keys=[nat_shipping_1_id])
    nat_shipping_2 = db.relationship("ShippingService", foreign_keys=[nat_shipping_2_id])
    nat_shipping_3 = db.relationship("ShippingService", foreign_keys=[nat_shipping_3_id])
    nat_shipping_4 = db.relationship("ShippingService", foreign_keys=[nat_shipping_4_id])
    int_shipping_1 = db.relationship("ShippingService", foreign_keys=[int_shipping_1_id])
    int_shipping_2 = db.relationship("ShippingService", foreign_keys=[int_shipping_2_id])
    int_shipping_3 = db.relationship("ShippingService", foreign_keys=[int_shipping_3_id])
    int_shipping_4 = db.relationship("ShippingService", foreign_keys=[int_shipping_4_id])

    serial_data = db.relationship("ProductSD", backref="product", lazy="select")
    global_ids = db.relationship("PrdGlobalID", backref="product", lazy="select")
    currprocstat = db.relationship("Product_CurrProcStat", backref="product", lazy="select", uselist=False)
    actions = db.relationship("PricingAction", backref="product", lazy="select")
    extoffers = db.relationship("ExtOffer", backref="product", lazy="select")
    featurevalues = db.relationship("Product_ProductFeatureValue", backref="product", lazy="select")
    links = db.relationship("ProductLink", backref="product", lazy="select")
    marketplace_attributes = db.relationship("Marketplace_Product_Attributes", backref="product", lazy="select")
    notifications = db.relationship("ProductNotification", backref="product", lazy="select")
    orders = db.relationship("Order_Product_Attributes", backref="product", lazy="select")
    pictures = db.relationship("ProductPicture", backref="product", lazy="select")
    pricing_logs = db.relationship("PricingLog", backref="product", lazy="select")
    pre_orders = db.relationship("PreOrder", backref="product", lazy="select")
    stock = db.relationship("Product_Stock_Attributes", backref="product", lazy="select")
    stock_receipts = db.relationship("PSR_Attributes", backref="product", lazy="select")
    wsr_products = db.relationship("WSRProduct", backref="product", lazy="select")
    wsi_products = db.relationship("WSIProduct", backref="product", lazy="select")
    tags = db.relationship("PrTagRelation", backref="product", lazy="select")
    users = db.relationship("Product_User_Attributes", backref="product", lazy="select")
    psa_update_queue = db.relationship("PSAUpdateQueue", backref="product", lazy="select")
    pricing_rules = db.relationship("PPrRule", backref="product", lazy="select")

    def __init__(self, hsp_id_type, hsp_id, name=None, brand=None, mpn=None, release_date=None, shipping_service_id: int = 6, int_shipping_id: int = 10, shipping_profile_id: int = 4):
        if ' ' in name:
            k = 0
            while len(name)>255:
                name = ' '.join(name.split(' ')[:-1])
                k+=1
                if k > 10:
                    name = name[:255]
                    break
        else:
            name = name[:255]
        self.block_release_date = False
        self.hsp_id_type = hsp_id_type
        self.hsp_id = hsp_id
        self.tax_group = 1
        self.short_sell = False
        self.state = 0
        self.name = name
        self.brand = brand
        self.mpn = mpn
        self.nat_shipping_1_id = shipping_service_id
        self.int_shipping_1_id = int_shipping_id
        self.shipping_profile_id = shipping_profile_id
        self.images_taken = False
        self.pricing_bundle_id = 1
        pre_order = False
        try:
            if release_date is not None:
                self.release_date = release_date
                if release_date > datetime.now():
                    pre_order = True
        except:
            self.release_date = None
        r = afterbuy_api.get_shop_products({'Anr': [hsp_id]})
        tree = ETree.fromstring(r.text)
        err_code = tree.find('.//ErrorCode')
        if err_code is not None:
            if err_code.text == '15':
                anr = hsp_id
                while anr[0] == '0':
                    anr = anr[1:]
                product_tree = ETree.Element('Products')
                product = ETree.SubElement(product_tree, 'Product')
                p_ident = ETree.SubElement(product, 'ProductIdent')
                add_node('ProductInsert', 1, p_ident)
                add_node('ProductID', 0, p_ident)
                add_node('Anr', anr, p_ident)
                add_node('EAN', hsp_id, p_ident)
                if hsp_id[:6] != '000000':
                    add_node('ManufacturerStandardProductIDType', 'EAN', product)
                    add_node('ManufacturerStandardProductIDValue', hsp_id, product)
                add_node('EAN', hsp_id, product)
                add_node('Name', name, product)
                add_node('Anr', anr, product)
                add_node('TaxRate', float_to_comma(tax_group[1]['national']), product)
                add_node('Stock', 1, product)
                add_node('Discontinued', 1, product)
                add_node('MinimumStock', 5, product)
                if pre_order:
                    tags = ETree.SubElement(product, 'Tags')
                    add_node('Tag', 'PRE ORDER', tags)
                r = afterbuy_api.update_shop_products(product_tree)
                tree = ETree.fromstring(r.text)
                afterbuy_id = tree.find('.//ProductID')
                if afterbuy_id is not None:
                    if afterbuy_id.text == '0':
                        t.sleep(5)
                        r = afterbuy_api.get_shop_products({'Anr': hsp_id})
                        tree = ETree.fromstring(r.text)
                        afterbuy_id = tree.find('.//ProductID')
                    self.internal_id = afterbuy_id.text
                    print('--------------------------------------')
                    print('NEW PRODUCT')
                    print(f'AfterbuyID: {self.internal_id}.')
                    print(f'Name: {self.name}.')
                else:
                    err_code = tree.find('.//ErrorCode')
                    if err_code is not None:
                        print('--------------------------------------')
                        raise SystemError(f'ERROR {err_code.text}: {tree.find(".//ErrorLongDescription").text}')
                    else:
                        print('--------------------------------------')
                        raise SystemError(f'UNKNOWN ERROR: {r.text}')
            else:
                print('--------------------------------------')
                raise SystemError(f'ERROR {err_code.text}: {tree.find(".//ErrorLongDescription").text}')
        else:
            afterbuy_id = tree.find('.//ProductID').text
            self.internal_id = str(afterbuy_id)


    def add_basic_product_data(self, stock_id, dscrpt='', mpa_name='', idealo_action=True):
        product_tree = ETree.Element('Products')
        product_tree = self.ab_upload_xml_gen(product_tree, stock_location_1=True, weight=True)
        r = afterbuy_api.update_shop_products(product_tree)
        print(r.text)
        psa = Product_Stock_Attributes('Neu & OVP', 0, None, None, None, None, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                       datetime.now().replace(year=2100, month=1, day=1, hour=23, minute=59, second=59, microsecond=999999), self.id, stock_id)
        toy_cat = ProductCategory.query.filter_by(name='Spielzeug').first()
        toy_cat_ids = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]
        psa.last_seen = datetime.now()
        db.session.add(psa)
        db.session.add(Product_CurrProcStat(self.id))
        db.session.commit()
        plc = ProductLinkCategory.query.filter_by(name='Ebay').first()
        no_link = False
        check_link = ProductLink.query.filter_by(product_id=self.id, category_id=plc.id).first()
        if check_link:
            if 'http' not in check_link.link:
                db.session.delete(check_link)
                no_link = True
        else:
            no_link = True
        if no_link:
            ebay_link = 'https://www.ebay.de/sch/i.html?_nkw=' + self.hsp_id + '&LH_ItemCondition=3&rt=nc&LH_BIN=1'
            db.session.add(ProductLink(ebay_link, plc.id, self.id))
            db.session.commit()
        marketplaces = Marketplace.query.all()
        for marketplace in marketplaces:
            mpa = Marketplace_Product_Attributes(marketplace.id, self.id)
            mpa.mp_hsp_id = self.hsp_id
            db.session.add(mpa)
            db.session.commit()
            mpa.name = mpa_name if mpa_name else self.name
            mpa.block_selling_price = False
            if marketplace.name == 'Idealo':
                mpa.commission = 0.04
            elif marketplace.name == 'Ebay':
                if self.category_id:
                    if self.category_id in toy_cat_ids:
                        mpa.commission = 0.11
                    else:
                        mpa.commission = 0.09
                else:
                    mpa.commission = 0.11
                description_1 = self.name + '\nPlaystation 4 / PS4 Xbox ONE PC Nintendo Switch'
                description_2 = dscrpt
                description_3 = 'FEATURES\n\nWAS BEINHALTET DIESE EDITION?'
                description_4 = '''WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN\nNeu und originalverpackt\nEuropäische Verkaufsversion\nDeutsche Verkaufsversion mit USK Kennzeichnung\nDie Spielehülle beinhaltet nur einen Download-Code, Speicherkarte nicht vorhanden\nSpielsprache: xy | Texte: xy'''
                if self.release_date:
                    if self.release_date > datetime.now():
                        description_4 += '\nRelease-Datum: ' + datetime.strftime(self.release_date, '%d.%m.%Y') + ' / Voraussichtlicher Versand am ' + datetime.strftime(
                            self.release_date - timedelta(days=1), '%d.%m.%Y')
                db.session.add(Marketplace_Product_Attributes_Description(1, description_1, mpa.id))
                db.session.commit()
                db.session.add(Marketplace_Product_Attributes_Description(2, description_2, mpa.id))
                db.session.commit()
                db.session.add(Marketplace_Product_Attributes_Description(3, description_3, mpa.id))
                db.session.commit()
                db.session.add(Marketplace_Product_Attributes_Description(4, description_4, mpa.id))
                db.session.commit()
            elif marketplace.name == 'Lotus':
                mpa.commission = 0.015
            db.session.commit()
            try:
                self.generate_mp_price(marketplace.id, 3, min_margin=.01, send=False, save=True)
            except Exception as e:
                print(e)
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = datetime.strptime('2100-01-01', '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)

        new_pricingaction = PricingAction('Kuchenboden', start, end, 'Automatisch generiert', self.id, [stock_id])
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': 30, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                         mp_ids=[mp.id for mp in marketplaces])

        new_pricingaction = PricingAction('Fix Preis', start, end, 'Automatisch generiert', self.id, [stock_id])
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 0, 'rank': None, 'prc_margin': None, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                         mp_ids=[mp.id for mp in marketplaces])

        for pr in [0, 5, 10, 15, 20, 25, 40]:
            new_pricingaction = PricingAction(f'Marktpreis {pr}%', start, end, 'Automatisch generiert', self.id, [stock_id])
            new_pricingaction.active = False
            db.session.add(new_pricingaction)
            db.session.commit()
            new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': pr, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}}, active=False,
                                             mp_ids=[mp.id for mp in marketplaces])
        for pr in [-30, -20, -10, 0, 5, 10, 20, 30]:
            new_pricingaction = PricingAction(f'Abverkauf {pr}%', start, end, 'Automatisch generiert', self.id, [stock_id])
            new_pricingaction.active = True if pr==5 else False
            db.session.add(new_pricingaction)
            db.session.commit()
            new_pricingaction.add_strategies({'all': {'label': 3, 'rank': None, 'prc_margin': pr, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}}, active=pr==0,
                                             mp_ids=[mp.id for mp in marketplaces])
        new_pricingaction = PricingAction(f'Marktpreis 0-10%', start, end, 'Automatisch generiert', self.id, [stock_id])
        new_pricingaction.active = False
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': 0, 'prc_max_margin': 10, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                         active=False, mp_ids=[mp.id for mp in marketplaces])
        new_pricingaction = PricingAction(f'Marktpreis 0-15%', start, end, 'Automatisch generiert', self.id, [stock_id])
        new_pricingaction.active = False
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': 0, 'prc_max_margin': 15, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                         active=False, mp_ids=[mp.id for mp in marketplaces])
        new_pricingaction = PricingAction(f'Marktpreis 0-20%', start, end, 'Automatisch generiert', self.id, [stock_id])
        new_pricingaction.active = False
        db.session.add(new_pricingaction)
        db.session.commit()
        new_pricingaction.add_strategies({'all': {'label': 1, 'rank': None, 'prc_margin': 0, 'prc_max_margin': 20, 'promotion_quantity': None, 'update_factor': None, 'update_rule_hours': None, 'update_rule_quantity': None}},
                                         active=False, mp_ids=[mp.id for mp in marketplaces])
        if idealo_action:
            idealo = Marketplace.query.filter_by(name='Idealo').first()
            try:
                self.mp_upload(idealo.id, authorization=idealo_offer.get_access_token())
            except Exception as e:
                print(e)

    def gen_measurements(self):
        return f'{int(self.length)}x{int(self.width)}x{int(self.height)}' if self.length is not None and self.width is not None and self.height is not None else '-'

    def match_5_groups(self):
        et_title = ProductFeature.query.filter_by(name='title', source='Entertainment Trading').first()
        vi_title = ProductFeature.query.filter_by(name='Titel', source='Vitrex').first()
        id_title = ProductFeature.query.filter_by(name='title', source='Idealo').first()
        p_ts = self.name.replace(':', '').replace(' / ', '/').replace(' - ', ' ').lower().split(' ')
        tokens = set([p_t.strip() for p_t in p_ts])
        query = db.session.query(
            ProductFeature, ProductFeatureValue, Product_ProductFeatureValue, Product
        ).filter(
            ProductFeature.id == ProductFeatureValue.productfeature_id
        ).filter(
            ProductFeatureValue.id == Product_ProductFeatureValue.productfeaturevalue_id
        ).filter(
            Product_ProductFeatureValue.product_id == Product.id
        ).filter(
            Product.id == self.id
        ).filter(
            ProductFeature.id.in_([et_title.id, vi_title.id, id_title.id])
        ).all()
        for pf, pfv, ppfv, p in query:
            p_ts = pfv.value.replace(':', '').replace(' / ', '/').replace(' - ', ' ').lower().split(' ')
            p_ts = set([p_t.strip().replace('(', '').replace(')', '') for p_t in p_ts])
            tokens = set.union(tokens, p_ts)
        return db.session.query(
            ProductGroup, func.count(PrGrTokens.id), func.count(PrGrToken.id)
        ).filter(
            PrGrToken.name.in_(list(tokens))
        ).filter(
            PrGrTokens.token_id == PrGrToken.id
        ).filter(
            PrGrTokens.group_id == ProductGroup.id
        ).filter(
            ProductGroup.leaf == True
        ).group_by(
            ProductGroup.id
        ).order_by(
            func.count(PrGrTokens.id).desc()
        ).limit(
            5
        ).all()


    def get_mp_tags(self, marketplace_id: int, pretty: bool = False, only_tags: bool = False):
        if type(marketplace_id) != int:
            raise TypeError('Variable marketplace_id must be of type int.')
        query = db.session.query(ProductTag, PrTagRelation).filter(
            PrTagRelation.product_id == self.id
        ).filter(
            PrTagRelation.tag_id == ProductTag.id
        ).filter(
            ProductTag.marketplace_id == marketplace_id
        ).all()
        if pretty is False and only_tags is False:
            return query
        elif pretty is False:
            return [tag.name for tag, _ in query]
        else:
            return ', '.join([tag.name for tag, _ in query])


    def psa_update(self):
        short_sell_off = False
        no_stock = False
        short_sell_on = False
        back_in_stock = False
        mp_update_dict = {}
        for mpa in self.marketplace_attributes:
            mp_update_dict[mpa.marketplace_id] = {'update': False, 'update_price': False, 'custom_price': None, 'ps_id': None}
        tags = []
        if self.cheapest_stock_id:
            curr_lag_days = Stock.query.filter_by(id=self.cheapest_stock_id).first().lag_days
        else:
            curr_lag_days = -1
        stock, buying_price = self.get_cheapest_buying_price_all()
        if stock is None:
            stock = Stock.query.filter_by(id=1).first()
        if buying_price is not None and buying_price != self.cheapest_buying_price:
            psa = Product_Stock_Attributes.query.filter_by(
                product_id=self.id, stock_id=stock.id
            ).filter(
                Product_Stock_Attributes.avail_date <= datetime.now()
            ).filter(
                Product_Stock_Attributes.termination_date >= datetime.now()
            ).first()
            for mpa in self.marketplace_attributes:
                if mpa.uploaded:
                    mpa.max_stock = min(mpa.max_stock, psa.quantity)
                    mpa.min_stock = min(mpa.max_stock, mpa.min_stock)
                    mpa.pr_update_dur = 6
                    k = datetime.now().hour // 6
                    mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
        self.cheapest_stock_id = stock.id if stock else None
        self.cheapest_buying_price = buying_price
        db.session.commit()
        mul = int(self.get_own_real_stock() < 1)
        update_release = False
        pre_order = False
        if self.release_date:
            pre_order = True if self.release_date > datetime.now() else False
            if self.release_date >= datetime.now():
                update_release = True
        elif mul == 0:
            pre_order = False
            update_release = True
            self.release_date = datetime.now() - timedelta(days=1)
            db.session.commit()
        if update_release or curr_lag_days != stock.lag_days or self.update_psa is True:
            self.update_psa = False
            db.session.commit()
        if buying_price is None:
            if self.short_sell is True:
                self.short_sell = False
                db.session.commit()
                short_sell_off = True
            no_stock = True
            for key in mp_update_dict:
                mp_update_dict[key]['update'] = True
            tags = ['x']
            if pre_order:
                tags.append('PRE ORDER')
        else:
            if stock.id != 1 and mul == 0:
                for key in mp_update_dict:
                    mp_update_dict[key]['update'] = True
            if stock.owned is True and self.short_sell is True:
                self.short_sell = False
                db.session.commit()
                short_sell_off = True
                for key in mp_update_dict:
                    mp_update_dict[key]['update'] = True
                tags = ['x']
                if pre_order:
                    tags.append('PRE ORDER')
                for mpa in self.marketplace_attributes:
                    if mpa.uploaded:
                        mpa.pr_update_dur = 6
                        k = datetime.now().hour // 6
                        mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
            elif stock.owned is False and self.short_sell is False:
                self.short_sell = True
                db.session.commit()
                short_sell_on = True
                for key in mp_update_dict:
                    mp_update_dict[key]['update'] = True
                tags = ['LVK']
                if pre_order:
                    tags.append('PRE ORDER')
                for mpa in self.marketplace_attributes:
                    if mpa.uploaded:
                        mpa.pr_update_dur = 6
                        k = datetime.now().hour // 6
                        mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
            elif stock.owned is True and self.short_sell is False:
                db.session.commit()
                back_in_stock = True
                for key in mp_update_dict:
                    mp_update_dict[key]['update'] = True
                if pre_order:
                    tags.append('PRE ORDER')
                for mpa in self.marketplace_attributes:
                    if mpa.uploaded:
                        mpa.pr_update_dur = 6
                        k = datetime.now().hour // 6
                        mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
            for mpa in self.marketplace_attributes:
                margin = .01 if self.short_sell or self.get_own_stock() > 5 else 0.15
                last_price_log = self.get_last_price_by_mp(mpa.marketplace_id)
                curr_price = last_price_log.selling_price if last_price_log else mpa.selling_price
                if mpa.block_selling_price is not True:
                    self.generate_mp_price(mpa.marketplace_id, 3, min_margin=margin, send=False, save=True)
                pa, ps = db.session.query(PricingAction, PricingStrategy).filter(
                    PricingAction.product_id==self.id
                ).filter(
                    PricingAction.id==PricingStrategy.pricingaction_id
                ).filter(
                    PricingAction.active==True
                ).first()
                try:
                    custom_price = self.generate_mp_price(mpa.marketplace_id, strategy_label=ps.label, strategy_id=ps.id, min_margin=ps.prc_margin / 100 if ps.prc_margin is not None else None,
                                                          max_margin=ps.prc_max_margin / 100 if ps.prc_max_margin is not None else None, rank=ps.rank if ps.rank is not None else 0,
                                                          ext_offers=self.get_mp_ext_offers(mpa.marketplace_id) if ps.label in [1, 2] else None, send=False)[8]
                except Exception:
                    custom_price = None
                if custom_price is not None and custom_price != curr_price:
                    mp_update_dict[mpa.marketplace_id] = {'update': True, 'update_price': True, 'custom_price': custom_price, 'ps_id': ps.id}
                elif custom_price is None and curr_price != mpa.selling_price:
                    mp_update_dict[mpa.marketplace_id] = {'update': True, 'update_price': True, 'custom_price': None, 'ps_id': None}
                mpa.name = self.name if not mpa.name else mpa.name
                db.session.commit()
        return short_sell_off, no_stock, short_sell_on, back_in_stock, mp_update_dict, tags


    def magento_upload(self, auth):
        mpa = Marketplace_Product_Attributes.query.filter_by(product_id=self.id, marketplace_id=1).first()
        stock = self.get_own_stock_attributes()
        quant = stock.quantity if stock else 0
        description = ''
        short_description = ''
        weight = self.weight if self.weight else .0
        media_gallery_entries = []
        bigpic = ProductPicture.query.filter_by(product_id=self.id, pic_type=0).first()
        if bigpic:
            b64_encoded_string = base64.b64encode(requests.get('https://strikeusifucan.com/' + bigpic.link).content).decode("utf8")
            raw_data = {'base64_encoded_data': b64_encoded_string, 'type': 'image/jpeg', 'name': bigpic.link}
            media_gallery_entries.append({"media_type": "image", "types": ["image", "thumbnail", "swatch"], "label": bigpic.link, "content": raw_data, "file": bigpic.link})
        smallpic = ProductPicture.query.filter_by(product_id=self.id, pic_type=1).first()
        if smallpic:
            b64_encoded_string = base64.b64encode(requests.get('https://strikeusifucan.com/' + smallpic.link).content).decode("utf8")
            raw_data = {'base64_encoded_data': b64_encoded_string, 'type': 'image/jpeg', 'name': smallpic.link}
            media_gallery_entries.append({"media_type": "image", "types": ["image"], "label": smallpic.link, "content": raw_data, "file": smallpic.link})
        otherpics = ProductPicture.query.filter_by(product_id=self.id).filter(ProductPicture.pic_type == 2).all()
        for pic in otherpics:
            b64_encoded_string = base64.b64encode(requests.get('https://strikeusifucan.com/' + pic.link).content).decode("utf8")
            raw_data = {'base64_encoded_data': b64_encoded_string, 'type': 'image/jpeg', 'name': pic.link}
            media_gallery_entries.append({"media_type": "image", "types": ["image"], "label": pic.link, "content": raw_data, "file": pic.link})
        try:
            r = post_product(auth, self.id, self.internal_id, self.hsp_id, mpa.name, mpa.selling_price, quant, type_id='simple', description=description, short_description=short_description,
                             weight=weight, is_in_stock=quant > 0, media_gallery_entries=media_gallery_entries)
            return r
        except Exception as e:
            print(e)


    def get_shipping_dict(self, marketplace_id):
        sd = {'national': {}, 'international': {}}
        query = db.session.query(ShippingService, MPShippingService, ShippingProfilePrice).filter(
            or_(ShippingService.id == self.nat_shipping_1_id,
                ShippingService.id == self.nat_shipping_2_id,
                ShippingService.id == self.nat_shipping_3_id,
                ShippingService.id == self.nat_shipping_4_id,
                ShippingService.id == self.int_shipping_1_id,
                ShippingService.id == self.int_shipping_2_id,
                ShippingService.id == self.int_shipping_3_id,
                ShippingService.id == self.int_shipping_4_id)
        ).filter(
            MPShippingService.shipping_service_id == ShippingService.id
        ).filter(
            MPShippingService.marketplace_id == marketplace_id
        ).filter(
            ShippingProfilePrice.profile_id == self.shipping_profile_id
        ).filter(
            ShippingProfilePrice.mp_service_id == MPShippingService.id
        ).all()
        for row in query:
            if row[0].international:
                sd['international'][row[0].id] = {'code': row[1].code, 'value': row[2].price}
            else:
                sd['national'][row[0].id] = {'code': row[1].code, 'value': row[2].price}
        return sd


    def get_ebay_shipping(self):
        sd = {}
        query = db.session.query(ShippingService, MPShippingService, ShippingProfilePrice).filter(
            or_(ShippingService.id == self.nat_shipping_1_id,
                ShippingService.id == self.nat_shipping_2_id,
                ShippingService.id == self.nat_shipping_3_id,
                ShippingService.id == self.nat_shipping_4_id,
                ShippingService.id == self.int_shipping_1_id,
                ShippingService.id == self.int_shipping_2_id,
                ShippingService.id == self.int_shipping_3_id,
                ShippingService.id == self.int_shipping_4_id)
        ).filter(
            MPShippingService.shipping_service_id == ShippingService.id
        ).filter(
            MPShippingService.marketplace_id == 2
        ).filter(
            ShippingProfilePrice.profile_id == self.shipping_profile_id
        ).filter(
            ShippingProfilePrice.mp_service_id == MPShippingService.id
        ).all()
        for row in query:
            if row[0].international:
                sd['international'] = {'code': row[1].code, 'value': row[2].price}
            else:
                sd['national'] = {'code': row[1].code, 'value': row[2].price}
        return sd


    def mp_upload(self, marketplace_id: int, features: bool = False, category: bool = False, custom_price: float = None, custom_quantity: int = None, pricingstrategy_id: int = None, authorization=None):
        if self.cheapest_stock_id is None:
            s, pr = self.get_cheapest_buying_price_all()
            self.cheapest_stock_id = s.id if s is not None else None
            self.cheapest_buying_price = pr
            db.session.commit()
        if self.cheapest_stock_id is None or self.cheapest_buying_price == 0:
            print('----------------------------------------------------------------------')
            print(self.id)
            print('There is no stock with positive inventory for this product or buying_price is 0.00 €.')
            print('----------------------------------------------------------------------')
            self.cheapest_stock_id = 1
            self.cheapest_buying_price = None
            if self.cheapest_buying_price == 0:
                for mpa in self.marketplace_attributes:
                    mpa.max_stock = 0
                    mpa.min_stock = 0
            db.session.commit()
        psa = Product_Stock_Attributes.query.filter_by(stock_id=self.cheapest_stock_id, product_id=self.id).first()
        marketplace = Marketplace.query.filter_by(id=marketplace_id).first()
        sd = self.get_shipping_dict(marketplace_id)
        mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace_id, product_id=self.id).first()
        last_price_log = self.get_last_price_by_mp(marketplace.id)
        selling_price = last_price_log.selling_price if last_price_log else mpa.selling_price
        selling_price = custom_price if custom_price else selling_price
        if mpa.upload_clearance is False:
            raise SystemError(f'Product ist not cleared for upload on {marketplace.name}.')
        stock = Stock.query.filter_by(id=self.cheapest_stock_id).first()
        own_stock_real = self.get_own_real_stock()
        mul = int(own_stock_real < 1)
        own_stock = self.get_own_stock()
        mpa.curr_stock = min(max(0, own_stock - mpa.quantity_delta if mpa.quantity_delta else own_stock), mpa.max_stock) if mpa.curr_stock == 0 else mpa.curr_stock
        upload_quant = custom_quantity if custom_quantity is not None else mpa.curr_stock
        if self.release_date is None:
            if mul == 0:
                self.release_date = datetime.now()-timedelta(days=1)
                lag_days = 0
            else:
                raise SystemError('Product needs a valid release-date for upload or must be in stock.')
        else:
            lag_days = stock.lag_days
        db.session.commit()
        if marketplace.name == 'Idealo':
            if not self.nat_shipping_1:
                delivery = None
                delivery_comment = None
            else:
                w_days = working_days_in_range(date.today(), mpa.product.release_date.date()) if mpa.product.release_date >= datetime.now() else 0
                w_days += lag_days * mul
                w_days += self.productcategory.get_stock_ship_days(self.cheapest_stock_id) * mul if self.productcategory else 0
                nat_shipping_1 = ShippingService.query.filter_by(id=self.nat_shipping_1_id).first()
                delivery = 'Lieferzeit: ' + str(nat_shipping_1.min_days + w_days) + '-' + str(nat_shipping_1.max_days + w_days) + ' Werktage'
                if self.release_date > datetime.now():
                    delivery_comment = f'Release-Datum: {datetime.strftime(self.release_date, "%d.%m.%Y")} / Voraussichtlicher Versand am {datetime.strftime(self.release_date - timedelta(days=1), "%d.%m.%Y")}'
                else:
                    delivery_comment = 'Auf Lager, versandfertig innerhalb von 24 Stunden' if mul == 0 else f'Ware bestellt, versandfertig innerhalb von {24 * (w_days)} Stunden'
            cop = max(0, own_stock-mpa.quantity_delta) if mpa.quantity_delta else max(0, own_stock) if upload_quant > 0 else 0
            r = idealo_offer.put_offer(authorization, self.id, self.internal_id, mpa.name, '%0.2f' % mpa.selling_price if not custom_price else '%0.2f' % custom_price, 'lotusicafe', {'PAYPAL': '0.00'},
                                       dict((sd['national'][key]['code'], '%0.2f' % sd['national'][key]['value']) for key in sd['national']), True, 'PARCEL_SERVICE',
                                       url='https://www.ebay.de/usr/lotus-icafe', brand=self.brand, eans=[mpa.mp_hsp_id], hans=[self.mpn] if self.mpn != 'nicht zutreffend' else [''], delivery_comment=delivery_comment,
                                       delivery=delivery, checkout_limit_per_period=cop if mpa.max_stock > 0 else 0, quantity_per_order=max(0, upload_quant))
        elif marketplace.name == 'Ebay' and mpa.sell_api == True:
            toy_cat = ProductCategory.query.filter_by(id=27).first()
            toy_cats = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]
            descr = mpa.gen_description()
            if self.category_id in toy_cats and 'ACHTUNG' not in descr:
                raise SystemError('Toys must contain a warning in their description.')
            w_days = working_days_in_range(date.today(), mpa.product.release_date.date()) if mpa.product.release_date >= datetime.now() else 0
            w_days += lag_days * mul
            w_days += self.productcategory.get_stock_ship_days(self.cheapest_stock_id) * mul if self.productcategory else 0
            possible_days = [0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40]
            if w_days > 20:
                mpa.upload_ready = True
                db.session.commit()
                return ebay_api.put_inventory_item(brand=self.brand, description='', ean=mpa.mp_hsp_id, mpn=self.mpn, quantity=max(0, upload_quant), sku=self.internal_id, title=mpa.name, product_id=self.id)
            days = min(i for i in possible_days if i >= w_days)
            image_array = []
            for image in sorted(self.pictures, key=lambda x: x.pic_type):
                if image.link:
                    image_array.append(environ.get('IMAGE_SERVER') + image.link)
            feature_dict = {}
            cat_feature_ids = []
            if self.productcategory is not None:
                cat_features = db.session.query(ProductCategory_ProductFeature.productfeature_id).filter(ProductCategory_ProductFeature.productcategory_id == self.productcategory.id).all()
                cat_feature_ids = [cat_feature[0] for cat_feature in cat_features]
            query = db.session.query(Product_ProductFeatureValue, ProductFeatureValue, ProductFeature).filter(
                Product_ProductFeatureValue.product_id == self.id
            ).filter(
                Product_ProductFeatureValue.productfeaturevalue_id == ProductFeatureValue.id
            ).filter(
                ProductFeatureValue.productfeature_id == ProductFeature.id
            ).filter(
                ProductFeature.source == 'lotus'
            ).filter(
                ProductFeature.id.in_(cat_feature_ids) if self.productcategory is not None else True
            ).order_by(
                ProductFeature.id
            ).all()
            if query:
                feature_name = query[0][2].name
                feature_dict[feature_name] = [query[0][1].value]
                if len(query) > 1:
                    for conn, pfv, pf in query[1:]:
                        if pf.name != feature_name:
                            feature_name = pf.name
                            feature_dict[feature_name] = [pfv.value]
                        else:
                            feature_dict[feature_name].append(pfv.value)
            if 'Herausgeber' in feature_dict:
                if len(feature_dict['Herausgeber']) > 1:
                    feature_dict['Herausgeber'] = [feature_dict['Herausgeber'][0]]
            if 'Typ' in feature_dict:
                if len(feature_dict['Typ']) > 1:
                    feature_dict['Typ'] = [feature_dict['Typ'][0]]
            if 'Material' in feature_dict:
                if len(feature_dict['Material']) > 1:
                    feature_dict['Material'] = [', '.join(feature_dict['Material'])]
            if 'Marke' not in feature_dict:
                feature_dict['Marke'] = [self.brand]
            feature_dict.pop('Warnhinweise', None)
            if 'Altersempfehlung' in feature_dict:
                if len(feature_dict['Altersempfehlung']) > 1:
                    val = ''
                    for el in feature_dict['Altersempfehlung']:
                        if 'bis' in el:
                            val += el
                        else:
                            num = "".join(re.findall("\d+", el))
                            val = f'{num} {val}'
                    feature_dict['Altersempfehlung'] = [val]
            put_inv_req = ebay_api.put_inventory_item(brand=self.brand, description='', ean=mpa.mp_hsp_id, feature_dict=feature_dict, image_array=image_array, mpn=self.mpn, quantity=max(0, upload_quant),
                                                      sku=self.internal_id, title=mpa.name, product_id=self.id)
            if self.productcategory is not None:
                category_id = mpa.mp_cat_id
            else:
                category_id = ''
            ebay_shipping_info = self.get_ebay_shipping()
            if "international" in ebay_shipping_info:
                shipping_services = [{"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["national"]["value"]}, "shippingServiceType": "DOMESTIC"},
                                     {"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["international"]["value"]}, "shippingServiceType": "INTERNATIONAL"}]
                ff_policy_id = ebay_ff_policy_ids[f'{ebay_shipping_info["national"]["code"]} & {ebay_shipping_info["international"]["code"]} - {days} DAYS']
            else:
                shipping_services = [{"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["national"]["value"]}, "shippingServiceType": "DOMESTIC"}]
                ff_policy_id = ebay_ff_policy_ids[f'{ebay_shipping_info["national"]["code"]} - {days} DAYS']
            get_offer_req = ebay_api.get_offer(sku=self.internal_id)
            if not get_offer_req.ok:
                put_offer_req = ebay_api.create_offer(currency='EUR', description=descr, fulfillment_policy_id=ff_policy_id, quantity=max(0, upload_quant), sku=self.internal_id,
                                                      price=selling_price if not custom_price else custom_price, shipping_services=shipping_services, vat=tax_group[self.tax_group]['national'],
                                                      product_id=self.id, category_id=category_id)
                data = put_offer_req.json()
                offer_id = data['offerId']
            else:
                data = get_offer_req.json()
                offer_id = data['offers'][0]['offerId']
                put_offer_req = ebay_api.update_offer(offer_id=offer_id, currency='EUR', description=descr, fulfillment_policy_id=ff_policy_id, quantity=max(0, upload_quant),
                                                      price=selling_price if not custom_price else custom_price, shipping_services=shipping_services, vat=tax_group[self.tax_group]['national'],
                                                      product_id=self.id, category_id=category_id)
            r = ebay_api.publish_offer(offer_id=offer_id)
            if r.ok:
                listing_id_req = ebay_api.get_offer(sku=self.internal_id)
                data = listing_id_req.json()
                mpa.marketplace_system_id = data["offers"][0]["listing"]["listingId"]
                db.session.commit()
        elif marketplace.name == 'Lotus':
            image_array = []
            for image in sorted(self.pictures, key=lambda x: x.pic_type):
                if image.link:
                    image_array.append(environ.get('IMAGE_SERVER') + image.link)
            r = shopify.post_product(mpa.gen_description(), mpa.name, image_array, self.productcategory.name, self.hsp_id, max(0, upload_quant), selling_price, self.internal_id, self.weight)
            if r.ok:
                data = r.json()
                mpa.marketplace_system_id = data['product']['id']
                db.session.commit()
        else:
            raise SystemError('Marketplace not implemented.')
        if r.ok:
            mpa.uploaded = True
            self.add_pricing_log(marketplace_id, mpa.selling_price if not custom_price else custom_price, psa.id, pricingstrategy_id=pricingstrategy_id)
            db.session.commit()
        return r


    def mp_update(self, marketplace_id: int, title: bool = False, price: bool = False, custom_price: float = None, shipping_cost: bool = False, shipping_time: bool = False, brand: bool = False,
                  ean: bool = False, mpn: bool = False, quantity: bool = False, custom_quantity: int = None, images: bool = False, description: bool = False, description_revise_mode: str = '', features: bool = False,
                  category: bool = False, sku: bool = False, weight: bool = False, pricingstrategy_id: int = None, authorization=None):
        """
        Function to update a product on a given marketplace. All parameters except for marketplace_id and connection are booleans indicating whether or not the attribute should be updated.
        :param marketplace_id: int
        :param title: bool
        :param price: bool
        :param custom_price: float
        :param shipping_cost: bool
        :param shipping_time: bool
        :param brand: bool
        :param ean: bool
        :param mpn: bool
        :param quantity: bool
        :param custom_quantity: int
        :param images: bool
        :param description: bool
        :param description_revise_mode: bool
        :param features: bool
        :param category: bool
        :param sku: bool
        :param weight: bool
        :param pricingstrategy_id: int
        :param authorization: bool
        @Idealo:    access_dict generated via idealo_offer.get_access_token().
        @Ebay:      Trading_Connection via ebaysdk.
        :return:
        """
        if self.cheapest_stock_id is None:
            s, pr = self.get_cheapest_buying_price_all()
            self.cheapest_stock_id = s.id if s is not None else None
            self.cheapest_buying_price = pr
            db.session.commit()
        if self.cheapest_stock_id is None or self.cheapest_buying_price == 0:
            print('----------------------------------------------------------------------')
            print(self.id)
            print('There is no stock with positive inventory for this product or buying_price is 0.00 €.')
            print('----------------------------------------------------------------------')
            self.cheapest_stock_id = 1
            self.cheapest_buying_price = None
            if self.cheapest_buying_price == 0:
                for mpa in self.marketplace_attributes:
                    mpa.max_stock = 0
                    mpa.min_stock = 0
                    quantity = True
            db.session.commit()
        psa = Product_Stock_Attributes.query.filter_by(stock_id=self.cheapest_stock_id, product_id=self.id).first()
        marketplace = Marketplace.query.filter_by(id=marketplace_id).first()
        mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace_id, product_id=self.id).first()
        if mpa.upload_clearance is False:
            raise SystemError(f'Product ist not cleared for upload on {marketplace.name}.')
        last_price_log = self.get_last_price_by_mp(marketplace.id)
        selling_price = last_price_log.selling_price if last_price_log else mpa.selling_price
        selling_price = custom_price if custom_price else selling_price
        if shipping_cost:
            sd = self.get_shipping_dict(marketplace_id)
        own_stock = self.get_own_stock()
        stock = Stock.query.filter_by(id=self.cheapest_stock_id).first()
        own_stock_real = self.get_own_real_stock()
        mul = int(own_stock_real < 1)
        if self.release_date is None:
            if own_stock == 0:
                lag_days = 40
            elif mul == 0:
                self.release_date = datetime.now()-timedelta(days=1)
                lag_days = 0
            else:
                raise SystemError('To calculate shipping-time a release-date must be provided.')
        else:
            lag_days = stock.lag_days
        update_quant = 0
        if quantity:
            if mpa.curr_stock > mpa.max_stock:
                mpa.curr_stock = min(max(0, own_stock - mpa.quantity_delta if mpa.quantity_delta else own_stock), mpa.max_stock)
            else:
                mpa.curr_stock = min(max(0, own_stock - mpa.quantity_delta if mpa.quantity_delta else own_stock), mpa.max_stock) if mpa.curr_stock == 0 else mpa.curr_stock
            update_quant = custom_quantity if custom_quantity is not None else mpa.curr_stock
        db.session.commit()
        if marketplace.name == 'Idealo':
            delivery_comment = None
            delivery = None
            if shipping_time:
                if not self.nat_shipping_1 or not self.release_date:
                    delivery = None
                    delivery_comment = None
                else:
                    w_days = working_days_in_range(date.today(), mpa.product.release_date.date()) if mpa.product.release_date >= datetime.now() else 0
                    w_days += lag_days * mul
                    w_days += self.productcategory.get_stock_ship_days(self.cheapest_stock_id) * mul if self.productcategory else 0
                    delivery = f'Lieferzeit: {self.nat_shipping_1.min_days + w_days}-{self.nat_shipping_1.max_days + w_days} Werktage'
                    if self.release_date > datetime.now():
                        delivery_comment = f'Release-Datum: {datetime.strftime(self.release_date, "%d.%m.%Y")} / Voraussichtlicher Versand am {datetime.strftime(self.release_date - timedelta(days=1), "%d.%m.%Y")}'
                    else:
                        delivery_comment = 'Auf Lager, versandfertig innerhalb von 24 Stunden' if mul == 0 else f'Ware bestellt, versandfertig innerhalb von {24 * (w_days)} Stunden'
            cop = max(0, own_stock-mpa.quantity_delta) if mpa.quantity_delta else max(0, own_stock) if update_quant > 0 else 0 if quantity else None
            if mpa.max_stock <= 0:
                cop = 0
            print(cop)
            r = idealo_offer.patch_offer(authorization, self.id, self.internal_id, title=mpa.name if title else None, price=selling_price if price else None, brand=self.brand if brand else None,
                                         eans=[mpa.mp_hsp_id] if ean else None, hans=[self.mpn] if mpn and self.mpn != 'nicht zutreffend' else [''], delivery_comment=delivery_comment if shipping_time else None,
                                         delivery=delivery if shipping_time else None, checkout_limit_per_period=cop if quantity else None, quantity_per_order=max(0, update_quant) if quantity else None)
        elif marketplace.name == 'Ebay' and mpa.sell_api==False:
            if os.environ['EBAY_TR_API_LIMIT'] == '1':
                if datetime.now().hour == 9:
                    os.environ['EBAY_TR_API_LIMIT'] = '0'
                    set_key(env_vars_path, 'EBAY_TR_API_LIMIT', os.environ['EBAY_TR_API_LIMIT'])
                else:
                    raise SystemError('Number of Ebay-Trading-API-Calls for today exceeded. Reset at 09:00 MEZ.')
            if not mpa.uploaded:
                raise SystemError('Offer must be online to be updated.')
            else:
                if not mpa.marketplace_system_id:
                    mpa.marketplace_system_id = self.get_ebay_id()
                    db.session.commit()
                    if mpa.marketplace_system_id is None:
                        raise SystemError('An offer could not be found for this product. Please check if it is online and provide a valid offer_id.')
                image_array = []
                days = None
                if shipping_time:
                    w_days = working_days_in_range(date.today(), mpa.product.release_date.date()) if mpa.product.release_date >= datetime.now() else 0
                    w_days += lag_days * mul
                    w_days += self.productcategory.get_stock_ship_days(self.cheapest_stock_id) * mul if self.productcategory else 0
                    possible_days = [0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40]
                    if w_days > 40:
                        update_quant = 0
                    else:
                        days = min(i for i in possible_days if i >= w_days)
                if images:
                    for image in sorted(self.pictures, key=lambda x: x.pic_type):
                        if image.link:
                            image_array.append(environ.get('IMAGE_SERVER') + image.link)
                    description=True
                    description_revise_mode='Replace'
                shipping_service_dict = {'ShippingServiceOptions': [], 'InternationalShippingServiceOption': []}
                if shipping_cost:
                    for key in sd['national']:
                        shipping_service_dict['ShippingServiceOptions'].append({'ShippingService': sd['national'][key]['code'], 'ShippingServiceCost': sd['national'][key]['value'], 'FreeShipping': int(sd['national'][key]['value'] == 0)})
                    for key in sd['international']:
                        shipping_service_dict['InternationalShippingServiceOption'].append({'ShipToLocation': 'Worldwide', 'ShippingService': sd['international'][key]['code'], 'ShippingServiceCost': sd['international'][key]['value'],
                                                                                            'FreeShipping': int(sd['international'][key]['value'] == 0)})
                feature_list = []
                if features:
                    cat_feature_ids = []
                    if self.productcategory is not None:
                        cat_features = db.session.query(ProductCategory_ProductFeature.productfeature_id).filter(ProductCategory_ProductFeature.productcategory_id == self.productcategory.id).all()
                        cat_feature_ids = [cat_feature[0] for cat_feature in cat_features]
                    query = db.session.query(Product_ProductFeatureValue, ProductFeatureValue, ProductFeature).filter(
                        Product_ProductFeatureValue.product_id == self.id
                    ).filter(
                        Product_ProductFeatureValue.productfeaturevalue_id == ProductFeatureValue.id
                    ).filter(
                        ProductFeatureValue.productfeature_id == ProductFeature.id
                    ).filter(
                        ProductFeature.source == 'lotus'
                    ).filter(
                        ProductFeature.id.in_(cat_feature_ids) if self.productcategory is not None else True
                    ).order_by(
                        ProductFeature.id
                    ).all()
                    if query:
                        feature = query[0][2]
                        feature_dict = {'Name': feature.name}
                        values = ''
                        for row in query:
                            if row[2].name != feature.name:
                                if feature_dict:
                                    if len(values) > 65:
                                        featurevalues = feature.get_value_product_values(self.id)
                                        if feature.name in ['Textsprache im Spiel / Subtitles', 'Sprachausgabe / Ingame language']:
                                            featurevalues_test = [get_iso_lang_code(featurevalue, ext_vals=True) for featurevalue in featurevalues]
                                            values = ', '.join(featurevalues_test)
                                            if len(values) > 65:
                                                featurevalues = [get_iso_lang_code(featurevalue) for featurevalue in featurevalues]
                                                values = ', '.join(featurevalues)
                                        else:
                                            m = 0
                                            while len(values) > 65 and m < 20:
                                                m += 1
                                                featurevalues.pop()
                                                values = ', '.join(featurevalues)
                                    feature_dict['Value'] = values
                                    feature_list.append(feature_dict)
                                    feature_dict = {}
                                feature = row[2]
                                feature_dict['Name'] = row[2].name
                                values = row[1].value
                            else:
                                values += ', ' + row[1].value
                        feature_dict['Value'] = values
                        feature_list.append(feature_dict)
                if category and self.productcategory is not None:
                    category_id = self.productcategory.get_marketplace_code(marketplace_id)
                else:
                    category_id = None
                try:
                    r = ebay_api.patch_product(authorization, mpa.marketplace_system_id, description=mpa.gen_description() if description else None, description_revise_mode=description_revise_mode if description else None,
                                               dispatch_time_max=days if shipping_time else None, image_array=image_array if images else None, feature_array=feature_list if features else None, category_id=category_id if category_id else None,
                                               mpn=self.mpn if mpn else None, brand=self.brand if brand else None, ean=mpa.mp_hsp_id if ean else None, quantity=max(0, update_quant) if quantity else None, sku=self.internal_id if sku else None,
                                               price=selling_price if price else None, vat=tax_group[self.tax_group]['national'] if price else None, title=mpa.name if title else None,
                                               shipping_service_dict=shipping_service_dict if shipping_cost else None)
                except Exception as e:
                    if 'Code: 518' in str(e):
                        os.environ['EBAY_TR_API_LIMIT'] = '1'
                        set_key(env_vars_path, 'EBAY_TR_API_LIMIT', os.environ['EBAY_TR_API_LIMIT'])
                    raise e
        elif marketplace.name == 'Ebay' and mpa.sell_api == True:
            if not mpa.uploaded:
                raise SystemError('Offer must be online to be updated.')
            else:
                toy_cat = ProductCategory.query.filter_by(id=27).first()
                toy_cats = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]
                descr = mpa.gen_description()
                if self.category_id in toy_cats and 'ACHTUNG' not in descr:
                    raise SystemError('Toys must contain a warning in their description.')
                get_inv_req = ebay_api.get_inventory_item(sku=self.internal_id)
                get_offer_req = ebay_api.get_offer(sku=self.internal_id)
                if not get_inv_req.ok or not get_offer_req.ok:
                    raise SystemError(f'Could not find a matching offer for this request. Make sure it is uploaded first.\n{get_inv_req.text}\n{get_offer_req.text}')
                else:
                    if mpa.curr_stock > mpa.max_stock:
                        mpa.curr_stock = min(max(0, self.get_own_stock() - mpa.quantity_delta if mpa.quantity_delta else self.get_own_stock()), mpa.max_stock)
                    else:
                        mpa.curr_stock = min(max(0, self.get_own_stock() - mpa.quantity_delta if mpa.quantity_delta else self.get_own_stock()), mpa.max_stock) if mpa.curr_stock == 0 else mpa.curr_stock
                    update_quant = custom_quantity if custom_quantity is not None else mpa.curr_stock
                    data = get_offer_req.json()
                    offer_id = data['offers'][0]['offerId']
                    if own_stock > 0:
                        w_days = working_days_in_range(date.today(), mpa.product.release_date.date()) if mpa.product.release_date >= datetime.now() else 0
                        w_days += lag_days * mul
                        w_days += self.productcategory.get_stock_ship_days(self.cheapest_stock_id) * mul if self.productcategory else 0
                    else:
                        w_days = 40
                    possible_days = [0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40]
                    if w_days > 40:
                        days = 40
                        update_quant = 0
                    else:
                        days = min(i for i in possible_days if i >= w_days)
                    image_array = []
                    for image in sorted(self.pictures, key=lambda x: x.pic_type):
                        if image.link:
                            image_array.append(environ.get('IMAGE_SERVER') + image.link)
                    feature_dict = {}
                    cat_feature_ids = []
                    if self.productcategory is not None:
                        cat_features = db.session.query(ProductCategory_ProductFeature.productfeature_id).filter(ProductCategory_ProductFeature.productcategory_id == self.productcategory.id).all()
                        cat_feature_ids = [cat_feature[0] for cat_feature in cat_features]
                    query = db.session.query(Product_ProductFeatureValue, ProductFeatureValue, ProductFeature).filter(
                        Product_ProductFeatureValue.product_id == self.id
                    ).filter(
                        Product_ProductFeatureValue.productfeaturevalue_id == ProductFeatureValue.id
                    ).filter(
                        ProductFeatureValue.productfeature_id == ProductFeature.id
                    ).filter(
                        ProductFeature.source == 'lotus'
                    ).filter(
                        ProductFeature.id.in_(cat_feature_ids) if self.productcategory is not None else True
                    ).order_by(
                        ProductFeature.id
                    ).all()
                    if query:
                        feature_name = query[0][2].name
                        feature_dict[feature_name] = [query[0][1].value]
                        if len(query) > 1:
                            for conn, pfv, pf in query[1:]:
                                if pf.name != feature_name:
                                    feature_name = pf.name
                                    feature_dict[feature_name] = [pfv.value]
                                else:
                                    feature_dict[feature_name].append(pfv.value)
                    if 'Herausgeber' in feature_dict:
                        if len(feature_dict['Herausgeber']) > 1:
                            feature_dict['Herausgeber'] = [feature_dict['Herausgeber'][0]]
                    if 'Material' in feature_dict:
                        if len(feature_dict['Material']) > 1:
                            feature_dict['Material'] = [', '.join(feature_dict['Material'])]
                    if 'Marke' not in feature_dict:
                        feature_dict['Marke'] = [self.brand]
                    if 'Typ' in feature_dict:
                        if len(feature_dict['Typ']) > 1:
                            feature_dict['Typ'] = [feature_dict['Typ'][0]]
                    feature_dict.pop('Warnhinweise', None)
                    if 'Altersempfehlung' in feature_dict:
                        if len(feature_dict['Altersempfehlung']) > 1:
                            val = ''
                            for el in feature_dict['Altersempfehlung']:
                                if 'bis' in el:
                                    val += el
                                else:
                                    num = "".join(re.findall("\d+", el))
                                    val = f'{num} {val}'
                            feature_dict['Altersempfehlung'] = [val]
                    ebay_api.put_inventory_item(brand=self.brand, description='', ean=mpa.mp_hsp_id, feature_dict=feature_dict, image_array=image_array, mpn=self.mpn, quantity=max(0, update_quant),
                                                sku=self.internal_id, title=mpa.name, product_id=self.id)
                    if self.productcategory is not None:
                        category_id = mpa.mp_cat_id
                    else:
                        category_id = ''
                    ebay_shipping_info = self.get_ebay_shipping()
                    if "international" in ebay_shipping_info:
                        shipping_services = [{"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["national"]["value"]}, "shippingServiceType": "DOMESTIC"},
                                             {"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["international"]["value"]}, "shippingServiceType": "INTERNATIONAL"}]
                        ff_policy_id = ebay_ff_policy_ids[f'{ebay_shipping_info["national"]["code"]} & {ebay_shipping_info["international"]["code"]} - {days} DAYS']
                    else:
                        shipping_services = [{"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["national"]["value"]}, "shippingServiceType": "DOMESTIC"}]
                        ff_policy_id = ebay_ff_policy_ids[f'{ebay_shipping_info["national"]["code"]} - {days} DAYS']
                    print(f'SHORT-SELL:\t{self.short_sell}')
                    print(f'OWN-STOCK:\t{own_stock}')
                    print(f'DAYS:\t{days}')
                    print(f'POL-ID:\t{ff_policy_id}')
                    r = ebay_api.update_offer(offer_id=offer_id, currency='EUR', description=descr, fulfillment_policy_id=ff_policy_id, quantity=max(0, update_quant),
                                              price=selling_price if not custom_price else custom_price, shipping_services=shipping_services, vat=tax_group[self.tax_group]['national'],
                                              product_id=self.id, category_id=category_id)
        elif marketplace.name == 'Lotus':
            image_array = []
            if images:
                for image in sorted(self.pictures, key=lambda x: x.pic_type):
                    if image.link:
                        image_array.append(environ.get('IMAGE_SERVER') + image.link)
            r = shopify.put_product(mpa.marketplace_system_id, mpa.gen_description() if description else None, mpa.name if title else None, image_array if images else None,
                                    self.productcategory.name if category else None, self.hsp_id if ean else None, max(0, update_quant) if quantity else None, selling_price if price else None,
                                    self.internal_id if sku else None, self.weight if weight else None)
        else:
            raise SystemError('Marketplace not implemented.')
        if r.status_code < 300 and price is True:
            mpa.uploaded = True
            self.add_pricing_log(marketplace_id, selling_price if not custom_price else custom_price, psa.id, pricingstrategy_id=pricingstrategy_id)
            db.session.commit()
        return r


    def mp_prq_update(self, marketplace_id: int, shipping_time: bool = True, quantity: bool = True, price: bool = True, shipping_cost: bool = True, custom_quantity: int = None, custom_price: int = None,
                      pricingstrategy_id: int = None, authorization=None, check_clearance: bool = True):
        if self.cheapest_stock_id is None:
            s, pr = self.get_cheapest_buying_price_all()
            self.cheapest_stock_id = s.id if s is not None else None
            self.cheapest_buying_price = pr
            db.session.commit()
        if self.cheapest_stock_id is None or self.cheapest_buying_price == 0:
            print('----------------------------------------------------------------------')
            print(self.id)
            print('There is no stock with positive inventory for this product or buying_price is 0.00 €.')
            print('----------------------------------------------------------------------')
            self.cheapest_stock_id = 1
            self.cheapest_buying_price = None
            if self.cheapest_buying_price == 0:
                for mpa in self.marketplace_attributes:
                    mpa.max_stock = 0
                    mpa.min_stock = 0
                    quantity = True
            db.session.commit()
        psa = Product_Stock_Attributes.query.filter_by(stock_id=self.cheapest_stock_id, product_id=self.id).first()
        marketplace = Marketplace.query.filter_by(id=marketplace_id).first()
        mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace_id, product_id=self.id).first()
        if mpa.upload_clearance is False and check_clearance is True:
            raise SystemError(f'Product ist not cleared for upload on {marketplace.name}.')
        last_price_log = self.get_last_price_by_mp(marketplace.id)
        selling_price = last_price_log.selling_price if last_price_log else mpa.selling_price
        selling_price = custom_price if custom_price else selling_price
        if shipping_cost:
            sd = self.get_shipping_dict(marketplace_id)
        stock = Stock.query.filter_by(id=self.cheapest_stock_id).first()
        own_stock_real = self.get_own_real_stock()
        mul = int(own_stock_real < 1)
        if self.release_date is None:
            if mul == 0:
                self.release_date = datetime.now()-timedelta(days=1)
                lag_days = 0
            else:
                raise SystemError('To calculate shipping-time a release-date must be provided.')
        else:
            lag_days = stock.lag_days
        update_quant = 0
        own_stock = self.get_own_stock()
        if quantity:
            if mpa.curr_stock > mpa.max_stock:
                mpa.curr_stock = min(max(0, own_stock - mpa.quantity_delta if mpa.quantity_delta else own_stock), mpa.max_stock)
            else:
                mpa.curr_stock = min(max(0, own_stock - mpa.quantity_delta if mpa.quantity_delta else own_stock), mpa.max_stock) if mpa.curr_stock == 0 else mpa.curr_stock
            update_quant = custom_quantity if custom_quantity is not None else mpa.curr_stock
        db.session.commit()
        if marketplace.name == 'Idealo':
            delivery_comment = None
            delivery = None
            if shipping_time:
                if not self.nat_shipping_1 or not self.release_date:
                    delivery = None
                    delivery_comment = None
                else:
                    w_days = working_days_in_range(date.today(), mpa.product.release_date.date()) if mpa.product.release_date >= datetime.now() else 0
                    w_days += lag_days * mul
                    w_days += self.productcategory.get_stock_ship_days(self.cheapest_stock_id) * mul if self.productcategory else 0
                    delivery = f'Lieferzeit: {self.nat_shipping_1.min_days + w_days}-{self.nat_shipping_1.max_days + w_days} Werktage'
                    if self.release_date > datetime.now():
                        delivery_comment = f'Release-Datum: {datetime.strftime(self.release_date, "%d.%m.%Y")} / Voraussichtlicher Versand am {datetime.strftime(self.release_date - timedelta(days=1), "%d.%m.%Y")}'
                    else:
                        delivery_comment = 'Auf Lager, versandfertig innerhalb von 24 Stunden' if mul == 0 else f'Ware bestellt, versandfertig innerhalb von {24 * (w_days)} Stunden'
            cop = max(0, own_stock-mpa.quantity_delta) if mpa.quantity_delta else max(0, own_stock) if update_quant > 0 else 0 if quantity else None
            r = idealo_offer.patch_offer(authorization, self.id, self.internal_id, price = selling_price if price else None, delivery_comment = delivery_comment if shipping_time else None,
                                         delivery=delivery if shipping_time else None, checkout_limit_per_period=cop if mpa.max_stock > 0 else 0, quantity_per_order=max(0, update_quant) if quantity else None)
        elif marketplace.name == 'Ebay' and mpa.sell_api == True:
            if not mpa.uploaded:
                raise SystemError('Offer must be online to be updated.')
            else:
                toy_cat = ProductCategory.query.filter_by(id=27).first()
                toy_cats = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]
                descr = mpa.gen_description()
                if self.category_id in toy_cats and 'ACHTUNG' not in descr:
                    raise SystemError('Toys must contain a warning in their description.')
                get_inv_req = ebay_api.get_inventory_item(sku=self.internal_id)
                get_offer_req = ebay_api.get_offer(sku=self.internal_id)
                print(get_inv_req)
                print(get_offer_req)
                if not get_inv_req.ok or not get_offer_req.ok:
                    raise SystemError(f'Could not find a matching offer for this request. Make sure it is uploaded first.\n{get_inv_req.text}\n{get_offer_req.text}')
                else:
                    if mpa.curr_stock > mpa.max_stock:
                        mpa.curr_stock = min(max(0, self.get_own_stock() - mpa.quantity_delta if mpa.quantity_delta else self.get_own_stock()), mpa.max_stock)
                    else:
                        mpa.curr_stock = min(max(0, self.get_own_stock() - mpa.quantity_delta if mpa.quantity_delta else self.get_own_stock()), mpa.max_stock) if mpa.curr_stock == 0 else mpa.curr_stock
                    update_quant = custom_quantity if custom_quantity is not None else mpa.curr_stock
                    data = get_offer_req.json()
                    offer_id = data['offers'][0]['offerId']
                    w_days = working_days_in_range(date.today(), mpa.product.release_date.date()) if mpa.product.release_date >= datetime.now() else 0
                    w_days += lag_days * mul
                    w_days += self.productcategory.get_stock_ship_days(self.cheapest_stock_id) * mul if self.productcategory else 0
                    possible_days = [0, 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40]
                    if w_days > 20:
                        days = 20
                        update_quant = 0
                    else:
                        days = min(i for i in possible_days if i >= w_days)
                    if self.productcategory is not None:
                        category_id = mpa.mp_cat_id
                    else:
                        category_id = ''
                    ebay_shipping_info = self.get_ebay_shipping()
                    if "international" in ebay_shipping_info:
                        shipping_services = [{"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["national"]["value"]}, "shippingServiceType": "DOMESTIC"},
                                             {"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["international"]["value"]}, "shippingServiceType": "INTERNATIONAL"}]
                        ff_policy_id = ebay_ff_policy_ids[f'{ebay_shipping_info["national"]["code"]} & {ebay_shipping_info["international"]["code"]} - {days} DAYS']
                    else:
                        shipping_services = [{"priority": 1, "shippingCost": {"currency": "EUR", "value": ebay_shipping_info["national"]["value"]}, "shippingServiceType": "DOMESTIC"}]
                        ff_policy_id = ebay_ff_policy_ids[f'{ebay_shipping_info["national"]["code"]} - {days} DAYS']
                    p = ebay_api.put_inventory_item(sku=self.internal_id, product_id=self.id, quantity=max(0, update_quant))
                    r = ebay_api.update_offer(offer_id=offer_id, currency='EUR', description=mpa.gen_description(), fulfillment_policy_id=ff_policy_id, quantity=max(0, update_quant),
                                              price=selling_price, shipping_services=shipping_services, vat=tax_group[self.tax_group]['national'],
                                              product_id=self.id, category_id=category_id)
        elif marketplace.name == 'Lotus':
            r = shopify.put_product(mpa.marketplace_system_id, max(0, update_quant) if quantity else None, selling_price if price else None)
        else:
            raise SystemError(f'Marketplace {mpa.marketplace.name} not implemented for this function.')
        if r.status_code < 300:
            mpa.uploaded = True
            self.add_pricing_log(marketplace_id, selling_price, psa.id, pricingstrategy_id=pricingstrategy_id)
            db.session.commit()
        return r


    def mp_delete(self, marketplace_id: int, authorization=None):
        marketplace = Marketplace.query.filter_by(id=marketplace_id).first()
        mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace_id, product_id=self.id).first()
        if marketplace.name == 'Idealo':
            return idealo_offer.delete_offer(authorization, self.id, self.internal_id)
        elif marketplace.name == 'Ebay' and mpa.sell_api is True:
            return ebay_api.delete_inventory_item(sku=self.internal_id)
        elif marketplace.name == 'Lotus':
            return shopify.del_product(mpa.marketplace_system_id)
        else:
            raise SystemError(f'Marketplace {mpa.marketplace.name} not implemented for this function.')


    def mp_offer_check(self, marketplace_id: int, quant: int, price: float, not_listed: bool):
        if type(marketplace_id) != int:
            raise TypeError('Variable marketplace_id must be of type int.')
        if quant is not None and type(quant) != int:
            raise TypeError('Variable quant must be of type int.')
        if price is not None and type(price) != float:
            raise TypeError('Variable price must be of type float.')
        if type(not_listed) != bool:
            raise TypeError('Variable not_listed must be of type bool.')
        mpa = Marketplace_Product_Attributes.query.filter_by(product_id=self.id, marketplace_id=marketplace_id).first()
        if quant is not None:
            quant_diff_tag = ProductTag.query.filter_by(name='AVAILQUANT-DIFF', marketplace_id=marketplace_id).first()
            check_quant_diff_tag = PrTagRelation.query.filter_by(tag_id=quant_diff_tag.id, product_id=self.id).first()
            if mpa.curr_stock != quant and check_quant_diff_tag is None:
                db.session.add(PrTagRelation(self.id, quant_diff_tag.id))
                db.session.commit()
            elif mpa.curr_stock == quant and check_quant_diff_tag is not None:
                db.session.delete(check_quant_diff_tag)
                db.session.commit()
            oos_tag = ProductTag.query.filter_by(name='OUT_OF_STOCK', marketplace_id=marketplace_id).first()
            check_oos_tag = PrTagRelation.query.filter_by(tag_id=oos_tag.id, product_id=self.id).first()
            if quant == 0 and check_oos_tag is None:
                db.session.add(PrTagRelation(self.id, oos_tag.id))
                db.session.commit()
            elif quant > 0 and check_oos_tag is not None:
                db.session.delete(check_oos_tag)
                db.session.commit()
        if price is not None:
            pr_log = self.get_last_price_by_mp(marketplace_id)
            if pr_log is not None:
                price_diff_tag = ProductTag.query.filter_by(name='PRICE-DIFF', marketplace_id=marketplace_id).first()
                check_price_diff_tag = PrTagRelation.query.filter_by(tag_id=price_diff_tag.id, product_id=self.id).first()
                if pr_log.selling_price != price and check_price_diff_tag is None:
                    db.session.add(PrTagRelation(self.id, price_diff_tag.id))
                    db.session.commit()
                elif pr_log.selling_price == price and check_price_diff_tag is not None:
                    db.session.delete(check_price_diff_tag)
                    db.session.commit()
        not_listed_tag = ProductTag.query.filter_by(name='NOT LISTED', marketplace_id=marketplace_id).first()
        check_not_listed_tag = PrTagRelation.query.filter_by(tag_id=not_listed_tag.id, product_id=self.id).first()
        if not_listed is True and check_not_listed_tag is None:
            db.session.add(PrTagRelation(self.id, not_listed_tag.id))
            db.session.commit()
        elif not_listed is False and check_not_listed_tag is not None:
            db.session.delete(check_not_listed_tag)
            db.session.commit()


    def ab_upload_xml_gen(self, product_tree: ETree, insert: bool = False, ean: bool = False, mpn: bool = False, name: bool = False, descriptions: bool = False, search_optimization: bool = False, buying_price: bool = False,
                          selling_price: bool = False, stock_update: dict = None, tags: list = None, weight: bool = False, images: bool = False, brand: bool = False, stock_location_1: bool = False):
        ebay = Marketplace.query.filter_by(name='Ebay').first()
        ebay_mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=ebay.id, product_id=self.id).first()
        product = ETree.SubElement(product_tree, 'Product')
        p_ident = ETree.SubElement(product, 'ProductIdent')
        add_node('ProductInsert', str(int(insert)), p_ident)
        add_node('ProductID', self.internal_id, p_ident)
        if ean:
            add_node('Anr', self.hsp_id, product)
            add_node('EAN', self.hsp_id, product)
            add_node('ManufacturerStandardProductIDType', self.hsp_id_type, product)
            add_node('ManufacturerStandardProductIDValue', self.hsp_id, product)
        if name:
            add_node('Name', ebay_mpa.name, product) if name else None
            add_node('TitleReplace', '1', product)
        add_node('ManufacturerPartNumber', self.mpn, product) if mpn else None
        if descriptions:
            description = ebay_mpa.gen_description()
            add_node('Description', description, product)
        if search_optimization:
            seo = f'{self.productcategory.name}' if self.productcategory else ''
            seo += f' {ebay_mpa.name}'.replace(' ', '-')
            add_node('SeoName', seo, product)
            search_alias = f'{ebay_mpa.name} EAN {self.hsp_id}'
            search_alias += f' MPN {self.mpn}' if self.mpn else ''
            search_alias += f' {self.brand}'
            add_node('SearchAlias', search_alias, product)
            add_node('ShortDescription', seo, product)
        if buying_price:
            add_node('BuyingPrice', float_to_comma(self.buying_price), product)
        if selling_price:
            add_node('SellingPrice', float_to_comma(ebay_mpa.selling_price), product)
            add_node('TaxRate', float_to_comma(tax_group[self.tax_group]["national"]), product)
        if stock_update:
            add_node('Quantity', stock_update["quantity"], product) if 'quantity' in stock_update else None
            add_node('AddQuantity', stock_update["add_quantity"], product) if 'add_quantity' in stock_update else None
            add_node('AuctionQuantity', stock_update["auction_quantity"], product) if 'auction_quantity' in stock_update else None
            add_node('AddAuctionQuantity', stock_update["add_auction_quantity"], product) if 'add_auction_quantity' in stock_update else None
            add_node('MergeStock', stock_update["merge_stock"], product) if 'merge_stock' in stock_update else None
        if tags:
            tag_node = ETree.SubElement(product, 'Tags')
            for tag in tags:
                add_node('Tag', tag, tag_node)
        if stock_location_1 is True:
            add_node('Stocklocation_1', self.internal_id, product)
        add_node('Stock', '1', product)
        add_node('Discontinued', '1', product)
        add_node('Weight', float_to_comma(self.weight), product) if weight else None
        if images:
            bigpic = ProductPicture.query.filter_by(product_id=self.id, pic_type=0).first()
            if bigpic:
                add_node('ImageLargeURL', lookup.image_server + bigpic.link, product) if bigpic.link else None
            smallpic = ProductPicture.query.filter_by(product_id=self.id, pic_type=1).first()
            if smallpic:
                add_node('ImageSmallURL', lookup.image_server + smallpic.link, product) if smallpic.link else None
        if brand:
            add_node('ProductBrand', self.brand, product) if self.brand else None
        return product_tree


    def add_pricing_log(self, marketplace_id: int, selling_price: float, product_stock_attributes_id: int, pricingstrategy_id: int = None):
        pricing_log = self.get_last_price_by_mp(marketplace_id)
        sd = self.get_shipping_dict(marketplace_id)
        set_log = False
        log = None
        if pricing_log:
            if pricing_log.pricingstrategy_id != pricingstrategy_id and pricingstrategy_id is not None or abs(pricing_log.selling_price - selling_price) >= 0.01:
                set_log = True
        else:
            set_log = True
        if set_log:
            ns_1 = sd['national'].get(self.nat_shipping_1_id)
            ns_2 = sd['national'].get(self.nat_shipping_2_id)
            ns_3 = sd['national'].get(self.nat_shipping_3_id)
            ns_4 = sd['national'].get(self.nat_shipping_4_id)
            is_1 = sd['international'].get(self.int_shipping_1_id)
            is_2 = sd['international'].get(self.int_shipping_2_id)
            is_3 = sd['international'].get(self.int_shipping_3_id)
            is_4 = sd['international'].get(self.int_shipping_4_id)
            log = PricingLog(selling_price, ns_1['value'] if ns_1 else None, ns_2['value'] if ns_2 else None, ns_3['value'] if ns_3 else None, ns_4['value'] if ns_4 else None, is_1['value'] if is_1 else None,
                             is_2['value'] if is_2 else None, is_3['value'] if is_3 else None, is_4['value'] if is_4 else None, datetime.now(), marketplace_id, pricingstrategy_id, self.id, product_stock_attributes_id)
            db.session.add(log)
            mpa = Marketplace_Product_Attributes.query.filter_by(product_id=self.id, marketplace_id=marketplace_id)
            mpa.pr_update_dur = 6
            k = datetime.now().hour // 6
            mpa.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
            db.session.commit()
        return log


    def generate_mp_price(self, marketplace_id: int, strategy_label: int, strategy_id: int = None, min_margin: float = None, max_margin: float = None, rank: int = 0, ext_offers: list = None, authorization=None,
                          send: bool = True, save: bool = False):
        if type(marketplace_id) != int:
            raise TypeError('Variable marketplace_id must be of type int.')
        if type(strategy_label) != int:
            raise TypeError('Variable strategy_label must be of type int.')
        if strategy_id is not None:
            if type(strategy_id) != int:
                raise TypeError('Variable strategy_id must be of type int.')
            s = PricingStrategy.query.filter_by(id=strategy_id).first()
            if not s:
                raise ValueError(f'No PricingStrategy with id {strategy_id} found.')
        if min_margin is not None and type(min_margin) != float:
            raise TypeError('Optional variable min_margin must be of type float.')
        if rank is not None and type(rank) != int:
            raise TypeError('Optional variable rank must be of type int.')
        if ext_offers is None:
            ext_offers = []
        elif type(ext_offers) != list:
            raise TypeError('Optional variable ext_offers must be of type list.')
        if strategy_label in [1, 3] and min_margin is None:
            raise SystemError('This strategy requires a min_margin.')
        if strategy_label == 2 and (rank is None or min_margin is None):
            raise SystemError('This strategy requires the variables rank and min_margin.')
        if self.cheapest_buying_price is None:
            s, pr = self.get_cheapest_buying_price_all()
            self.cheapest_stock_id = s.id if s is not None else None
            self.cheapest_buying_price = pr if pr > 0 else None
            db.session.commit()
            if self.cheapest_buying_price is None:
                raise SystemError('This product requires a valid buying_price.')
        if self.cheapest_stock_id is None or self.cheapest_buying_price == 0:
            print('----------------------------------------------------------------------')
            print(self.id)
            print('There is no stock with positive inventory for this product or buying_price is 0.00 €.')
            print('----------------------------------------------------------------------')
            self.cheapest_stock_id = 1
            self.cheapest_buying_price = None
            if self.cheapest_buying_price == 0:
                for mpa in self.marketplace_attributes:
                    mpa.max_stock = 0
                    mpa.min_stock = 0
            db.session.commit()
        if self.tax_group is None:
            raise SystemError('This product requires a valid tax_group.')
        elif self.tax_group not in tax_group:
            raise SystemError('This product requires a valid tax_group.')
        mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace_id, product_id=self.id).first()
        if mpa.commission is None:
            raise SystemError('This product requires a valid commission for this marketplace.')
        if send and mpa.marketplace.name == 'Ebay' and not mpa.marketplace_system_id and mpa.uploaded:
            mpa.marketplace_system_id = self.get_ebay_id()
            db.session.commit()
            if mpa.marketplace_system_id is None:
                raise SystemError('An offer could not be found for this product. Please check if it is online and provide a valid offer_id.')
        query = db.session.query(ShippingService, MPShippingService, ShippingProfilePrice).filter(
            or_(ShippingService.id == self.nat_shipping_1_id,
                ShippingService.id == self.nat_shipping_2_id,
                ShippingService.id == self.nat_shipping_3_id,
                ShippingService.id == self.nat_shipping_4_id)
        ).filter(
            MPShippingService.shipping_service_id == ShippingService.id
        ).filter(
            MPShippingService.marketplace_id == marketplace_id
        ).filter(
            ShippingProfilePrice.profile_id == self.shipping_profile_id
        ).filter(
            ShippingProfilePrice.mp_service_id == MPShippingService.id
        ).all()
        if not query:
            raise SystemError('Shipping needs to be configured for this Product.')
        _, i = min((row[2].price-row[0].price, i) for (i, row) in enumerate(query))
        shipping = query[i][2].price
        own_shipping = query[i][0].price
        if shipping is None or own_shipping is None:
            raise SystemError('Shipping needs to be configured for this Product.')
        price = None
        sent_own = False
        sent_kb = False
        no_result = False
        neg_margin = False
        ult_err = False
        no_stock = False
        not_listed = False
        price_logged = False
        if mpa.marketplace.name == 'Idealo' and ext_offers:
            ext_offers[0]['price'] = ext_offers[0]['price'] * 1.04
            ext_offers[0]['shipping'] = ext_offers[0]['shipping'] * 1.04
        if strategy_label == 0:
            price = mpa.selling_price
            sent_own = True
        if strategy_label == 1 or strategy_label == 2:
            price_found = False
            no_result = True
            for ext_offer in ext_offers[min(rank, len(ext_offers)-1):]:
                no_result = False
                ext_price = float(ext_offer['price'])
                ext_shipping = float(ext_offer['shipping'])
                cents = ext_price + ext_shipping - math.floor(ext_price + ext_shipping)
                price = math.floor(ext_price + ext_shipping) - 1 + 0.89 + int(cents >= 0.4) * 0.5 + int(cents >= 0.9) * 0.5 - shipping
                margin = marketplace_price_performance_measure(mpa.marketplace.name, price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                               tax_group[self.tax_group]['national'])['prc_margin']
                if margin >= min_margin:
                    if margin < 0:
                        neg_margin = True
                    price_found = True
                    break
            if not price_found:
                if no_result is True:
                    min_price = math.floor(self.cheapest_buying_price + shipping) + 0.89 + math.floor(self.cheapest_buying_price / 2)
                    margin = marketplace_price_performance_measure(mpa.marketplace.name, min_price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                                   tax_group[self.tax_group]['national'])['prc_margin']
                    if margin > min_margin:
                        while margin > min_margin:
                            min_price -= 0.5
                            margin = marketplace_price_performance_measure(mpa.marketplace.name, min_price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                                           tax_group[self.tax_group]['national'])['prc_margin']
                        min_price += 0.5
                    else:
                        while margin < min_margin:
                            min_price += 0.5
                            margin = marketplace_price_performance_measure(mpa.marketplace.name, min_price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                                           tax_group[self.tax_group]['national'])['prc_margin']
                    price = min_price
                else:
                    price = mpa.selling_price if max_margin is None else math.inf
                sent_own = True
            if max_margin is not None:
                max_price = math.floor(self.cheapest_buying_price + shipping) + 0.89 + math.floor(self.cheapest_buying_price / 2)
                margin = marketplace_price_performance_measure(mpa.marketplace.name, max_price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                               tax_group[self.tax_group]['national'])['prc_margin']
                if margin > max_margin:
                    while margin > max_margin:
                        max_price -= 0.5
                        margin = marketplace_price_performance_measure(mpa.marketplace.name, max_price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                                       tax_group[self.tax_group]['national'])['prc_margin']
                else:
                    while margin < max_margin:
                        max_price += 0.5
                        margin = marketplace_price_performance_measure(mpa.marketplace.name, max_price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                                       tax_group[self.tax_group]['national'])['prc_margin']
                    max_price -= 0.5
                price = min(max_price, price) if no_result is False else max_price
        elif strategy_label == 3:
            price = math.floor(self.cheapest_buying_price + shipping) + 0.89 + math.floor(self.cheapest_buying_price / 2)
            margin = marketplace_price_performance_measure(mpa.marketplace.name, price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                           tax_group[self.tax_group]['national'])['prc_margin']
            if margin > min_margin:
                while margin > min_margin:
                    price -= 0.5
                    margin = marketplace_price_performance_measure(mpa.marketplace.name, price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                                   tax_group[self.tax_group]['national'])['prc_margin']
                price += 0.5
            else:
                while margin < min_margin:
                    price += 0.5
                    margin = marketplace_price_performance_measure(mpa.marketplace.name, price, shipping, own_shipping, self.cheapest_buying_price, mpa.commission,
                                                                   tax_group[self.tax_group]['national'])['prc_margin']
        pricing_log = self.get_last_price_by_mp(marketplace_id)
        last_price = pricing_log.selling_price if pricing_log else None
        if last_price == price:
            if pricing_log.pricingstrategy_id != strategy_id and send == True:
                if self.cheapest_stock_id:
                    psa = Product_Stock_Attributes.query.filter_by(stock_id=self.cheapest_stock_id, product_id=self.id).first()
                else:
                    own_stock = Stock.query.filter_by(owned=True).order_by(Stock.id).first()
                    psa = Product_Stock_Attributes.query.filter_by(stock_id=own_stock.id, product_id=self.id).first()
                self.add_pricing_log(marketplace_id, price, psa.id, pricingstrategy_id=strategy_id)
                db.session.commit()
        elif last_price != price and price > 0:
            print(last_price)
            print(price)
            if save is True and mpa.block_selling_price is False:
                mpa.selling_price = price
                db.session.commit()
            if send:
                if self.cheapest_stock_id:
                    psa = Product_Stock_Attributes.query.filter_by(stock_id=self.cheapest_stock_id, product_id=self.id).first()
                else:
                    own_stock = Stock.query.filter_by(owned=True).order_by(Stock.id).first()
                    psa = Product_Stock_Attributes.query.filter_by(stock_id=own_stock.id, product_id=self.id).first()
                if mpa.uploaded is False:
                    if mpa.marketplace.name in ['Lotus', 'Ebay'] and mpa.uploaded is False:
                        not_listed = True
                        return [sent_own, sent_kb, no_result, neg_margin, ult_err, no_stock, not_listed, price_logged]
                    else:
                        r = self.mp_upload(int(marketplace_id), custom_price=price, authorization=authorization)
                        if r.status_code < 300:
                            self.add_pricing_log(marketplace_id, price, psa.id, pricingstrategy_id=strategy_id)
                            price_logged = True
                else:
                    r = self.mp_prq_update(int(marketplace_id), price=True, custom_price=price, shipping_cost=True, shipping_time=True, pricingstrategy_id=strategy_id, authorization=authorization)
                    if r.status_code < 300:
                        price_logged = True
        return [sent_own, sent_kb, no_result, neg_margin, ult_err, no_stock, not_listed, price_logged, price]


    def get_ebay_id(self):
        ebay_request = {'keywords': {self.hsp_id},
                        'itemFilter': [{'name': 'Seller', 'value': 'lotus-icafe'}],
                        'sortOrder': 'PricePlusShippingLowest'
                        }
        finding_connection = Finding_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), siteid="EBAY-DE")
        response = finding_connection.execute('findItemsAdvanced', ebay_request)
        if int(response.reply.paginationOutput.totalPages) > 0:
            for item in response.reply.searchResult.item:
                return item.itemId
        return None


    def get_mp_ext_offers(self, marketplace_id: int):
        marketplace = Marketplace.query.filter_by(id=marketplace_id).first()
        if marketplace.name in ['Idealo', 'Lotus']:
            ebay = Marketplace.query.filter_by(name='Ebay').first()
            pricing_log = self.get_last_price_by_mp(ebay.id)
            ebay_price = pricing_log.selling_price if pricing_log else None

            offers = ExtOffer.query.outerjoin(ExtSeller).outerjoin(ExtPlatform).filter(
                ExtOffer.product_id == self.id
            ).filter(
                ExtOffer.marketplace_id == marketplace_id
            ).filter(
                ExtSeller.name != 'lotus-icafe'
            ).filter(
                ExtPlatform.name != 'lotusicafe'
            ).filter(
                ExtOffer.last_seen >= datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=18)
            ).all()
            offers.sort(key=lambda x: x.selling_price + x.shipping_price)
            return [{'price': offer.selling_price, 'shipping': offer.shipping_price} for offer in offers if offer.selling_price!=ebay_price]
        elif marketplace.name == 'Ebay':
            mpa = Marketplace_Product_Attributes.query.filter_by(product_id=self.id, marketplace_id=marketplace_id).first()
            request = {
                'keywords': {mpa.search_term},
                'itemFilter': [
                    {'name': 'Condition', 'value': 'New'},
                    {'name': 'ListingType', 'value': 'FixedPrice'},
                    {'name': 'MinQuantity', 'value': 2},
                    {'name': 'ExcludeSeller', 'value': 'lotus-icafe'}
                ],
                'sortOrder': 'PricePlusShippingLowest'
            }
            finding_connection = Finding_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), siteid="EBAY-DE")
            r = finding_connection.execute('findItemsAdvanced', request)
            if r.status_code < 300:
                print(r.text)
                if int(r.reply.paginationOutput.totalPages) > 0:
                    ext_offers = []
                    for item in r.reply.searchResult.item:
                        try:
                            ext_offer = {'price': item.sellingStatus.convertedCurrentPrice.value, 'shipping': item.shippingInfo.shippingServiceCost.value}
                            ext_offers.append(ext_offer)
                        except Exception as e:
                            print(e)
                            continue
                    return ext_offers
                else:
                    return []
            else:
                return []

    def cheapest_stock(self):
        return Stock.query.filter_by(id=self.cheapest_stock_id).first()

    def get_featurevalues(self):
        subquery = db.session.query(
            Product_ProductFeatureValue.id.label('ppfv_id'), ProductFeatureValue.id.label('pfv_id'), ProductFeature.id.label('pf_id')
        ).filter(
            ProductFeature.source == 'lotus'
        ).filter(
            Product_ProductFeatureValue.product_id == self.id
        ).filter(
            Product_ProductFeatureValue.productfeaturevalue_id == ProductFeatureValue.id
        ).filter(
            ProductFeatureValue.productfeature_id == ProductFeature.id
        ).subquery()
        return ProductFeatureValue.query.join(subquery, ProductFeatureValue.id==subquery.c.pfv_id).all()

    def get_ext_featurevalues(self):
        subquery = db.session.query(
            Product_ProductFeatureValue.id.label('ppfv_id'), ProductFeatureValue.id.label('pfv_id'), ProductFeature.id.label('pf_id')
        ).filter(
            ProductFeature.source != 'lotus'
        ).filter(
            Product_ProductFeatureValue.product_id == self.id
        ).filter(
            Product_ProductFeatureValue.productfeaturevalue_id == ProductFeatureValue.id
        ).filter(
            ProductFeatureValue.productfeature_id == ProductFeature.id
        ).subquery()

        return ProductFeatureValue.query.join(subquery, ProductFeatureValue.id==subquery.c.pfv_id).all()

    def get_orders(self):
        ids = Order_Product_Attributes.query.filter_by(product_id=self.id).all()
        return Order.query.filter(Order.id.in_([item.order_id for item in ids])).all()

    def get_stocks(self):
        ids = Product_Stock_Attributes.query.filter_by(product_id=self.id).all()
        return Stock.query.filter(Stock.id.in_([item.stock_id for item in ids])).all()

    def get_users(self):
        ids = Product_User_Attributes.query.filter_by(product_id=self.id).all()
        return User.query.filter(User.id.in_([item.user_id for item in ids])).all()

    def bigpic(self):
        return ProductPicture.query.filter_by(product_id=self.id, pic_type=0).first()

    def smallpic(self):
        return ProductPicture.query.filter_by(product_id=self.id, pic_type=1).first()

    def otherpics(self):
        return ProductPicture.query.filter_by(product_id=self.id, pic_type=2).all()

    def picturearray(self):
        try:
            return [self.bigpic().link, self.smallpic().link] + [pic.link for pic in self.otherpics()]
        except:
            return []

    def productlink(self, category_id):
        link = ProductLink.query.filter_by(product_id=self.id, category_id=category_id).first()
        if link is not None:
            return link.link
        else:
            return ''

    def get_marketplace_attributes(self, marketplace_id):
        return Marketplace_Product_Attributes.query.filter_by(product_id=self.id, marketplace_id=marketplace_id).first()

    def get_last_10_prices_mp(self, marketplace_id):
        logs = PricingLog.query.filter_by(product_id=self.id, marketplace_id=marketplace_id).order_by(PricingLog.set_date.desc()).limit(10).all()
        logs.reverse()
        if len(logs)<10:
            logs = (10-len(logs))*[None] + logs
        return logs

    def get_cheapest_ext_idealo_price(self):
        timestamp = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=18)
        offer = ExtOffer.query.filter_by(
            product_id=self.id, marketplace_id=1
        ).filter(
            ExtOffer.last_seen >= timestamp
        ).filter(
            ExtOffer.seller_id != 1830
        ).filter(
            ExtOffer.seller_id != 26
        ).order_by(
            ExtOffer.selling_price
        ).first()
        if offer:
            return offer
        else:
            return None

    def get_three_cheapest_ext_stocks(self):
        ps = db.session.query(
            Product_Stock_Attributes.buying_price, Stock
        ).filter(
            Product_Stock_Attributes.product_id == self.id
        ).filter(
            Product_Stock_Attributes.stock_id == Stock.id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).filter(
            Stock.owned==False
        ).order_by(
            Product_Stock_Attributes.buying_price
        ).limit(
            3
        ).all()
        return ps + [None] * (3-len(ps))

    def get_cheapest_stock(self):
        if self.short_sell:
            stocks = Stock.query.filter_by(owned=False).all()
        else:
            stocks = Stock.query.filter_by(owned=True).all()
        min_price = math.inf
        cheapest = None
        for stock in stocks:
            obj = self.get_stock_by_id(stock.id)
            if obj != None:
                if stock.owned:
                    buying_price = self.get_own_buying_price()
                else:
                    buying_price = obj.buying_price
                if buying_price != None:
                    if buying_price < min_price and obj.quantity > 0:
                        min_price = buying_price
                        cheapest = stock
                    elif self.release_date:
                        if self.release_date > datetime.now():
                            if buying_price < min_price:
                                min_price = buying_price
                                cheapest = stock
        if cheapest:
            #if self.get_own_buying_price():
            #    if self.get_own_buying_price() == min_price:
            #        return Stock.query.filter_by(id=1).first()
            return cheapest
        else:
            return None

    def get_cheapest_buying_price(self):
        if self.short_sell:
            stocks = Stock.query.filter_by(owned=False).all()
        else:
            stocks = Stock.query.filter_by(owned=True).all()
        min_price = math.inf
        cheapest = None
        for stock in stocks:
            obj = self.get_stock_by_id(stock.id)
            if obj != None:
                if stock.owned:
                    buying_price = self.get_own_buying_price()
                else:
                    buying_price = obj.buying_price
                if buying_price != None:
                    if buying_price < min_price and obj.quantity > 0:
                        min_price = buying_price
                        cheapest = stock
                    elif self.release_date:
                        if self.release_date > datetime.now():
                            if buying_price < min_price:
                                min_price = buying_price
                                cheapest = stock
        if cheapest:
            #if self.get_own_buying_price():
            #    if self.get_own_buying_price() == min_price:
            #        return Stock.query.filter_by(id=1).first(), min_price
            return cheapest, min_price
        else:
            return None, None


    def get_cheapest_buying_price_all(self):
        owned = None
        min_quant = 1
        if self.release_date:
            if self.release_date > datetime.now():
                min_quant = 0
        if self.get_own_real_stock() <= 0:
            owned = False
        query = db.session.query(
            Stock, func.min(Product_Stock_Attributes.buying_price)
        ).filter(
            Product_Stock_Attributes.stock_id == Stock.id
        ).filter(
            Product_Stock_Attributes.quantity >= min_quant
        ).filter(
            Product_Stock_Attributes.product_id == self.id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).filter(
            Stock.owned == owned if owned != None else True
        ).group_by(
            Stock.id
        ).order_by(
            func.min(Product_Stock_Attributes.buying_price)
        ).first()
        return (query[0], query[1]) if query else (None, None)


    def get_own_buying_price_depr(self):
        supplier = Supplier.query.filter_by(firmname='Lager').first()
        last_system_order = WSReceipt.query.filter_by(supplier_id=supplier.id, name='Nullbestellung').order_by(WSReceipt.order_time.desc()).first()

        current_shipping_stat = db.session.query(
            Order.id.label('orderid'), ShippingStatus_Log.id.label('ssl_id'), func.rank().over(order_by=ShippingStatus_Log.init_date.desc(), partition_by=Order.id).label('rnk')
        ).filter(
            ShippingStatus_Log.order_id == Order.id
        ).order_by(
            ShippingStatus_Log.init_date.desc()
        ).subquery()

        result = db.session.query(
            Order_Product_Attributes.product_id, func.max(Order_Product_Attributes.id), func.max(Order.id), func.max(current_shipping_stat.c.orderid), func.max(ShippingStatus_Log.id),
            case([(func.sum(Order_Product_Attributes.shipped)==0, 0)], else_=(func.sum(Order_Product_Attributes.price*Order_Product_Attributes.shipped))/func.sum(Order_Product_Attributes.shipped)).label('result')
        ).outerjoin(
            current_shipping_stat, current_shipping_stat.c.orderid == Order.id
        ).filter(
            Order_Product_Attributes.order_id == Order.id
        ).filter(
            Order_Product_Attributes.product_id == self.id
        ).filter(
            Order.order_time >= last_system_order.order_time
        ).filter(
            Order.order_time >= last_system_order.order_time
        ).filter(
            ShippingStatus_Log.label == 'abgeschlossen'
        ).filter(
            current_shipping_stat.c.rnk == 1
        ).filter(
            ShippingStatus_Log.id == current_shipping_stat.c.ssl_id
        ).group_by(
            Order_Product_Attributes.product_id
        ).first()
        if result:
            return result.result
        else:
            return self.buying_price

    def get_own_buying_price(self):
        start_dt = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        bp = db.session.query(
            case([(func.sum(WSRProduct.quantity) == 0, 0)], else_=(func.sum(WSRProduct.price * WSRProduct.quantity) / func.sum(WSRProduct.quantity)))
        ).filter(
            and_(
                WSRProduct.product_id == self.id,
                WSRProduct.complete == True,
                WSRProduct.completed_at >= start_dt
            )
        ).group_by(
            WSRProduct.product_id
        ).scalar()
        if bp is not None and bp != 0:
            return bp
        else:
            return self.buying_price

    def get_own_buying_price_from(self, order_time):
        orders = db.session.query(
            Order_Product_Attributes, Order
        ).filter(
            Order_Product_Attributes.order_id == Order.id
        ).filter(
            Order_Product_Attributes.product_id == self.id
        ).filter(
            Order.order_time >= order_time
        ).all()
        try:
            summed_price = sum([obj[0].price * obj[0].shipped for obj in orders if obj[1].get_current_shipping_stat_label() == 'abgeschlossen'])
            summed_quantity = sum([obj[0].shipped for obj in orders if obj[1].get_current_shipping_stat_label() == 'abgeschlossen'])
            return summed_price / summed_quantity
        except:
            return None

    def get_own_buying_price_date(self, dt):
        start_dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        bp = db.session.query(
            case([(func.sum(WSRProduct.quantity) == 0, 0)], else_=(func.sum(WSRProduct.price * WSRProduct.quantity) / func.sum(WSRProduct.quantity)))
        ).filter(
            and_(
                WSRProduct.product_id == self.id,
                WSRProduct.complete == True,
                WSRProduct.init_dt >= start_dt,
                WSRProduct.completed_at <= dt
            )
        ).group_by(
            WSRProduct.product_id
        ).scalar()
        if bp is not None and bp != 0:
            return bp
        else:
            return self.buying_price

    @hybrid_method
    def get_own_stock(self):
        subquery = db.session.query(
            StockUpdateQueue.psa_id.label('psa_id'), func.sum(StockUpdateQueue.update_amount).label('update_amount')
        ).filter(
            StockUpdateQueue.proc_dt == None
        ).group_by(
            StockUpdateQueue.psa_id
        ).subquery()

        stock = db.session.query(
            (Product_Stock_Attributes.quantity + func.coalesce(subquery.c.update_amount, 0)).label('own_stock')
        ).outerjoin(
            subquery, Product_Stock_Attributes.id == subquery.c.psa_id
        ).filter(
            Product_Stock_Attributes.stock_id == 1,
            Product_Stock_Attributes.product_id == self.id,
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).first()

        if stock:
            return stock.own_stock
        else:
            return 0

    @get_own_stock.expression
    def get_own_stock(cls):
        subquery = db.session.query(
            StockUpdateQueue.psa_id.label('psa_id'), func.sum(StockUpdateQueue.update_amount).label('update_amount')
        ).filter(
            StockUpdateQueue.proc_dt == None
        ).group_by(
            StockUpdateQueue.psa_id
        ).subquery()

        stock = db.session.query(
            (Product_Stock_Attributes.quantity + func.coalesce(subquery.c.update_amount, 0)).label('own_stock')
        ).outerjoin(
            subquery, Product_Stock_Attributes.id == subquery.c.psa_id
        ).filter(
            Product_Stock_Attributes.stock_id == 1,
            Product_Stock_Attributes.product_id == cls.id,
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).first()

        if stock:
            return stock.own_stock
        else:
            return 0

    def get_own_real_stock(self):
        subquery = db.session.query(
            StockUpdateQueue.psa_id.label('psa_id'), func.sum(StockUpdateQueue.update_amount).label('update_amount')
        ).filter(
            StockUpdateQueue.proc_dt == None
        ).group_by(
            StockUpdateQueue.psa_id
        ).subquery()

        stock = db.session.query(
            (Product_Stock_Attributes.quantity + func.coalesce(subquery.c.update_amount, 0)).label('own_stock')
        ).outerjoin(
            subquery, Product_Stock_Attributes.id == subquery.c.psa_id
        ).filter(
            Product_Stock_Attributes.stock_id == 1,
            Product_Stock_Attributes.product_id == self.id,
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).first()
        if stock:
            return stock.own_stock - 100 if self.short_sell else stock.own_stock
        else:
            return 0

    @hybrid_method
    def get_num_actions(self):
        actions = PricingAction.query.filter(
            PricingAction.product_id==self.id
        ).all()
        num = 0
        for action in actions:
            if action.archived is False:
                num+=1
        return num

    @get_num_actions.expression
    def get_num_actions(cls):
        actions = PricingAction.query.filter(
            PricingAction.product_id==cls.id
        ).all()
        num = 0
        for action in actions:
            if action.archived is False:
                num+=1
        return num

    @hybrid_method
    def get_summed_stock(self):
        stock = db.session.query(
            func.count(Stock.id), func.sum(Product_Stock_Attributes.quantity).label("summed_stock"), Product
        ).filter(
            Stock.id == Product_Stock_Attributes.stock_id
        ).filter(
            Product.id == Product_Stock_Attributes.product_id
        ).filter(
            Product.id == self.id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.last_seen >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not Stock.owned else True
        ).group_by(
            Product.id
        ).first()
        if stock:
            return stock.summed_stock
        else:
            return 0

    @get_summed_stock.expression
    def get_summed_stock(cls):
        stock = db.session.query(
            func.count(Stock.id), func.sum(Product_Stock_Attributes.quantity).label("summed_stock"), Product
        ).filter(
            Stock.id == Product_Stock_Attributes.stock_id
        ).filter(
            Product.id == Product_Stock_Attributes.product_id
        ).filter(
            Product.id == cls.id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.last_seen >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not Stock.owned else True
        ).group_by(
            Product.id
        ).first()
        if stock:
            return stock.summed_stock
        else:
            return 0

    @hybrid_method
    def get_stock_by_stock(self, stock_id):
        stock = db.session.query(
            func.count(Stock.id), func.sum(Product_Stock_Attributes.quantity).label("summed_stock"), Product
        ).filter(
            Stock.id == Product_Stock_Attributes.stock_id
        ).filter(
            Product.id == Product_Stock_Attributes.product_id
        ).filter(
            Product.id == self.id
        ).filter(
            Stock.id == stock_id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
            if not Stock.owned else True
        ).filter(
            Product_Stock_Attributes.last_seen >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not Stock.owned else True
        ).group_by(
            Product.id
        ).first()
        if stock:
            return stock.summed_stock
        else:
            return 0

    @get_stock_by_stock.expression
    def get_stock_by_stock(cls, stock_id):
        stock = db.session.query(
            func.count(Stock.id), func.sum(Product_Stock_Attributes.quantity).label("summed_stock"), Product
        ).filter(
            Stock.id == Product_Stock_Attributes.stock_id
        ).filter(
            Product.id == Product_Stock_Attributes.product_id
        ).filter(
            Product.id == cls.id
        ).filter(
            Stock.id == stock_id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
            if not Stock.owned else True
        ).filter(
            Product_Stock_Attributes.last_seen >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not Stock.owned else True
        ).group_by(
            Product.id
        ).first()
        if stock:
            return stock.summed_stock
        else:
            return 0

    def get_stock_by_id(self, stock_id):
        stock = db.session.query(
            Product_Stock_Attributes
        ).filter(
            Product_Stock_Attributes.product_id == self.id
        ).filter(
            Product_Stock_Attributes.stock_id == stock_id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).first()
        if stock:
            return stock
        else:
            return None

    def stock_html_generator(self):
        def decimal_or_none(s):
            if s:
                return "{:.2f}".format(s) + ' €'
            else:
                return ''

        def int_or_none(i):
            if i:
                return str(i) + '  Stk.'
            else:
                return ''

        subquery = db.session.query(Product_Stock_Attributes).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).filter(
            Product_Stock_Attributes.product_id == self.id
        ).subquery()

        stocks = db.session.query(
            Stock, subquery.c.buying_price, subquery.c.shipping_cost, subquery.c.quantity, subquery.c.lag_days
        ).outerjoin(
            subquery, subquery.c.stock_id == Stock.id
        ).order_by(
            Stock.id
        ).all()
        out = ''

        for stock in stocks:
            try:
                if stock[0].owned:
                    out += '<td>' + decimal_or_none(self.get_own_buying_price()) + '<br>'+ decimal_or_none(stock[2]) + '<br>' + int_or_none(stock[3]) + '<br>' + int_or_none(stock[4]) + '</td>'
                else:
                    out += '<td>' + decimal_or_none(stock[1]) + '<br>'+ decimal_or_none(stock[2]) + '<br>' + int_or_none(stock[3]) + '<br>' + int_or_none(stock[4]) + '</td>'
            except Exception as e:
                print(e)
                out += ''
        return out

    def get_stock_by_id_html_generator2(self, stock_id, owned):
        def decimal_or_none(s):
            if s:
                return "{:.2f}".format(s) + ' €'
            else:
                return ''

        stock = db.session.query(
            Product_Stock_Attributes
        ).filter(
            Product_Stock_Attributes.product_id == self.id
        ).filter(
            Product_Stock_Attributes.stock_id == stock_id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).first()
        if stock:
            try:
                if owned:
                    return decimal_or_none(self.get_own_buying_price()) + '<br>'+ decimal_or_none(stock.shipping_cost) + '<br>' + str(stock.quantity) + '  Stk.<br>' + str(stock.lag_days)
                else:
                    return decimal_or_none(stock.buying_price) + '<br>'+ decimal_or_none(stock.shipping_cost) + '<br>' + str(stock.quantity) + '  Stk.<br>' + str(stock.lag_days)
            except:
                return ''
        else:
            return ''

    '''
    {% if stock.owned %}
        {{ '%0.2f' % (product.get_own_buying_price())|float + ' €' if product.get_stock_by_id(stock.id) }}<br>
        {{ '%0.2f' % (product.get_stock_by_id(stock.id).shipping_cost)|float + ' €' if product.get_stock_by_id(stock.id) }}<br>
        {{ product.get_stock_by_id(stock.id).quantity|string + '  Stk.' if product.get_stock_by_id(stock.id)}}<br>
        {{ product.get_stock_by_id(stock.id).lag_days }}
    {% else %}
        {{ '%0.2f' % (product.get_stock_by_id(stock.id).buying_price)|float + ' €' if product.get_stock_by_id(stock.id) }}<br>
        {{ '%0.2f' % (product.get_stock_by_id(stock.id).shipping_cost)|float + ' €' if product.get_stock_by_id(stock.id) }}<br>
        {{ product.get_stock_by_id(stock.id).quantity|string + '  Stk.' if product.get_stock_by_id(stock.id)}}<br>
        {{ product.get_stock_by_id(stock.id).lag_days }}
    {% endif %}
    '''

    @hybrid_method
    def current_rank_by_marketplace(self, marketplace_id):
        now = datetime.now()
        if now.hour < 1:
            supremum = now.replace(hour=1, minute=0, second=0, microsecond=0)
            minimum = (now - timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
        elif now.hour < 5:
            supremum = now.replace(hour=5, minute=0, second=0, microsecond=0)
            minimum = (now - timedelta(days=1)).replace(hour=21, minute=0, second=0, microsecond=0)
        elif now.hour < 9:
            supremum = now.replace(hour=9, minute=0, second=0, microsecond=0)
            minimum = now.replace(hour=1, minute=0, second=0, microsecond=0)
        elif now.hour < 13:
            supremum = now.replace(hour=13, minute=0, second=0, microsecond=0)
            minimum = now.replace(hour=5, minute=0, second=0, microsecond=0)
        elif now.hour < 17:
            supremum = now.replace(hour=17, minute=0, second=0, microsecond=0)
            minimum = now.replace(hour=9, minute=0, second=0, microsecond=0)
        elif now.hour < 21:
            supremum = now.replace(hour=21, minute=0, second=0, microsecond=0)
            minimum = now.replace(hour=13, minute=0, second=0, microsecond=0)
        else:
            supremum = now
            minimum = now.replace(hour=17, minute=0, second=0, microsecond=0)
        marketplace = Marketplace.query.filter_by(id=marketplace_id).first()
        if marketplace.name in ['Idealo', 'Lotus']:
            offer = ExtOffer.query.filter_by(
                product_id=self.id, marketplace_id=marketplace_id
            ).filter(
                supremum > ExtOffer.last_seen
            ).filter(
                ExtOffer.last_seen >= minimum
            ).filter(
                ExtOffer.get_platform_name()=='lotusicafe'
            ).first()
            if offer:
                return offer.rank
            else:
                return None
        elif marketplace.name == 'Ebay':
            offer = ExtOffer.query.filter_by(
                product_id=self.id
            ).filter(
                supremum > ExtOffer.last_seen
            ).filter(
                ExtOffer.last_seen >= minimum
            ).filter(
                ExtOffer.get_seller_name()=='lotus-icafe'
            ).filter(
                ExtOffer.get_platform_name()=='Ebay'
            ).first()
            if offer:
                return offer.rank
            else:
                return None
        else:
            return None

    @current_rank_by_marketplace.expression
    def current_rank_by_marketplace(cls, marketplace_id):
        now = datetime.now()
        if now.hour < 1:
            supremum = now.replace(hour=1, minute=0, second=0, microsecond=0)
            minimum = (now - timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
        elif now.hour < 5:
            supremum = now.replace(hour=5, minute=0, second=0, microsecond=0)
            minimum = (now - timedelta(days=1)).replace(hour=21, minute=0, second=0, microsecond=0)
        elif now.hour < 9:
            supremum = now.replace(hour=9, minute=0, second=0, microsecond=0)
            minimum = now.replace(hour=1, minute=0, second=0, microsecond=0)
        elif now.hour < 13:
            supremum = now.replace(hour=13, minute=0, second=0, microsecond=0)
            minimum = now.replace(hour=5, minute=0, second=0, microsecond=0)
        elif now.hour < 17:
            supremum = now.replace(hour=17, minute=0, second=0, microsecond=0)
            minimum = now.replace(hour=9, minute=0, second=0, microsecond=0)
        elif now.hour < 21:
            supremum = now.replace(hour=21, minute=0, second=0, microsecond=0)
            minimum = now.replace(hour=13, minute=0, second=0, microsecond=0)
        else:
            supremum = now
            minimum = now.replace(hour=17, minute=0, second=0, microsecond=0)
        marketplace = Marketplace.query.filter_by(id=marketplace_id).first()
        if marketplace.name in ['Idealo', 'Lotus']:
            offer = ExtOffer.query.filter_by(
                product_id=cls.id, marketplace_id=marketplace_id
            ).filter(
                supremum > ExtOffer.last_seen
            ).filter(
                ExtOffer.last_seen >= minimum
            ).filter(
                ExtOffer.get_platform_name()=='lotusicafe'
            ).first()
            if offer:
                return offer.rank
            else:
                return None
        elif marketplace.name == 'Ebay':
            offer = ExtOffer.query.filter_by(
                product_id=cls.id
            ).filter(
                supremum > ExtOffer.last_seen
            ).filter(
                ExtOffer.last_seen >= minimum
            ).filter(
                ExtOffer.get_seller_name()=='lotus-icafe'
            ).filter(
                ExtOffer.get_platform_name()=='Ebay'
            ).first()
            if offer:
                return offer.rank
            else:
                return None
        else:
            return None

    def get_performance_by_mp(self, marketplace_id):
        mpa = Marketplace_Product_Attributes.query.filter_by(
            product_id=int(self.id), marketplace_id=int(marketplace_id)
        ).first()
        query = db.session.query(ShippingService, MPShippingService, ShippingProfilePrice).filter(
            or_(ShippingService.id == self.nat_shipping_1_id,
                ShippingService.id == self.nat_shipping_2_id,
                ShippingService.id == self.nat_shipping_3_id,
                ShippingService.id == self.nat_shipping_4_id)
        ).filter(
            MPShippingService.shipping_service_id == ShippingService.id
        ).filter(
            MPShippingService.marketplace_id == marketplace_id
        ).filter(
            ShippingProfilePrice.profile_id == self.shipping_profile_id
        ).filter(
            ShippingProfilePrice.mp_service_id == MPShippingService.id
        ).all()
        if not query:
            print('Shipping needs to be configured for this Product.')
            return 'Fehler bei der Berechnung.'
        _, i = min((row[2].price - row[0].price, i) for (i, row) in enumerate(query))
        shipping = query[i][2].price
        own_shipping = query[i][0].price
        performance_dict = marketplace_price_performance_measure(mpa.marketplace.name, mpa.selling_price, shipping, own_shipping, mpa.product.get_cheapest_buying_price_all()[1],
                                                                 mpa.commission, tax_group[self.tax_group]['national'])
        if performance_dict['prc_margin'] and performance_dict['abs_margin']:
            return 'Marge: ' + (str("%.2f" % (performance_dict['prc_margin'] * 100))).replace('.', ',') + ' % - Absolut: ' + (str("%.2f" % performance_dict['abs_margin'])).replace('.', ',') + ' €'
        else:
            return 'Fehler bei der Berechnung.'

    def get_avgmargin_by_mp_sellp_shipp(self, marketplace_id, selling_price, shipping_price, num):
        if num == 0:
            return 0
        mpas = Marketplace_Product_Attributes.query.filter_by(
            product_id=int(self.id), marketplace_id=marketplace_id
        ).all()
        query = db.session.query(ShippingService, MPShippingService, ShippingProfilePrice).filter(
            or_(ShippingService.id == self.nat_shipping_1_id,
                ShippingService.id == self.nat_shipping_2_id,
                ShippingService.id == self.nat_shipping_3_id,
                ShippingService.id == self.nat_shipping_4_id)
        ).filter(
            MPShippingService.shipping_service_id == ShippingService.id
        ).filter(
            MPShippingService.marketplace_id == marketplace_id
        ).filter(
            ShippingProfilePrice.profile_id == self.shipping_profile_id
        ).filter(
            ShippingProfilePrice.mp_service_id == MPShippingService.id
        ).all()
        if not query:
            raise SystemError('Shipping needs to be configured for this Product.')
        _, i = min((row[2].price - row[0].price, i) for (i, row) in enumerate(query))
        own_shipping = query[i][0].price
        s = 0
        found = False
        bp = self.get_own_buying_price()
        if bp is None or self.release_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            bp = self.get_cheapest_buying_price_all()[1]
        for mpa in mpas:
            if self.release_date:
                if self.release_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                    performance_dict = marketplace_price_performance_measure(mpa.marketplace.name, selling_price, shipping_price, own_shipping, bp,
                                                                             mpa.commission, tax_group[self.tax_group]['national'])
                else:
                    performance_dict = marketplace_price_performance_measure(mpa.marketplace.name, selling_price, shipping_price, own_shipping, bp,
                                                                             mpa.commission, tax_group[self.tax_group]['national'])
            else:
                performance_dict = marketplace_price_performance_measure(mpa.marketplace.name, selling_price, shipping_price, own_shipping, bp,
                                                                         mpa.commission, tax_group[self.tax_group]['national'])
            if performance_dict['prc_margin'] and performance_dict['abs_margin']:
                found = True
                s += performance_dict['prc_margin'] * 100
        if found:
            return s * num
        else:
            return 0

    def get_last_price_by_mp(self, marketplace_id):
        return PricingLog.query.filter_by(
            product_id=self.id, marketplace_id=marketplace_id
        ).order_by(
            PricingLog.set_date.desc()
        ).first()

    def get_num_sales(self):
        product_query = db.session.query(
            func.count(PricingLog.id), func.coalesce(func.sum(Sale.quantity), 0).label('sales')
        ).filter(
            PricingLog.product_id == self.id
        ).filter(
            Sale.pricinglog_id == PricingLog.id
        ).group_by(
            PricingLog.product_id
        ).first()
        if product_query:
            return product_query[1]
        else:
            return 0


class ShippingProvider(db.Model):
    __tablename__ = "shipping_provider"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)

    name = db.Column(db.String(80))

    shipping_services = db.relationship("ShippingService", backref="provider", lazy="select")

    def __init__(self, name: str):
        if type(name) != str:
            raise TypeError('Variable name must be of type str.')
        else:
            if not name:
                raise ValueError('Variable name must have at least on character.')
            check_prov = ShippingProvider.query.filter_by(name=name).first()
            if check_prov:
                raise ValueError('Provider with this name already exists.')
            else:
                self.init_datetime = datetime.now()
                self.name = name


class ShippingService(db.Model):
    __tablename__ = "shipping_service"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)

    internal_id = db.Column(db.String)
    international = db.Column(db.Boolean())
    signature = db.Column(db.Boolean)
    tracking = db.Column(db.Boolean)
    min_days = db.Column(db.Integer)
    max_days = db.Column(db.Integer)
    name = db.Column(db.String(80))
    price = db.Column(db.Float())
    weight_kg = db.Column(db.Float)
    length_mm = db.Column(db.Integer)
    width_mm = db.Column(db.Integer)
    height_mm = db.Column(db.Integer)

    provider_id = db.Column(db.Integer, db.ForeignKey("shipping_provider.id"))

    serial_data = db.relationship("ShippingServiceSD", backref="service", lazy="select")

    def __init__(self, international: Union[str, bool], signature: bool, tracking: bool, min_days: int, max_days: int, name: str, price: Union[str, float], provider: Union[int, str],
                 internal_id: str, weight_kg: Union[int, float], length_mm: Union[int, float], width_mm: Union[int, float], height_mm: Union[int, float]):
        if type(international) not in {str, bool}:
            raise TypeError('Variable international must be of type str or bool.')
        elif type(signature) != bool:
            raise TypeError('Variable signature must be of type bool.')
        elif type(tracking) != bool:
            raise TypeError('Variable tracking must be of type bool.')
        elif type(min_days) != int:
            raise TypeError('Variable min_days must be of type int.')
        elif type(max_days) != int:
            raise TypeError('Variable max_days must be of type int.')
        elif type(name) != str:
            raise TypeError('Variable name must be of type str.')
        elif type(price) not in {str, float}:
            raise TypeError('Variable price must be of type str or float.')
        elif type(provider) not in {str, int}:
            raise TypeError('Variable provider must be of type str or int.')
        elif type(internal_id) != str:
            raise TypeError('Variable internal_id must be of type str.')
        elif type(weight_kg) not in {int, float}:
            raise TypeError('Variable weight_kg must be of type int or float.')
        elif type(length_mm) not in {int, float}:
            raise TypeError('Variable length_mm must be of type int or float.')
        elif type(width_mm) not in {int, float}:
            raise TypeError('Variable width_mm must be of type int or float.')
        elif type(height_mm) not in {int, float}:
            raise TypeError('Variable height_mm must be of type int or float.')
        else:
            if type(international) == str and international not in {'international', 'national'}:
                raise ValueError('Variable international must be of type bool or a str in {"international", "national"}.')
            if min_days < 0:
                raise ValueError('Variable min_days must be non-negative.')
            if max_days < 0:
                raise ValueError('Variable max_days must be non-negative.')
            if min_days > max_days:
                raise ValueError('Variable max_days must be greater than or equal to variable min_days.')
            if not name:
                raise ValueError('Variable name must have at least on character.')
            if type(price) == str and not check_float(price):
                raise ValueError('Variable float must be of type float or a str, s.t. float(price) does not fail.')
            if type(provider) == int:
                check_provider = ShippingProvider.query.filter_by(id=provider).first()
                if not check_provider:
                    raise ValueError
            else:
                check_provider = ShippingProvider.query.filter_by(name=provider).first()
                if not check_provider:
                    check_provider = ShippingProvider(provider)
                    db.session.add(check_provider)
                    db.session.commit()
            if weight_kg <= 0:
                raise ValueError('Variable weight_kg must be positive.')
            if length_mm <= 0:
                raise ValueError('Variable length_mm must be positive.')
            if width_mm <= 0:
                raise ValueError('Variable width_mm must be positive.')
            if height_mm <= 0:
                raise ValueError('Variable height_mm must be positive.')
            test_int = international if type(international) == bool else international == 'international'
            check_service = ShippingService.query.filter_by(name=name, provider_id=check_provider.id, international=test_int).first()
            if check_service:
                raise ValueError('Shipping-service with this configuration already exists.')
            else:
                self.init_datetime = datetime.now()
                self.international = international if type(international) == bool else international == 'international'
                self.signature = signature
                self.tracking = tracking
                self.min_days = min_days
                self.max_days = max_days
                self.name = name
                self.price = float(price)
                self.internal_id = internal_id
                self.weight_kg = weight_kg
                self.height_cm = length_mm
                self.width_cm = width_mm
                self.depth_cm = height_mm
                self.provider_id = check_provider.id
                self.serial_data.append(ShippingServiceSD(float(price)))


    def get_shipping_prices(self, profile_id):
        shipping_dict = {'own': self.price}
        mps_query = db.session.query(MPShippingService, ShippingProfilePrice, ShippingProfile).filter(
            ShippingProfile.id == profile_id
        ).filter(
            MPShippingService.shipping_service_id == self.id
        ).filter(
            MPShippingService.id == ShippingProfilePrice.mp_service_id
        ).filter(
            ShippingProfile.id == ShippingProfilePrice.profile_id
        ).all()
        for row in mps_query:
            shipping_dict[f'mp_{row[0].marketplace_id}'] = row[1].price
        return shipping_dict


    def get_shipping_price_mp(self, profile_id, mp_id):
        mps = db.session.query(MPShippingService, ShippingProfilePrice, ShippingProfile).filter(
            ShippingProfile.id == profile_id
        ).filter(
            MPShippingService.shipping_service_id == self.id
        ).filter(
            MPShippingService.id == ShippingProfilePrice.mp_service_id
        ).filter(
            MPShippingService.marketplace_id == mp_id
        ).filter(
            ShippingProfile.id == ShippingProfilePrice.profile_id
        ).first()
        return mps[1].price if mps else None


class ShippingServiceSD(db.Model):
    __tablename__ = "shipping_service_sd"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)
    rep_datetime = db.Column(db.DateTime)

    price = db.Column(db.Float())

    service_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))

    def __init__(self, price: Union[str, float], service_id: int = None):
        if type(price) not in {str, float}:
            raise TypeError('Variable price must be of type str or float.')
        elif service_id != None and type(service_id) != int:
            raise TypeError('Optional variable service_id must be of type int.')
        else:
            if type(price) == str and not check_float(price):
                raise ValueError('Variable float must be of type float or a str, s.t. float(price) does not fail.')
            elif service_id != None:
                check_service = ShippingService.query.filter_by(id=service_id).first()
                if not check_service:
                    raise ValueError(f'No service found with id {service_id}.')
            self.init_datetime = datetime.now()
            self.price = float(price)
            self.service_id = service_id


class MPShippingService(db.Model):
    __tablename__ = "mp_shipping_service"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)

    code = db.Column(db.String(80))

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    shipping_service_id = db.Column(db.Integer, db.ForeignKey("shipping_service.id"))

    profiles = db.relationship("ShippingProfilePrice", backref="mp_service", lazy="select")

    def __init__(self, code: str, marketplace_id: int, shipping_service_id: int):
        if type(code) != str:
            raise TypeError('Variable code must be of type str.')
        elif type(marketplace_id) != int:
            raise TypeError('Variable marketplace_id must be of type int.')
        elif type(shipping_service_id) != int:
            raise TypeError('Variable shipping_service_id must be of type int.')
        else:
            if not code:
                raise ValueError('Variable code must have at least one character.')
            self.init_datetime = datetime.now()
            self.code = code
            self.marketplace_id = marketplace_id
            self.shipping_service_id = shipping_service_id


class ShippingProfilePrice(db.Model):
    __tablename__ = "shipping_profile_price"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)

    price = db.Column(db.Float())

    mp_service_id = db.Column(db.Integer, db.ForeignKey("mp_shipping_service.id"))
    profile_id = db.Column(db.Integer, db.ForeignKey("shipping_profile.id"))

    serial_data = db.relationship("ShippingProfilePriceSD", backref="shipping_profile_price", lazy="select")

    def __init__(self, price: Union[str, float], mp_service_id: int, profile_id: int = None):
        if type(price) not in {str, float}:
            raise TypeError('Variable price must be of type str or float.')
        elif type(mp_service_id) != int:
            raise TypeError('Variable mp_service_id must be of type int.')
        elif profile_id is not None and type(profile_id) != int:
            raise TypeError('Optional variable profile_id must be of type int.')
        else:
            if type(price) == str and not check_float(price):
                raise ValueError('Variable price must be of type float or a str, s.t. float(price) does not fail.')
            check_service = MPShippingService.query.filter_by(id=mp_service_id).first()
            if not check_service:
                raise ValueError(f'No service found with id {mp_service_id}.')
            if profile_id:
                check_profile = ShippingProfile.query.filter_by(id=profile_id).first()
                if not check_profile:
                    raise ValueError(f'No profile found with id {profile_id}.')
            self.init_datetime = datetime.now()
            self.price = price
            self.mp_service_id = mp_service_id
            self.profile_id = profile_id
            self.serial_data.append(ShippingProfilePriceSD(float(price)))


    def update_price(self, price: Union[str, float]):
        if type(price) not in {str, float}:
            raise TypeError('Variable price must be of type str or float.')
        else:
            if type(price) == str and not check_float(price):
                raise ValueError('Variable price must be of type float or a str, s.t. float(price) does not fail.')
            if self.price != price:
                self.serial_data.append(ShippingProfilePriceSD(float(price)))
                self.price = price


class ShippingProfilePriceSD(db.Model):
    __tablename__ = "shipping_profile_price_sd"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)
    rep_datetime = db.Column(db.DateTime)

    price = db.Column(db.Float())

    spp_id = db.Column(db.Integer, db.ForeignKey("shipping_profile_price.id"))

    def __init__(self, price: Union[str, float], spp_id: int = None):
        if type(price) not in {str, float}:
            raise TypeError('Variable price must be of type str or float.')
        elif spp_id != None and type(spp_id) != int:
            raise TypeError('Optional variable spp_id must be of type int.')
        else:
            if type(price) == str and not check_float(price):
                raise ValueError('Variable price must be of type float or a str, s.t. float(price) does not fail.')
            elif spp_id != None:
                check_price = ShippingProfilePrice.query.filter_by(id=spp_id).first()
                if not check_price:
                    raise ValueError(f'No price found with id {spp_id}.')
            self.init_datetime = datetime.now()
            self.price = float(price)
            self.spp_id = spp_id


class ShippingProfile(db.Model):
    __tablename__ = "shipping_profile"
    id = db.Column(db.Integer, primary_key=True)
    init_datetime = db.Column(db.DateTime)

    name = db.Column(db.String(80))

    mp_services = db.relationship("ShippingProfilePrice", backref="profile", lazy="select")
    products = db.relationship("Product", backref="shipping_profile", lazy="select")

    def __init__(self, name: str, service_dict: dict = None):
        if service_dict != None and type(service_dict) != dict:
            raise TypeError('Variable service_dict must be of type dict.')
        else:
            if service_dict is None:
                service_dict = {}
        if type(name) != str:
            raise TypeError('Variable name must be of type str.')
        else:
            self.init_datetime = datetime.now()
            self.name = name
            for key in service_dict:
                mps = MPShippingService.query.filter_by(id=int(key)).first()
                if not mps:
                    raise ValueError(f'No MPShippingService found with id {key}.')
                self.mp_services.append(ShippingProfilePrice(service_dict[key], mps.id))

    def create_ebay_shipping_array(self):
        ebay = Marketplace.query.filter_by(name='Ebay').first()
        query = db.session.query(ShippingProfile, ShippingProfilePrice, MPShippingService, ShippingService).filter(
            ShippingProfile.id == ShippingProfilePrice.profile_id
        ).filter(
            ShippingProfilePrice.mp_service_id == MPShippingService.id
        ).filter(
            MPShippingService.shipping_service_id == ShippingService.id
        ).filter(
            ShippingProfile.id == self.id
        ).filter(
            MPShippingService.marketplace_id == ebay.id
        ).all()
        shipping_list = []
        for _, spp, mps, ss in query:
            shipping_list.append({
                "costType": "FLAT_RATE",
                "optionType": "INTERNATIONAL" if ss.international else "DOMESTIC",
                "packageHandlingCost":
                    {
                        "currency": "EUR",
                        "value": spp.price
                    },
                    "shippingServices":
                        [
                            {
                                "additionalShippingCost":
                                    {
                                        "currency": "CurrencyCodeEnum : [AED,AFN,ALL...]",
                                        "value": "string"
                                    },
                                "buyerResponsibleForPickup": "boolean",
                                "buyerResponsibleForShipping": "boolean",
                                "freeShipping": "boolean",
                                "shippingCarrierCode": "string",
                                "shippingCost":
                                    {
                                        "currency": "CurrencyCodeEnum : [AED,AFN,ALL...]",
                                        "value": "string"
                                    },
                                "shippingServiceCode": "string",
                                "shipToLocations":
                                    {
                                        "regionExcluded": [
                                            {
                                                "regionName": "string",
                                                "regionType": "RegionTypeEnum : [COUNTRY,COUNTRY_REGION,STATE_OR_PROVINCE...]"
                                            }
                                        ],
                                        "regionIncluded":
                                            [
                                                {
                                                    "regionName": "string",
                                                    "regionType": "RegionTypeEnum : [COUNTRY,COUNTRY_REGION,STATE_OR_PROVINCE...]"
                                                }
                                            ]
                                    },
                                "sortOrder": "integer",
                                "surcharge":
                                    {
                                        "currency": "CurrencyCodeEnum : [AED,AFN,ALL...]",
                                        "value": "string"
                                    }
                            }
                        ]
                })
        print(query)
        return True


class ProductPicture(db.Model):
    __tablename__ = "productpicture"
    id = db.Column(db.Integer, primary_key=True)

    pic_type = db.Column(db.Integer)
    link = db.Column(db.String(255))

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, pic_type, link, product_id):
        self.pic_type = pic_type
        self.link = link
        self.product_id = product_id


class ProductLink(db.Model):
    __tablename__ = "productlink"
    id = db.Column(db.Integer, primary_key=True)

    link = db.Column(db.String(500))
    ext_idealo_watch_active = db.Column(db.Boolean)

    category_id = db.Column(db.Integer, db.ForeignKey("productlinkcategory.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, link, category_id, product_id):
        self.link = link
        self.category_id = category_id
        self.product_id = product_id


class ProductLinkCategory(db.Model):
    __tablename__ = "productlinkcategory"
    id = db.Column(db.Integer, primary_key=True)

    active = db.Column(db.Boolean)
    name = db.Column(db.String(100))

    links = db.relationship("ProductLink", backref="productlinkcategory", lazy="select")
    marketplace = db.relationship("Marketplace", backref="productlinkcategory", lazy="select", uselist=False)

    def __init__(self, name):
        self.active = True
        self.name = name


class PrCatStock_Attr(db.Model):
    __tablename__ = "pr_cat_stock_attr"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    ship_days = db.Column(db.Integer)
    cat_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))
    stock_id = db.Column(db.Integer, db.ForeignKey("stock.id"))

    def __init__(self, ship_days: int, cat_id: int = None, stock_id: int = None):
        if type(ship_days) != int:
            raise TypeError('Variable ship_days must be of type int.')
        if cat_id is not None and type(cat_id) != int:
            raise TypeError('Variable cat_id must be of type int.')
        if stock_id is not None and type(stock_id) != int:
            raise TypeError('Variable stock_id must be of type int.')
        self.init_dt = datetime.now()
        self.ship_days = ship_days
        self.cat_id = cat_id
        self.stock_id = stock_id


class ProductCategory(db.Model):
    __tablename__ = "productcategory"
    id = db.Column(db.Integer, primary_key=True)

    active = db.Column(db.Boolean)
    internal_id = db.Column(db.String(20))
    name = db.Column(db.String(100))
    parent_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))

    children = db.relationship("ProductCategory", backref=backref('parent', remote_side=[id]))
    marketplaces = db.relationship("Marketplace_ProductCategory", backref="productcategory", lazy="select")
    mp_cats = db.relationship("MPCat_PrCat", backref="pr_cat", lazy="select")
    products = db.relationship("Product", backref="productcategory", lazy="select")
    productfeatures = db.relationship("ProductCategory_ProductFeature", backref="productcategory", lazy="select")
    stock_lags = db.relationship("PrCatStock_Attr", backref="cat", lazy="select")

    def __init__(self, internal_id, name):
        self.active = True
        self.internal_id = internal_id
        self.name = name
        stocks = Stock.query.all()
        for stock in stocks:
            self.stock_lags.append(PrCatStock_Attr(ship_days=0, stock_id=stock.id))

    def self_update(self, ship_days: dict = None, mp_data: dict = None):
        if ship_days:
            pcs_attrs = PrCatStock_Attr.query.filter(PrCatStock_Attr.id.in_([int(key) for key in ship_days])).all()
            for pcs_attr in pcs_attrs:
                pcs_attr.ship_days = ship_days[str(pcs_attr.id)]
            db.session.commit()
        if mp_data:
            for mp_id in mp_data:
                if 'mp_code' in mp_data[mp_id]:
                    mpc = Marketplace_ProductCategory.query.filter_by(marketplace_id=int(mp_id), productcategory_id=self.id).first()
                    if mpc:
                        mpc.marketplace_system_id = mp_data[mp_id]['mp_code']
                    else:
                        db.session.add(Marketplace_ProductCategory(mp_data[mp_id]['mp_code'], int(mp_id), self.id))
                        db.session.commit()
                if 'mp_cat_id' in mp_data[mp_id]:
                    mp_cat_conn = MPCat_PrCat.query.filter_by(pr_cat_id=self.id, mp_cat_id=mp_data[mp_id]['mp_cat_id']).first()
                    if mp_cat_conn is None:
                        check_conn = db.session.query(
                            MPCat_PrCat, MPCategory
                        ).filter(
                            MPCategory.id == MPCat_PrCat.mp_cat_id
                        ).filter(
                            MPCat_PrCat.pr_cat_id == self.id
                        ).filter(
                            MPCategory.mp_id == int(mp_id)
                        ).first()
                        if check_conn:
                            db.session.delete(check_conn[0])
                            db.session.commit()
                        db.session.add(MPCat_PrCat(mp_data[mp_id]['mp_cat_id'], self.id))
                        db.session.commit()


    def get_stock_ship_days(self, stock_id):
        pcs = PrCatStock_Attr.query.filter_by(cat_id=self.id, stock_id=stock_id).first()
        return pcs.ship_days if pcs else 0


    def get_marketplaces(self):
        ids = Marketplace_ProductCategory.query.filter_by(productcategory_id=self.id).all()
        return Marketplace.query.filter(Marketplace.id.in_([item.marketplace_id for item in ids])).all()

    def get_productfeatures(self):
        ids = ProductCategory_ProductFeature.query.filter_by(productcategory_id=self.id).all()
        return ProductFeature.query.filter(ProductFeature.id.in_([item.productfeature_id for item in ids])).all()

    def magento_upload(self, auth):
        return 5

    def get_oldest_predecessor(self):
        cat = self
        while cat.parent:
            cat = cat.parent
        return cat

    @hybrid_method
    def get_oldest_predecessor_name(self):
        cat = ProductCategory.query.filter_by(id=self.parent_id).first()
        if cat is not None:
            while cat.parent_id:
                cat = cat.parent
            return cat.name
        else:
            return self.name

    @get_oldest_predecessor_name.expression
    def get_oldest_predecessor_name(cls):
        cat = ProductCategory.query.filter_by(id=cls.parent_id).first()
        if cat is not None:
            while cat.parent_id:
                cat = cat.parent
            return cat.name
        else:
            return cls.name

    def get_predecessors(self):
        predecessors = []
        cat = self
        while cat.parent:
            predecessors.append(cat.parent)
            cat = cat.parent
        predecessors.reverse()
        return predecessors

    def get_predecessors(self):
        predecessor_list = []
        node = self
        if node.parent is None:
            return [node]
        while node.parent:
            predecessor_list.append(node.parent)
            node = node.parent
        return predecessor_list

    def get_successors(self):
        def add_to_list(node, successors):
            successors.append(node)
            for c in node.children:
                add_to_list(c, successors)
            return successors
        successor_list = []
        for child in sorted(self.children, key=lambda c: c.name):
            add_to_list(child, successor_list)
        return successor_list

    def get_successor_tree(self):
        def add_to_tree(node, tree, depth):
            tree.append((node, depth))
            for c in node.children:
                add_to_tree(c, tree, depth+1)
            return tree
        successor_tree = []
        for child in sorted(self.children, key=lambda c: c.name):
            add_to_tree(child, successor_tree, 0)
        return successor_tree

    def get_family(self):
        return self.get_predecessors() + self.get_successors()

    def get_family_tree(self):
        def add_to_tree(node, tree, depth, parent_id):
            tree.append((node, depth, parent_id))
            for c in node.children:
                add_to_tree(c, tree, depth+1, node.id)
            return tree
        n = self
        while n.parent:
            n = n.parent
        successor_tree = []
        for child in sorted(n.children, key=lambda c: c.name):
            add_to_tree(child, successor_tree, 0, n.id)
        return successor_tree

    def get_marketplace_code(self, marketplace_id):
        mpc = Marketplace_ProductCategory.query.filter_by(marketplace_id=marketplace_id, productcategory_id=self.id).first()
        if mpc:
            return mpc.marketplace_system_id if mpc.marketplace_system_id else ''
        else:
            ''


class Marketplace_ProductCategory(db.Model):
    __tablename__ = "marketplace_productcategory"
    id = db.Column(db.Integer, primary_key=True)

    marketplace_system_id = db.Column(db.String(50))

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    productcategory_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))

    def __init__(self, marketplace_system_id, marketplace_id, productcategory_id):
        self.marketplace_system_id = marketplace_system_id
        self.marketplace_id = marketplace_id
        self.productcategory_id = productcategory_id


class MPCat_PrCat(db.Model):
    __tablename__ = "mp_cat_pr_cat"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    mp_cat_id = db.Column(db.Integer, db.ForeignKey("mp_category.id"))
    pr_cat_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))

    def __init__(self, mp_cat_id: int, pr_cat_id: int):
        self.init_dt = datetime.now()
        self.mp_cat_id = mp_cat_id
        self.pr_cat_id = pr_cat_id


class ProductCategory_ProductFeature(db.Model):
    __tablename__ = "productcategory_productfeature"
    id = db.Column(db.Integer, primary_key=True)

    productcategory_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))
    productfeature_id = db.Column(db.Integer, db.ForeignKey("productfeature.id"))

    def __init__(self, productcategory_id, productfeature_id):
        self.productcategory_id = productcategory_id
        self.productfeature_id = productfeature_id


class ProductFeature(db.Model):
    __tablename__ = "productfeature"
    id = db.Column(db.Integer, primary_key=True)

    active = db.Column(db.Boolean)
    internal_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    source = db.Column(db.String(100))
    fixed_values = db.Column(db.Boolean)

    marketplaces = db.relationship("Marketplace_ProductFeature", backref="productfeature", lazy="select")
    productcategories = db.relationship("ProductCategory_ProductFeature", backref="productfeature", lazy="select")
    values = db.relationship("ProductFeatureValue", backref="productfeature", lazy="select")

    def __init__(self, internal_id, name, fixed_values):
        self.active = True
        self.internal_id = internal_id
        self.name = name
        self.fixed_values = fixed_values

    def get_marketplaces(self):
        ids = Marketplace_ProductFeature.query.filter_by(productfeature_id=self.id).all()
        return Marketplace.query.filter(Marketplace.id.in_([item.marketplace_id for item in ids])).all()

    def get_productcategories(self):
        ids = ProductCategory_ProductFeature.query.filter_by(productfeature_id=self.id).all()
        return ProductCategory.query.filter(ProductCategory.id.in_([item.productcategory_id for item in ids])).all()

    def get_value_product(self, product_id):
        values = db.session.query(
            ProductFeature, ProductFeatureValue, Product_ProductFeatureValue, Product
        ).filter(
            ProductFeature.id == self.id
        ).filter(
            Product.id == int(product_id)
        ).filter(
            ProductFeature.id == ProductFeatureValue.productfeature_id
        ).filter(
            ProductFeatureValue.id == Product_ProductFeatureValue.productfeaturevalue_id
        ).filter(
            Product.id == Product_ProductFeatureValue.product_id
        ).all()
        value_list = [value[1] for value in values]
        return value_list

    def get_value_product_values(self, product_id):
        values = db.session.query(
            ProductFeature, ProductFeatureValue, Product_ProductFeatureValue, Product
        ).filter(
            ProductFeature.id==self.id
        ).filter(
            Product.id==int(product_id)
        ).filter(
            ProductFeature.id==ProductFeatureValue.productfeature_id
        ).filter(
            ProductFeatureValue.id==Product_ProductFeatureValue.productfeaturevalue_id
        ).filter(
            Product.id==Product_ProductFeatureValue.product_id
        ).all()
        value_list = []
        for value in values:
            value_list.append(value[1].value)
        return value_list

    def get_min_5_values(self):
        feature_values = ProductFeatureValue.query.outerjoin(
            Product_ProductFeatureValue
        ).filter(
            ProductFeatureValue.productfeature_id==self.id
        ).having(
            func.count(Product_ProductFeatureValue.id) >= 5
        ).group_by(
            ProductFeatureValue.id
        ).order_by(
            ProductFeatureValue.value
        ).all()
        return feature_values


class Marketplace_ProductFeature(db.Model):
    __tablename__ = "marketplace_productfeature"
    id = db.Column(db.Integer, primary_key=True)

    marketplace_system_id = db.Column(db.String(100))

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    productfeature_id = db.Column(db.Integer, db.ForeignKey("productfeature.id"))

    def __init__(self, marketplace_system_id, marketplace_id, productfeature_id):
        self.marketplace_system_id = marketplace_system_id
        self.marketplace_id = marketplace_id
        self.productfeature_id = productfeature_id


class ProductFeatureValue(db.Model):
    __tablename__ = "productfeaturevalue"
    id = db.Column(db.Integer, primary_key=True)

    active = db.Column(db.Boolean)
    value = db.Column(db.String(8191))

    productfeature_id = db.Column(db.Integer, db.ForeignKey("productfeature.id"))
    int_value_id = db.Column(db.Integer, db.ForeignKey("productfeaturevalue.id"))

    ext_values = db.relationship("ProductFeatureValue", backref="int_value", lazy="select", remote_side=[id], uselist=True)
    products = db.relationship("Product_ProductFeatureValue", backref="productfeaturevalue", lazy="select")

    def __init__(self, value, productfeature_id):
        self.active = True
        self.value = value
        self.productfeature_id = productfeature_id

    def get_products(self):
        ids = Product_ProductFeatureValue.query.filter_by(productfeaturevalue_id=self.id).all()
        return Product.query.filter(Product.id.in_([int(item.product_id) for item in ids])).all()

    def get_ext_values(self):
        return ProductFeatureValue.query.filter_by(int_value_id=self.id).all()


class Product_ProductFeatureValue(db.Model):
    __tablename__ = "product_productfeaturevalue"
    id = db.Column(db.Integer(), primary_key=True)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    productfeaturevalue_id = db.Column(db.Integer(), db.ForeignKey("productfeaturevalue.id"))

    def __init__(self, product_id, productfeaturevalue_id):
        self.product_id = product_id
        self.productfeaturevalue_id = productfeaturevalue_id


class Marketplace_Product_Attributes(db.Model):
    __tablename__ = "marketplace_product_attributes"
    id = db.Column(db.Integer(), primary_key=True)
    uploaded = db.Column(db.Boolean)
    upload_date = db.Column(db.DateTime)
    marketplace_system_id = db.Column(db.String(100))
    mp_cat_id = db.Column(db.String(100))
    mp_hsp_id = db.Column(db.String(20))
    name = db.Column(db.String(255))
    link = db.Column(db.String(500))
    selling_price = db.Column(db.Float)
    block_selling_price = db.Column(db.Boolean)
    shipping_dhl_cost = db.Column(db.Float)
    shipping_dhl_time = db.Column(db.String(80))
    shipping_dhl_comment = db.Column(db.String(80))
    shipping_dp_cost = db.Column(db.Float())
    shipping_dp_time = db.Column(db.String(80))
    shipping_dp_comment = db.Column(db.String(80))
    shipping_dpd_cost = db.Column(db.Float())
    shipping_dpd_time = db.Column(db.String(80))
    shipping_dpd_comment = db.Column(db.String(80))
    shipping_hermes_cost = db.Column(db.Float())
    shipping_hermes_time = db.Column(db.String(80))
    shipping_hermes_comment = db.Column(db.String(80))
    sell_api = db.Column(db.Boolean)
    upload_ready = db.Column(db.Boolean)
    upload_clearance = db.Column(db.Boolean)
    update_price = db.Column(db.Float)
    update_quantity = db.Column(db.Integer)
    update = db.Column(db.Boolean)
    pr_update_dur = db.Column(db.Integer)
    pr_update_ts = db.Column(db.DateTime)
    curr_rank = db.Column(db.Integer())
    curr_stock = db.Column(db.Integer())
    min_stock = db.Column(db.Integer())
    max_stock = db.Column(db.Integer())
    commission = db.Column(db.Float)
    quantity_delta = db.Column(db.Integer)
    price_regulation = db.Column(db.Boolean)
    factor = db.Column(db.Float)
    search_term = db.Column(db.String(100))
    category_path = db.Column(db.String(511))

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    descriptions = db.relationship("Marketplace_Product_Attributes_Description",
                                   backref="marketplace_product_attributes", lazy="select")

    def __init__(self, marketplace_id, product_id, min_stock: int = 1, max_stock: int = 3):
        self.sell_api = True
        self.uploaded = False
        self.upload_clearance = True
        self.marketplace_id = marketplace_id
        self.product_id = product_id
        self.curr_stock = 0
        self.min_stock = min_stock
        self.max_stock = max_stock
        self.pr_update_dur = 6
        k = datetime.now().hour // 6
        self.pr_update_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=(k + 1) * 6)
        product = Product.query.filter_by(id=product_id).first()
        self.search_term = str(product.hsp_id)

    def get_descriptions(self):
        full_description = ''
        for description in self.descriptions:
            full_description += description.text
        return full_description

    @hybrid_method
    def get_marketplace_id(self):
        return self.marketplace_id

    @get_marketplace_id.expression
    def get_marketplace_id(cls):
        return cls.marketplace_id

    def gen_description(self):
        if self.marketplace.name in ['Ebay', 'Idealo']:
            if len(self.descriptions) == 1:
                return self.descriptions[0].text
            if len(self.descriptions) < 3:
                raise SystemError('Provide at least three description-fields.')
            else:
                bigpic = ProductPicture.query.filter_by(product_id=self.product.id, pic_type=0).first()
                smallpic = ProductPicture.query.filter_by(product_id=self.product.id, pic_type=1).first()
                self.descriptions.sort(key=lambda mpa_description: mpa_description.id)
                description_headlist = self.descriptions[0].text.splitlines()
                description_list = self.descriptions[1].text.splitlines()
                otherdescrpt = []
                for descr in self.descriptions[2:]:
                    otherdescrpt.append(descr.text.splitlines())
                description = '<div align="center">'
                for x in description_headlist:
                    description += '<font size="6"><font face="TIMES NEW ROMAN">' + x + '</font></font><br>'
                description += '</div>'
                description += '<font face="TIMES NEW ROMAN"><font size="5"><br><b>' + description_list[0].upper() + '</b>'
                for x in description_list[1:]:
                    description += '<br>' + x
                description += '<br></font></font><br><br>'
                for descr in otherdescrpt:
                    for x in descr:
                        if x != '':
                            description += '<b><font face="TIMES NEW ROMAN"><font size="5">' + descr[
                                0].upper() + '</font></font></b><br>'
                            for y in descr[1:]:
                                description += '<li><font face="TIMES NEW ROMAN"><font size="5">' + y + '</font></font></li>'
                            description += '<br><br>'
                            break
                otherpics = ProductPicture.query.filter_by(product_id=self.product.id).filter(ProductPicture.pic_type == 2).all()
                description += '<div align="center"><img src="' + 'https://strikeusifucan.com/' + bigpic.link + '" ' \
                               'float="left" border="0" height="640"><img src="' + 'https://strikeusifucan.com/' \
                               '' + smallpic.link + '" float="left" border="0" height="640"><br>'
                for pic in otherpics:
                    description += '<img src="' + 'https://strikeusifucan.com/' + pic.link + '" ' \
                                   'float="left" border="0" height="640">'
                description += '</div>'
                return description
        elif self.marketplace.name in ['Lotus']:
            return self.descriptions[0].text
        else:
            raise SystemError(f'Marketplace {self.marketplace.name} not implemented for this function.')


class Marketplace_Product_Attributes_Description(db.Model):
    __tablename__ = "marketplace_product_attributes_description"
    id = db.Column(db.Integer(), primary_key=True)

    position = db.Column(db.Integer())
    text = db.Column(db.String)

    marketplace_product_attributes_id = db.Column(db.Integer, db.ForeignKey("marketplace_product_attributes.id"))

    def __init__(self, position, text, marketplace_product_attributes_id):
        self.position = position
        self.text = text
        self.marketplace_product_attributes_id = marketplace_product_attributes_id


class MPCategory(db.Model):
    __tablename__ = "mp_category"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(100))
    mp_cat_id = db.Column(db.String(100))
    leaf = db.Column(db.Boolean)
    mp_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    parent_id = db.Column(db.Integer, db.ForeignKey("mp_category.id"))

    children = db.relationship("MPCategory", backref=backref('parent', remote_side=[id]))
    pr_cats = db.relationship("MPCat_PrCat", backref="mp_cat", lazy="select")

    def __init__(self, name: str, mp_cat_id: str, mp_id: int,  parent_id: int, leaf: bool = None):
        if type(name) != str:
            raise TypeError('Variable name must be of type str.')
        if type(mp_cat_id) != str:
            raise TypeError('Variable mp_id must be of type str.')
        if type(mp_id) != int:
            raise TypeError('Variable mp_id must be of type int.')
        if parent_id is not None and type(parent_id) != int:
            raise TypeError('Variable parent_id must be of type int.')
        if leaf is not None and type(leaf) != bool:
            raise TypeError('Variable leaf must be of type bool.')
        self.init_dt = datetime.now()
        self.name = name
        self.mp_cat_id = mp_cat_id
        self.mp_id = mp_id
        self.parent_id = parent_id
        self.leaf = leaf

    def get_oldest_predecessor(self):
        cat = self
        while cat.parent:
            cat = cat.parent
        return cat

    @hybrid_method
    def get_oldest_predecessor_name(self):
        cat = ProductCategory.query.filter_by(id=self.parent_id).first()
        if cat is not None:
            while cat.parent_id:
                cat = cat.parent
            return cat.name
        else:
            return self.name

    @get_oldest_predecessor_name.expression
    def get_oldest_predecessor_name(cls):
        cat = ProductCategory.query.filter_by(id=cls.parent_id).first()
        if cat is not None:
            while cat.parent_id:
                cat = cat.parent
            return cat.name
        else:
            return cls.name

    def get_predecessors(self):
        predecessor_list = []
        node = self
        if node.parent is None:
            return [node]
        while node.parent:
            predecessor_list.append(node.parent)
            node = node.parent
        return predecessor_list

    def get_successors(self):
        def add_to_list(node, successors):
            successors.append(node)
            for c in node.children:
                add_to_list(c, successors)
            return successors
        successor_list = []
        for child in self.children:
            add_to_list(child, successor_list)
        return successor_list

    def get_successor_tree(self):
        def add_to_tree(node, tree, depth, parent_id):
            tree.append((node, depth, parent_id))
            for c in node.children:
                add_to_tree(c, tree, depth+1, node.id)
            return tree
        successor_tree = []
        for child in sorted(self.children, key=lambda c: c.name):
            add_to_tree(child, successor_tree, 0, self.id)
        return successor_tree

    def get_family(self):
        return self.get_predecessors() + self.get_successors()

    def get_family_tree(self):
        def add_to_tree(node, tree, depth, parent_id):
            tree.append((node, depth, parent_id))
            for c in node.children:
                add_to_tree(c, tree, depth+1, node.id)
            return tree
        n = self
        while n.parent:
            n = n.parent
        successor_tree = []
        for child in sorted(n.children, key=lambda c: c.name):
            add_to_tree(child, successor_tree, 0, n.id)
        return successor_tree


class Marketplace(db.Model):
    __tablename__ = "marketplace"
    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(100))
    link = db.Column(db.String(255))

    productlinkcategory_id = db.Column(db.Integer, db.ForeignKey("productlinkcategory.id"))

    extoffers = db.relationship("ExtOffer", backref="marketplace", lazy="select")
    marketplaceattributes = db.relationship("Marketplace_Product_Attributes", backref="marketplace", lazy="select")
    productcategories = db.relationship("Marketplace_ProductCategory", backref="marketplace", lazy="select")
    productfeatures = db.relationship("Marketplace_ProductFeature", backref="marketplace", lazy="select")
    pricing_logs = db.relationship("PricingLog", backref="marketplace", lazy="select")
    pricingstrategy = db.relationship("PricingStrategy", backref="marketplace", lazy="select")
    sales = db.relationship("Sale", backref="marketplace", lazy="select")
    reports = db.relationship("MPReport", backref="marketplace", lazy="select")
    p_update_logs = db.relationship("ProductUpdateLog", backref="marketplace", lazy="select")

    def __init__(self, name, link):
        self.name = name
        self.link = link

    def get_productcategories(self):
        ids = Marketplace_ProductCategory.query.filter_by(marketplace_id=self.id).all()
        return ProductCategory.query. \
            filter(ProductCategory.id.in_([int(item.productcategory_id) for item in ids])).all()

    def get_productfeatures(self):
        ids = Marketplace_ProductFeature.query.filter_by(marketplace_id=self.id).all()
        return ProductFeature.query. \
            filter(ProductFeature.id.in_([int(item.productfeature_id) for item in ids])).all()

    def get_productlink(self, product_id):
        return ProductLink.query.filter_by(product_id=product_id,
                                           category_id=self.productlinkcategory_id).first()

    def get_extoffers_by_product(self, product_id, supremum, minimum):
        return ExtOffer.query.filter_by(
            product_id=product_id, marketplace_id=self.id
        ).filter(
            supremum > ExtOffer.last_seen
        ).filter(
            ExtOffer.last_seen >= minimum
        ).all()


class PricingStrategy(db.Model):
    __tablename__ = "pricingstrategy"
    id = db.Column(db.Integer(), primary_key=True)

    active = db.Column(db.Boolean)
    archived = db.Column(db.Boolean)
    label = db.Column(db.Integer)
    rank = db.Column(db.Integer)
    prc_margin = db.Column(db.Float)
    prc_max_margin = db.Column(db.Float)
    promotion_quantity = db.Column(db.Integer)
    sale_count = db.Column(db.Integer)
    update_factor = db.Column(db.Float)
    update_rule_hours = db.Column(db.Integer)
    update_rule_quantity = db.Column(db.Integer)

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    pricingaction_id = db.Column(db.Integer, db.ForeignKey("pricingaction.id"))

    noncompeting_platforms = db.relationship("ExtPlatform_PricingStrategy_NonCompeting",
                                             backref="pricingstrategy", lazy="select")
    noncompeting_sellers = db.relationship("ExtSeller_PricingStrategy_NonCompeting",
                                           backref="pricingstrategy", lazy="select")
    pricinglogs = db.relationship("PricingLog", backref="pricingstrategy", lazy="select")

    def __init__(self, label, rank, prc_margin, promotion_quantity, update_factor, update_rule_hours, update_rule_quantity, marketplace_id, pricingaction_id, prc_max_margin: float = None, active: bool = False, archived: bool = False):
        self.active = active
        self.archived = archived
        self.label = label
        self.rank = rank
        self.prc_margin = prc_margin
        self.prc_max_margin = prc_max_margin
        self.promotion_quantity = promotion_quantity
        self.update_factor = update_factor
        self.update_rule_hours = update_rule_hours
        self.update_rule_quantity = update_rule_quantity
        self.marketplace_id = marketplace_id
        self.pricingaction_id = pricingaction_id

    def get_noncompeting_platforms(self):
        ids = ExtPlatform_PricingStrategy_NonCompeting.query.filter_by(pricingstrategy_id=self.id).all()
        return ExtPlatform.query.filter(ExtPlatform.id.in_([int(item.extplatform_id) for item in ids])).all()

    def get_noncompeting_sellers(self):
        ids = ExtSeller_PricingStrategy_NonCompeting.query.filter_by(pricingstrategy_id=self.id).all()
        return ExtSeller.query.filter(ExtSeller.id.in_([int(item.extseller_id) for item in ids])).all()

    def get_label(self):
        if self.label == 0:
            return 'Keine Aktion'
        elif self.label == 1:
            return 'Optimarge'
        elif self.label == 2:
            return 'Platzierung'
        elif self.label == 3:
            return 'Abverkauf'
        else:
            return 'nicht vergeben'

    @hybrid_method
    def get_performance(self, wanted_property, active_start, active_end):
        seen_latest = False
        latest_prc_margin = None
        summed_prc_margins = 0
        summed_abs_margins = 0
        summed_price = 0
        summed_shipping = 0

        one = False
        quantity = 0

        self.pricinglogs.sort(key=lambda x: x.set_date, reverse=True)

        for log in self.pricinglogs:
            pa = PricingAction.query.filter_by(id=self.pricingaction_id).first()
            mp = Marketplace.query.filter_by(id=self.marketplace_id).first()
            mpa = Marketplace_Product_Attributes.query.filter_by(product_id=pa.product_id,
                                                                 marketplace_id=self.marketplace_id).first()
            performance_dict = marketplace_price_performance_measure(mp.name, log.selling_price, log.shipping_price, pa.product.shipping_dhl, log.product_stock_attributes.buying_price, mpa.commission,
                                                                     tax_group[mpa.product.tax_group]['national'])
            if not seen_latest:
                latest_prc_margin = performance_dict['prc_margin']

            sales = Sale.query.filter_by(
                pricinglog_id=log.id
            ).filter(
                Sale.timestamp >= active_start
            ).filter(
                Sale.timestamp <= active_end
            ).all()
            if sales:
                summed_prc_margins += performance_dict['prc_margin']
                summed_abs_margins += performance_dict['abs_margin']
                summed_price += log.selling_price
                summed_shipping += log.shipping_price
                quantity += len(log.sales)

                one = True
        if one:
            if wanted_property == 'mean_prc_margin':
                return summed_prc_margins / quantity
            if wanted_property == 'mean_abs_margin':
                return summed_abs_margins / quantity
            if wanted_property == 'mean_price':
                return summed_price / quantity
            if wanted_property == 'mean_shipping':
                return summed_shipping / quantity
            if wanted_property == 'real_sales':
                return quantity
            if wanted_property == 'latest_prc_margin':
                return latest_prc_margin
        else:
            if wanted_property == 'latest_prc_margin':
                return latest_prc_margin
            else:
                return None

    @get_performance.expression
    def get_performance(cls, wanted_property, active_start, active_end):
        seen_latest = False
        latest_prc_margin = None
        summed_prc_margins = 0
        summed_abs_margins = 0
        summed_price = 0
        summed_shipping = 0

        one = False
        quantity = 0

        pricinglogs = PricingLog.query.order_by(PricingLog.set_date.desc()).filter_by(pricingstrategy_id=cls.id).all()

        for log in pricinglogs:
            pa = PricingAction.query.filter_by(id=cls.pricingaction_id).first()
            mp = Marketplace.query.filter_by(id=cls.marketplace_id).first()
            mpa = Marketplace_Product_Attributes.query.filter_by(product_id=pa.product_id,
                                                                 marketplace_id=cls.marketplace_id).first()
            performance_dict = marketplace_price_performance_measure(mp.name, log.selling_price, log.shipping_price, pa.product.shipping_dhl, log.product_stock_attributes.buying_price, mpa.commission,
                                                                     tax_group[mpa.product.tax_group]['national'])
            if not seen_latest:
                latest_prc_margin = performance_dict['prc_margin']

            sales = Sale.query.filter_by(
                pricinglog_id=log.id
            ).filter(
                Sale.timestamp >= active_start
            ).filter(
                Sale.timestamp <= active_end
            ).all()
            if sales:
                if performance_dict['prc_margin'] and performance_dict['abs_margin']:
                    summed_prc_margins += performance_dict['prc_margin']
                    summed_abs_margins += performance_dict['abs_margin']
                    summed_price += log.selling_price
                    summed_shipping += log.shipping_price
                    quantity += len(log.sales)
                else:
                    one = False
                    break

                one = True
        if one:
            if wanted_property == 'mean_prc_margin':
                return summed_prc_margins / quantity
            if wanted_property == 'mean_abs_margin':
                return summed_abs_margins / quantity
            if wanted_property == 'mean_price':
                return summed_price / quantity
            if wanted_property == 'mean_shipping':
                return summed_shipping / quantity
            if wanted_property == 'real_sales':
                return quantity
            if wanted_property == 'latest_prc_margin':
                return latest_prc_margin
        else:
            if wanted_property == 'latest_prc_margin':
                return latest_prc_margin
            else:
                return None


class PricingAction_User_Attributes(db.Model):
    __tablename__ = "pricingaction_user_attributes"
    id = db.Column(db.Integer(), primary_key=True)

    pricingaction_id = db.Column(db.Integer, db.ForeignKey("pricingaction.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    checked = db.Column(db.Boolean)

    def __init__(self, pricingaction_id, user_id):
        self.pricingaction_id = pricingaction_id
        self.user_id = user_id


class PPrRule(db.Model):
    __tablename__ = "ppr_rule"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    priority = db.Column(db.Integer)

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    pricing_rule_id = db.Column(db.Integer, db.ForeignKey("pricing_rule.id"))


class PricingRule(db.Model):
    __tablename__ = "pricing_rule"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(100))
    # if_min_margin = db.Column(db.Integer)
    # if_max_margin = db.Column(db.Integer)
    if_strategy = db.Column(db.String(100))
    then_strategy = db.Column(db.String(100))
    if_sale_suc_h = db.Column(db.Integer)
    if_sale_fail_h = db.Column(db.Integer)
    if_sale_num = db.Column(db.Integer)
    if_sale_rev = db.Column(db.Integer)
    # then_min_margin = db.Column(db.Integer)
    # then_max_margin = db.Column(db.Integer)

    pricing_bundle_id = db.Column(db.Integer, db.ForeignKey("pricing_bundle.id"))


class PricingBundle(db.Model):
    __tablename__ = "pricing_bundle"
    id = db.Column(db.Integer, primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(100))

    pricing_rules = db.relationship("PricingRule", backref="pricing_bundle", lazy="select")
    products = db.relationship("Product", backref="pricing_bundle", lazy="select")


class PricingAction(db.Model):
    __tablename__ = "pricingaction"
    id = db.Column(db.Integer(), primary_key=True)

    active = db.Column(db.Boolean)
    archived = db.Column(db.Boolean)
    is_extension = db.Column(db.Boolean)
    name = db.Column(db.String(100))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    promotion_quantity = db.Column(db.Integer)
    sale_count = db.Column(db.Integer)
    comment = db.Column(db.String(500))

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    parent_id = db.Column(db.Integer, db.ForeignKey("pricingaction.id"))

    extensions = db.relationship("PricingAction", backref="parent", lazy="select", remote_side=[id])
    stocks = db.relationship("PricingAction_Stock", backref="pricingaction", lazy="select")
    strategies = db.relationship("PricingStrategy", backref="pricingaction", lazy="select")
    suppliers = db.relationship("PricingAction_Supplier", backref="pricingaction", lazy="select")
    users = db.relationship("PricingAction_User_Attributes", backref="pricingaction", lazy="select")

    def __init__(self, name, start, end, comment, product_id, stock_ids):
        self.active = False
        self.archived = False
        self.name = name
        self.start = start
        self.end = end
        self.comment = comment
        self.product_id = product_id
        for stock_id in stock_ids:
            self.stocks.append(PricingAction_Stock(stock_id=stock_id))


    def add_strategies(self, strategies: dict, active: bool = False, mp_ids: list = None):
        if 'all' in strategies:
            for mp_id in mp_ids:
                db.session.add(PricingStrategy(strategies['all']['label'], strategies['all']['rank'], strategies['all']['prc_margin'], strategies['all']['promotion_quantity'], strategies['all']['update_factor'],
                                               strategies['all']['update_rule_hours'], strategies['all']['update_rule_quantity'], mp_id, self.id, active=active,
                                               prc_max_margin=strategies['all']['prc_max_margin'] if 'prc_max_margin' in strategies['all'] else None))
                db.session.commit()

        else:
            for mp in strategies:
                db.session.add(PricingStrategy(strategies[mp]['label'], strategies[mp]['rank'], strategies[mp]['prc_margin'], strategies[mp]['promotion_quantity'], strategies[mp]['update_factor'],
                                               strategies[mp]['update_rule_hours'], strategies[mp]['update_rule_quantity'], mp, self.id, active=active,
                                               prc_max_margin=strategies[mp]['prc_max_margin'] if 'prc_max_margin' in strategies[mp] else None))
                db.session.commit()

    def get_stocks(self):
        ids = PricingAction_Stock.query.filter_by(pricingaction_id=self.id).all()
        return Stock.query.filter(Stock.id.in_([int(item.stock_id) for item in ids])).all()

    def get_suppliers(self):
        ids = PricingAction_Supplier.query.filter_by(pricingaction_id=self.id).all()
        return Supplier.query.filter(Supplier.id.in_([int(item.supplier_id) for item in ids])).all()

    def get_users(self):
        ids = PricingAction_User_Attributes.query.filter_by(pricingaction_id=self.id).all()
        return User.query.filter(User.id.in_([int(item.user_id) for item in ids])).all()

    @hybrid_method
    def get_sales(self, start, end):
        sales = db.session.query(
            PricingAction, func.count(PricingStrategy.id), func.count(PricingLog.id), func.sum(Sale.quantity).label("sales_quantity")
        ).filter(
            PricingAction.id == self.id
        ).filter(
            PricingAction.id == PricingStrategy.pricingaction_id
        ).filter(
            PricingStrategy.id == PricingLog.pricingstrategy_id
        ).filter(
            PricingLog.id == Sale.pricinglog_id
        ).filter(
            Sale.timestamp >= start
        ).filter(
            Sale.timestamp <= end
        ).group_by(
            PricingAction.id
        ).first()
        if sales:
            return sales.sales_quantity
        else:
            return 0

    @get_sales.expression
    def get_sales(cls, start, end):
        sales = db.session.query(
            PricingAction, func.count(PricingStrategy.id), func.count(PricingLog.id), func.sum(Sale.quantity).label("sales_quantity")
        ).filter(
            PricingAction.id == cls.id
        ).filter(
            PricingAction.id == PricingStrategy.pricingaction_id
        ).filter(
            PricingStrategy.id == PricingLog.pricingstrategy_id
        ).filter(
            PricingLog.id == Sale.pricinglog_id
        ).filter(
            Sale.timestamp >= start
        ).filter(
            Sale.timestamp <= end
        ).group_by(
            PricingAction.id
        ).first()
        if sales:
            return sales.sales_quantity
        else:
            return 0


class PricingAction_Stock(db.Model):
    __tablename__ = "pricingaction_stock"
    id = db.Column(db.Integer(), primary_key=True)

    pricingaction_id = db.Column(db.Integer, db.ForeignKey("pricingaction.id"))
    stock_id = db.Column(db.Integer, db.ForeignKey("stock.id"))

    def __init__(self, pricingaction_id: int = None, stock_id: int = None):
        self.pricingaction_id = pricingaction_id if pricingaction_id else None
        self.stock_id = stock_id if stock_id else None


class PricingAction_Supplier(db.Model):
    __tablename__ = "pricingaction_supplier"
    id = db.Column(db.Integer(), primary_key=True)

    pricingaction_id = db.Column(db.Integer, db.ForeignKey("pricingaction.id"))
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"))

    def __init__(self, pricingaction_id, supplier_id):
        self.pricingaction_id = pricingaction_id
        self.supplier_id = supplier_id


class PricingLog(db.Model):
    __tablename__ = "pricinglog"
    id = db.Column(db.Integer(), primary_key=True)

    selling_price = db.Column(db.Float)
    shipping_price = db.Column(db.Float)
    nat_shipping_1 = db.Column(db.Float)
    nat_shipping_2 = db.Column(db.Float)
    nat_shipping_3 = db.Column(db.Float)
    nat_shipping_4 = db.Column(db.Float)
    int_shipping_1 = db.Column(db.Float)
    int_shipping_2 = db.Column(db.Float)
    int_shipping_3 = db.Column(db.Float)
    int_shipping_4 = db.Column(db.Float)
    set_date = db.Column(db.DateTime)

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    pricingstrategy_id = db.Column(db.Integer, db.ForeignKey("pricingstrategy.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    product_stock_attributes_id = db.Column(db.Integer, db.ForeignKey("product_stock_attributes.id"))

    sales = db.relationship("Sale", backref="pricinglog", lazy="select")

    def __init__(self, selling_price, nat_shipping_1, nat_shipping_2, nat_shipping_3, nat_shipping_4, int_shipping_1, int_shipping_2, int_shipping_3, int_shipping_4, set_date, marketplace_id,
                 pricingstrategy_id, product_id, product_stock_attributes_id):
        self.selling_price = selling_price
        self.nat_shipping_1 = nat_shipping_1
        self.nat_shipping_2 = nat_shipping_2
        self.nat_shipping_3 = nat_shipping_3
        self.nat_shipping_4 = nat_shipping_4
        self.int_shipping_1 = int_shipping_1
        self.int_shipping_2 = int_shipping_2
        self.int_shipping_3 = int_shipping_3
        self.int_shipping_4 = int_shipping_4
        self.set_date = set_date
        self.marketplace_id = marketplace_id
        self.pricingstrategy_id = pricingstrategy_id
        self.product_id = product_id
        self.product_stock_attributes_id = product_stock_attributes_id

    @hybrid_method
    def get_marketplace_id(self):
        pricingstrategy = PricingStrategy.query.filter_by(id=self.pricingstrategy_id).first()
        if pricingstrategy:
            return pricingstrategy.marketplace_id
        else:
            return None

    @get_marketplace_id.expression
    def get_marketplace_id(cls):
        pricingstrategy = PricingStrategy.query.filter_by(id=cls.pricingstrategy_id).first()
        if pricingstrategy:
            return pricingstrategy.marketplace_id
        else:
            return None

    def get_num_sales(self):
        return sum(sale.quantity for sale in self.sales)


class Sale(db.Model):
    __tablename__ = "sale"
    id = db.Column(db.Integer(), primary_key=True)

    order_number = db.Column(db.String)
    mp_order_id = db.Column(db.String(50))
    shipping_id = db.Column(db.String)
    awb = db.Column(db.String)
    tracking_number = db.Column(db.String(50))
    shipping_method = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime)
    send_by = db.Column(db.DateTime)
    deliver_by = db.Column(db.DateTime)
    sendable_by = db.Column(db.DateTime)
    sent_by = db.Column(db.DateTime)
    pickup_ready_by = db.Column(db.DateTime)
    received_by = db.Column(db.DateTime)
    refused_by = db.Column(db.DateTime)
    failed_by = db.Column(db.DateTime)
    return_by = db.Column(db.DateTime)
    returned_by = db.Column(db.DateTime)
    punctual = db.Column(db.Boolean)
    quantity = db.Column(db.Integer)
    chp_buying_price = db.Column(db.Float)
    own_buying_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)
    shipping_price = db.Column(db.Float)
    chp_margin = db.Column(db.Float)
    own_margin = db.Column(db.Float)
    own_stock = db.Column(db.Boolean)
    cancelled = db.Column(db.Boolean)
    short_sell = db.Column(db.Boolean)
    pre_order = db.Column(db.Boolean)
    international = db.Column(db.Boolean)

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    pricinglog_id = db.Column(db.Integer, db.ForeignKey("pricinglog.id"))

    shipping_events = db.relationship("ShippingEvent", backref="sale", lazy="select")

    def __init__(self, order_number, timestamp, quantity, chp_buying_price, own_buying_price, selling_price, shipping_price, chp_margin, own_margin, marketplace_id, pricinglog_id, own_stock, short_sell, pre_order, international):
        self.order_number = order_number
        self.timestamp = timestamp
        self.quantity = quantity
        self.chp_buying_price = chp_buying_price
        self.own_buying_price = own_buying_price
        self.selling_price = selling_price
        self.shipping_price = shipping_price
        self.chp_margin = chp_margin
        self.own_margin = own_margin
        self.marketplace_id = marketplace_id
        self.pricinglog_id = pricinglog_id
        self.own_stock = own_stock
        self.short_sell = short_sell
        self.pre_order = pre_order
        self.international = international
        self.cancelled = False


class ShippingEvent(db.Model):
    __tablename__ = "shipping_event"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    timestamp = db.Column(db.DateTime)
    status = db.Column(db.String(500))
    text = db.Column(db.String(500))
    short_status = db.Column(db.String(100))
    ice = db.Column(db.String(5))
    ric = db.Column(db.String(5))
    location = db.Column(db.String(100))
    country = db.Column(db.String(100))
    _return = db.Column(db.Boolean)

    sale_id = db.Column(db.Integer, db.ForeignKey("sale.id"))

    def __init__(self, timestamp: datetime, status: str, text: str, short_status: str, ice: str, ric: str, location: str, country: str, _return: bool, sale_id: int):
        self.init_dt = datetime.now()
        self.timestamp = timestamp
        self.status = status
        self.text = text
        self.short_status = short_status
        self.ice = ice
        self.ric = ric
        self.location = location
        self.country = country
        self._return = _return
        self.sale_id = sale_id


class Order_Product_Attributes(db.Model):
    __tablename__ = "order_product_attributes"
    id = db.Column(db.Integer(), primary_key=True)

    ordered = db.Column(db.Integer)
    shipped = db.Column(db.Integer)
    price = db.Column(db.Float)
    prc_tax = db.Column(db.Float)

    order_id = db.Column(db.Integer(), db.ForeignKey("order.id"))
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))

    def __init__(self, ordered, shipped, price, prc_tax, order_id, product_id):
        self.ordered = ordered
        self.shipped = shipped
        self.price = price
        self.prc_tax = prc_tax
        self.order_id = order_id
        self.product_id = product_id

    def gross_price(self):
        return classic_round(self.price*(1+0.01*self.prc_tax))


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(255))
    order_time = db.Column(db.DateTime)
    delivery_time = db.Column(db.DateTime)
    price = db.Column(db.Float)
    additional_cost = db.Column(db.Float)
    comment = db.Column(db.String(500))
    sent = db.Column(db.Boolean)
    tracking_number = db.Column(db.String(50))
    complete = db.Column(db.Boolean)
    external_id = db.Column(db.String(50))
    afterbuy_id = db.Column(db.String(20))

    paymentmethod_id = db.Column(db.Integer(), db.ForeignKey("paymentmethod.id"))
    stock_id = db.Column(db.Integer(), db.ForeignKey("stock.id"))
    supplier_id = db.Column(db.Integer(), db.ForeignKey("supplier.id"))

    paymentstatus_logs = db.relationship("PaymentStatus_Log", backref="order", lazy="select")
    products = db.relationship("Order_Product_Attributes", backref="order", lazy="select")
    shippingstatus_logs = db.relationship("ShippingStatus_Log", backref="order", lazy="select")

    def __init__(self, name, order_time, delivery_time, price, additional_cost, comment, stock_id, paymentmethod_id, supplier_id, complete: bool = False):
        self.name = name
        self.order_time = order_time
        self.delivery_time = delivery_time
        self.price = price
        self.additional_cost = additional_cost
        self.comment = comment
        self.stock_id = stock_id
        self.paymentmethod_id = paymentmethod_id
        self.supplier_id = supplier_id
        self.complete = complete

    def get_products(self):
        ids = Order_Product_Attributes.query.filter_by(order_id=self.id).all()
        return Product.query.filter(Product.id.in_([int(item.product_id) for item in ids])).all()

    def get_current_payment_stat(self):
        return PaymentStatus_Log.query.order_by(PaymentStatus_Log.init_date.desc()).filter_by(order_id=self.id).first()

    @hybrid_method
    def get_current_shipping_stat(self):
        return ShippingStatus_Log.query.order_by(ShippingStatus_Log.init_date.desc()).filter_by(order_id=self.id).first()

    @get_current_shipping_stat.expression
    def get_current_shipping_stat(cls):
        return ShippingStatus_Log.query.order_by(ShippingStatus_Log.init_date.desc()).filter_by(order_id=cls.id).first()

    @hybrid_method
    def get_current_shipping_stat_label(self):
        current_shipping_stat = ShippingStatus_Log.query.order_by(ShippingStatus_Log.init_date.desc()).filter_by(order_id=self.id).first()
        if current_shipping_stat:
            return current_shipping_stat.label
        else:
            return 'Kein Zustand'

    @get_current_shipping_stat_label.expression
    def get_current_shipping_stat_label(cls):
        current_shipping_stat = ShippingStatus_Log.query.order_by(ShippingStatus_Log.init_date.desc()).filter_by(order_id=cls.id).first()
        if current_shipping_stat:
            return current_shipping_stat.label
        else:
            return 'Kein Zustand'

    def combined_history(self):
        shipping_list = ShippingStatus_Log.query.filter_by(order_id=self.id).all()
        for el in shipping_list:
            el.shipping = True
        payment_list = PaymentStatus_Log.query.filter_by(order_id=self.id).all()
        for el in payment_list:
            el.shipping = False
        history = shipping_list + payment_list
        history.sort(key=lambda x: x.init_date, reverse=True)
        return history

    def net_price(self):
        return sum([product.price * product.ordered for product in self.products])

    def gross_price(self):
        return sum([product.price * (1 + product.prc_tax * 0.01) * product.ordered for product in self.products])


class PaymentMethod(db.Model):
    __tablename__ = "paymentmethod"
    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(255))

    orders = db.relationship("Order", backref="paymentmethod", lazy="select")

    def __init__(self, name):
        self.name = name


class PaymentStatus_Log(db.Model):
    __tablename__ = "paymentstatus_log"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))

    label = db.Column(db.String(80))
    comment = db.Column(db.String(80))

    order_id = db.Column(db.Integer(), db.ForeignKey("order.id"))

    def __init__(self, user_id, label, comment, order_id):
        self.init_date = datetime.now()
        self.user_id = user_id
        self.label = label
        self.comment = comment
        self.order_id = order_id


class ShippingStatus_Log(db.Model):
    __tablename__ = "shippingstatus_log"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))

    label = db.Column(db.String(80))
    comment = db.Column(db.String(80))

    order_id = db.Column(db.Integer(), db.ForeignKey("order.id"))

    def __init__(self, user_id, label, comment, order_id):
        self.init_date = datetime.now()
        self.user_id = user_id
        self.label = label
        self.comment = comment
        self.order_id = order_id


class Supplier(db.Model):
    __tablename__ = "supplier"
    id = db.Column(db.Integer(), primary_key=True)

    isfirm = db.Column(db.Boolean)
    salutation = db.Column(db.String(40))
    firmname = db.Column(db.String(255))
    name = db.Column(db.String(100))
    firstname = db.Column(db.String(100))
    fon = db.Column(db.String(50))
    email = db.Column(db.String(100))
    address = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    std_tax = db.Column(db.String(20))

    stocks = db.relationship("Stock", backref="supplier", lazy="select")
    orders = db.relationship("Order", backref="supplier", lazy="select")
    pricingactions = db.relationship("PricingAction_Supplier", backref="supplier", lazy="select")
    pre_orders = db.relationship("PreOrder_Supplier", backref="supplier", lazy="select")
    stock_receipts = db.relationship("StockReceipt", backref="supplier", lazy="select")
    ws_receipts = db.relationship("WSReceipt", backref="supplier", lazy="select")
    invoices = db.relationship("WSInvoice", backref="supplier", lazy="select")

    def __init__(self, isfirm, salutation, firmname, name, fon, email):
        self.isfirm = isfirm
        self.salutation = salutation
        self.firmname = firmname
        self.name = name
        self.fon = fon
        self.email = email

    def get_pricingactions(self):
        ids = PricingAction_Supplier.query.filter_by(supplier_id=self.id).all()
        return PricingAction.query.filter(PricingAction.id.in_([int(item.pricingaction_id) for item in ids])).all()

    @hybrid_method
    def get_name(self):
        if self.isfirm:
            return self.firmname
        elif self.firstname:
            return self.salutation + ' ' + self.firstname + ' ' + self.name
        else:
            return self.salutation + ' ' + self.name

    @get_name.expression
    def get_name(cls):
        if cls.isfirm:
            return cls.firmname
        elif cls.firstname:
            return cls.salutation + ' ' + cls.firstname + ' ' + cls.name
        else:
            return cls.salutation + ' ' + cls.name


class PreOrder(db.Model):
    __tablename__ = "preorder"
    id = db.Column(db.Integer(), primary_key=True)

    sales = db.Column(db.Integer)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))

    suppliers = db.relationship("PreOrder_Supplier", backref="preorder", lazy="select")

    def __init__(self, sales, product_id):
        self.sales = sales
        self.product_id = product_id

    def quantity(self):
        return sum(s.quantity for s in self.suppliers)

    def supplier_quantity(self, supplier_id):
        conn = PreOrder_Supplier.query.filter_by(preorder_id=self.id, supplier_id=supplier_id).first()
        return conn.quantity if conn != None else 0

    def other_supplier_quantities(self):
        conn = db.session.query(
            func.coalesce(func.sum(PreOrder_Supplier.quantity), 0), func.coalesce(func.count(Supplier.id), 0)
        ).filter(
            PreOrder_Supplier.supplier_id==Supplier.id
        ).filter(
            PreOrder_Supplier.preorder_id==self.id
        ).filter(
            Supplier.firmname != 'Vitrex'
        ).filter(
            Supplier.firmname != 'Groß Electronic'
        ).group_by(
            PreOrder_Supplier.preorder_id
        ).first()
        return conn[0] if conn != None else 0


class PreOrder_Supplier(db.Model):
    __tablename__ = "preorder_supplier"
    id = db.Column(db.Integer(), primary_key=True)

    quantity = db.Column(db.Integer)

    preorder_id = db.Column(db.Integer(), db.ForeignKey("preorder.id"))
    supplier_id = db.Column(db.Integer(), db.ForeignKey("supplier.id"))

    def __init__(self, quantity, preorder_id, supplier_id):
        self.quantity = quantity
        self.preorder_id = preorder_id
        self.supplier_id = supplier_id


'''
class StockShelfUnit(db.Model):
    __tablename__ = "stock_shelf_unit"
    id = db.Column(db.Integer(), primary_key=True)

    stock_number = db.Column(db.Integer)
    name = db.Column(db.String(255))
    description = db.Column(db.String(1000))

    pr_categories = db.relationship("SSU_PrC", backref="shelf_unit", lazy="select")
'''


class WSReceipt(db.Model):
    __tablename__ = "ws_receipt"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(255))
    units = db.Column(db.Integer)
    net_price = db.Column(db.Float)
    gross_price = db.Column(db.Float)
    positions = db.Column(db.Integer)
    num_products = db.Column(db.Integer)
    inv_status = db.Column(db.Integer)
    add_cost = db.Column(db.Float)
    comment = db.Column(db.String(500))
    external_id = db.Column(db.String(50))
    afterbuy_id = db.Column(db.String(20))
    completed_at = db.Column(db.DateTime)

    stock_id = db.Column(db.Integer(), db.ForeignKey("stock.id"))
    supplier_id = db.Column(db.Integer(), db.ForeignKey("supplier.id"))
    invoice_id = db.Column(db.Integer(), db.ForeignKey("ws_invoice.id"), nullable=False)
    invoice = db.relationship("WSInvoice", back_populates="receipt", uselist=False)

    parcels = db.relationship("WSRParcel", backref="ws_receipt", lazy="select")

    def __init__(self, name, supplier_id, stock_id: int = 1, units: int = 1, comment: str = None, net_price: float = None, gross_price: float = None, positions: int = None, num_products: int = None,
                 inv_status: float = None, add_cost: float = None, external_id: str = None, afterbuy_id: str = None, completed_at: datetime = None):
        self.init_dt = datetime.now()
        self.name = name
        self.units = units
        self.net_price = net_price
        self.gross_price = gross_price
        self.positions = positions
        self.num_products = num_products
        self.inv_status = inv_status
        self.add_cost = add_cost
        self.comment = comment
        self.external_id = external_id
        self.afterbuy_id = afterbuy_id
        self.stock_id = stock_id
        self.supplier_id = supplier_id
        self.completed_at = completed_at

    def calc_net_price(self):
        return sum([product.price * product.quantity for parcel in self.parcels for product in parcel.products])

    def calc_gross_price(self):
        return sum([product.price * (1 + product.tax) * product.quantity for parcel in self.parcels for product in parcel.products])

    def get_product_quantity(self):
        return sum(sum(p.quantity for p in parcel.products) for parcel in self.parcels)

    def get_product_positions(self):
        return sum(sum(1 for p in parcel.products) for parcel in self.parcels)

    def check_invoice(self):
        if self.invoice:
            inv = self.invoice
            return int('%0.2f' % self.net_price == '%0.2f' % inv.net_price) + int('%0.2f' % self.gross_price == '%0.2f' % inv.gross_price) + int(self.positions == inv.positions) + int(self.num_products == inv.num_products)
        else:
            return -1


class WSRParcel(db.Model):
    __tablename__ = "wsr_parcel"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    tracking_number = db.Column(db.String(50))

    ws_receipt_id = db.Column(db.Integer(), db.ForeignKey("ws_receipt.id"))

    products = db.relationship("WSRProduct", backref="wsr_parcel", lazy="select")

    def __init__(self, tracking_number, ws_receipt_id):
        self.init_dt = datetime.now()
        self.tracking_number = tracking_number
        self.ws_receipt_id = ws_receipt_id

    def get_quantity(self):
        return sum(p.quantity for p in self.products)


class WSRProduct(db.Model):
    __tablename__ = "wsr_product"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    tax = db.Column(db.Float)
    complete = db.Column(db.Boolean)
    completed_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    wsr_parcel_id = db.Column(db.Integer(), db.ForeignKey("wsr_parcel.id"))

    def __init__(self, quantity, price, tax, wsr_parcel_id, product_id, complete: bool = False, completed_at: datetime = None, opened_at: datetime = None):
        self.init_dt = datetime.now()
        self.quantity = quantity
        self.price = price
        self.tax = tax
        self.wsr_parcel_id = wsr_parcel_id
        self.product_id = product_id
        self.complete = complete
        self.completed_at = completed_at
        self.opened_at = opened_at

    def gross_price(self):
        return classic_round(self.price*(1+self.tax))


class WSIProduct(db.Model):
    __tablename__ = "wsi_product"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    tax = db.Column(db.Float)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    ws_invoice_id = db.Column(db.Integer(), db.ForeignKey("ws_invoice.id"))

    def __init__(self, quantity, price, tax, ws_invoice_id, product_id):
        self.init_dt = datetime.now()
        self.quantity = quantity
        self.price = price
        self.tax = tax
        self.ws_invoice_id = ws_invoice_id
        self.product_id = product_id

    def gross_price(self):
        return classic_round(self.price*(1+self.tax))


class WSInvoice(db.Model):
    __tablename__ = "ws_invoice"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    name = db.Column(db.String(255))
    invoice_number = db.Column(db.String(50))
    invoice_dt = db.Column(db.DateTime)
    target_dt = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    paid = db.Column(db.Boolean)
    net_price = db.Column(db.Float)
    gross_price = db.Column(db.Float)
    positions = db.Column(db.Integer)
    num_products = db.Column(db.Integer)
    add_cost = db.Column(db.Float)
    comment = db.Column(db.String(500))
    afterbuy_id = db.Column(db.String(20))
    completed_at = db.Column(db.DateTime)

    supplier_id = db.Column(db.Integer(), db.ForeignKey("supplier.id"))
    receipt = db.relationship("WSReceipt", backref="ws_invoice", lazy="select", uselist=False)

    products = db.relationship("WSIProduct", backref="ws_invoice", lazy="select")

    def __init__(self, name: str = None, invoice_number: str = None, invoice_dt: datetime = None, target_dt: datetime = None, paid_at: datetime = None, paid: bool = None, net_price: float = None,
                 gross_price: float = None, positions: int = None, num_products: int = None, add_cost: float = None, comment: str = None, afterbuy_id: str = None, completed_at: datetime = None,
                 supplier_id: int = None, ws_receipt_id: int = None):
        self.init_dt = datetime.now()
        self.name = name
        self.invoice_number = invoice_number
        self.invoice_dt = invoice_dt
        self.target_dt = target_dt
        self.paid_at = paid_at
        self.paid = paid
        self.net_price = net_price
        self.gross_price = gross_price
        self.positions = positions
        self.num_products = num_products
        self.add_cost = add_cost
        self.comment = comment
        self.afterbuy_id = afterbuy_id
        self.completed_at = completed_at
        self.supplier_id = supplier_id
        self.ws_receipt_id = ws_receipt_id

    def calc_net_price(self):
        return sum([product.price * product.quantity for product in self.products])

    def calc_gross_price(self):
        return sum([product.price * (1 + product.tax) * product.quantity for product in self.products])

    def get_product_quantity(self):
        return sum(p.quantity for p in self.products)

    def get_product_positions(self):
        return sum(1 for p in self.products)


class PSR_Attributes(db.Model):
    __tablename__ = "psr_attributes"
    id = db.Column(db.Integer(), primary_key=True)

    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    tax = db.Column(db.Float)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    stock_receipt_id = db.Column(db.Integer(), db.ForeignKey("stock_receipt.id"))

    def __init__(self, quantity, price, tax, stock_receipt_id, product_id):
        self.quantity = quantity
        self.price = price
        self.tax = tax
        self.stock_receipt_id = stock_receipt_id
        self.product_id = product_id

    def gross_price(self):
        return classic_round(self.price*(1+self.tax))


class Packaging(db.Model):
    __tablename__ = "packaging"
    id = db.Column(db.Integer(), primary_key=True)
    init_dt = db.Column(db.DateTime)

    length_mm = db.Column(db.Integer)
    width_mm = db.Column(db.Integer)
    height_mm = db.Column(db.Integer)
    weight_g = db.Column(db.Integer)
    cost = db.Column(db.Float)

    def __init__(self, length: int, width: int, height: int, weight: int, cost: float = None):
        self.init_dt = datetime.now()
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight
        self.cost = cost


class StockReceipt(db.Model):
    __tablename__ = "stock_receipt"
    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(255))
    tracking_number = db.Column(db.String(50))
    units = db.Column(db.Integer)
    delivery_time = db.Column(db.DateTime)
    price = db.Column(db.Float)
    add_cost = db.Column(db.Float)
    comment = db.Column(db.String(500))
    external_id = db.Column(db.String(50))
    afterbuy_id = db.Column(db.String(20))

    stock_id = db.Column(db.Integer(), db.ForeignKey("stock.id"))
    supplier_id = db.Column(db.Integer(), db.ForeignKey("supplier.id"))

    products = db.relationship("PSR_Attributes", backref="stock_receipt", lazy="select")

    def __init__(self, name, delivery_time, price, add_cost, comment, stock_id, supplier_id, external_id: str = None, afterbuy_id: str = None, tracking_number: str = None, units: int = 1):
        self.name = name
        self.tracking_number = tracking_number
        self.external_id = external_id
        self.afterbuy_id = afterbuy_id
        self.units = units
        self.delivery_time = delivery_time
        self.price = price
        self.add_cost = add_cost
        self.comment = comment
        self.stock_id = stock_id
        self.supplier_id = supplier_id

    def net_price(self):
        return sum([product.price * product.quantity for product in self.products])

    def gross_price(self):
        return sum([product.price * (1 + product.tax) * product.quantity for product in self.products])


# noinspection PySimplifyBooleanCheck
class Stock(db.Model):
    __tablename__ = "stock"
    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(100))
    owned = db.Column(db.Boolean)
    lag_days = db.Column(db.Integer)

    supplier_id = db.Column(db.Integer(), db.ForeignKey("supplier.id"))

    orders = db.relationship("Order", backref="stock", lazy="select")
    products = db.relationship("Product_Stock_Attributes", backref="stock", lazy="select")
    pricingactions = db.relationship("PricingAction_Stock", backref="stock", lazy="select")
    stock_receipts = db.relationship("StockReceipt", backref="stock", lazy="select")
    cat_lags = db.relationship("PrCatStock_Attr", backref="stock", lazy="select")

    def __init__(self, name, owned, lag_days):
        self.name = name
        self.owned = owned
        self.lag_days = lag_days
        cats = ProductCategory.query.all()
        for cat in cats:
            self.cat_lags.append(PrCatStock_Attr(ship_days=0, cat_id=cat.id))

    def get_products(self):
        ids = Product_Stock_Attributes.query.filter_by(stock_id=self.id).all()
        return Product.query.filter(Product.id.in_([int(item.product_id) for item in ids])).all()

    def get_pricingactions(self):
        ids = PricingAction_Stock.query.filter_by(stock_id=self.id).all()
        return PricingAction.query.filter(PricingAction.id.in_([int(item.pricingaction_id) for item in ids])).all()

    def get_available_products(self):
        return Product_Stock_Attributes.query.filter_by(stock_id=self.id).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).all()

    @hybrid_method
    def get_supplier_label(self):
        if self.owned == True:
            return 'Eigenes Lager'
        else:
            supplier = Supplier.query.filter_by(id=self.supplier_id).first()
            return supplier.get_name()

    @get_supplier_label.expression
    def get_supplier_label(cls):
        if cls.owned == True:
            return 'Eigenes Lager'
        else:
            supplier = Supplier.query.filter_by(id=cls.supplier_id).first()
            return supplier.get_name()


class Product_Stock_Attributes(db.Model):
    __tablename__ = "product_stock_attributes"
    id = db.Column(db.Integer(), primary_key=True)

    internal_id = db.Column(db.String(100))
    loc = db.Column(db.String(20))
    sku = db.Column(db.String(20))
    condition = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    buying_price = db.Column(db.Float)
    shipping_cost = db.Column(db.Float)
    prc_tax = db.Column(db.Float)
    lag_days = db.Column(db.Integer)
    avail_date = db.Column(db.DateTime)
    termination_date = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    user_generated = db.Column(db.Boolean)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    stock_id = db.Column(db.Integer(), db.ForeignKey("stock.id"))

    pricinglogs = db.relationship("PricingLog", backref="product_stock_attributes", lazy="select")
    serial_data = db.relationship("PSASerialData", backref="product_stock_attributes", lazy="select")
    stock_updates = db.relationship("StockUpdateQueue", backref="product_stock_attributes", lazy="select")

    def __init__(self, condition, quantity, buying_price, shipping_cost, prc_tax, lag_days, avail_date, termination_date,
                 product_id, stock_id, internal_id=None, sku=None, user_id=None):
        self.internal_id = internal_id
        self.sku = sku
        self.condition = condition
        self.quantity = quantity
        self.buying_price = buying_price
        self.shipping_cost = shipping_cost
        self.prc_tax = prc_tax
        self.lag_days = lag_days
        self.avail_date = avail_date
        self.termination_date = termination_date
        self.product_id = product_id
        self.stock_id = stock_id
        self.serial_data.append(PSASerialData(quantity=quantity, buying_price=buying_price, user_id=user_id))

    def self_update(self, termination_date: datetime = None, quantity: int = None, buying_price: float = None, user_id: int = None):
        if termination_date is not None and type(termination_date) != datetime:
            raise TypeError('Variable termination_date must be of type datetime')
        if quantity is not None and type(quantity) != int:
            raise TypeError('Variable quantity must be of type int')
        if buying_price is not None and type(buying_price) != float:
            raise TypeError('Variable buying_price must be of type float')
        if user_id is not None and type(user_id) != int:
            raise TypeError('Variable user_id must be of type int')
        if quantity is not None or buying_price is not None:
            if buying_price is not None and buying_price != self.buying_price:
                db.session.add(PSAUpdateQueue(self.product.id))
                db.session.commit()
            self.buying_price = buying_price if buying_price is not None else self.buying_price
            self.quantity = quantity if quantity is not None and self.stock_id != 1 else self.quantity
            last_sd = PSASerialData.query.filter_by(psa_id=self.id).order_by(PSASerialData.init_date_time.desc()).first()
            if last_sd is not None:
                last_sd.rep_datetime = datetime.now()
            buying_price = last_sd.buying_price if last_sd is not None and buying_price is None else buying_price
            quantity = last_sd.quantity if last_sd is not None and quantity is None else quantity
            db.session.add(PSASerialData(quantity, buying_price, self.id, user_id))
            self.termination_date = termination_date if termination_date else self.termination_date
            db.session.commit()

    def get_current_quantity(self):
        counter = 0
        for log in self.pricinglogs:
            for sale in log.sales:
                counter += sale.quantity
        return self.quantity - counter


class PSASerialData(db.Model):
    __tablename__ = "psa_serial_data"
    id = db.Column(db.Integer, primary_key=True)
    init_date_time = db.Column(db.DateTime)
    rep_datetime = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    quantity = db.Column(db.Integer)
    buying_price = db.Column(db.Float)

    psa_id = db.Column(db.Integer, db.ForeignKey("product_stock_attributes.id"))

    def __init__(self, quantity: int, buying_price: float, psa_id: int = None, user_id: int = None):
        self.init_date_time = datetime.now()
        self.user_id = user_id
        self.quantity = quantity
        self.buying_price = buying_price
        self.psa_id = psa_id


class ExtOffer(db.Model):
    __tablename__ = "extoffer"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)

    selling_price = db.Column(db.Float())
    shipping_price = db.Column(db.Float())
    direct_checkout = db.Column(db.Boolean)
    rank = db.Column(db.Integer())
    delivery_time = db.Column(db.String(80))
    free_return = db.Column(db.Integer)
    seller_rating = db.Column(db.Integer)
    voucher = db.Column(db.Boolean)

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    platform_id = db.Column(db.Integer(), db.ForeignKey("extplatform.id"))
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    seller_id = db.Column(db.Integer(), db.ForeignKey("extseller.id"))

    def __init__(self, selling_price, shipping_price, direct_checkout, rank, delivery_time, free_return, seller_rating, voucher, marketplace_id, platform_id, product_id, seller_id):
        self.init_date = datetime.now()
        self.last_seen = datetime.now()
        self.selling_price = selling_price
        self.shipping_price = shipping_price
        self.direct_checkout = direct_checkout
        self.rank = rank
        self.delivery_time = delivery_time
        self.free_return = free_return
        self.seller_rating = seller_rating
        self.voucher = voucher
        self.marketplace_id = marketplace_id
        self.platform_id = platform_id
        self.product_id = product_id
        self.seller_id = seller_id

    @hybrid_method
    def get_seller_name(self):
        seller = ExtSeller.query.filter_by(id=self.seller_id).first()
        return seller.name

    @get_seller_name.expression
    def get_seller_name(cls):
        seller = ExtSeller.query.filter_by(id=cls.seller_id).first()
        return seller.name

    @hybrid_method
    def get_platform_name(self):
        platform = ExtPlatform.query.filter_by(id=self.platform_id).first()
        return platform.name

    @get_platform_name.expression
    def get_platform_name(cls):
        platform = ExtPlatform.query.filter_by(id=cls.platform_id).first()
        return platform.name


class ExtSeller(db.Model):
    __tablename__ = "extseller"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)

    name = db.Column(db.String(255))

    offers = db.relationship("ExtOffer", backref="extseller", lazy="select")
    strategies = db.relationship("ExtSeller_PricingStrategy_NonCompeting", backref="extseller", lazy="select")

    def __init__(self, name):
        self.init_date = datetime.now()
        self.name = name

    def get_strategies(self):
        ids = ExtSeller_PricingStrategy_NonCompeting.query.filter_by(extseller_id=self.id).all()
        return PricingStrategy.query. \
            filter(PricingStrategy.id.in_([int(item.pricingstrategy_id) for item in ids])).all()


class ExtSeller_PricingStrategy_NonCompeting(db.Model):
    __tablename__ = "extseller_pricingstrategy_noncompeting"
    id = db.Column(db.Integer(), primary_key=True)

    extseller_id = db.Column(db.Integer, db.ForeignKey("extseller.id"))
    pricingstrategy_id = db.Column(db.Integer, db.ForeignKey("pricingstrategy.id"))

    def __init__(self, extseller_id, pricingstrategy_id):
        self.extseller_id = extseller_id
        self.pricingstrategy_id = pricingstrategy_id


class ExtPlatform(db.Model):
    __tablename__ = "extplatform"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)

    name = db.Column(db.String(255))

    offers = db.relationship("ExtOffer", backref="extplatform", lazy="select")
    strategies = db.relationship("ExtPlatform_PricingStrategy_NonCompeting", backref="extplatform", lazy="select")

    def __init__(self, name):
        self.init_date = datetime.now()
        self.name = name

    def get_strategies(self):
        ids = ExtPlatform_PricingStrategy_NonCompeting.query.filter_by(extplatform_id=self.id).all()
        return PricingStrategy.query. \
            filter(PricingStrategy.id.in_([int(item.pricingstrategy_id) for item in ids])).all()


class ExtPlatform_PricingStrategy_NonCompeting(db.Model):
    __tablename__ = "extplatform_pricingstrategy_noncompeting"
    id = db.Column(db.Integer(), primary_key=True)

    extplatform_id = db.Column(db.Integer, db.ForeignKey("extplatform.id"))
    pricingstrategy_id = db.Column(db.Integer, db.ForeignKey("pricingstrategy.id"))

    def __init__(self, extplatform_id, pricingstrategy_id):
        self.extplatform_id = extplatform_id
        self.pricingstrategy_id = pricingstrategy_id


class IdealoWatchScriptLog(db.Model):
    __tablename__ = "idealowatchscriptlog"
    id = db.Column(db.Integer(), primary_key=True)

    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    last_product_id = db.Column(db.Integer)

    def __init__(self, start):
        self.start = start


######################################################################################

###################################   VERSIONING   ###################################

######################################################################################


class User_Version(db.Model):
    __tablename__ = "user_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    active = db.Column(db.Boolean)
    confirmed = db.Column(db.Boolean)
    wait_for_pricingaction_thread = db.Column(db.Boolean)
    wait_for_product_thread = db.Column(db.Boolean)
    confirmation_code = db.Column(db.String(255))
    username = db.Column(db.String(50))
    password = db.Column(db.String(255))
    name = db.Column(db.String(100))
    firstname = db.Column(db.String(100))
    birthday = db.Column(db.DateTime)
    fon = db.Column(db.String(50))
    email = db.Column(db.String(100))
    address = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    profilepic = db.Column(db.String(10))

    def __init__(self, system_id, active, confirmed, confirmation_code, username, password, name, firstname, birthday,
                 fon, email, address, zipcode, city, country, profilepic):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.active = active
        self.confirmed = confirmed
        self.confirmation_code = confirmation_code
        self.username = username
        self.password = password
        self.name = name
        self.firstname = firstname
        self.birthday = birthday
        self.fon = fon
        self.email = email
        self.address = address
        self.zipcode = zipcode
        self.city = city
        self.country = country
        self.profilepic = profilepic


class Role_User_Attributes_Version(db.Model):
    __tablename__ = "role_user_attributes_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, system_id, role_id, user_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.role_id = role_id
        self.user_id = user_id


class Product_Version(db.Model):
    __tablename__ = "product_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    internal_id = db.Column(db.String(20))
    hsp_id_type = db.Column(db.String(50))
    hsp_id = db.Column(db.String(20))
    mpn = db.Column(db.String(20))
    name = db.Column(db.String(100))
    brand = db.Column(db.String)
    measurements = db.Column(db.String(20))
    weight = db.Column(db.Float)
    packagenr = db.Column(db.String(20))
    shipping_dhl = db.Column(db.Float)
    shipping_dp = db.Column(db.Float)
    shipping_dpd = db.Column(db.Float)
    shipping_hermes = db.Column(db.Float)

    category_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))

    def __init__(self, system_id, internal_id, hsp_id_type, hsp_id, mpn, name, brand, measurements, weight, packagenr,
                 shipping_dhl, shipping_dp, shipping_dpd, shipping_hermes, category_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.internal_id = internal_id
        self.hsp_id_type = hsp_id_type
        self.hsp_id = hsp_id
        self.mpn = mpn
        self.name = name
        self.brand = brand
        self.measurements = measurements
        self.weight = weight
        self.packagenr = packagenr
        self.shipping_dhl = shipping_dhl
        self.shipping_dp = shipping_dp
        self.shipping_dpd = shipping_dpd
        self.shipping_hermes = shipping_hermes
        self.category_id = category_id


class ProductPicture_Version(db.Model):
    __tablename__ = "productpicture_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    pic_type = db.Column(db.Integer)
    link = db.Column(db.String(255))

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, system_id, pic_type, link, product_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.pic_type = pic_type
        self.link = link
        self.product_id = product_id


class ProductLink_Version(db.Model):
    __tablename__ = "productlink_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    link = db.Column(db.String(500))

    category_id = db.Column(db.Integer, db.ForeignKey("productlinkcategory.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, system_id, link, category_id, product_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.link = link
        self.category_id = category_id
        self.product_id = product_id


class ProductLinkCategory_Version(db.Model):
    __tablename__ = "productlinkcategory_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    active = db.Column(db.Boolean)
    name = db.Column(db.String(100))

    def __init__(self, system_id, active, name):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.active = active
        self.name = name


class ProductCategory_Version(db.Model):
    __tablename__ = "productcategory_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    active = db.Column(db.Boolean)
    internal_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))

    def __init__(self, system_id, active, internal_id, name):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.active = active
        self.internal_id = internal_id
        self.name = name


class Marketplace_ProductCategory_Version(db.Model):
    __tablename__ = "marketplace_productcategory_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    marketplace_system_id = db.Column(db.String(50))

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    productcategory_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))

    def __init__(self, system_id, marketplace_system_id, marketplace_id, productcategory_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.marketplace_system_id = marketplace_system_id
        self.marketplace_id = marketplace_id
        self.productcategory_id = productcategory_id


class ProductCategory_ProductFeature_Version(db.Model):
    __tablename__ = "productcategory_productfeature_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    productcategory_id = db.Column(db.Integer, db.ForeignKey("productcategory.id"))
    productfeature_id = db.Column(db.Integer, db.ForeignKey("productfeature.id"))

    def __init__(self, system_id, productcategory_id, productfeature_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.productcategory_id = productcategory_id
        self.productfeature_id = productfeature_id


class ProductFeature_Version(db.Model):
    __tablename__ = "productfeature_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    active = db.Column(db.Boolean)
    internal_id = db.Column(db.String(20))
    name = db.Column(db.String(100))
    fixed_values = db.Column(db.Boolean)

    def __init__(self, system_id, active, internal_id, name, fixed_values):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.active = active
        self.internal_id = internal_id
        self.name = name
        self.fixed_values = fixed_values


class Marketplace_ProductFeature_Version(db.Model):
    __tablename__ = "marketplace_productfeature_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    marketplace_system_id = db.Column(db.String(100))

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    productfeature_id = db.Column(db.Integer, db.ForeignKey("productfeature.id"))

    def __init__(self, system_id, marketplace_system_id, marketplace_id, productfeature_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.marketplace_system_id = marketplace_system_id
        self.marketplace_id = marketplace_id
        self.productfeature_id = productfeature_id


class ProductFeatureValue_Version(db.Model):
    __tablename__ = "productfeaturevalue_version"
    id = db.Column(db.Integer, primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    active = db.Column(db.Boolean)
    value = db.Column(db.String(200))

    productfeature_id = db.Column(db.Integer, db.ForeignKey("productfeature.id"))

    def __init__(self, system_id, active, value, productfeature_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.active = active
        self.value = value
        self.productfeature_id = productfeature_id


class Product_ProductFeatureValue_Version(db.Model):
    __tablename__ = "product_productfeaturevalue_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    productfeaturevalue_id = db.Column(db.Integer(), db.ForeignKey("productfeaturevalue.id"))
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))

    def __init__(self, system_id, productfeaturevalue_id, product_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.productfeaturevalue_id = productfeaturevalue_id
        self.product_id = product_id


class Marketplace_Product_Attributes_Version(db.Model):
    __tablename__ = "marketplace_product_attributes_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    uploaded = db.Column(db.Boolean)
    upload_date = db.Column(db.DateTime)
    marketplace_system_id = db.Column(db.String(100))
    name = db.Column(db.String(80))
    link = db.Column(db.String(500))
    selling_price = db.Column(db.Float)
    shipping_dhl_cost = db.Column(db.Float)
    shipping_dhl_time = db.Column(db.String(80))
    shipping_dhl_comment = db.Column(db.String(80))
    shipping_dp_cost = db.Column(db.Float())
    shipping_dp_time = db.Column(db.String(80))
    shipping_dp_comment = db.Column(db.String(80))
    shipping_dpd_cost = db.Column(db.Float())
    shipping_dpd_time = db.Column(db.String(80))
    shipping_dpd_comment = db.Column(db.String(80))
    shipping_hermes_cost = db.Column(db.Float())
    shipping_hermes_time = db.Column(db.String(80))
    shipping_hermes_comment = db.Column(db.String(80))
    commission = db.Column(db.Float)
    quantity_delta = db.Column(db.Integer)
    price_regulation = db.Column(db.Boolean)
    factor = db.Column(db.Float)

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, system_id, uploaded, upload_date, marketplace_system_id, name, selling_price, shipping_dhl_cost,
                 shipping_dhl_time, shipping_dhl_comment, shipping_dp_cost, shipping_dp_time, shipping_dp_comment,
                 shipping_dpd_cost, shipping_dpd_time, shipping_dpd_comment, shipping_hermes_cost, shipping_hermes_time,
                 shipping_hermes_comment, commission, quantity_delta, price_regulation, factor, marketplace_id,
                 product_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.uploaded = uploaded
        self.upload_date = upload_date
        self.marketplace_system_id = marketplace_system_id
        self.name = name
        self.selling_price = selling_price
        self.shipping_dhl_cost = shipping_dhl_cost
        self.shipping_dhl_time = shipping_dhl_time
        self.shipping_dhl_comment = shipping_dhl_comment
        self.shipping_dp_cost = shipping_dp_cost
        self.shipping_dp_time = shipping_dp_time
        self.shipping_dp_comment = shipping_dp_comment
        self.shipping_dpd_cost = shipping_dpd_cost
        self.shipping_dpd_time = shipping_dpd_time
        self.shipping_dpd_comment = shipping_dpd_comment
        self.shipping_hermes_cost = shipping_hermes_cost
        self.shipping_hermes_time = shipping_hermes_time
        self.shipping_hermes_comment = shipping_hermes_comment
        self.commission = commission
        self.quantity_delta = quantity_delta
        self.price_regulation = price_regulation
        self.factor = factor
        self.marketplace_id = marketplace_id
        self.product_id = product_id


class Marketplace_Product_Attributes_Description_Version(db.Model):
    __tablename__ = "marketplace_product_attributes_description_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    text = db.Column(db.String(500))

    marketplace_product_attributes_id = db.Column(db.Integer, db.ForeignKey("marketplace_product_attributes.id"))

    def __init__(self, system_id, text, marketplace_product_attributes_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.text = text
        self.marketplace_product_attributes_id = marketplace_product_attributes_id


class Marketplace_Version(db.Model):
    __tablename__ = "marketplace_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    name = db.Column(db.String(100))
    link = db.Column(db.String(255))

    productlinkcategory_id = db.Column(db.Integer, db.ForeignKey("productlinkcategory.id"))

    def __init__(self, system_id, name, link):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.name = name
        self.link = link


class PricingAction_Version(db.Model):
    __tablename__ = "pricingaction_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    active = db.Column(db.Boolean)
    archived = db.Column(db.Boolean)
    name = db.Column(db.Integer)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    promotion_quantity = db.Column(db.Integer)
    comment = db.Column(db.String(500))

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))

    def __init__(self, system_id, active, archived, name, start, end, promotion_quantity, comment, product_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.active = active
        self.archived = archived
        self.name = name
        self.start = start
        self.end = end
        self.promotion_quantity = promotion_quantity
        self.comment = comment
        self.product_id = product_id


class PricingAction_Supplier_Version(db.Model):
    __tablename__ = "pricingaction_supplier_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    pricingaction_id = db.Column(db.Integer, db.ForeignKey("pricingaction.id"))
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"))

    def __init__(self, system_id, pricingaction_id, supplier_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.pricingaction_id = pricingaction_id
        self.supplier_id = supplier_id


class PricingStrategy_Version(db.Model):
    __tablename__ = "pricingstrategy_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    active = db.Column(db.Boolean)
    archived = db.Column(db.Boolean)
    label = db.Column(db.Integer)
    rank = db.Column(db.Integer)
    prc_margin = db.Column(db.Float)
    promotion_quantity = db.Column(db.Integer)
    update_factor = db.Column(db.Float)
    update_rule_hours = db.Column(db.Integer)
    update_rule_quantity = db.Column(db.Integer)

    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"))
    pricingaction_id = db.Column(db.Integer, db.ForeignKey("pricingaction.id"))

    def __init__(self, system_id, active, archived, label, rank, prc_margin, promotion_quantity, update_factor,
                 update_rule_hours, update_rule_quantity, marketplace_id, pricingaction_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.active = active
        self.archived = archived
        self.label = label
        self.rank = rank
        self.prc_margin = prc_margin
        self.promotion_quantity = promotion_quantity
        self.update_factor = update_factor
        self.update_rule_hours = update_rule_hours
        self.update_rule_quantity = update_rule_quantity
        self.marketplace_id = marketplace_id
        self.pricingaction_id = pricingaction_id


class Order_Product_Attributes_Version(db.Model):
    __tablename__ = "order_product_attributes_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    ordered = db.Column(db.Integer())
    shipped = db.Column(db.Integer())
    price = db.Column(db.Float())
    prc_tax = db.Column(db.Float())

    order_id = db.Column(db.Integer(), db.ForeignKey("order.id"))
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))

    def __init__(self, system_id, ordered, shipped, price, prc_tax, order_id, product_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.ordered = ordered
        self.shipped = shipped
        self.price = price
        self.prc_tax = prc_tax
        self.order_id = order_id
        self.product_id = product_id


class Order_Version(db.Model):
    __tablename__ = "order_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    name = db.Column(db.String(255))
    order_time = db.Column(db.DateTime)
    delivery_time = db.Column(db.DateTime)
    price = db.Column(db.Float)
    additional_cost = db.Column(db.Float)
    comment = db.Column(db.String(500))

    paymentmethod_id = db.Column(db.Integer(), db.ForeignKey("paymentmethod.id"))
    stock_id = db.Column(db.Integer(), db.ForeignKey("stock.id"))
    supplier_id = db.Column(db.Integer(), db.ForeignKey("supplier.id"))

    def __init__(self, system_id, name, order_time, delivery_time, price, additional_cost, comment, stock_id, paymentmethod_id, supplier_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.name = name
        self.order_time = order_time
        self.delivery_time = delivery_time
        self.price = price
        self.additional_cost = additional_cost
        self.comment = comment
        self.paymentmethod_id = paymentmethod_id
        self.stock_id = stock_id
        self.supplier_id = supplier_id


class PaymentMethod_Version(db.Model):
    __tablename__ = "paymentmethod_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    name = db.Column(db.String(255))

    def __init__(self, system_id, name):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.name = name


class Supplier_Version(db.Model):
    __tablename__ = "supplier_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    isfirm = db.Column(db.Boolean)
    salutation = db.Column(db.String(40))
    firmname = db.Column(db.String(255))
    name = db.Column(db.String(100))
    firstname = db.Column(db.String(100))
    fon = db.Column(db.String(50))
    email = db.Column(db.String(100))
    address = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))

    def __init__(self, system_id, isfirm, salutation, firmname, name, firstname, fon, email, address, zipcode, city,
                 country):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.isfirm = isfirm
        self.salutation = salutation
        self.firmname = firmname
        self.name = name
        self.firstname = firstname
        self.fon = fon
        self.email = email
        self.address = address
        self.zipcode = zipcode
        self.city = city
        self.country = country


class Stock_Version(db.Model):
    __tablename__ = "stock_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    name = db.Column(db.String(100))
    owned = db.Column(db.Boolean)
    lag_days = db.Column(db.Integer)

    supplier_id = db.Column(db.Integer(), db.ForeignKey("supplier.id"))

    def __init__(self, system_id, owned, lag_days, supplier_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.owned = owned
        self.lag_days = lag_days
        self.supplier_id = supplier_id


class Product_Stock_Attributes_Version(db.Model):
    __tablename__ = "product_stock_attributes_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    condition = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    buying_price = db.Column(db.Float)
    shipping_cost = db.Column(db.Float)
    prc_tax = db.Column(db.Float)
    lag_days = db.Column(db.Integer)
    avail_date = db.Column(db.DateTime)
    termination_date = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    stock_id = db.Column(db.Integer(), db.ForeignKey("stock.id"))

    def __init__(self, system_id, condition, quantity, buying_price, shipping_cost, lag_days, avail_date,
                 termination_date, last_seen, product_id, stock_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.condition = condition
        self.quantity = quantity
        self.buying_price = buying_price
        self.shipping_cost = shipping_cost
        self.lag_days = lag_days
        self.avail_date = avail_date
        self.termination_date = termination_date
        self.last_seen = last_seen
        self.product_id = product_id
        self.stock_id = stock_id


class ExtSeller_PricingStrategy_NonCompeting_Version(db.Model):
    __tablename__ = "extseller_pricingstrategy_noncompeting_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    extseller_id = db.Column(db.Integer, db.ForeignKey("extseller.id"))
    pricingstrategy_id = db.Column(db.Integer, db.ForeignKey("pricingstrategy.id"))

    def __init__(self, system_id, extseller_id, pricingstrategy_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.extseller_id = extseller_id
        self.pricingstrategy_id = pricingstrategy_id


class ExtPlatform_PricingStrategy_NonCompeting_Version(db.Model):
    __tablename__ = "extplatform_pricingstrategy_noncompeting_version"
    id = db.Column(db.Integer(), primary_key=True)
    init_date = db.Column(db.DateTime)
    system_id = db.Column(db.Integer)

    extplatform_id = db.Column(db.Integer, db.ForeignKey("extplatform.id"))
    pricingstrategy_id = db.Column(db.Integer, db.ForeignKey("pricingstrategy.id"))

    def __init__(self, system_id, extplatform_id, pricingstrategy_id):
        self.init_date = datetime.now()
        self.system_id = system_id
        self.extplatform_id = extplatform_id
        self.pricingstrategy_id = pricingstrategy_id

