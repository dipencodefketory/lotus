# -*- coding: utf-8 -*-

from lotus import app, db, tax_group, csrf, env_vars_path
from basismodels import *
from flask import render_template, request, redirect, url_for, session, flash, Response, jsonify, make_response
from flask_mail import Mail, Message
from sqlalchemy import func, or_, and_, any_, distinct
from sqlalchemy.sql.expression import cast, label
from sqlalchemy import String as sqlalchemy_String
from sqlalchemy import Integer as sqlalchemy_Integer
from functools import wraps
from threading import Thread
from passlib.hash import sha256_crypt
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from ebaysdk.finding import Connection as Finding_Connection
from ebaysdk.trading import Connection as Trading_Connection
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth
import html
from os import urandom
import os.path
from datetime import *
import time
import math
import operator
import numpy as np
import seaborn as sns
import io
import csv
import re
import time as t
import ftplib
from lookup import spec_trait_2_dict, spec_trait_3_dict, version_normalizer_dict, platform_dict, region_dict, comma_split_features
from ws_order import send_order
from functions import *
from sqlalchemy import text
from typing import List
import product_processor
from routines import ebay_description_generator, ab_product_update
import ebay_api
import idealo_offer
import html2text
from entertainment_trading import get_order
from os import environ
from dotenv import load_dotenv
from other_apis import dl_translate
from validate_addresses import correct_addresses
import traceback

load_dotenv(env_vars_path)
h = html2text.HTML2Text()
h.body_width = 0


mail = Mail(app)


class SellInAttributeObject:
    def __init__(self, name, values, necessary):
        self.name = name
        self.values = values
        self.necessary = necessary


def async(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrap


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorisierter Zugriff.', 'danger')
            return redirect(url_for('center_login'))
    return wrap


def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            user = User.query.filter_by(id=session['user_id']).first()
            for role in roles:
                loop_role = Role.query.filter_by(name=role).first()
                if loop_role not in user.get_roles():
                    flash('Unauthorisierter Zugriff.', 'danger')
                    return redirect(url_for('center_dashboard'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def new_pageload(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        user = User.query.filter_by(id=session['user_id']).first()
        if (datetime.now() - user.lastpageload).seconds > 43200:
            session.clear()
            flash('Automatisch ausgeloggt.', 'danger')
            return redirect(url_for('center_login'))
        else:
            user.lastpageload = datetime.now()
            db.session.commit()
            return f(*args, **kwargs)
    return wrap


@async
def send_async_email(application, msg):
    with application.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    try:
        msg.body = text_body
    except:
        pass
    msg.html = html_body
    send_async_email(app, msg)


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('center_dashboard'))


@app.route('/center/login', methods=['GET'])
def center_login():
    if 'logged_in' in session:
        return redirect(url_for('center_dashboard'))
    else:
        return render_template('center/login.html')


@app.route('/center/loginhandle', methods=['POST'])
def center_loginhandle():
    if 'logged_in' in session:
        return redirect(url_for('center_dashboard'))
    else:
        password_candidate = request.form['password']
        user = User.query.filter_by(username=request.form['username'].lower()).first()
        if user:
            actual_password = user.password
            if sha256_crypt.verify(password_candidate, actual_password):
                session['logged_in'] = True
                session['username'] = user.username
                session['user_id'] = user.id
                session['roles'] = [role.name for role in user.get_roles()]
                session['picture_server'] = 'https://strikeusifucan.com/'
                session['product_id_choice'] = False
                session['pricingaction_id_choice'] = False
                session['center_product_filters'] = None
                session['product_filter_infos'] = {'datalimit_whole': None,
                                                   'datalimit_page': 25,
                                                   'datalimit_offset': 0,
                                                   'product_sort': 'id',
                                                   'product_sort_dir': 'DESC',
                                                   'product_ids': [],
                                                   'productcategory_ids': [],
                                                   'tag_ids': [],
                                                   'keyword_search': [],
                                                   'mp_listing_dict': {},
                                                   'own_stock_min': None,
                                                   'own_stock_max': None,
                                                   'action_num': None,
                                                   'ext_idealo_watch_active': None,
                                                   'short_sell_active': None,
                                                   'min_sell_date': None,
                                                   'max_sell_date': None,
                                                   'state': None,
                                                   'currprocstat': None}
                session['stock_filter_infos'] = {'datalimit_page': 25,
                                                 'datalimit_whole': None,
                                                 'product_ids': [],
                                                 'quantity': None,
                                                 'buying_price': None,
                                                 'last_update': None,
                                                 'lag_days': None,
                                                 'shipping_cost': None,
                                                 'datalimit_offset': 0,
                                                 'sort_dir': 'DESC',
                                                 'sort': 'id'}

                session['stock_products_filter_infos'] = {'datalimit_page': 25,
                                                          'datalimit_whole': None,
                                                          'product_ids': [],
                                                          'quantity': None,
                                                          'buying_price': None,
                                                          'lag_days': None,
                                                          'shipping_cost': None,
                                                          'datalimit_offset': 0,
                                                          'sort_dir': 'DESC',
                                                          'sort': 'id'}
                marketplaces = Marketplace.query.all()
                for marketplace in marketplaces:
                    session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)] = None

                session['dynamic_pricing_filter_infos'] = {'marketplace_options': {},
                                                           'resultlimit': 10,
                                                           'except_mp': ['Kuchenboden', 'Leerverkauf'],
                                                           'short_sell_active': None,
                                                           'activity': None,
                                                           'order_by': 'p_name',
                                                           'order_by_dir': 'ASC'}
                session['orders_sales_filter_infos'] = {'product_ids': [],
                                                        'product_id_type': 'id',
                                                        'min_sale_date': (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0),
                                                        'max_sale_date': datetime.now().replace(hour=23, minute=59, second=59),
                                                        'min_release_date': None,
                                                        'max_release_date': None,
                                                        'min_sale': None,
                                                        'max_sale': None,
                                                        'min_stock': None,
                                                        'max_stock': None,
                                                        'page': 1,
                                                        'datalimit_page': 25,
                                                        'datalimit_whole': None,
                                                        'sort_dir': 'DESC',
                                                        'sort': 'id'}
                user.lastpageload = datetime.now()
                db.session.commit()

                flash('Willkommen ' + user.firstname + '!', 'success')
                return redirect(url_for('center_dashboard'))
            else:
                flash('Fehlerhafte Login-Daten.', 'danger')
                return redirect(url_for('center_login'))
        else:
            flash('Benutzer nicht gefunden.', 'danger')
            return redirect(url_for('center_login'))


@app.route('/center/privacy_policy')
def center_privacy_policy():
    return render_template('center/privacy_policy.html')


@app.route('/center/register', methods=['GET', 'POST'])
def center_register():
    if 'logged_in' in session:
        return redirect(url_for('center_dashboard'))
    else:
        if request.method == 'POST':
            username = request.form['username']
            name = request.form['name']
            firstname = request.form['firstname']
            email = request.form['email']
            if (username != ''
            and name != ''
            and firstname != ''
            and email != ''):
                if User.query.filter_by(username=username.lower()).first() is None:
                    if User.query.filter_by(email=email.lower()).first() is None:
                        password = urandom(16).hex()[:10]
                        confirmation_code = urandom(16).hex()
                        user = User(username.lower(), sha256_crypt.encrypt(password),
                                    sha256_crypt.encrypt(confirmation_code), name, firstname, email.lower())
                        db.session.add(user)
                        db.session.commit()
                        link = url_for('center_confirm_user', user_id=user.id, confirmation_code=confirmation_code, _external=True)
                        link = link.replace('%2C', ',')
                        send_email('Vielen Dank für deine Registrierung', 'system@lotusicafe.de', [email],
                                   render_template('center/emails/register.txt',
                                                   user=user, password=password, link=link),
                                   render_template('center/emails/register.html',
                                                   user=user, password=password, link=link))
                        flash('Erfolgreich registriert.', 'success')
                        return redirect(url_for('center_login'))
                    else:
                        flash('Diese E-mail-Adresse ist bereits vergeben.', 'danger')
                else:
                    flash('Dieser Benutzername ist bereits vergeben.', 'danger')
            else:
                flash('Bitte alle Felder aufüllen.', 'danger')
        return render_template('center/register.html')


@app.route('/center/confirm_user/<user_id>,<confirmation_code>')
def center_confirm_user(user_id, confirmation_code):
    user = User.query.filter_by(id=int(user_id)).first()
    if user:
        if sha256_crypt.verify(confirmation_code, user.confirmation_code):
            user.confirmed = True
            db.session.commit()
            flash('Dein Account wurde bestätigt.', 'success')
            return redirect(url_for('center_login'))
        else:
            flash('Fehlerhafter Bestätigungscode.', 'danger')
            return redirect(url_for('center_login'))
    else:
        flash('Benutzer nicht gefunden.', 'danger')
        return redirect(url_for('center_login'))


@app.route('/center/newpassword', methods=['GET', 'POST'])
def center_newpassword():
    if 'logged_in' in session:
        return redirect(url_for('center_dashboard'))
    else:
        if request.method == 'POST':
            user = User.query.filter_by(username=request.form['username'].lower()).first()
            password_candidate = request.form['oldpassword']
            if user:
                actual_password = user.password
                if sha256_crypt.verify(password_candidate, actual_password):
                    newpassword = request.form['password']
                    passwordconfirm = request.form['passwordconfirm']
                    if newpassword != passwordconfirm:
                        flash('Die Passwörter stimmen nicht überein.', 'danger')
                    else:
                        user.password = sha256_crypt.encrypt(newpassword)
                        db.session.commit()
                        flash('Das Passwort wurde erfolgreich geändert.', 'success')
                        return redirect(url_for('center_login'))
                else:
                    flash('Fehlerhafte Login-Daten.', 'danger')
            else:
                flash('Benutzer nicht gefunden.', 'danger')
        return render_template('center/newpassword.html')


@app.route('/center/forgotpassword', methods=['GET', 'POST'])
def center_forgotpassword():
    if 'logged_in' in session:
        return redirect(url_for('center_dashboard'))
    else:
        if request.method == 'POST':
            user = User.query.filter_by(username=request.form['username'].lower()).first()
            if user:
                if user.email != request.form['email'].lower() or user.username != request.form['username'].lower():
                    flash('Username und E-Mail-Adresse stimmen nicht überein.', 'danger')
                else:                    
                    password = urandom(16).hex()[:10]
                    user.password = sha256_crypt.encrypt(password)
                    db.session.commit()
                    send_email('Passwort zurücksetzen', 'system@lotusicafe.de', [user.email],
                               render_template('center/emails/forgotpassword.txt', user=user, password=password),
                               render_template('center/emails/forgotpassword.html', user=user, password=password))
                    flash('Eine E-Mail mit deinem neuen Passwort wurde soeben versandt.', 'success')
                    return redirect(url_for('center_login'))
            else:
                flash('Benutzer nicht gefunden.', 'danger')
        return render_template('center/forgotpassword.html')


@app.route('/center/logout')
@is_logged_in
def center_logout():
    session.clear()
    flash('Erfolgreich ausgeloggt.', 'success')
    return redirect(url_for('center_login'))


@app.route('/center/dashboard', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_dashboard():
    mp_report_dates = [d.strftime('%d.%m.%Y') for d in [datetime.now()-timedelta(days=30-i) for i in range(31)]]
    mps = Marketplace.query.order_by(Marketplace.id).all()
    mp_ids = [mp.id for mp in mps]
    mp_dict = {}
    mp_reports = {}
    mp_pra_reports = {}
    pa_names = db.session.query(PricingAction.name).filter(PricingAction.archived == False).group_by(PricingAction.name).order_by(PricingAction.name).all() + [('Keine Aktion',)]
    palette_1 = sns.color_palette("Spectral", len(pa_names)).as_hex()
    for i, mp in enumerate(mps):
        reps = MPReport.query.filter_by(marketplace_id=mp.id).filter(MPReport.init_date >= (datetime.now()-timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)).order_by(MPReport.init_date).all()
        max_d = reps[-1].init_date.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = (datetime.now()-max_d).days
        mp_reports[mp.id] = {}
        mp_reports[mp.id]['id_tuple'] = (mp_ids[i-1], mp_ids[i+1] if i+1 < len(mp_ids) else mp_ids[0])
        mp_reports[mp.id]['est_uploaded'] = (31 - len(reps) - delta) * [0] + [rep.est_uploaded for rep in reps] + delta * [0]
        mp_reports[mp.id]['est_active'] = (31 - len(reps) - delta) * [0] + [rep.est_active for rep in reps] + delta * [0]
        mp_reports[mp.id]['est_inactive'] = (31 - len(reps) - delta) * [0] + [rep.est_inactive for rep in reps] + delta * [0]
        mp_reports[mp.id]['uploaded'] = (31 - len(reps) - delta) * [0] + [rep.uploaded for rep in reps] + delta * [0]
        mp_reports[mp.id]['active'] = (31 - len(reps) - delta) * [0] + [rep.active for rep in reps] + delta * [0]
        mp_reports[mp.id]['inactive'] = (31 - len(reps) - delta) * [0] + [rep.inactive for rep in reps] + delta * [0]
        mp_pra_reports[mp.id] = {}
        mp_pra_reports[mp.id]['id_tuple'] = (mp_ids[i-1], mp_ids[i+1] if i+1 < len(mp_ids) else mp_ids[0])
        for i, pa_name in enumerate(pa_names):
            pa_name = pa_name[0]
            pa_reps = PrActionReport.query.filter_by(
                marketplace_id=mp.id, name=pa_name
            ).filter(
                MPReport.init_date >= (datetime.now()-timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
            ).order_by(MPReport.init_date).all()
            max_rep_d = pa_reps[-1].init_date.replace(hour=0, minute=0, second=0, microsecond=0)
            delta = (datetime.now()-max_rep_d).days
            mp_pra_reports[mp.id][pa_name] = {}
            mp_pra_reports[mp.id][pa_name]['color_tuple'] = (palette_1[i], palette_1[i])
            mp_pra_reports[mp.id][pa_name]['num_sales'] = (31 - len(pa_reps) - delta) * [0] + [rep.num_sales for rep in pa_reps] + delta * [0]
            mp_pra_reports[mp.id][pa_name]['num_active'] = (31 - len(pa_reps) - delta) * [0] + [rep.num_active for rep in pa_reps] + delta * [0]
        mp_dict[mp.id] = mp
    pra_reports = {}
    for i, pa_name in enumerate(pa_names):
        pa_name = pa_name[0]
        pra_reports[pa_name] = {'color_tuple': (palette_1[i], palette_1[i]),
                                'num_sales': list(sum(np.array(mp_pra_reports[mp.id][pa_name]['num_sales']) for mp in mps)),
                                'num_active': list(sum(np.array(mp_pra_reports[mp.id][pa_name]['num_active']) for mp in mps))}
    daily_reps = DailyReport.query.filter(DailyReport.init_date >= (datetime.now() - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)).order_by(DailyReport.init_date).all()
    max_d = daily_reps[-1].init_date.replace(hour=0, minute=0, second=0, microsecond=0)
    delta = (datetime.now()-max_d).days
    daily_reports = {'sellable': (31 - len(daily_reps) - delta) * [0] + [rep.sellable for rep in daily_reps] + delta * [0],
                     'pos_stock': (31 - len(daily_reps) - delta) * [0] + [rep.pos_stock for rep in daily_reps] + delta * [0],
                     'zero_sell': (31 - len(daily_reps) - delta) * [0] + [rep.sellable - rep.pos_stock - rep.pre_order for rep in daily_reps] + delta * [0],
                     'pre_order': (31 - len(daily_reps) - delta) * [0] + [rep.pre_order for rep in daily_reps] + delta * [0]
                     }

    stock_ids = db.session.query(Stock.id).filter_by(owned=True).all()

    sellable = db.session.query(
        Product_Stock_Attributes, Product.id
    ).filter(
        Product_Stock_Attributes.quantity > 0
    ).filter(
        Product_Stock_Attributes.stock_id.in_(stock_ids)
    ).filter(
        Product_Stock_Attributes.product_id == Product.id
    ).count()

    pos_stock = db.session.query(
        Product_Stock_Attributes, Product.id
    ).filter(
        Product_Stock_Attributes.quantity > Product.short_sell.cast(sqlalchemy_Integer) * 100
    ).filter(
        Product_Stock_Attributes.stock_id.in_(stock_ids)
    ).filter(
        Product_Stock_Attributes.product_id == Product.id
    ).count()

    short_sell = Product.query.filter_by(short_sell=True).count()
    pre_order = Product.query.filter(Product.release_date > datetime.now()).count()
    proc_prods = Product_CurrProcStat.query.filter(
        or_(
            and_(Product_CurrProcStat.proc_user_id == None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.product_id != None),
            and_(Product_CurrProcStat.product_id != None, Product_CurrProcStat.review == True)
        )
    ).count()

    to_conf_prods = Product_CurrProcStat.query.filter(
        and_(Product_CurrProcStat.proc_user_id != None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.product_id != None)
    ).count()

    conf_prods = Product_CurrProcStat.query.filter(
        and_(Product_CurrProcStat.proc_user_id != None, Product_CurrProcStat.conf_user_id != None, Product_CurrProcStat.product_id != None)
    ).count()

    live_report = {'sellable': sellable, 'pos_stock': pos_stock, 'zero_sell': sellable - pos_stock - pre_order, 'pre_order': pre_order, 'proc_prods': proc_prods, 'conf_prods': conf_prods, 'to_conf_prods': to_conf_prods}

    wss = Wholesaler.query.order_by(Wholesaler.id).all()
    ws_ids = [ws.id for ws in wss]
    ws_reports = {}
    ws_dict = {}
    for i, ws in enumerate(wss):
        reps = WSReport.query.filter_by(wholesaler_id=ws.id).filter(WSReport.init_date >= (datetime.now()-timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)).order_by(WSReport.init_date).all()
        max_d = reps[-1].init_date.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = (datetime.now()-max_d).days
        ws_reports[ws.id] = {}
        ws_reports[ws.id]['id_tuple'] = (ws_ids[i-1], ws_ids[i+1] if i+1 < len(ws_ids) else ws_ids[0])
        ws_reports[ws.id]['num_all'] = (31 - len(reps) - delta) * [0] + [rep.num_all for rep in reps] + delta * [0]
        ws_reports[ws.id]['num_pos_stock'] = (31 - len(reps) - delta) * [0] + [rep.num_pos_stock for rep in reps] + delta * [0]
        ws_reports[ws.id]['num_pre_order'] = (31 - len(reps) - delta) * [0] + [rep.num_pre_order for rep in reps] + delta * [0]
        ws_reports[ws.id]['num_imp'] = (31 - len(reps) - delta) * [0] + [rep.num_imp for rep in reps] + delta * [0]
        ws_reports[ws.id]['num_imp_pos_stock'] = (31 - len(reps) - delta) * [0] + [rep.num_imp_pos_stock for rep in reps] + delta * [0]
        ws_reports[ws.id]['num_imp_pre_order'] = (31 - len(reps) - delta) * [0] + [rep.num_imp_pre_order for rep in reps] + delta * [0]
        ws_dict[ws.id] = ws
    return render_template('center/dashboard.html', mp_reports=mp_reports, mp_report_dates=mp_report_dates, mp_dict=mp_dict, daily_reports=daily_reports, live_report=live_report, ws_reports=ws_reports, ws_dict=ws_dict,
                           mp_pra_reports=mp_pra_reports, pra_reports= pra_reports)


#####################################################################################

####################################   PRODUCT   ####################################

#####################################################################################

#SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB   PRODUCT   SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB#

@app.route('/center/product/product_sort/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_product_product_sort(val):
    if val == session['product_filter_infos']['product_sort']:
        if session['product_filter_infos']['product_sort_dir'] == 'DESC':
            session['product_filter_infos'] = {'datalimit_whole': None,
                                               'datalimit_page': 25,
                                               'datalimit_offset': 0,
                                               'product_sort': 'id',
                                               'product_sort_dir': 'ASC',
                                               'product_ids': [],
                                               'productcategory_ids': [],
                                               'tag_ids': [],
                                               'keyword_search': [],
                                               'mp_listing_dict': {},
                                               'own_stock_min': None,
                                               'own_stock_max': None,
                                               'action_num': None,
                                               'ext_idealo_watch_active': None,
                                               'short_sell_active': None,
                                               'min_sell_date': None,
                                               'max_sell_date': None,
                                               'state': None,
                                               'currprocstat': None}
            marketplaces = Marketplace.query.all()
            for marketplace in marketplaces:
                session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)] = None
            session['product_filter_infos']['product_sort_dir'] = 'ASC'
            session['product_filter_infos']['product_sort'] = val
        else:
            session['product_filter_infos'] = {'datalimit_whole': None,
                                               'datalimit_page': 25,
                                               'datalimit_offset': 0,
                                               'product_sort': 'id',
                                               'product_sort_dir': 'DESC',
                                               'product_ids': [],
                                               'productcategory_ids': [],
                                               'tag_ids': [],
                                               'keyword_search': [],
                                               'mp_listing_dict': {},
                                               'own_stock_min': None,
                                               'own_stock_max': None,
                                               'action_num': None,
                                               'ext_idealo_watch_active': None,
                                               'short_sell_active': None,
                                               'min_sell_date': None,
                                               'max_sell_date': None,
                                               'state': None,
                                               'currprocstat': None}
            marketplaces = Marketplace.query.all()
            for marketplace in marketplaces:
                session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)] = None
            session['product_filter_infos']['product_sort'] = val
    else:
        session['product_filter_infos'] = {'datalimit_whole': None,
                                           'datalimit_page': 25,
                                           'datalimit_offset': 0,
                                           'product_sort': 'id',
                                           'product_sort_dir': 'DESC',
                                           'product_ids': [],
                                           'productcategory_ids': [],
                                           'tag_ids': [],
                                           'keyword_search': [],
                                           'mp_listing_dict': {},
                                           'own_stock_min': None,
                                           'own_stock_max': None,
                                           'action_num': None,
                                           'ext_idealo_watch_active': None,
                                           'short_sell_active': None,
                                           'min_sell_date': None,
                                           'max_sell_date': None,
                                           'state': None,
                                           'currprocstat': None}
        marketplaces = Marketplace.query.all()
        for marketplace in marketplaces:
            session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)] = None
        session['product_filter_infos']['product_sort'] = val
    return jsonify({})


# noinspection PySimplifyBooleanCheck
@app.route('/center/product/products', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_products():
    stocks = Stock.query.all()
    marketplaces = Marketplace.query.all()
    mp_tags = dict((mp.id, ProductTag.query.filter_by(marketplace_id=mp.id).all()) for mp in marketplaces)

    product_subquery_ids = None

    idealo_link_cat = ProductLinkCategory.query.filter_by(name='Idealo').first()

    ext_watch_ids = ProductLink.query.filter(
        ProductLink.category_id == idealo_link_cat.id
    ).filter(
        ProductLink.ext_idealo_watch_active == True
    ).filter(
        ProductLink.link != ''
    ).all()

    ext_p_ids = [result.product_id for result in ext_watch_ids]

    ext_watch_product_ids = []
    tag_filter_ids = []

    if session['product_filter_infos']['tag_ids']:
        query = db.session.query(
            func.count(ProductTag.id), PrTagRelation.product_id
        ).filter(
            ProductTag.id.in_(session['product_filter_infos']['tag_ids'])
        ).filter(
            ProductTag.id == PrTagRelation.product_id
        ).group_by(
            PrTagRelation.product_id
        ).all()
        tag_filter_ids = [p_id for _, p_id in query]

    ext_watch_product_ids = db.session.query(
        Product.id
    ).filter(
        Product.id.in_(ext_p_ids)
    )

    if session['product_filter_infos']['ext_idealo_watch_active'] == False:
        ext_watch_product_ids = db.session.query(
            Product.id
        ).filter(
            Product.id.notin_(ext_watch_product_ids)
        )

    sale_product_ids = []
    if session['product_filter_infos']['min_sell_date'] is not None or session['product_filter_infos']['max_sell_date'] is not None:
        sales = Sale.query.filter(
            Sale.timestamp >= datetime.strptime(session['product_filter_infos']['min_sell_date'], '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            if session['product_filter_infos']['min_sell_date'] else True
        ).filter(
            Sale.timestamp <= datetime.strptime(session['product_filter_infos']['max_sell_date'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            if session['product_filter_infos']['max_sell_date'] else True
        ).all()

        for sale in sales:
            sale_product_ids.append(sale.pricinglog.product.id)
        print(sale_product_ids)

    for marketplace in marketplaces:
        product_subquery = db.session.query(
            Product.id, func.count(Marketplace_Product_Attributes.id)
        ).filter(
            Marketplace_Product_Attributes.marketplace_id == marketplace.id
        ).filter(
            Marketplace_Product_Attributes.product_id == Product.id
        ).filter(
            Marketplace_Product_Attributes.uploaded == session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)]
            if session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)] is not None else True
        ).group_by(
            Product.id
        ).all()

        if product_subquery_ids:
            product_subquery_ids = intersection(product_subquery_ids, [res[0] for res in product_subquery])
        else:
            product_subquery_ids = [res[0] for res in product_subquery]

    p_id_list = None

    if session['product_filter_infos']['action_num']:

        subquery = db.session.query(PricingAction.product_id).filter(PricingAction.archived == False).subquery()
        ps = db.session.query(
            Product.id
        ).outerjoin(
            subquery, subquery.c.product_id == Product.id
        ).group_by(
            Product.id
        ).having(
            sign(func.count(subquery.c.product_id), session['product_filter_infos']['action_num'], session['product_filter_infos']['action_num-operator'])
            if session['product_filter_infos']['action_num'] else True
        ).all()

        p_id_list = [res[0] for res in ps]

    owns_stock_ids = []
    if session['product_filter_infos']['own_stock_min'] is not None or session['product_filter_infos']['own_stock_max'] is not None:
        stocks = Stock.query.filter_by(owned=True).all()
        stock_ids = [stock.id for stock in stocks]

        psas = db.session.query(
            Product_Stock_Attributes.product_id, func.sum(Product_Stock_Attributes.quantity)
        ).filter(
            Product_Stock_Attributes.stock_id.in_(stock_ids)
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).group_by(
            Product_Stock_Attributes.product_id
        ).having(
            func.sum(Product_Stock_Attributes.quantity) >= session['product_filter_infos']['own_stock_min'] if session['product_filter_infos']['own_stock_min'] is not None else True
        ).having(
            func.sum(Product_Stock_Attributes.quantity) <= session['product_filter_infos']['own_stock_max'] if session['product_filter_infos']['own_stock_max'] is not None else True
        ).all()
        owns_stock_ids = [result[0] for result in psas]

    print(session['product_filter_infos']['short_sell_active']!=None)
    if 'stock' in session['product_filter_infos']['product_sort']:
        product_query = db.session.query(
            Product
        ).outerjoin(
            Product_Stock_Attributes
        ).outerjoin(
            Marketplace_Product_Attributes
        ).outerjoin(
            Marketplace_Product_Attributes_Description
        ).outerjoin(
            Product_CurrProcStat
        ).filter(
            Product.id.in_(tag_filter_ids) if tag_filter_ids else True
        ).filter(
                or_(and_(Product_CurrProcStat.proc_user_id == None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.product_id != None),
                    and_(Product_CurrProcStat.product_id != None, Product_CurrProcStat.review == True)) if session['product_filter_infos']['currprocstat'] == 'open' else True
        ).filter(
            and_(Product_CurrProcStat.proc_user_id != None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.review == False) if session['product_filter_infos']['currprocstat'] == 'processed' else True
        ).filter(
            and_(Product_CurrProcStat.conf_user_id != None, Product_CurrProcStat.review == False) if session['product_filter_infos']['currprocstat'] == 'confirmed' else True
        ).filter(
            Product.state == int(session['product_filter_infos']['state']) if session['product_filter_infos']['state']!=None else True
        ).filter(
            Product.id.in_(session['product_filter_infos']['product_ids']) if session['product_filter_infos']['product_ids'] else True
        ).filter(
            Product.id.in_(owns_stock_ids) if session['product_filter_infos']['own_stock_min'] is not None or session['product_filter_infos']['own_stock_max'] is not None else True
        ).filter(
            Product.id.in_(product_subquery_ids) if product_subquery_ids is not None else True
        ).filter(
            Product.id.in_(sale_product_ids) if sale_product_ids!=[] else True
        ).filter(
            Product.category_id.in_(session['product_filter_infos']['productcategory_ids']) if session['product_filter_infos']['productcategory_ids'] else True
        ).filter(
            Product.short_sell == session['product_filter_infos']['short_sell_active'] if session['product_filter_infos']['short_sell_active'] != None else True
        ).filter(
            or_(
                *[func.lower(Product.name).like("%" + name + "%") for name in session['product_filter_infos']['keyword_search']],
                *[func.lower(Product.brand).like("%" + name + "%") for name in session['product_filter_infos']['keyword_search']]
            ) if session['product_filter_infos']['keyword_search'] else True
        ).filter(
            Product_Stock_Attributes.stock_id == int(session['product_filter_infos']['product_sort'].split('_')[1])
        ).filter(
            Product.id.in_(p_id_list) if p_id_list != None else True
        ).filter(
            Product.id.in_(ext_watch_product_ids) if session['product_filter_infos']['ext_idealo_watch_active'] != None else True
        ).order_by(
            func.max(Product_Stock_Attributes.quantity).desc()
            if session['product_filter_infos']['product_sort_dir'] == 'DESC'
            else func.max(Product_Stock_Attributes.quantity)
        ).group_by(
            Product.id
        ).limit(
            session['product_filter_infos']['datalimit_whole']
        ).all()
    else:
        product_query = db.session.query(
            Product
        ).outerjoin(
            Marketplace_Product_Attributes
        ).outerjoin(
            Product_CurrProcStat
        ).filter(
            Product.id.in_(tag_filter_ids) if tag_filter_ids else True
        ).filter(
                or_(and_(Product_CurrProcStat.proc_user_id == None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.product_id != None),
                    and_(Product_CurrProcStat.product_id != None, Product_CurrProcStat.review == True)) if session['product_filter_infos']['currprocstat'] == 'open' else True
        ).filter(
            and_(Product_CurrProcStat.proc_user_id != None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.review == False) if session['product_filter_infos']['currprocstat'] == 'processed' else True
        ).filter(
            and_(Product_CurrProcStat.conf_user_id != None, Product_CurrProcStat.review == False) if session['product_filter_infos']['currprocstat'] == 'confirmed' else True
        ).filter(
            Product.state == int(session['product_filter_infos']['state']) if session['product_filter_infos']['state']!=None else True
        ).filter(
            Product.id.in_(session['product_filter_infos']['product_ids']) if session['product_filter_infos']['product_ids'] else True
        ).filter(
            Product.id.in_(product_subquery_ids) if product_subquery_ids is not None else True
        ).filter(
            Product.id.in_(owns_stock_ids) if session['product_filter_infos']['own_stock_min'] is not None or session['product_filter_infos']['own_stock_max'] is not None else True
        ).filter(
            Product.id.in_(sale_product_ids) if sale_product_ids!=[] else True
        ).filter(
            Product.category_id.in_(session['product_filter_infos']['productcategory_ids']) if session['product_filter_infos']['productcategory_ids'] else True
        ).filter(
            Product.short_sell == session['product_filter_infos']['short_sell_active'] if session['product_filter_infos']['short_sell_active'] != None else True
        ).filter(
            or_(
                *[func.lower(Product.name).like("%" + name + "%") for name in session['product_filter_infos']['keyword_search']],
                *[func.lower(Product.brand).like("%" + name + "%") for name in session['product_filter_infos']['keyword_search']]
            ) if session['product_filter_infos']['keyword_search'] else True
        ).filter(
            Product.id.in_(p_id_list) if p_id_list != None else True
        ).filter(
            Product.id.in_(ext_watch_product_ids) if session['product_filter_infos']['ext_idealo_watch_active'] != None else True
        ).order_by(
            getattr(Product, session['product_filter_infos']['product_sort']).desc()
            if session['product_filter_infos']['product_sort_dir'] == 'DESC'
            else getattr(Product, session['product_filter_infos']['product_sort'])
        ).group_by(
            Product.id
        ).limit(
            session['product_filter_infos']['datalimit_whole']
        ).all()

    result_length = len(product_query)
    if (session['product_filter_infos']['datalimit_offset'] + 1) * session['product_filter_infos']['datalimit_page'] < result_length:
        products = [res for res in product_query[session['product_filter_infos']['datalimit_offset']*session['product_filter_infos']['datalimit_page']:
                                                 (session['product_filter_infos']['datalimit_offset']+1)*session['product_filter_infos']['datalimit_page']]]
    else:
        products = [res for res in product_query[session['product_filter_infos']['datalimit_offset']*session['product_filter_infos']['datalimit_page']:]]
    categories = ProductCategory.query.filter_by(active=True).all()
    with open(os.path.abspath(f'{environ.get("USER_PRODUCT_PATH")}/products_{session["user_id"]}.csv'), 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([p.id for p in product_query])
    if request.method == 'POST':
        mp_listing_dict = {}
        for marketplace in marketplaces:
            mp_listing_dict[str(marketplace.id)] = str_to_bool(request.form[str(marketplace.id)+'listed'])
        session['product_filter_infos']['mp_listing_dict'] = mp_listing_dict
        if request.form['filter_datalimit_page'] != '':
            session['product_filter_infos']['datalimit_page'] = int(request.form['filter_datalimit_page'])
        else:
            session['product_filter_infos']['datalimit_page'] = 25
        if request.form['filter_datalimit_whole'] != '':
            session['product_filter_infos']['datalimit_whole'] = request.form['filter_datalimit_whole']
        else:
            session['product_filter_infos']['datalimit_whole'] = None
        keyword_search = request.form['keyword_search'].replace('; ', ';').replace('; ', ';').replace(' ;', ';').replace(' ;', ';').lower().split(';')
        session['product_filter_infos']['keyword_search'] = keyword_search
        id_type = request.form['id_type']
        session['product_filter_infos']['product_id_type'] = id_type
        product_ids = []
        if request.form['product_ids'] != '':
            product_ids = request.form['product_ids']
            product_ids = product_ids.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
            pattern = ';' + '{2,}'
            product_ids = re.sub(pattern, ';', product_ids)
            if product_ids[-1] == ';':
                product_ids = product_ids[:-1]
            if id_type == 'id':
                product_ids = [int(product_id) for product_id in product_ids.split(';')]
                session['product_filter_infos']['product_ids'] = product_ids
            elif id_type == 'Internal_ID':
                product_ids = [product_id for product_id in product_ids.split(';')]
                session['product_filter_infos']['product_ids'] = product_ids
                filtered_products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
                product_ids = [product.id for product in filtered_products]
            else:
                product_ids = [product_id for product_id in product_ids.split(';')]
                session['product_filter_infos']['product_ids'] = product_ids
                filtered_products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
                product_ids = [product.id for product in filtered_products]
        else:
            session['product_filter_infos']['product_ids'] = []

        session['product_filter_infos']['ext_idealo_watch_active'] = str_to_bool(request.form['ext_idealo_watch_active'])
        session['product_filter_infos']['short_sell_active'] = str_to_bool(request.form['short_sell_active'])

        action_num = request.form['action_num']
        session['product_filter_infos']['action_num'] = action_num

        action_num_operator = request.form['action_num-operator']
        session['product_filter_infos']['action_num-operator'] = action_num_operator

        own_stock_min = str_to_float(money_to_float(request.form['own_stock_min']))
        session['product_filter_infos']['own_stock_min'] = own_stock_min

        own_stock_max = str_to_float(money_to_float(request.form['own_stock_max']))
        session['product_filter_infos']['own_stock_max'] = own_stock_max

        session['product_filter_infos']['min_sell_date'] = request.form['min_sell_date'] if request.form['min_sell_date'] else None
        session['product_filter_infos']['max_sell_date'] = request.form['max_sell_date'] if request.form['max_sell_date'] else None

        productcategory_ids = request.form.getlist('category_filter')
        productcategory_ids = [int(category_id) for category_id in productcategory_ids]
        session['product_filter_infos']['productcategory_ids'] = productcategory_ids

        tag_ids = request.form.getlist('tag_filter')
        tag_ids = [int(tag_id) for tag_id in tag_ids]
        session['product_filter_infos']['tag_ids'] = tag_ids

        state = str_to_int(request.form['state'])
        session['product_filter_infos']['state'] = state

        session['product_filter_infos']['currprocstat'] = request.form['currprocstat'] if request.form['currprocstat'] else None

        marketplaces = Marketplace.query.all()

        ext_watch_product_ids = db.session.query(
            Product.id
        ).filter(
            Product.id.in_(ext_p_ids)
        )

        if session['product_filter_infos']['tag_ids']:
            query = db.session.query(
                func.count(ProductTag.id), PrTagRelation.product_id
            ).filter(
                ProductTag.id.in_(session['product_filter_infos']['tag_ids'])
            ).filter(
                ProductTag.id == PrTagRelation.tag_id
            ).group_by(
                PrTagRelation.product_id
            ).having(
                func.count(ProductTag.id)==len(session['product_filter_infos']['tag_ids'])
            ).all()
            tag_filter_ids = [p_id for _, p_id in query]

        if session['product_filter_infos']['ext_idealo_watch_active'] == False:
            ext_watch_product_ids = db.session.query(
                Product.id
            ).filter(
                Product.id.notin_(ext_watch_product_ids)
            )

        sale_product_ids = []
        if session['product_filter_infos']['min_sell_date'] is not None or session['product_filter_infos']['max_sell_date'] is not None:
            sales = Sale.query.filter(
                Sale.timestamp >= datetime.strptime(session['product_filter_infos']['min_sell_date'], '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
                if session['product_filter_infos']['min_sell_date'] else True
            ).filter(
                Sale.timestamp <= datetime.strptime(session['product_filter_infos']['max_sell_date'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
                if session['product_filter_infos']['max_sell_date'] else True
            ).all()

            for sale in sales:
                sale_product_ids.append(sale.pricinglog.product.id)

        product_subquery_ids = None

        for marketplace in marketplaces:
            product_subquery = db.session.query(
                Product.id, func.count(Marketplace_Product_Attributes.id)
            ).filter(
                Marketplace_Product_Attributes.marketplace_id == marketplace.id
            ).filter(
                Marketplace_Product_Attributes.product_id == Product.id
            ).filter(
                Marketplace_Product_Attributes.uploaded == session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)]
                if session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)] is not None else True
            ).group_by(
                Product.id
            ).all()

            if product_subquery_ids:
                product_subquery_ids = intersection(product_subquery_ids, [res[0] for res in product_subquery])
            else:
                product_subquery_ids = [res[0] for res in product_subquery]

        p_id_list = None

        if session['product_filter_infos']['action_num']:
            subquery = db.session.query(PricingAction.product_id).filter(PricingAction.archived == False).subquery()
            ps = db.session.query(
                Product.id
            ).outerjoin(
                subquery, subquery.c.product_id == Product.id
            ).group_by(
                Product.id
            ).having(
                sign(func.count(subquery.c.product_id), session['product_filter_infos']['action_num'], session['product_filter_infos']['action_num-operator'])
                if session['product_filter_infos']['action_num'] else True
            ).all()

            p_id_list = [res[0] for res in ps]

        owns_stock_ids = []
        if own_stock_min is not None or own_stock_max is not None :
            stocks = Stock.query.filter_by(owned=True).all()
            stock_ids = [stock.id for stock in stocks]

            psas = db.session.query(
                Product_Stock_Attributes.product_id, func.sum(Product_Stock_Attributes.quantity)
            ).filter(
                Product_Stock_Attributes.stock_id.in_(stock_ids)
            ).filter(
                Product_Stock_Attributes.avail_date <= datetime.now()
            ).filter(
                Product_Stock_Attributes.termination_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).group_by(
                Product_Stock_Attributes.product_id
            ).having(
                func.sum(Product_Stock_Attributes.quantity) >= own_stock_min if own_stock_min is not None else True
            ).having(
                func.sum(Product_Stock_Attributes.quantity) <= own_stock_max if own_stock_max is not None else True
            ).all()
            owns_stock_ids = [result[0] for result in psas]

        if 'stock' in session['product_filter_infos']['product_sort']:
            product_query = db.session.query(
                Product
            ).outerjoin(
                Product_Stock_Attributes
            ).outerjoin(
                Marketplace_Product_Attributes
            ).outerjoin(
                Product_CurrProcStat
            ).filter(
                Product.id.in_(tag_filter_ids) if tag_filter_ids else True
            ).filter(
                or_(and_(Product_CurrProcStat.proc_user_id == None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.product_id != None),
                    and_(Product_CurrProcStat.product_id != None, Product_CurrProcStat.review == True)) if session['product_filter_infos']['currprocstat'] == 'open' else True
            ).filter(
                and_(Product_CurrProcStat.proc_user_id != None, Product_CurrProcStat.conf_user_id == None) if session['product_filter_infos']['currprocstat'] == 'processed' else True
            ).filter(
                Product_CurrProcStat.conf_user_id != None if session['product_filter_infos']['currprocstat'] == 'confirmed' else True
            ).filter(
                Product.state == int(session['product_filter_infos']['state']) if session['product_filter_infos']['state']!=None else True
            ).outerjoin(
                Marketplace_Product_Attributes_Description
            ).filter(
                Product.id.in_(product_ids) if product_ids else True
            ).filter(
                Product.id.in_(product_subquery_ids) if product_subquery_ids is not None else True
            ).filter(
                Product.id.in_(owns_stock_ids) if own_stock_min is not None or own_stock_max is not None else True
            ).filter(
                Product.id.in_(sale_product_ids) if sale_product_ids!=[] else True
            ).filter(
                Product.category_id.in_(session['product_filter_infos']['productcategory_ids']) if session['product_filter_infos']['productcategory_ids'] else True
            ).filter(
                Product.short_sell == session['product_filter_infos']['short_sell_active'] if session['product_filter_infos']['short_sell_active'] != None else True
            ).filter(
                or_(
                    *[func.lower(Product.name).like("%" + name + "%") for name in session['product_filter_infos']['keyword_search']],
                    *[func.lower(Product.brand).like("%" + name + "%") for name in session['product_filter_infos']['keyword_search']]
                ) if session['product_filter_infos']['keyword_search'] else True
            ).filter(
                Product.id.in_(p_id_list) if p_id_list != None else True
            ).filter(
                Product_Stock_Attributes.stock_id == int(session['product_filter_infos']['product_sort'].split('_')[1])
            ).filter(
                Product.id.in_(ext_watch_product_ids) if session['product_filter_infos']['ext_idealo_watch_active'] != None else True
            ).order_by(
                func.max(Product_Stock_Attributes.quantity).desc()
                if session['product_filter_infos']['product_sort_dir'] == 'DESC'
                else func.max(Product_Stock_Attributes.quantity)
            ).group_by(
                Product.id
            ).limit(
                session['product_filter_infos']['datalimit_whole']
            ).all()
        else:
            product_query = db.session.query(
                Product
            ).outerjoin(
                Marketplace_Product_Attributes
            ).outerjoin(
                Marketplace_Product_Attributes_Description
            ).outerjoin(
                Product_CurrProcStat
            ).filter(
                Product.id.in_(tag_filter_ids) if tag_filter_ids else True
            ).filter(
                or_(and_(Product_CurrProcStat.proc_user_id == None, Product_CurrProcStat.conf_user_id == None, Product_CurrProcStat.product_id != None),
                    and_(Product_CurrProcStat.product_id != None, Product_CurrProcStat.review == True)) if session['product_filter_infos']['currprocstat'] == 'open' else True
            ).filter(
                and_(Product_CurrProcStat.proc_user_id != None, Product_CurrProcStat.conf_user_id == None) if session['product_filter_infos']['currprocstat'] == 'processed' else True
            ).filter(
                Product_CurrProcStat.conf_user_id != None if session['product_filter_infos']['currprocstat'] == 'confirmed' else True
            ).filter(
                Product.state == int(session['product_filter_infos']['state']) if session['product_filter_infos']['state']!=None else True
            ).filter(
                Product.id.in_(product_ids) if product_ids else True
            ).filter(
                Product.id.in_(product_subquery_ids) if product_subquery_ids is not None else True
            ).filter(
                Product.id.in_(owns_stock_ids) if own_stock_min is not None or own_stock_max is not None else True
            ).filter(
                Product.id.in_(sale_product_ids) if sale_product_ids!=[] else True
            ).filter(
                Product.category_id.in_(session['product_filter_infos']['productcategory_ids']) if session['product_filter_infos']['productcategory_ids'] else True
            ).filter(
                Product.short_sell == session['product_filter_infos']['short_sell_active'] if session['product_filter_infos']['short_sell_active'] != None else True
            ).filter(
                or_(
                    *[func.lower(Product.name).like("%" + name + "%") for name in session['product_filter_infos']['keyword_search']],
                    *[func.lower(Product.brand).like("%" + name + "%") for name in session['product_filter_infos']['keyword_search']]
                ) if session['product_filter_infos']['keyword_search'] else True
            ).filter(
                Product.id.in_(p_id_list) if p_id_list != None else True
            ).filter(
                Product.id.in_(ext_watch_product_ids) if session['product_filter_infos']['ext_idealo_watch_active'] != None else True
            ).order_by(
                getattr(Product, session['product_filter_infos']['product_sort']).desc()
                if session['product_filter_infos']['product_sort_dir'] == 'DESC'
                else getattr(Product, session['product_filter_infos']['product_sort'])
            ).group_by(
                Product.id
            ).limit(
                session['product_filter_infos']['datalimit_whole']
            ).all()
        result_length = len(product_query)
        if (session['product_filter_infos']['datalimit_offset'] + 1) * session['product_filter_infos']['datalimit_page'] < result_length:
            products = [res for res in product_query[session['product_filter_infos']['datalimit_offset'] * session['product_filter_infos']['datalimit_page']:
                                                     (session['product_filter_infos']['datalimit_offset'] + 1) *session['product_filter_infos']['datalimit_page']]]
        else:
            products = [res for res in product_query[session['product_filter_infos']['datalimit_offset'] * session['product_filter_infos']['datalimit_page']:]]

        with open(os.path.abspath(f'{environ.get("USER_PRODUCT_PATH")}/products_{session["user_id"]}.csv'), 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([p.id for p in product_query])
    return render_template('center/product/products.html', products=products, categories=categories, marketplaces=marketplaces, stocks=stocks, result_length=result_length, mp_tags=mp_tags)


@app.route('/center/product/products/print_csv', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_products_print_csv():
    ids = []
    with open(os.path.abspath(f'{environ.get("USER_PRODUCT_PATH")}/products_{session["user_id"]}.csv'), encoding='utf-8') as csv_file:
        print(csv_file)
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            print(row)
            ids = row
    print(ids)
    ps = db.session.query(Product, Marketplace_Product_Attributes, Product_Stock_Attributes).filter(
        Marketplace_Product_Attributes.product_id == Product.id
    ).filter(
        Product_Stock_Attributes.product_id == Product.id
    ).filter(
        Product_Stock_Attributes.stock_id == 1
    ).filter(
        Product.id.in_(ids)
    ).order_by(
        Product.id, Marketplace_Product_Attributes.marketplace_id
    ).all()

    file = io.StringIO()
    writer = csv.writer(file)
    first_row = ['id', 'internal_id', 'hsp_id', 'name', 'quantity', 'idealo_uploaded', 'ebay_uploaded']
    writer.writerow(first_row)
    row = []
    curr_p = ps[-1][0].id

    mps = Marketplace.query.all()
    if len(ps) > len(mps):
        for i, p in enumerate(ps):
            if p[0].id != curr_p:
                curr_p = p[0].id
                row = [p[0].id, p[0].internal_id, p[0].hsp_id, p[0].name, p[2].quantity, p[1].uploaded]
            else:
                row.append(p[1].uploaded)
                writer.writerow(row)
                row = []
    else:
        for i, p in enumerate(ps):
            if i==0:
                row = [p[0].id, p[0].internal_id, p[0].hsp_id, p[0].name, p[2].quantity, p[1].uploaded]
            else:
                row.append(p[1].uploaded)
                writer.writerow(row)
                row = []


    output = make_response(file.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/center/redirect/stock/products/filtered/<product_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_redirect_stock_products_filtered(product_id):
    session['stock_products_filter_infos'] = {'datalimit_page': 25,
                                              'datalimit_whole': None,
                                              'product_ids': [int(product_id)],
                                              'quantity': None,
                                              'buying_price': None,
                                              'lag_days': None,
                                              'shipping_cost': None,
                                              'datalimit_offset': 0,
                                              'sort_dir': 'DESC',
                                              'sort': 'id'}
    return redirect(url_for('center_stock_products'))


@app.route('/center/product/products/find_products/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_products_find_products(val):
    val = val.lower()
    products = Product.query.filter(or_(cast(Product.id, sqlalchemy_String).like("%"+ val +"%"),
                                        Product.hsp_id.like("%" + val + "%"),
                                        Product.internal_id.like("%" + val + "%"),
                                        func.lower(Product.name).like("%" + val + "%")
                                        )).all()
    out = ''
    for product in products:
        out += '<option id="' + str(product.id) + ' - ' + product.name + '" value="' + str(product.id) + '' \
               ' - ' + product.internal_id + ' - ' + product.hsp_id + ' - ' + product.name + '"></option>'
    return jsonify({'out': out})


@app.route('/center/product/products/change_upload_status/<product_id>,<marketplace_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def change_product_products_change_upload_status(product_id, marketplace_id):
    mpa = Marketplace_Product_Attributes.query.filter_by(product_id=int(product_id),
                                                         marketplace_id=int(marketplace_id)).first()
    if mpa.uploaded:
        mpa.uploaded = False
    else:
        mpa.uploaded = True
    db.session.commit()
    return jsonify({})


@app.route('/center/product/products/turnpage/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_product_products_turnpage(val):
    product_sort_dir = session['product_filter_infos']['product_sort_dir']
    product_sort = session['product_filter_infos']['product_sort']
    session['product_filter_infos'] = {'datalimit_whole': None,
                                       'datalimit_page': 25,
                                       'datalimit_offset': int(val)-1,
                                       'product_sort': 'id',
                                       'product_sort_dir': 'DESC',
                                       'product_ids': [],
                                       'productcategory_ids': [],
                                       'tag_ids': [],
                                       'keyword_search': [],
                                       'mp_listing_dict': {},
                                       'own_stock_min': None,
                                       'own_stock_max': None,
                                       'action_num': None,
                                       'ext_idealo_watch_active': None,
                                       'short_sell_active': None,
                                       'min_sell_date': None,
                                       'max_sell_date': None,
                                       'state': None,
                                       'currprocstat': None}
    marketplaces = Marketplace.query.all()
    for marketplace in marketplaces:
        session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)] = None
    session['product_filter_infos']['product_sort_dir'] = product_sort_dir
    session['product_filter_infos']['product_sort'] = product_sort
    return jsonify({})


@app.route('/center/product/addproduct', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('SUPERADMIN')
def center_product_addproduct():
    products = Product.query.order_by(Product.name).all()
    productcategories = ProductCategory.query.order_by(ProductCategory.name).all()
    productlinkcategories = ProductLinkCategory.query.order_by(ProductLinkCategory.name).all()
    if request.method == 'POST' and request.form['btn'] == 'addproduct':
        internal_id = request.form['internal_id']
        checkproduct = Product.query.filter_by(internal_id=internal_id).first()
        if checkproduct:
            flash('Ein Produkt mit der internen ID ' + internal_id + ' existiert bereits.', 'danger')
        else:
            hsp_id_type = request.form['hsp_id_type']
            hsp_id = request.form['hsp_id']
            if hsp_id_type == 'EAN':
                while len(hsp_id)<13:
                    hsp_id = '0'+hsp_id
            mpn = request.form['mpn']
            name = request.form['name']
            category_id = str_to_float(money_to_float(request.form['product_category']))
            brand = request.form['brand']
            measurements = request.form['measurements']
            weight = str_to_float(weight_to_float(request.form['weight']))
            packagenr = request.form['packagenr']
            bigpic = request.form['bigpic']
            smallpic = request.form['smallpic']
            additional_pictures = request.form['additional_pictures'].split(' ')[:-1]
            if (hsp_id != ''
            and bigpic != ''
            and smallpic != ''):
                newprod = Product(hsp_id_type, hsp_id)
                newprod.internal_id = internal_id
                newprod.mpn = mpn
                newprod.name = name
                newprod.brand = brand
                newprod.measurements = measurements
                newprod.weight = weight
                newprod.packagenr = packagenr
                newprod.category_id = category_id
                db.session.add(newprod)
                bigpicture = ProductPicture(0, bigpic, newprod.id)
                db.session.add(bigpicture)
                smallpicture = ProductPicture(1, smallpic, newprod.id)
                db.session.add(smallpicture)
                for pic in additional_pictures:
                    addpic = ProductPicture(2, pic, newprod.id)
                    db.session.add(addpic)
                marketplaces = Marketplace.query.all()
                for marketplace in marketplaces:
                    db.session.add(Marketplace_Product_Attributes(marketplace.id, newprod.id))
                db.session.commit()
                for category in productlinkcategories:
                    link = request.form['link'+str(category.id)]
                    checklink = ProductLink.query.filter_by(product_id=newprod.id, category_id=category.id).first()
                    if checklink:
                        checklink.link = link
                    else:
                        newlink = ProductLink(link, category.id, newprod.id)
                        if category.name == 'Idealo':
                            newlink.ext_idealo_watch_active = True
                        db.session.add(newlink)
                    db.session.commit()
                flash('Das Produkt ' + name + ' wurde erfolgreich hinzugefügt.', 'success')
                return redirect(url_for('center_product_products'))
            else:
                flash('Bitte fülle alle mit * gekennzeichneten Felder aus.', 'danger')
    elif request.method == 'POST':
        genprod = Product.query.filter_by(id=int(request.form['productattrchoices'].split(' - ')[0])).first()
        return render_template('center/product/add_product.html', products=products, genprod=genprod, productlinkcategories=productlinkcategories, productcategories=productcategories)
    return render_template('center/product/add_product.html', products=products, productlinkcategories=productlinkcategories, productcategories=productcategories)


@app.route('/center/product/quickedit/proc_sources', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_quickedit_proc_sources():
    products = Product.query.filter(Product.id.in_(session['product_list'])).all()
    return render_template('center/product/quickedit_proc_sources.html', products=products)


@app.route('/center/product/quickedit/proc_sources_worker/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_quickedit_proc_sources_worker():
    if request.form['task'] == 'Idealo':
        products = Product.query.filter(Product.id.in_(session['product_list'])).all()
        for product in products:
            ebay_link = ProductLink.query.filter_by(category_id=3, product_id=product.id).first()
            vitrex_link = ProductLink.query.filter_by(category_id=5, product_id=product.id).first()
            ogdb_link = ProductLink.query.filter_by(category_id=1, product_id=product.id).first()
            idealo_link = ProductLink.query.filter_by(category_id=4, product_id=product.id).first()
            if ebay_link:
                ebay_link.link = request.form[f'ebay_{product.id}']
            else:
                db.session.add(ProductLink(request.form[f'ebay_{product.id}'], 3, product.id))
            if vitrex_link:
                vitrex_link.link = request.form[f'vitrex_{product.id}']
            else:
                db.session.add(ProductLink(request.form[f'vitrex_{product.id}'], 5, product.id))
            if ogdb_link:
                ogdb_link.link = request.form[f'ogdb_{product.id}']
            else:
                db.session.add(ProductLink(request.form[f'ogdb_{product.id}'], 1, product.id))
            if idealo_link:
                idealo_link.link = request.form[f'idealo_{product.id}']
            else:
                db.session.add(ProductLink(request.form[f'idealo_{product.id}'], 4, product.id))
            db.session.commit()
            id_source = request.form[f'idealo_source_{product.id}']
            if id_source:
                product_processor.idealo_data_extractor(product.id, id_source)
    elif request.form['task'] == 'Vitrex':
        product = Product.query.filter_by(id=int(request.form['p_id'])).first()
        filename = '/home/lotus/lager/Vitrex_' + datetime.now().strftime('%Y_%m_%d') + '.csv'
        with open(filename, encoding='cp1252') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=';', dialect=csv.excel)
            for row in csv_reader:
                hsp_id = row['EAN']
                if hsp_id:
                    while len(hsp_id) < 13:
                        hsp_id = '0' + hsp_id
                else:
                    continue
                if hsp_id == product.hsp_id:
                    for key in row:
                        product_feature_name = key
                        value = row[key]
                        feature = ProductFeature.query.filter_by(name=product_feature_name, source='Vitrex').first()
                        if feature is None:
                            feature = ProductFeature(None, product_feature_name, False)
                            feature.source = 'Vitrex'
                            db.session.add(feature)
                            db.session.commit()
                        if len(value) > 16383:
                            continue
                        if product_feature_name in comma_split_features:
                            values = value.split(',')
                            for value in values:
                                feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                                if feature_value is None:
                                    feature_value = ProductFeatureValue(value, feature.id)
                                    db.session.add(feature_value)
                                    db.session.commit()

                                if product not in feature_value.get_products():
                                    db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                                    db.session.commit()
                        else:
                            feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                            if feature_value is None:
                                feature_value = ProductFeatureValue(value, feature.id)
                                db.session.add(feature_value)
                                db.session.commit()

                            if product not in feature_value.get_products():
                                db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                                db.session.commit()
    elif request.form['task'] == 'ET':
        product = Product.query.filter_by(id=int(request.form['p_id'])).first()
        ent_trading_csv = '/home/lotus/lager/Enttrading_' + datetime.now().strftime('%Y_%m_%d') + '.csv'
        with open(ent_trading_csv, encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=';', dialect=csv.excel)
            for row in csv_reader:
                hsp_id = row['ean'].strip()
                if hsp_id:
                    while len(hsp_id) < 13:
                        hsp_id = '0' + hsp_id
                else:
                    continue
                if hsp_id == Product.hsp_id:
                    for key in row:
                        product_feature_name = key
                        value = row[key]
                        feature = ProductFeature.query.filter_by(name=product_feature_name, source='Entertainment Trading').first()
                        if feature is None:
                            feature = ProductFeature(None, product_feature_name, False)
                            feature.source = 'Entertainment Trading'
                            db.session.add(feature)
                            db.session.commit()
                        if len(value) > 16383:
                            continue
                        if product_feature_name in comma_split_features:
                            values = value.split(',')
                            for value in values:
                                feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                                if feature_value is None:
                                    feature_value = ProductFeatureValue(value, feature.id)
                                    db.session.add(feature_value)
                                    db.session.commit()

                                if product not in feature_value.get_products():
                                    db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                                    db.session.commit()
                        else:
                            feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                            if feature_value is None:
                                feature_value = ProductFeatureValue(value, feature.id)
                                db.session.add(feature_value)
                                db.session.commit()

                            if product not in feature_value.get_products():
                                db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                                db.session.commit()
    elif request.form['task'] == 'Proc_Product':
        product_processor.proc_product(int(request.form['p_id']))
    return jsonify({'response': 200})


@app.route('/center/product/quickedit_step1', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_quickedit_step1():
    session['product_filter_infos'] = {'datalimit_whole': None,
                                       'datalimit_page': 25,
                                       'datalimit_offset': 0,
                                       'product_sort': 'id',
                                       'product_sort_dir': 'DESC',
                                       'product_ids': session['product_list'],
                                       'productcategory_ids': [],
                                       'tag_ids': [],
                                       'keyword_search': [],
                                       'mp_listing_dict': {},
                                       'own_stock_min': None,
                                       'own_stock_max': None,
                                       'action_num': None,
                                       'ext_idealo_watch_active': None,
                                       'short_sell_active': None,
                                       'min_sell_date': None,
                                       'max_sell_date': None,
                                       'state': None,
                                       'currprocstat': None}
    marketplaces = Marketplace.query.all()
    for marketplace in marketplaces:
        session['product_filter_infos']['mp_listing_dict'][str(marketplace.id)] = None
    productcategories = ProductCategory.query.all()
    ebay = Marketplace.query.filter_by(name='Ebay').first()

    query = db.session.query(
        Product
    ).join(
        Marketplace_Product_Attributes
    ).outerjoin(
        Marketplace_Product_Attributes_Description
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == ebay.id
    ).filter(
        Marketplace_Product_Attributes_Description.position.in_([2, 3])
    ).filter(
        Product.id.in_(session['product_list'])
    ).add_entity(
        Marketplace_Product_Attributes_Description
    ).order_by(
        Product.id, Marketplace_Product_Attributes_Description.position
    ).all()
    return render_template('center/product/quickedit_step1.html', query=query, productcategories=productcategories, st2_dict=spec_trait_2_dict, st3_dict=spec_trait_3_dict)


@app.route('/center/product/quickedit_step1_worker/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_quickedit_step1_worker():
    product = Product.query.filter_by(id=request.form['product_id']).first()
    product.spec_trait_0 = request.form['st_0']
    product.spec_trait_1 = request.form['st_1']
    product.spec_trait_2 = request.form['st_2']
    product.spec_trait_3 = request.form['st_3']
    product.category_id = int(request.form['category_id']) if request.form['category_id'] else None
    product.brand = request.form['brand']
    product.mpn = request.form['mpn']
    product.release_date = datetime.strptime(request.form['release_date'], '%d.%m.%Y')
    db.session.commit()

    mpd_2 = Marketplace_Product_Attributes_Description.query.filter_by(id=int(request.form['description_2_id'])).first()
    mpd_2.text = request.form['description_2']
    mpd_3 = Marketplace_Product_Attributes_Description.query.filter_by(id=int(request.form['description_3_id'])).first()
    mpd_3.text = request.form['description_3']
    db.session.commit()
    return jsonify({'response': 200})


@app.route('/center/product/quickedit_step2', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_quickedit_step2():
    products = Product.query.filter(Product.id.in_(session['product_list'])).all()
    features = ProductFeature.query.filter_by(source='lotus').all()
    return render_template('center/product/quickedit_step2.html', products=products, features=features, st2_dict=spec_trait_2_dict, st3_dict=spec_trait_3_dict)


@app.route('/center/product/quickedit_step2/generate_rows', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_quickedit_step2_generate_rows():
    features = ProductFeature.query.filter_by(source='lotus').order_by(ProductFeature.id).all()
    pfs = ProductFeature.query.filter_by(source='lotus').subquery()
    query = Product.query.outerjoin(Product_ProductFeatureValue).outerjoin(ProductFeatureValue).outerjoin(ProductFeature).add_entity(ProductFeatureValue).filter(
        ProductFeature.source == 'lotus'
    ).filter(
        Product.id.in_(session['product_list'])
    ).order_by(
        Product.id, ProductFeature.id, ProductFeatureValue.value
    ).all()
    body = '<tbody style="border-bottom: solid 1px rgb(222, 226, 230);">'
    i=0
    id_set = set(session['product_list'])
    while i<len(query):
        row = query[i]
        product = row[0]
        if product.id in id_set:
            id_set.remove(product.id)
        if product.productcategory:
            cat_list = product.productcategory.get_productfeatures()
        else:
            cat_list = []
        value = row[1]
        body += f'<tr id="{ product.id }">' \
                f'<td class="white"  style="position: absolute; top: auto; left: 0; width: 100px; border-bottom-width: 1px; margin-top: -1px; height: 200px">' \
                f'{ product.id }<br>' \
                f'{ product.hsp_id }<br>' \
                f'{ product.internal_id }' \
                f'</td>' \
                f'<td class="white" style="position: absolute; top: auto; left: 100px; width: 400px; border-bottom-width: 1px; margin-top: -1px; height: 200px">' \
                f'<input type="text" id="name_{ product.id }" name="name_{ product.id }" class="form-control tiny" value="{ product.name }">' \
                f'<input type="text" id="st_0_{ product.id }" name="st_0_{ product.id }" class="form-control tiny" value="{ product.spec_trait_0 if product.spec_trait_0 else "" }">' \
                f'<input type="text" id="st_1_{ product.id }" name="st_1_{ product.id }" class="form-control tiny" value="{ product.spec_trait_1 if product.spec_trait_1 else "" }">'
        if product.category_id in spec_trait_2_dict:
            body += f'<select class="form-control tiny" id="st_2_{ product.id }" name="st_2_{ product.id }">' \
                    f'<option value=""></option>'
            for el in spec_trait_2_dict[product.category_id]:
                body += f'<option value="{ el }" {"selected" if el==product.spec_trait_2 else ""}>{ el }</option>'
            body += f'</select>'
        else:
            body += f'<input type="text" id="st_2_{ product.id }" name="st_2_{ product.id }" class="form-control tiny" value="{ product.spec_trait_2 if product.spec_trait_2 else "" }">'
        if product.category_id in spec_trait_3_dict:
            body += f'<select class="form-control tiny" id="st_3_{ product.id }" name="st_3_{ product.id }">' \
                    f'<option value=""></option>'
            for el in spec_trait_3_dict[product.category_id]:
                body += f'<option value="{ el }" {"selected" if el==product.spec_trait_3 else ""}>{ el }</option>'
            body += f'</select>'
        else:
            body += f'<input type="text" id="st_3_{ product.id }" name="st_3_{ product.id }" class="form-control tiny" value="{ product.spec_trait_3 if product.spec_trait_3 else "" }">'
        body += f'</td>'
        for feature in features:
            body += f'<td style="height: 200px">'
            if feature.fixed_values:
                body += f'<select id="feature{ feature.id }_{ product.id }" name="feature{ feature.id }_{ product.id }" class="form-control tiny"'
                if product.productcategory:
                    if feature not in cat_list:
                        body += f'readonly'
                body += f'>'
                for val in sorted(feature.values, key=lambda v: v.value):
                    body += f'<option value="{ val.value }" { "selected" if val.id == value.id else "" }>{ val.value } </option>'
                body += f'</select>'
                if value.productfeature_id == feature.id and product.id==row[0].id:
                    i+=1
                    if i>=len(query):
                        break
                    row = query[i]
                    value = row[1]
            else:
                body += f'<input type="text" id="feature{ feature.id }_{ product.id }" name="feature{ feature.id }_{ product.id }" list="{ feature.id }-{ feature.name }" class="form-control tiny"' \
                        f'value="'
                if value.productfeature_id != feature.id:
                    body += f'"'
                    if product.productcategory:
                        if feature not in cat_list:
                            body += f'readonly'
                    body += f'>' \
                            f'<datalist id="{ feature.id }-{ feature.name }">'
                    for val in sorted(feature.values, key=lambda v: v.value):
                        body += f'<option value="{ val.value }"></option>'
                    body += f'</datalist>'
                else:
                    while value.productfeature_id == feature.id and product.id==row[0].id:
                        body += value.value
                        i+=1
                        if i>=len(query):
                            body += f'"'
                            if product.productcategory:
                                if feature not in product.productcategory.get_productfeatures():
                                    body += f'readonly'
                            body += f'>' \
                                    f'<datalist id="{ feature.id }-{ feature.name }">'
                            for val in sorted(feature.values, key=lambda v: v.value):
                                body += f'<option value="{ val.value }"></option>'
                            body += f'</datalist>'
                            break
                        row = query[i]
                        value = row[1]
                        if value.productfeature_id==feature.id and product.id==row[0].id:
                            body += ', '
                        else:
                            body += f'"'
                            if product.productcategory:
                                if feature not in product.productcategory.get_productfeatures():
                                    body += f'readonly'
                            body += f'>' \
                                    f'<datalist id="{ feature.id }-{ feature.name }">'
                            for val in sorted(feature.values, key=lambda v: v.value):
                                body += f'<option value="{ val.value }"></option>'
                            body += f'</datalist>'
        body += f'</td>' \
                f'</tr>' \
                f'<tr class="trclick" id="load_{ product.id }" style="display: None">' \
                f'<td>' \
                f'{ product.id }<br>' \
                f'{ product.hsp_id }' \
                f'</td>' \
                f'<td>' \
                f'{ product.name }' \
                f'</td>' \
                f'<td colspan="{ len(features) }">' \
                f'<div style="width: 100%; height: 60px; position: relative;">' \
                f'<div class="loader" style="height: 50px; width: 50px; margin: -25px"></div>' \
                f'</div>' \
                f'</td>' \
                f'</tr>' \
                f'<tr class="trclick" id="error_{ product.id }" style="display: None">' \
                f'<td>' \
                f'{ product.id }<br>' \
                f'{ product.hsp_id }' \
                f'</td>' \
                f'<td>' \
                f'{ product.name }' \
                f'</td>' \
                f'<td colspan="{ len(features) }">' \
                f' <b>FEHLER</b>' \
                f'</td>' \
                f'</tr>'
    for p_id in id_set:
        product=Product.query.filter_by(id=p_id).first()
        if product.productcategory:
            cat_list = product.productcategory.get_productfeatures()
        else:
            cat_list = []
        body += f'<tr id="{ product.id }">' \
                f'<td class="white"  style="position: absolute; top: auto; left: 0; width: 100px; border-bottom-width: 1px; margin-top: -1px; height: 200px">' \
                f'{ product.id }<br>' \
                f'{ product.hsp_id }' \
                f'</td>' \
                f'<td class="white" style="position: absolute; top: auto; left: 100px; width: 400px; border-bottom-width: 1px; margin-top: -1px; height: 200px">' \
                f'<input type="text" id="name_{ product.id }" name="name_{ product.id }" class="form-control tiny" value="{ product.name }">' \
                f'<input type="text" id="st_0_{ product.id }" name="st_0_{ product.id }" class="form-control tiny" value="{ product.spec_trait_0 if product.spec_trait_0 else "" }">' \
                f'<input type="text" id="st_1_{ product.id }" name="st_1_{ product.id }" class="form-control tiny" value="{ product.spec_trait_1 if product.spec_trait_1 else "" }">'
        if product.category_id in spec_trait_2_dict:
            body += f'<select class="form-control tiny" id="st_2_{ product.id }" name="st_2_{ product.id }">' \
                    f'<option value=""></option>'
            for el in spec_trait_2_dict[product.category_id]:
                body += f'<option value="{ el }" {"selected" if el==product.spec_trait_2 else ""}>{ el }</option>'
            body += f'</select>'
        else:
            body += f'<input type="text" id="st_2_{ product.id }" name="st_2_{ product.id }" class="form-control tiny" value="{ product.spec_trait_2 if product.spec_trait_2 else "" }">'
        if product.category_id in spec_trait_3_dict:
            body += f'<select class="form-control tiny" id="st_3_{ product.id }" name="st_3_{ product.id }">' \
                    f'<option value=""></option>'
            for el in spec_trait_3_dict[product.category_id]:
                body += f'<option value="{ el }" {"selected" if el==product.spec_trait_3 else ""}>{ el }</option>'
            body += f'</select>'
        else:
            body += f'<input type="text" id="st_3_{ product.id }" name="st_3_{ product.id }" class="form-control tiny" value="{ product.spec_trait_3 if product.spec_trait_3 else "" }">'
        body += f'</td>'
        for feature in features:
            body += f'<td style="height: 200px">'
            if feature.fixed_values:
                body += f'<select id="feature{ feature.id }_{ product.id }" name="feature{ feature.id }_{ product.id }" class="form-control tiny"'
                if product.productcategory:
                    if feature not in cat_list:
                        body += f'readonly'
                body += f'>'
                for val in sorted(feature.values, key=lambda v: v.value):
                    body += f'<option value="{ val.value }" { "selected" if val.id == value.id else "" }>{ val.value } </option>'
                body += f'</select>'
            else:
                body += f'<input type="text" id="feature{ feature.id }_{ product.id }" name="feature{ feature.id }_{ product.id }" list="{ feature.id }-{ feature.name }" class="form-control tiny"' \
                        f'value=""'
                if product.productcategory:
                    if feature not in cat_list:
                        body += f'readonly'
                body += f'>' \
                        f'<datalist id="{ feature.id }-{ feature.name }">'
                for val in sorted(feature.values, key=lambda v: v.value):
                    body += f'<option value="{ val.value }"></option>'
                body += f'</datalist>'
        body += f'</td>' \
                f'</tr>' \
                f'<tr class="trclick" id="load_{ product.id }" style="display: None">' \
                f'<td>' \
                f'{ product.id }<br>' \
                f'{ product.hsp_id }' \
                f'</td>' \
                f'<td>' \
                f'{ product.name }' \
                f'</td>' \
                f'<td colspan="{ len(features) }">' \
                f'<div style="width: 100%; height: 60px; position: relative;">' \
                f'<div class="loader" style="height: 50px; width: 50px; margin: -25px"></div>' \
                f'</div>' \
                f'</td>' \
                f'</tr>' \
                f'<tr class="trclick" id="error_{ product.id }" style="display: None">' \
                f'<td>' \
                f'{ product.id }<br>' \
                f'{ product.hsp_id }' \
                f'</td>' \
                f'<td>' \
                f'{ product.name }' \
                f'</td>' \
                f'<td colspan="{ len(features) }">' \
                f' <b>FEHLER</b>' \
                f'</td>' \
                f'</tr>'
    body += f'</tbody>'
    return jsonify({'body': body})


@app.route('/center/product/quickedit_step2_worker/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_quickedit_step2_worker():
    product = Product.query.filter_by(id=request.form['product_id']).first()
    features = ProductFeature.query.filter_by(source='lotus').all()
    product.name = request.form['name']
    product.spec_trait_0 = request.form['st_0']
    product.spec_trait_1 = request.form['st_1']
    product.spec_trait_2 = request.form['st_2']
    product.spec_trait_3 = request.form['st_3']
    if product.spec_trait_0:
        product.name = product.spec_trait_0
        product.name += f' - {product.spec_trait_1}' if product.spec_trait_1 else ''
        product.name += f' - {product.spec_trait_2}' if product.spec_trait_2 else ''
        product.name += f' - {product.spec_trait_3}' if product.spec_trait_3 else ''
    for mpa in product.marketplace_attributes:
        mpa.name = product.spec_trait_0 if product.spec_trait_0 else product.name
        mpa.name += f' - {product.spec_trait_1}' if product.spec_trait_1 else ''
        mpa.name += f' - {product.spec_trait_2}' if product.spec_trait_2 else ''
        mpa.name += ' - Neu & OVP'
        mpa.name += f' - {version_normalizer_dict[product.spec_trait_3]}' if product.spec_trait_3 in version_normalizer_dict else ''
        if mpa.marketplace.id == 1:
            if product.spec_trait_3 in ['AT', 'EU', 'UK', 'Nordic', 'PEGI', 'AUS'] and product.category_id == 1:
                if product.spec_trait_3 in ['UK', 'AUS']:
                    mpa.name += f' - Englisches Cover'
                else:
                    mpa.name += f' - {product.spec_trait_3} Cover'
            if product.release_date:
                if product.release_date > datetime.now():
                    mpa.name += ' - Release: ' + datetime.strftime(product.release_date, '%d.%m.%Y')
    cat_feature_ids = []
    if product.productcategory is not None:
        cat_features = db.session.query(ProductCategory_ProductFeature.productfeature_id).filter(ProductCategory_ProductFeature.productcategory_id == product.productcategory.id).all()
        cat_feature_ids = [cat_feature[0] for cat_feature in cat_features]
    for feature in features:
        if feature.id in cat_feature_ids or product.productcategory is None:
            if feature.active:
                print(feature.name)
                featurevalues = request.form[f'feature_{feature.id}']
                checkvalues = feature.get_value_product(product.id)
                if checkvalues:
                    for checkvalue in checkvalues:
                        connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=checkvalue.id).first()
                        if connection:
                            db.session.delete(connection)
                            db.session.commit()
                if featurevalues != '':
                    featurevalues = split_string(featurevalues, [',', ';']).replace(',', ';').split(';')
                    for featurevalue in featurevalues:
                        checkfeaturevalue = ProductFeatureValue.query.filter_by(productfeature_id=feature.id, value=featurevalue).first()
                        if checkfeaturevalue:
                            new_connection = Product_ProductFeatureValue(product.id, checkfeaturevalue.id)
                            db.session.add(new_connection)
                            db.session.commit()
                        else:
                            new_pfv = ProductFeatureValue(featurevalue, feature.id)
                            db.session.add(new_pfv)
                            db.session.commit()
                            new_connection = Product_ProductFeatureValue(product.id, new_pfv.id)
                            db.session.add(new_connection)
                            db.session.commit()
        else:
            checkvalues = feature.get_value_product(product.id)
            if checkvalues:
                for checkvalue in checkvalues:
                    connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=checkvalue.id).first()
                    if connection:
                        db.session.delete(connection)
                        db.session.commit()
    usk = False
    usk_val = ''
    insert_list = []
    for value in product.get_ext_featurevalues():
        if value.int_value_id:
            insert_list.append(value.int_value_id)
    for key in insert_list:
        featurevalue = ProductFeatureValue.query.filter_by(id=key).first()
        if featurevalue.productfeature.name == 'USK-Einstufung':
            usk = True
            usk_val = featurevalue.value.split(' ')[-1]
    ent_trading_dict = product_processor.get_ext_feature_dict(product.id, 'Entertainment Trading')
    vitrex_dict = product_processor.get_ext_feature_dict(product.id, 'Vitrex')
    if vitrex_dict:
        if 'Beschreibung' in vitrex_dict:
            description = h.handle(vitrex_dict['Beschreibung'].replace(' <BR> ', ' ').replace('<BR><BR>', '\n').replace(' <BR>', ' ').replace('<BR> ', ' '))
        else:
            description = ''
    elif ent_trading_dict:
        description = h.handle(ent_trading_dict['description'])
    else:
        description = ''
    ebay_description_generator(product, description, usk, usk_val, suppress_mid=True, user_id=session["user_id"])

    response=200
    return jsonify({'response': response})


@app.route('/center/product/quickedit_step3', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_quickedit_step3():
    mpas = Marketplace_Product_Attributes.query.filter(
        Marketplace_Product_Attributes.product_id.in_(session['product_list'])
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == 2
    ).all()
    for mpa in mpas:
        mpa.descriptions.sort(key=lambda x: x.id)
    return render_template('center/product/quickedit_step3.html', mpas=mpas)


@app.route('/center/product/quickedit_step3/translator/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_quickedit_step3_translator():
    r = dl_translate(request.form['text'])
    if r.ok:
        data = r.json()
        return jsonify({'status': 'success', 'translation': data['translations'][0]['text']})
    else:
        return jsonify({'status': 'error', 'msg´': r.text})


@app.route('/center/product/quickedit_step3_worker/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_quickedit_step3_worker():
    mpas = Marketplace_Product_Attributes.query.filter(
        Marketplace_Product_Attributes.product_id.in_(session['product_list'])
    ).filter(
        Marketplace_Product_Attributes.marketplace_id == 2
    ).all()
    try:
        for mpa in mpas:
            for description in mpa.descriptions:
                db.session.delete(description)
                db.session.commit()

            descriptionindex = int(request.form[f'descriptionindex_{mpa.id}'])
            i = 1
            j = 1
            while i < descriptionindex:
                try:
                    description = request.form[f'description_{mpa.id}_{i}']
                    db.session.add(Marketplace_Product_Attributes_Description(j, description, mpa.id))
                    with open('/home/lotus/mpad_position_log.txt', 'a') as file:
                        file.write(f'{datetime.now().strftime("%Y-%m-%d, %H:%M")}, {mpa.product_id}, {description}, {j}, {session["user_id"]}, quickedit_step4\n')
                    i += 1
                    j += 1
                except:
                    i += 1
            db.session.commit()
        response=200
    except:
        response=400
    return jsonify({'response': response})


@app.route('/center/product/quickedit_step4', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_quickedit_step4():
    query = db.session.query(Product, Marketplace_Product_Attributes).filter(
        Marketplace_Product_Attributes.product_id == Product.id
    ).filter(
        Product.id.in_(session['product_list'])
    ).order_by(
        Product.id, Marketplace_Product_Attributes.marketplace_id
    ).all()
    products = Product.query.filter(
        Product.id.in_(session['product_list'])
    ).order_by(
        Product.id
    ).all()
    mps = Marketplace.query.order_by(Marketplace.id).all()
    nat_shipping_services = ShippingService.query.filter_by(international=False).all()
    int_shipping_services = ShippingService.query.filter_by(international=True).all()
    shipping_profiles = ShippingProfile.query.all()
    return render_template('center/product/quickedit_step4.html', query=query, products=products, mps=mps, nat_shipping_services=nat_shipping_services, int_shipping_services=int_shipping_services, shipping_profiles=shipping_profiles)


@app.route('/center/product/quickedit_step4_worker/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_quickedit_step4_worker():
    mps = Marketplace.query.order_by(Marketplace.id).all()
    p = Product.query.filter_by(id=request.form['product_id']).first()
    p.shipping_profile_id = request.form['shipping_profile'] if request.form['shipping_profile'] != '0' else None
    p.nat_shipping_1_id = request.form['nat_shipping_1'] if request.form['nat_shipping_1'] != '0' else None
    p.nat_shipping_2_id = request.form['nat_shipping_2'] if request.form['nat_shipping_2'] != '0' else None
    p.int_shipping_1_id = request.form['int_shipping_1'] if request.form['int_shipping_1'] != '0' else None
    p.int_shipping_2_id = request.form['int_shipping_2'] if request.form['int_shipping_2'] != '0' else None
    for mp in mps:
        mpa = Marketplace_Product_Attributes.query.filter_by(product_id=p.id, marketplace_id=mp.id).first()
        try:
            mpa.name = request.form[f'name_{mp.id}']
            mpa.search_term = request.form[f'search_term_{mp.id}']
            db.session.commit()
            response=200
        except:
            response=400
    return jsonify({'response': response})


@app.route('/center/product/quickedit_upload', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_quickedit_upload():
    query = db.session.query(Product, PricingAction).filter(
        Product.id.in_(session['product_list'])
    ).filter(
        PricingAction.product_id == Product.id
    ).filter(
        PricingAction.active
    ).order_by(
        Product.id
    ).all()
    mps = Marketplace.query.order_by(Marketplace.id).all()
    return render_template('center/product/quickedit_upload.html', query=query, mps=mps)


@app.route('/center/product/quickedit_upload_worker/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_quickedit_upload_worker():
    result = {'afterbuy': {'result': 0, 'msg': ''}}
    mps = Marketplace.query.order_by(Marketplace.id).all()
    product = Product.query.filter_by(id=request.form['product_id']).first()
    try:
        if request.form['upload_afterbuy'] == 'true':
            r = ab_product_update(product_ids=[product.id], ean=True, mpn=True, name=True, descriptions=True, search_optimization=True, selling_price=True, weight=True, images=True, brand=True)
            res_tree = ETree.fromstring(r.text)
            call_stat = res_tree.find('.//CallStatus')
            if call_stat is not None:
                result['afterbuy'] = {'result': 1, 'msg': r.text} if call_stat.text == 'Success' else {'result': -1, 'msg': r.text}
            else:
                result['afterbuy'] = {'result': -1, 'msg': r.text}
        for mp in mps:
            result[f'mp_{mp.id}'] = {'result': 0, 'msg': ''}
            if request.form[f'upload_{ mp.id }'] == 'true':
                if mp.name=='Idealo':
                    authorization = idealo_offer.get_access_token()
                elif mp.name=='Ebay':
                    authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
                else:
                    return jsonify({'msg': f'Marketplace-Upload for {mp.name} not implemented.'})
                mpa = Marketplace_Product_Attributes.query.filter_by(product_id=product.id, marketplace_id=mp.id).first()
                try:
                    if mpa.uploaded:
                        r = product.mp_update(int(mp.id), title=True, price=True, shipping_cost=True, shipping_time=True, brand=True, ean=True, mpn=True, quantity=True, images=True,
                                          description=True, description_revise_mode='Replace', features=True, category=True, authorization=authorization)
                    else:
                        r = product.mp_upload(int(mp.id), features=True, category=True, authorization=authorization)
                    result[f'mp_{mp.id}'] = {'result': 1, 'msg': r.text} if r.ok else {'result': -1, 'msg': r.text}
                except Exception as e:
                    result[f'mp_{mp.id}'] = {'result': -1, 'msg': str(e)}
            res = 1
            for key in result:
                res = min(res, result[key]['result'])
            if res >= 0:
                product.state = 2
                pcpss = Product_CurrProcStat.query.filter(
                    Product_CurrProcStat.product_id == product.id
                ).filter(
                    Product_CurrProcStat.conf_user_id == None
                ).filter(
                    Product_CurrProcStat.proc_user_id != None
                ).all()
                for pcps in pcpss:
                    pcps.proc_user_id = int(session['user_id'])
                    pcps.proc_timestamp = datetime.now()
                db.session.commit()
        return jsonify(result)
    except Exception as e:
        result = {'afterbuy': {'result': -1, 'msg': str(e)}}
        for mp in mps:
            result[f'mp_{mp.id}'] = {'result': 0, 'msg': ''}
        return jsonify(result)


@app.route('/center/product/product/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_product(id):
    product = Product.query.filter_by(id=int(id)).first()
    productcategories = ProductCategory.query.order_by(ProductCategory.name).all()
    productlinkcategories = ProductLinkCategory.query.order_by(ProductLinkCategory.name).all()
    if request.method == 'POST':
        internal_id = request.form['internal_id']
        checkproduct = Product.query.filter_by(internal_id=internal_id).first()
        if checkproduct and checkproduct!=product:
            flash('Ein Produkt mit der internen ID ' + internal_id + ' existiert bereits.', 'danger')
        else:
            hsp_id_type = request.form['hsp_id_type']
            hsp_id = request.form['hsp_id']
            if hsp_id_type == 'EAN':
                while len(hsp_id) < 13:
                    hsp_id = '0' + hsp_id
            mpn = request.form['mpn']
            name = request.form['name']
            category_id = str_to_float(money_to_float(request.form['product_category']))
            brand = request.form['brand']
            release_date = request.form['release_date']
            measurements = request.form['measurements']
            weight = str_to_float(weight_to_float(request.form['weight']))
            p_tax_group = str_to_int(request.form['tax_group'])
            packagenr = request.form['packagenr']
            bigpic = request.form['bigpic']
            smallpic = request.form['smallpic']
            additional_pictures = request.form['additional_pictures'].split(' ')[:-1]
            if (hsp_id != ''
            and bigpic != ''
            and smallpic != ''):
                product.internal_id = internal_id
                product.hsp_id_type = hsp_id_type
                product.hsp_id = hsp_id
                product.mpn = mpn
                product.name = name
                product.brand = brand
                if release_date != '':
                    release_date = datetime.strptime(release_date, '%d.%m.%Y')
                    product.release_date = release_date
                product.category_id = category_id
                product.measurements = measurements
                product.weight = weight
                product.tax_group = p_tax_group
                product.packagenr = packagenr
                product.spec_trait_0 = request.form['spec_trait_0']
                product.spec_trait_1 = request.form['spec_trait_1']
                product.spec_trait_2 = request.form['spec_trait_2']
                product.spec_trait_3 = request.form['spec_trait_3']
                db.session.commit()
                pictures = ProductPicture.query.filter_by(product_id=product.id).all()
                for picture in pictures:
                    db.session.delete(picture)
                    db.session.commit()
                bigpicture = ProductPicture(0, bigpic, product.id)
                db.session.add(bigpicture)
                smallpicture = ProductPicture(1, smallpic, product.id)
                db.session.add(smallpicture)
                for pic in additional_pictures:
                    addpic = ProductPicture(2, pic, product.id)
                    db.session.add(addpic)
                db.session.commit()
                for category in productlinkcategories:
                    link = request.form['link'+str(category.id)]
                    checklink = ProductLink.query.filter_by(product_id=product.id, category_id=category.id).first()
                    if checklink:
                        checklink.link = link
                    else:
                        newlink = ProductLink(link, category.id, product.id)
                        if category.name == 'Idealo':
                            newlink.ext_idealo_watch_active = True
                        db.session.add(newlink)
                    db.session.commit()
                flash('Das Produkt ' + name + ' wurde erfolgreich editiert.', 'success')
            else:
                flash('Bitte fülle alle mit * gekennzeichneten Felder aus.', 'danger')
    return render_template('center/product/product.html', product=product, productlinkcategories=productlinkcategories, productcategories=productcategories)


@app.route('/center/product/block_release_date/<product_id>')
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_block_release_date(product_id):
    product = Product.query.filter_by(id=int(product_id)).first()
    if product.block_release_date:
        product.block_release_date = False
    else:
        product.block_release_date = True
    db.session.commit()
    return jsonify({})


@app.route('/center/product/update_ebay_images/<product_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_update_ebay_images(product_id):
    product = Product.query.filter_by(id=int(product_id)).first()
    mp = Marketplace.query.filter_by(name='Ebay').first()
    trading_api = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
    try:
        r = product.mp_update(mp.id, images=True, authorization=trading_api)
        if r.status_code < 300:
            flash('Success!', 'success')
        else:
            flash(r, 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('center_product_product', id=product_id))


@app.route('/center/product/features/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_features(id):
    product = Product.query.filter_by(id=int(id)).first()
    categories = ProductCategory.query.order_by(ProductCategory.name).filter_by(active=True).all()
    features = ProductFeature.query.order_by(ProductFeature.name).filter(
        ProductFeature.active==True
    ).filter(
        ProductFeature.source=='lotus'
    ).all()
    lotus_features = ProductFeature.query.filter_by(active=True, source='lotus').all()
    idealo = Marketplace.query.filter_by(name='Idealo').first()
    if request.method == 'POST' and request.form['btn'] == 'attributedata':
        form_category = request.form['category']
        if form_category == '0-0':
            product.category_id = None
            db.session.commit()
            for feature in lotus_features:
                if feature.active:
                    featurevalues = request.form[str(feature.id)]
                    checkvalues = feature.get_value_product(product.id)
                    if checkvalues:
                        for checkvalue in checkvalues:
                            connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=checkvalue.id).first()
                            if connection:
                                db.session.delete(connection)
                                db.session.commit()
                    if featurevalues != '':
                        featurevalues = split_string(featurevalues, [',', ';']).replace(',',';').split(';')
                        for featurevalue in featurevalues:
                            checkfeaturevalue = ProductFeatureValue.query.filter_by(productfeature_id=feature.id, value=featurevalue).first()
                            if checkfeaturevalue:
                                new_connection = Product_ProductFeatureValue(product.id, checkfeaturevalue.id)
                                db.session.add(new_connection)
                                db.session.commit()
                            else:
                                new_pfv = ProductFeatureValue(featurevalue, feature.id)
                                db.session.add(new_pfv)
                                db.session.commit()
                                new_connection = Product_ProductFeatureValue(product.id, new_pfv.id)
                                db.session.add(new_connection)
                                db.session.commit()
            flash('Attribute erfolgreich editiert.', 'success')
        else:
            category = ProductCategory.query.filter_by(id=int(form_category.split('-')[0])).first()
            category.products.append(product)
            cat_features = db.session.query(ProductCategory_ProductFeature.productfeature_id).filter(ProductCategory_ProductFeature.productcategory_id==category.id).all()
            cat_feature_ids = [cat_feature[0] for cat_feature in cat_features]
            for feature in lotus_features:
                if feature.id in cat_feature_ids:
                    if feature.active:
                        featurevalues = request.form[str(feature.id)]
                        checkvalues = feature.get_value_product(product.id)
                        if checkvalues:
                            for checkvalue in checkvalues:
                                connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id,
                                                                                         productfeaturevalue_id=checkvalue.id).first()
                                if connection:
                                    db.session.delete(connection)
                                    db.session.commit()
                        if featurevalues != '':
                            featurevalues = split_string(featurevalues, [',', ';']).replace(',',';').split(';')
                            for featurevalue in featurevalues:
                                checkfeaturevalue = ProductFeatureValue.query.filter_by(productfeature_id=feature.id, value=featurevalue).first()
                                if checkfeaturevalue:
                                    new_connection = Product_ProductFeatureValue(product.id, checkfeaturevalue.id)
                                    db.session.add(new_connection)
                                    db.session.commit()
                                else:
                                    new_pfv = ProductFeatureValue(featurevalue, feature.id)
                                    db.session.add(new_pfv)
                                    db.session.commit()
                                    new_connection = Product_ProductFeatureValue(product.id, new_pfv.id)
                                    db.session.add(new_connection)
                                    db.session.commit()
                else:
                    checkvalues = feature.get_value_product(product.id)
                    if checkvalues:
                        for checkvalue in checkvalues:
                            connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id,
                                                                                     productfeaturevalue_id=checkvalue.id).first()
                            if connection:
                                db.session.delete(connection)
                                db.session.commit()
            flash('Attribute erfolgreich editiert.', 'success')
        print('DONE')

    print('LOAD_PAGE')
    return render_template('center/product/features.html', product=product, categories=categories, features=features, idealo=idealo)


@app.route('/center/product/ext_features/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_ext_features(id):
    product = Product.query.filter_by(id=int(id)).first()
    feature_values = db.session.query(
        ProductFeatureValue
    ).outerjoin(
        ProductFeature
    ).outerjoin(
        Product_ProductFeatureValue
    ).outerjoin(
        Product
    ).filter(
        Product.id == product.id
    ).filter(
        ProductFeature.source != 'lotus'
    ).order_by(
        ProductFeatureValue.productfeature_id
    ).all()
    feature_dict = {'Idealo': {}, 'OGDB': {}, 'Vitrex': {}, 'Entertainment Trading': {}}
    for feature_value in feature_values:
        if feature_value.productfeature.name in feature_dict[feature_value.productfeature.source]:
            feature_dict[feature_value.productfeature.source][feature_value.productfeature.name].append(feature_value.value)
        else:
            feature_dict[feature_value.productfeature.source][feature_value.productfeature.name] = [feature_value.value]
    for source in feature_dict:
        for feature in feature_dict[source]:
            feature_dict[source][feature] = ', '.join(feature_dict[source][feature])
    if request.method=='POST':
        idealo = ProductLinkCategory.query.filter_by(name='Idealo').first()
        link = ProductLink.query.filter_by(category_id=idealo.id, product_id=product.id).first()
        if link:
            if link.link:
                if 'www' in link.link:
                    if 'OffersOfProduct' in link.link:
                        link = link.link
                        idealo_request = requests.get(link)
                        soup = BS(idealo_request.text, 'html.parser')

                        data_list = soup.findAll("li", {"class": "datasheet-listItem datasheet-listItem--properties row"})
                        for data in data_list:
                            product_feature_name = data.find_all(recursive=False)[0].text.replace('\n', '').replace('\t', '').replace('\xa0', ' ')
                            values = data.find_all(recursive=False)[1].text.replace('\n', '').replace('\t', '').replace('\xa0', ' ').replace(' / ', ', ').split(', ')

                            feature = ProductFeature.query.filter_by(name=product_feature_name, source='Idealo').first()
                            if feature is None:
                                feature = ProductFeature(None, product_feature_name, False)
                                feature.source = 'Idealo'
                                db.session.add(feature)
                                db.session.commit()
                            for value in values:
                                feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                                if feature_value is None:
                                    feature_value = ProductFeatureValue(value, feature.id)
                                    db.session.add(feature_value)
                                    db.session.commit()

                                if product not in feature_value.get_products():
                                    db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                                    db.session.commit()
        plc = ProductLinkCategory.query.filter_by(name='OGDB').first()
        link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if link:
            if link.link:
                shop_request = requests.get(link.link)
                shop_soup = BS(shop_request.text.replace("\xa0", " "), 'html.parser')
                rows = shop_soup.findAll(['tr'])
                for row in rows:
                    data_left = row.find("td", ["tboldc"])
                    data_right = row.find("td", ["tnormg", "tnorm"])
                    if data_left and data_right:
                        feature_name = data_left.text.replace("\xa0", " ").replace(':', '').replace("\n", "")
                        while feature_name[0] == ' ':
                            feature_name = feature_name[1:]
                        if feature_name == 'Allgemeine Informationen':
                            continue
                        if feature_name != 'Unverb. Preisempf.':
                            values = data_right.text[1:].replace("\r", "").replace("\n", "").replace("\xa0", "")
                            if not values:
                                continue
                            while values[0] == ' ':
                                values = values[1:]
                            while values[-1] == ' ':
                                values = values[:-1]
                            values = values.split(', ')
                        else:
                            values = [data_right.text[1:]]
                        feature = ProductFeature.query.filter_by(name=feature_name, source='OGDB').first()
                        if feature is None:
                            feature = ProductFeature(None, feature_name, False)
                            feature.source = 'OGDB'
                            db.session.add(feature)
                            db.session.commit()
                        for value in values:
                            if len(value) > 200:
                                continue
                            feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                            if feature_value is None:
                                feature_value = ProductFeatureValue(value, feature.id)
                                db.session.add(feature_value)
                                db.session.commit()

                            if product not in feature_value.get_products():
                                db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                                db.session.commit()

        plc = ProductLinkCategory.query.filter_by(name='Vitrex').first()
        link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if link:
            if link.link:
                shop_request = requests.get(link.link)
                shop_soup = BS(shop_request.text, 'html.parser')
                img = shop_soup.find("img", ['img-responsive center-block'])
                if img:
                    values = [img['src']]
                    product_feature_name = 'Bild'
                    feature = ProductFeature.query.filter_by(name=product_feature_name, source='Vitrex').first()
                    if feature is None:
                        feature = ProductFeature(None, product_feature_name, False)
                        feature.source = 'Vitrex'
                        db.session.add(feature)
                        db.session.commit()
                    for value in values:
                        if len(value) > 200:
                            continue
                        feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                        if feature_value is None:
                            feature_value = ProductFeatureValue(value, feature.id)
                            db.session.add(feature_value)
                            db.session.commit()

                        if product not in feature_value.get_products():
                            db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                            db.session.commit()
                rows = shop_soup.findAll("div", ['row vtx_facts_list'])
                for row in rows:
                    product_feature_name = row.findAll("div")[0].text[:-1]
                    values = [row.findAll("div")[1].text]
                    feature = ProductFeature.query.filter_by(name=product_feature_name, source='Vitrex').first()
                    if feature is None:
                        feature = ProductFeature(None, product_feature_name, False)
                        feature.source = 'Vitrex'
                        db.session.add(feature)
                        db.session.commit()
                    for value in values:
                        if len(value) > 200:
                            continue
                        feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                        if feature_value is None:
                            feature_value = ProductFeatureValue(value, feature.id)
                            db.session.add(feature_value)
                            db.session.commit()

                        if product not in feature_value.get_products():
                            db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                            db.session.commit()
                ebay = Marketplace.query.filter_by(name='Ebay').first()
                dscrpt = Marketplace_Product_Attributes_Description.query.filter_by(
                    marketplace_product_attributes_id=product.get_marketplace_attributes(ebay.id).id,
                    text=''
                ).first()
                if dscrpt:
                    description_2 = ''
                    description_wrapper = shop_soup.find("div", ['vtx_desc'])
                    if description_wrapper:
                        description_2 = description_wrapper.p.renderContents().decode().replace("\r", "").replace("\n", "").replace("\xa0", "")
                        while '<br>' in description_2.lower():
                            index = description_2.lower().index('<br>')
                            p1 = description_2[:index].strip()
                            if p1:
                                if p1[-1] in ['.', '?', '!']:
                                    description_2 = p1 + '\n' + description_2[index + 4:].strip()
                                else:
                                    description_2 = p1 + ' ' + description_2[index + 4:].strip()
                            else:
                                description_2 = description_2[index + 4:].strip()
                        while '<br/>' in description_2.lower():
                            index = description_2.lower().index('<br/>')
                            p1 = description_2[:index].strip()
                            if p1:
                                if p1[-1] in ['.', '?', '!']:
                                    description_2 = description_2[:index].strip() + '\n' + description_2[index + 5:].strip()
                                else:
                                    description_2 = p1 + ' ' + description_2[index + 5:].strip()
                            else:
                                description_2 = description_2[index + 5:].strip()
                    dscrpt.text = description_2
                    db.session.commit()
                else:
                    dscrpts = Marketplace_Product_Attributes_Description.query.filter_by(
                        marketplace_product_attributes_id=product.get_marketplace_attributes(ebay.id).id
                    ).all()
                    if len(dscrpts) < 3:
                        for d in dscrpts:
                            db.session.delete(d)
                        db.session.commit()
                        usk = False
                        usk_val = ''

                        usk_feature = ProductFeature.query.filter_by(name='USK-Einstufung', source='lotus').first()
                        for value in usk_feature.values:
                            if Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=value.id).first():
                                usk = True
                                usk_val = value.value.split(' ')[-1]

                        if usk:
                            version = 'Deutsche Version'
                        else:
                            version = 'EU Version'

                        version_ext = 'Deutsche Version mit USK ' + usk_val + ' Kennzeichnung' if usk else 'Europäische Verkaufsversion\nDeutsche Spielsprache und Texte verfügbar'

                        if 'Playstation 4 / PS4' in product.name:
                            console = 'Playstation 4 / PS4'
                        elif 'Playstation 5 / PS5' in product.name:
                            console = 'Playstation 5 / PS5'
                        elif 'Xbox ONE' in product.name:
                            console = 'Xbox ONE'
                        elif 'Xbox Series X' in product.name:
                            console = 'Xbox Series X'
                        elif 'PC' in product.name:
                            console = 'PC'
                        elif 'Nintendo 3DS' in product.name:
                            console = 'Nintendo 3DS'
                        elif 'Nintendo Switch' in product.name:
                            console = 'Nintendo Switch'
                        else:
                            console = 'Playstation 4 / PS4 Playstation 5 / PS5 Xbox ONE Xbox Series X PC'

                        description_1 = product.name + '\n' + console
                        description_2 = ''
                        description_wrapper = shop_soup.find("div", ['vtx_desc'])
                        if description_wrapper:
                            description_2 = description_wrapper.p.renderContents().decode().replace("\r", "").replace("\n", "").replace("\xa0", "")
                            while '<br>' in description_2.lower():
                                index = description_2.lower().index('<br>')
                                p1 = description_2[:index].strip()
                                if p1:
                                    if p1[-1] in ['.', '?', '!']:
                                        description_2 = p1 + '\n' + description_2[index + 4:].strip()
                                    else:
                                        description_2 = p1 + ' ' + description_2[index + 4:].strip()
                                else:
                                    description_2 = description_2[index + 4:].strip()
                            while '<br/>' in description_2.lower():
                                index = description_2.lower().index('<br/>')
                                p1 = description_2[:index].strip()
                                if p1:
                                    if p1[-1] in ['.', '?', '!']:
                                        description_2 = description_2[:index].strip() + '\n' + description_2[index + 5:].strip()
                                    else:
                                        description_2 = p1 + ' ' + description_2[index + 5:].strip()
                                else:
                                    description_2 = description_2[index + 5:].strip()
                        description_3 = 'WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN\nNeu und originalverpackt\n'+version_ext
                        if product.release_date:
                            if product.release_date > datetime.now():
                                description_3 += '\nRelease-Datum: ' + datetime.strftime(product.release_date, '%d.%m.%Y') + ' / Voraussichtlicher Versand am ' + datetime.strftime(product.release_date-timedelta(days=1), '%d.%m.%Y')
                        db.session.add(Marketplace_Product_Attributes_Description(1, description_1, product.get_marketplace_attributes(ebay.id).id))
                        db.session.commit()
                        db.session.add(Marketplace_Product_Attributes_Description(2, description_2, product.get_marketplace_attributes(ebay.id).id))
                        db.session.commit()
                        db.session.add(Marketplace_Product_Attributes_Description(3, description_3, product.get_marketplace_attributes(ebay.id).id))
                        db.session.commit()
        return redirect(url_for('center_product_ext_features', id=product.id))
    return render_template('center/product/ext_features.html', feature_dict=feature_dict, product=product)


@app.route('/center/product/ext_features/scrape_data/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_ext_features_scrape_data(id):
    idealo_data = request.form['idealo_data']
    response = scrape_idealo(int(id), idealo_data)
    if response==200:
        flash('Die Daten wurden erfolgreich generiert.', 'success')
    else:
        flash('Es ist ein Fehler aufgetreten.', 'danger')
    return redirect(url_for('center_product_ext_features', id=id))


@app.route('/center/product/update_features/<product_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_update_features(product_id):
    product = Product.query.filter_by(id=int(product_id)).first()

    insert_list = []
    for value in product.get_ext_featurevalues():
        if value.int_value_id:
            insert_list.append(value.int_value_id)
    print(insert_list)

    ids = Product_ProductFeatureValue.query.filter_by(product_id=product.id).all()
    print(ids)
    features = db.session.query(ProductFeature.id).filter(
        ProductFeature.source != 'lotus')

    print(features)
    pfvs = ProductFeatureValue.query.filter(
        ProductFeatureValue.productfeature_id.in_(features)
    ).filter(
        ProductFeatureValue.id.in_([item.productfeaturevalue_id for item in ids])
    ).all()
    print(pfvs)
    for pfv in pfvs:
        print(pfv.productfeature.source)
        print(len(pfv.productfeature.name))
        print(pfv.productfeature.id)
        print(pfv.value)
        print(pfv.id)
    for key in insert_list:
        featurevalue = ProductFeatureValue.query.filter_by(id=key).first()
        feature = featurevalue.productfeature
        if product.brand == None or product.brand == '':
            if feature.source == 'Idealo' and feature.name == 'Hersteller/Publisher':
                product.brand = featurevalue.value
                db.session.commit()
            elif feature.source == 'Idealo' and feature.name == 'Entwickler':
                product.brand = featurevalue.value
                db.session.commit()
        if feature.name == 'USK-Einstufung':
            usk = True
            usk_val = featurevalue.value.split(' ')[-1]
            for mpa in product.marketplace_attributes:
                if 'Deutsche Version' not in mpa.name and 'EU Version' not in mpa.name:
                    mpa.name += ' - Deutsche Version'
                    db.session.commit()
        connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=key).first()
        if not connection:
            db.session.add(Product_ProductFeatureValue(product.id, key))
            db.session.commit()

    return redirect(url_for('center_product_features', id=product.id))


@app.route('/center/product/update_ebay_features/<product_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_update_ebay_features(product_id):
    product = Product.query.filter_by(id=int(product_id)).first()
    mp = Marketplace.query.filter_by(name='Ebay').first()
    trading_api = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
    try:
        r = product.mp_update(mp.id, features=True, authorization=trading_api)
        if r.status_code < 300:
            flash('Success!', 'success')
        else:
            flash(r, 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('center_product_features', id=product_id))


@app.route('/center/product/get_idealo_data/<product_id>')
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_get_idealo_data(product_id):
    product = Product.query.filter_by(id=int(product_id)).first()
    idealo = ProductLinkCategory.query.filter_by(name='Idealo').first()
    link = ProductLink.query.filter_by(category_id=idealo.id, product_id=product.id).first()
    idealo_request = requests.get(link.link)

    soup = BS(idealo_request.text, 'html.parser')
    product_information_dict = {}
    seen_attributes = []

    data_list = soup.findAll("li", {"class": "datasheet-listItem datasheet-listItem--properties row"})
    for data in data_list:
        attribute = data.find_all(recursive=False)[0].text.replace('\n', '').replace('\t', '')
        if attribute not in seen_attributes:
            seen_attributes.append(attribute)
            value = data.find_all(recursive=False)[1].text.replace('\n', '').replace('\t', '')
            if attribute in product_information_dict:
                product_information_dict[attribute].append(value)
            else:
                product_information_dict[attribute] = [value]
    return jsonify({})


@app.route('/center/product/feature/changecategory/<id>')
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_feature_changecategory(id):
    category = ProductCategory.query.filter_by(id=int(id.split('-')[0])).first()

    features = ProductFeature.query.filter_by(active=True, source='lotus').all()

    feature_list = []

    for feature in features:
        if category:
            if feature in category.get_productfeatures():
                feature_list.append((feature.id, True))
            else:
                feature_list.append((feature.id, False))
        else:
            feature_list.append((feature.id, True))

    return jsonify({'list': feature_list})


@app.route('/center/product/feature/changefeaturevalues/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_feature_changefeaturevalues(id):
    product = Product.query.filter_by(id=int(id)).first()
    product_features = ProductFeature.query.filter_by(active=True, source='lotus').all()

    feature_dict = {}
    feature_list = []

    for feature in product_features:
        if feature.get_value_product(product.id):
            feature_list.append((feature.id, ', '.join(feature.get_value_product_values(product.id))))
        elif not feature.fixed_values:
            feature_list.append((feature.id, ''))
    feature_dict['list'] = feature_list
    if product.productcategory:
        feature_dict['category'] = str(product.category_id) + ' - ' + product.productcategory.name
    else:
        feature_dict['category'] = '0 - 0'
    return jsonify(feature_dict)


@app.route('/center/product/get_performance/<product_id>,<marketplace_id>,<selling_price>,<customer_shipping>,<own_shipping>,<commission>')
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_get_performance(product_id, marketplace_id, selling_price, customer_shipping, own_shipping, commission):
    mpa = Marketplace_Product_Attributes.query.filter_by(product_id=int(product_id), marketplace_id=int(marketplace_id)).first()
    try:
        performance_dict = marketplace_price_performance_measure(mpa.marketplace.name, str_to_float(money_to_float(selling_price)), str_to_float(money_to_float(customer_shipping)),
                                                                 str_to_float(money_to_float(own_shipping)), mpa.product.get_cheapest_buying_price_all()[1], str_to_float(money_to_float(commission)),
                                                                 tax_group[mpa.product.tax_group]['national'])
        if performance_dict['prc_margin'] and performance_dict['abs_margin']:
            return jsonify({'out': '(Marge: ' + (str("%.2f" % (performance_dict['prc_margin'] * 100))).replace('.', ',') + ' % - Absolut: ' + (str("%.2f" % performance_dict['abs_margin'])).replace('.', ',') + ' €)'})
        else:
            return jsonify({'out': '(Fehler bei der Berechnung.)'})
    except:
        return jsonify({'out': '(Fehler bei der Berechnung.)'})


@app.route('/center/product/marketplace_data/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_marketplace_data(id):
    product = Product.query.filter_by(id=int(id)).first()
    marketplaces = Marketplace.query.all()
    if request.method == 'POST':
        if request.form['checker'] == 'marketplace_chooser':
            marketplace_id = int(request.form['marketplace_chooser'])
            marketplace = Marketplace.query.filter_by(id=int(marketplace_id)).first()
            mp_attributes = Marketplace_Product_Attributes.query.\
                filter_by(product_id=product.id, marketplace_id=marketplace.id).first()
            mp_attributes_descriptions = mp_attributes.descriptions
            mp_attributes_descriptions.sort(key=lambda x: x.id)
            descriptions = list(zip([mp_attributes.descriptions.index(description)+1 for description in mp_attributes_descriptions], mp_attributes_descriptions))
            return render_template('center/product/marketplace_data.html',
                                   product=product, marketplaces=marketplaces, mp_attributes=mp_attributes,
                                   marketplace=marketplace, descriptions=descriptions)
        else:
            marketplace_id = request.form['marketplace_id']
            marketplace = Marketplace.query.filter_by(id=int(marketplace_id)).first()

            mp_attributes = Marketplace_Product_Attributes.query.\
                filter_by(product_id=product.id, marketplace_id=int(marketplace_id)).first()
            marketplace_system_id = request.form['marketplace_system_id']
            name = request.form['name']
            price = request.form['price']
            commission = request.form['commission']
            price_regulation = request.form.getlist('price_regulation')
            if (name != ''
            and price != ''
            and commission != ''):
                mp_attributes.marketplace_system_id = marketplace_system_id
                mp_attributes.name = name
                msg = ''
                mp_attributes.mp_hsp_id = request.form['mp_hsp_id']
                mp_attributes.search_term = request.form['search_term']
                mp_attributes.category_path = request.form['category_path']
                mp_attributes.selling_price = str_to_float(money_to_float(price))
                mp_attributes.commission = str_to_float(money_to_float(commission))
                mp_attributes.quantity_delta = int(request.form['quantity_delta'])
                if 'price_regulation' in price_regulation:
                    mp_attributes.price_regulation = True
                    mp_attributes.factor = str_to_float(money_to_float(request.form['factor']))
                else:
                    mp_attributes.price_regulation = False
                    mp_attributes.factor = None
                mp_attributes.min_stock = int(request.form['min_stock'])
                mp_attributes.max_stock = int(request.form['max_stock'])
                db.session.commit()
                with open('/home/lotus/mpa_selling_price_log.txt', 'a') as file:
                    file.write(f'{datetime.now().strftime("%Y-%m-%d, %H:%M")}, {product.id}, {mp_attributes.marketplace.name}, {mp_attributes.block_selling_price}, {mp_attributes.selling_price}, {session["user_id"]}, center_product_marketplace_data\n')
                for description in mp_attributes.descriptions:
                    db.session.delete(description)
                    db.session.commit()

                descriptionindex = int(request.form['descriptionindex'])
                i=1
                j=1
                while i<descriptionindex:
                    try:
                        description = request.form['description'+str(i)]
                        db.session.add(Marketplace_Product_Attributes_Description(j, description, mp_attributes.id))
                        with open('/home/lotus/mpad_position_log.txt', 'a') as file:
                            file.write(f'{datetime.now().strftime("%Y-%m-%d, %H:%M")}, {mp_attributes.product_id}, {description}, {j}, {session["user_id"]}, quickedit_step4\n')
                        i+=1
                        j+=1
                    except:
                        i+=1
                db.session.commit()
                mp_attributes_descriptions = mp_attributes.descriptions
                mp_attributes_descriptions.sort(key=lambda x: x.id)
                descriptions = list(zip([mp_attributes.descriptions.index(description)+1 for description in mp_attributes_descriptions], mp_attributes_descriptions))

                flash(marketplace.name+'-daten erfolgreich geupdatet. ' + msg, 'success')
                return render_template('center/product/marketplace_data.html',
                                       product=product, marketplaces=marketplaces, mp_attributes=mp_attributes,
                                       marketplace=marketplace, descriptions=descriptions)

            else:
                flash('Bitte fülle alle mit * gekennzeichneten Felder aus und gib mindestens für eine Versandart Versandkosten an!', 'danger')

    return render_template('center/product/marketplace_data.html', product=product, marketplaces=marketplaces)


@app.route('/center/product/marketplace_data/generate_description/<product_id>,<marketplace_id>')
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_marketplace_data_generate_description(product_id, marketplace_id):
    product = Product.query.filter_by(id=int(product_id)).first()
    plc = ProductLinkCategory.query.filter_by(name='Vitrex').first()
    link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
    if link:
        if link.link:
            shop_request = requests.get(link.link)
            shop_soup = BS(shop_request.text, 'html.parser')

            dscrpt = Marketplace_Product_Attributes_Description.query.filter_by(
                marketplace_product_attributes_id=product.get_marketplace_attributes(int(marketplace_id)).id,
                text=''
            ).first()

            if dscrpt:
                description_2 = ''
                description_wrapper = shop_soup.find("div", ['vtx_desc'])
                if description_wrapper:
                    description_2 = description_wrapper.p.renderContents().decode().replace("\r", "").replace("\n", "").replace("\xa0", "")
                    while '<br>' in description_2.lower():
                        index = description_2.lower().index('<br>')
                        p1 = description_2[:index].strip()
                        if p1:
                            if p1[-1] in ['.', '?', '!']:
                                description_2 = p1 + '\n' + description_2[index + 4:].strip()
                            else:
                                description_2 = p1 + ' ' + description_2[index + 4:].strip()
                        else:
                            description_2 = description_2[index + 4:].strip()
                    while '<br/>' in description_2.lower():
                        index = description_2.lower().index('<br/>')
                        p1 = description_2[:index].strip()
                        if p1:
                            if p1[-1] in ['.', '?', '!']:
                                description_2 = description_2[:index].strip() + '\n' + description_2[index + 5:].strip()
                            else:
                                description_2 = p1 + ' ' + description_2[index + 5:].strip()
                        else:
                            description_2 = description_2[index + 5:].strip()
                dscrpt.text = description_2
                db.session.commit()
            else:
                dscrpts = Marketplace_Product_Attributes_Description.query.filter_by(
                    marketplace_product_attributes_id=product.get_marketplace_attributes(int(marketplace_id)).id
                ).all()
                if len(dscrpts) < 3:
                    for d in dscrpts:
                        db.session.delete(d)
                    db.session.commit()
                    usk = False
                    usk_val = ''

                    usk_feature = ProductFeature.query.filter_by(name='USK-Einstufung', source='lotus').first()
                    for value in usk_feature.values:
                        if Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=value.id).first():
                            usk = True
                            usk_val = value.value.split(' ')[-1]

                    if usk:
                        version = 'Deutsche Version'
                    else:
                        version = 'EU Version'

                    version_ext = 'Deutsche Version mit USK ' + usk_val + ' Kennzeichnung' if usk else 'Europäische Verkaufsversion\nDeutsche Spielsprache und Texte verfügbar'

                    if 'Playstation 4 / PS4' in product.name:
                        console = 'Playstation 4 / PS4'
                    elif 'Playstation 5 / PS5' in product.name:
                        console = 'Playstation 5 / PS5'
                    elif 'Xbox ONE' in product.name:
                        console = 'Xbox ONE'
                    elif 'Xbox Series X' in product.name:
                        console = 'Xbox Series X'
                    elif 'PC' in product.name:
                        console = 'PC'
                    elif 'Nintendo 3DS' in product.name:
                        console = 'Nintendo 3DS'
                    elif 'Nintendo Switch' in product.name:
                        console = 'Nintendo Switch'
                    else:
                        console = 'Playstation 4 / PS4 Playstation 5 / PS5 Xbox ONE Xbox Series X PC'

                    description_1 = product.name + '\n' + console
                    description_2 = ''
                    description_wrapper = shop_soup.find("div", ['vtx_desc'])
                    if description_wrapper:
                        description_2 = description_wrapper.p.renderContents().decode().replace("\r", "").replace("\n", "").replace("\xa0", "")
                        while '<br>' in description_2.lower():
                            index = description_2.lower().index('<br>')
                            p1 = description_2[:index].strip()
                            if p1:
                                if p1[-1] in ['.', '?', '!']:
                                    description_2 = p1 + '\n' + description_2[index + 4:].strip()
                                else:
                                    description_2 = p1 + ' ' + description_2[index + 4:].strip()
                            else:
                                description_2 = description_2[index + 4:].strip()
                        while '<br/>' in description_2.lower():
                            index = description_2.lower().index('<br/>')
                            p1 = description_2[:index].strip()
                            if p1:
                                if p1[-1] in ['.', '?', '!']:
                                    description_2 = description_2[:index].strip() + '\n' + description_2[index + 5:].strip()
                                else:
                                    description_2 = p1 + ' ' + description_2[index + 5:].strip()
                            else:
                                description_2 = description_2[index + 5:].strip()
                    description_3 = 'WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN\nNeu und originalverpackt\n' + version_ext
                    if product.release_date:
                        if product.release_date > datetime.now():
                            description_3 += '\nRelease-Datum: ' + datetime.strftime(product.release_date, '%d.%m.%Y') + ' / Voraussichtlicher Versand am ' + datetime.strftime(
                                product.release_date - timedelta(days=1), '%d.%m.%Y')
                    db.session.add(Marketplace_Product_Attributes_Description(description_1, product.get_marketplace_attributes(int(marketplace_id)).id))
                    db.session.commit()
                    db.session.add(Marketplace_Product_Attributes_Description(description_2, product.get_marketplace_attributes(int(marketplace_id)).id))
                    db.session.commit()
                    db.session.add(Marketplace_Product_Attributes_Description(description_3, product.get_marketplace_attributes(int(marketplace_id)).id))
                    db.session.commit()
    return redirect(url_for('center_product_marketplace_data', id=product.id))


@app.route('/center/product/marketplace_data/upload/<product_id>,<marketplace_id>')
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_marketplace_data_upload(product_id, marketplace_id):
    product = Product.query.filter_by(id=int(product_id)).first()
    mp = Marketplace.query.filter_by(id=int(marketplace_id)).first()
    if mp.name=='Idealo':
        authorization = idealo_offer.get_access_token()
    elif mp.name=='Ebay':
        authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
    else:
        return jsonify({'msg': f'Marketplace-Upload for {mp.name} not implemented.'})
    mpa = Marketplace_Product_Attributes.query.filter_by(product_id=product.id, marketplace_id=mp.id).first()
    try:
        if mpa.uploaded:
            r = product.mp_update(int(marketplace_id), title=True, price=True, shipping_cost=True, shipping_time=True, brand=True, ean=True, mpn=True, quantity=True, images=True,
                                  description=True, description_revise_mode='Replace', features=True, category=True, custom_price=mpa.selling_price, authorization=authorization)
        else:
            r = product.mp_upload(int(marketplace_id), features=True, category=True, authorization=authorization)
        if r.status_code < 300:
            return jsonify({'msg': 'Success'})
        else:
            return jsonify({'msg': str(r.text)})
    except Exception as e:
        return jsonify({'msg': str(e)})


@app.route('/center/product/marketplace_data/update_price/<product_id>,<marketplace_id>,<price>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_marketplace_data_update_price(product_id, marketplace_id, price):
    product = Product.query.filter_by(id=int(product_id)).first()
    mp = Marketplace.query.filter_by(id=int(marketplace_id)).first()
    if mp.name=='Idealo':
        authorization = idealo_offer.get_access_token()
    elif mp.name=='Ebay':
        authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
    else:
        return jsonify({'msg': f'Marketplace-Upload for {mp.name} not implemented.'})
    mpa = Marketplace_Product_Attributes.query.filter_by(product_id=product.id, marketplace_id=int(marketplace_id)).first()
    try:
        mpa.selling_price = float(price)
        db.session.commit()
        r = product.mp_update(int(marketplace_id), price=True, shipping_cost=True, shipping_time=True, custom_price=mpa.selling_price, authorization=authorization)
        if r.status_code < 300:
            return jsonify({'msg': 'Der Preis wurde erfolgreich übermittelt.'})
        else:
            return jsonify({'msg': r.text})
    except Exception as e:
        return jsonify({'msg': str(e)})


@app.route('/center/product/marketplace_data/update_clearance/<mpa_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_marketplace_update_clearance(mpa_id):
    mpa = Marketplace_Product_Attributes.query.filter_by(id=int(mpa_id)).first()
    if mpa.upload_clearance is True:
        mpa.upload_clearance = False
    else:
        mpa.upload_clearance = True
    db.session.commit()
    return jsonify({})



@app.route('/center/product/pricingactions/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_pricingactions(id):
    product = Product.query.filter_by(id=int(id)).first()
    product.actions.sort(key=lambda x: x.active, reverse=True)
    product.marketplace_attributes.sort(key=lambda x: x.marketplace.name)
    nat_shipping_services = ShippingService.query.filter_by(international=False).all()
    int_shipping_services = ShippingService.query.filter_by(international=True).all()
    shipping_profiles = ShippingProfile.query.all()
    marketplaces = Marketplace.query.order_by(Marketplace.id).all()
    offerdict = {}
    for mpa in product.marketplace_attributes:
        offerdict[mpa.marketplace_id] = []
    if request.method == 'POST':
        if request.form['checker']=='update_prices':
            try:
                product.nat_shipping_1_id = int(request.form['nat_shipping_1']) if int(request.form['nat_shipping_1']) else None
                product.nat_shipping_2_id = int(request.form['nat_shipping_2']) if int(request.form['nat_shipping_2']) else None
                product.int_shipping_1_id = int(request.form['int_shipping_1']) if int(request.form['int_shipping_1']) else None
                product.int_shipping_2_id = int(request.form['int_shipping_2']) if int(request.form['int_shipping_2']) else None
                product.shipping_profile_id = int(request.form['shipping_profile'])
                for mpa in product.marketplace_attributes:
                    mpa.selling_price = str_to_float(money_to_float(request.form['selling_price'+str(mpa.id)]))
                    mpa.commission = str_to_float(money_to_float(request.form['commission'+str(mpa.id)]))
                db.session.commit()
                flash('Erfolgreich gespeichert.', 'success')
            except Exception as e:
                flash(str(e), 'danger')
        elif request.form['checker']=='filter_extoffers':
            try:
                minimum = datetime.strptime(request.form['start'], '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=999999)
                supremum = datetime.strptime(request.form['end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
                marketplace_id = int(request.form['marketplace'])
                offerdict = {}
                marketplace = Marketplace.query.filter_by(id=marketplace_id).first()
                offerdict[marketplace_id] = marketplace.get_extoffers_by_product(product.id, supremum, minimum)
            except Exception as e:
                flash(str(e), 'danger')
    return render_template('center/product/pricingactions.html', product=product, offerdict=offerdict, nat_shipping_services=nat_shipping_services, int_shipping_services=int_shipping_services,
                           shipping_profiles=shipping_profiles, marketplaces=marketplaces)


@app.route('/center/product/pricingactions/get_shipping_dict/<shipping_service_id>,<profile_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_pricingactions_get_shipping_dict(shipping_service_id, profile_id):
    service = ShippingService.query.filter_by(id=shipping_service_id).first()
    return jsonify(service.get_shipping_prices(profile_id))


@app.route('/center/product/block_selling_price/<mpa_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_block_selling_price(mpa_id):
    mpa = Marketplace_Product_Attributes.query.filter_by(id=int(mpa_id)).first()
    if mpa.block_selling_price:
        mpa.block_selling_price = False
    else:
        mpa.block_selling_price = True
    db.session.commit()
    return jsonify({})


@app.route('/center/product/archive_pricingaction/<pricingaction_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_archive_pricingaction(pricingaction_id):
    pricing_action = PricingAction.query.filter_by(id=int(pricingaction_id)).first()
    pricing_action.archived = True
    pricing_action.active = False
    for strategy in pricing_action.strategies:
        strategy.archived = True
        strategy.active = False
    db.session.commit()
    flash('Die Pricing-Aktion wurde erfolgreich archiviert.', 'success')
    return redirect(url_for('center_product_pricingactions', id=pricing_action.product_id))


@app.route('/center/product/ext_idealo_watch/<product_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_ext_idealo_watch(product_id):
    product = Product.query.filter_by(id=int(product_id)).first()
    plc_idealo = ProductLinkCategory.query.filter_by(name='Idealo').first()
    link = ProductLink.query.filter_by(product_id=product.id, category_id=plc_idealo.id).first()
    if link.ext_idealo_watch_active:
        link.ext_idealo_watch_active = False
    else:
        link.ext_idealo_watch_active = True
    db.session.commit()
    return jsonify({})


@app.route('/center/product/pricingactions/activate_pricingaction/<id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_pricingactions_activate_pricingaction(id):
    try:
        err = False
        err_msg = ''
        pricing_action = PricingAction.query.filter_by(id=int(id)).first()
        if pricing_action.start <= datetime.now() <= pricing_action.end:
            for pa in pricing_action.product.actions:
                pa.active = False
                for strategy in pa.strategies:
                    strategy.active = False
            db.session.commit()
            pricing_action.active = True
            if pricing_action.promotion_quantity != None:
                pricing_action.sale_count = 0
            for strategy in pricing_action.strategies:
                strategy.active = True
                if strategy.promotion_quantity != None:
                    strategy.sale_count = 0
            db.session.commit()

            for pricing_strategy in pricing_action.strategies:
                try:
                    if pricing_strategy.marketplace.name == 'Idealo':
                        authorization = idealo_offer.get_access_token()
                    elif pricing_strategy.marketplace.name == 'Ebay':
                        authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
                    else:
                        flash(f'Marketplace-Upload for {pricing_strategy.marketplace.name} not implemented.', 'danger')
                        return redirect(url_for('center_product_dynamic_pricing'))
                    pricing_action.product.generate_mp_price(marketplace_id=pricing_strategy.marketplace_id, strategy_label=pricing_strategy.label, strategy_id=pricing_strategy.id,
                                                             min_margin=pricing_strategy.prc_margin/100 if pricing_strategy.prc_margin is not None else None, rank=pricing_strategy.rank if pricing_strategy.rank is not None else 0,
                                                             ext_offers=pricing_action.product.get_mp_ext_offers(pricing_strategy.marketplace_id), authorization=authorization)
                except Exception as e:
                    err = True
                    err_msg += f'{pricing_strategy.marketplace.name}-Error: {str(e)}\n'
            if err is True:
                flash(err_msg, 'danger')
            else:
                flash('Aktion aktiviert.', 'success')
        else:
            flash('Wähle eine Pricing-Aktion im aktuellen Zeitraum aus!', 'danger')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('center_product_pricingactions', id=pricing_action.product_id))


@app.route('/center/product/add_pricingaction/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_add_pricingaction(id):
    product = Product.query.filter_by(id=int(id)).first()
    product.actions.sort(key=lambda x: x.active)
    marketplaces = Marketplace.query.all()
    if request.method == 'POST':
        checked_marketplace = request.form.getlist('marketplace_checkbox')
        if len(checked_marketplace)>0:
            name = request.form['name']
            promotion_quantity = request.form['promotion_quantity']
            start = datetime.strptime(request.form['start'], '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=999999)
            end = datetime.strptime(request.form['end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            comment = request.form['comment']
            new_pricingaction = PricingAction(name, start, end, comment, product.id, [1])
            if promotion_quantity!='':
                new_pricingaction.promotion_quantity = int(promotion_quantity)
                new_pricingaction.sale_count = 0
            else:
                new_pricingaction.promotion_quantity = None
            supplier_ids = request.form['supplier_ids'].replace(' ', '').split(';')
            if supplier_ids[0] == '':
                supplier_ids = []
            else:
                supplier_ids = [int(supplier_id) for supplier_id in supplier_ids]
            for supplier_id in supplier_ids:
                db.session.add(PricingAction_Supplier(new_pricingaction.id, supplier_id))
            stock_ids = request.form['stock_ids'].replace(' ', '').split(';')
            if stock_ids[0] == '':
                stock_ids = []
            else:
                stock_ids = [int(stock_id) for stock_id in stock_ids]
            for stock_id in stock_ids:
                db.session.add(PricingAction_Stock(new_pricingaction.id, stock_id))
            db.session.add(new_pricingaction)
            db.session.commit()
            for marketplace in checked_marketplace:
                strategy = request.form['strategy'+marketplace]
                quantity_share = request.form['quantity_share'+marketplace]
                if quantity_share != '':
                    quantity_share = str_to_float(money_to_float(quantity_share))
                    if new_pricingaction.promotion_quantity:
                        quantity_share = quantity_share*new_pricingaction.promotion_quantity//100
                else:
                    quantity_share = None
                rank = request.form['rank'+marketplace]
                if rank != '':
                    rank = int(rank)
                else:
                    rank = None
                prc_margin = str_to_float(prc_to_float(request.form['prc_margin'+marketplace]))
                update_rule_quantity = request.form['update_rule_quantity'+marketplace]
                if update_rule_quantity != '':
                    update_rule_quantity = int(update_rule_quantity)
                else:
                    update_rule_quantity = None
                update_rule_hours = request.form['update_rule_hours'+marketplace]
                if update_rule_hours != '':
                    update_rule_hours = int(update_rule_hours)
                else:
                    update_rule_hours = None
                update_factor = request.form['update_factor'+marketplace]
                if update_factor != '':
                    update_factor = str_to_float(money_to_float(update_factor))
                else:
                    update_factor = None
                new_pricingstrategy = PricingStrategy(strategy, rank, prc_margin, quantity_share, update_factor,
                                                      update_rule_hours, update_rule_quantity, marketplace,
                                                      new_pricingaction.id)
                if quantity_share:
                    new_pricingstrategy.sale_count = 0
                db.session.add(new_pricingstrategy)
                seller_ids = request.form['seller_ids'+marketplace].replace(' ', '').split(';')
                if seller_ids[0] == '':
                    seller_ids = []
                else:
                    seller_ids = [int(seller_id) for seller_id in request.form['seller_ids'+marketplace].replace(' ', '').split(';')]
                for seller_id in seller_ids:
                    db.session.add(ExtSeller_PricingStrategy_NonCompeting(seller_id, new_pricingstrategy.id))
                platform_ids = request.form['platform_ids'+marketplace].replace(' ', '').split(';')
                if platform_ids[0] == '':
                    platform_ids = []
                else:
                    platform_ids = [int(platform_id) for platform_id in request.form['platform_ids'+marketplace].replace(' ', '').split(';')]
                for platform_id in platform_ids:
                    db.session.add(ExtPlatform_PricingStrategy_NonCompeting(platform_id, new_pricingstrategy.id))
            db.session.commit()
            flash('Pricing-Aktion erfolgreich hinzugefügt.', 'success')
            activate = request.form.getlist('activate')
            if start.date() == datetime.now().date() and 'activate' in activate:
                return redirect(url_for('center_product_pricingactions_activate_pricingaction', id=new_pricingaction.id))
            else:
                return redirect(url_for('center_product_pricingactions', id=product.id))
        else:
            flash('Wähle mindestens einen Marketplace aus!', 'danger')

    next_month = datetime.now().replace(day=28) + timedelta(days=4)
    return render_template('center/product/add_pricingaction.html', product=product, marketplaces=marketplaces, now=datetime.now().strftime('%Y-%m-%d'),
                           init_end=(next_month - timedelta(days=next_month.day)).strftime('%Y-%m-%d') )


@app.route('/center/product/add_pricingaction/find_platforms/<val>,<marketplace>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_add_pricingaction_find_platforms(val, marketplace):
    val = val.lower()
    sql = text('SELECT extplatform.id FROM extplatform JOIN extoffer ON extoffer.platform_id=extplatform.id '
               'WHERE extoffer.marketplace_id=' + marketplace + ' GROUP BY extplatform.id')
    query = db.engine.execute(sql)
    platform_ids = [row.id for row in query]
    platforms = ExtPlatform.query.filter(or_(cast(ExtPlatform.id, sqlalchemy_String).like("%"+ val +"%"),
                                             func.lower(ExtPlatform.name).like("%" + val + "%")
                                             )).filter(ExtPlatform.id.in_(platform_ids)).all()
    out = ''
    for platform in platforms:
        out += '<option id="' + str(platform.id) + ' - ' + platform.name + '" value="' + str(platform.id) + ' - ' + platform.name + '">' \
               '</option>'
    return jsonify({'out': out})


@app.route('/center/product/add_pricingaction/find_sellers/<val>,<marketplace>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_add_pricingaction_find_sellers(val, marketplace):
    val = val.lower()
    sql = text('SELECT extseller.id FROM extseller JOIN extoffer ON extoffer.seller_id=extseller.id '
               'WHERE extoffer.marketplace_id=' + marketplace + ' GROUP BY extseller.id')
    query = db.engine.execute(sql)
    seller_ids = [row.id for row in query]
    sellers = ExtSeller.query.filter(or_(cast(ExtSeller.id, sqlalchemy_String).like("%"+ val +"%"),
                                         func.lower(ExtSeller.name).like("%" + val + "%")
                                         )).filter(ExtSeller.id.in_(seller_ids)).all()
    out = ''
    for seller in sellers:
        out += '<option id="' + str(seller.id) + ' - ' + seller.name + '" value="' + str(seller.id) + ' - ' + seller.name + '">' \
               '</option>'
    return jsonify({'out': out})


@app.route('/center/product/add_pricingaction/find_suppliers/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_add_pricingaction_find_suppliers(val):
    val = val.lower()
    suppliers = Supplier.query.filter(or_(cast(Supplier.id, sqlalchemy_String).like("%"+ val +"%"),
                                          func.lower(Supplier.get_name()).like("%" + val + "%")
                                          )).all()
    out = ''
    for supplier in suppliers:
        out += '<option id="' + str(supplier.id) + ' - ' + supplier.get_name() + '" value="' + str(supplier.id) + ' - ' + supplier.get_name() + '">' \
               '</option>'
    return jsonify({'out': out})


@app.route('/center/product/add_pricingaction/find_stocks/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_add_pricingaction_find_stocks(val):
    val = val.lower()

    stocks = db.session.query(
        Stock
    ).filter(
        or_(cast(Stock.id, sqlalchemy_String).like("%"+ val +"%"),
            func.lower(Stock.name).like("%" + val + "%"),
            func.lower(Stock.get_supplier_label()).like("%" + val + "%"))
    ).all()
    print(stocks)
    out = ''
    for stock in stocks:
        out += '<option id="' + str(stock.id) + ' - ' + stock.name + '" value="' + str(stock.id) + ' - ' + stock.name + ' - ' + stock.get_supplier_label() +'">' \
               '</option>'
    return jsonify({'out': out})


@app.route('/center/product/pricingaction/<pricingaction_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_pricingaction(pricingaction_id):
    pricingaction = PricingAction.query.filter_by(id=pricingaction_id).first()
    return render_template('center/product/pricingaction.html', pricingaction=pricingaction)


@app.route('/center/product/update_logs/<p_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_update_logs(p_id):
    p = Product.query.filter_by(id=p_id).first()
    puls = ProductUpdateLog.query.filter_by(product_id=p_id).order_by(ProductUpdateLog.init_date.desc()).all()
    return render_template('center/product/update_logs.html', p=p, puls=puls)


@app.route('/center/product/update_logs/details/<log_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_update_logs_details(log_id):
    log = ProductUpdateLog.query.filter_by(id=log_id).first()
    return jsonify({
        'mp_name': log.marketplace.name,
        'timestamp': log.init_date.strftime('%d.%m.%Y - %H:%M:%S'),
        'url': log.url,
        'data': log.data,
        'response': log.response,
        'status_code': log.status_code
    })

############################## ToDo: Rushed - Clean this

@app.route('/center/product/redirect_product/', methods=['POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_redirect_product():
    send_all = request.form.getlist('send_all')
    if 'True' in send_all:
        products = session['filtered_product_ids']
        session['product_list'] = products
    else:
        products = request.form.getlist('products')
        session['product_list'] = [int(x) for x in products]
    session['product_id_choice'] = True
    service = request.form['service']
    if len(products) == 0:
        flash('Bitte wähle mindestens eine Checkbox aus.', 'danger')
        return redirect(url_for('center_product_products'))
    elif service.startswith('mp_delete'):
        mp_id = service.split('-')[-1]
        return redirect(url_for('center_product_mp_delete', marketplace_id=mp_id))
    elif service.startswith('mp_export'):
        mp_id = service.split('-')[-1]
        return redirect(url_for('center_product_mp_export', marketplace_id=mp_id))
    elif request.form['service'] == 'delete':
        return redirect(url_for('center_product_delete_products'))
    elif request.form['service'] == 'ab_update_products':
        return redirect(url_for('center_product_update_afterbuy_products'))
    elif request.form['service'] == 'ab_update_product_prices':
        return redirect(url_for('center_product_update_afterbuy_prices'))
    elif request.form['service'] == 'activate_searchmode':
        products = Product.query.filter(Product.id.in_(session['product_list'])).all()
        for prod in products:
            prod.state = 0
        db.session.commit()
        return redirect(url_for('center_product_products'))
    elif request.form['service'] == 'confirm_products':
        products = Product.query.filter(Product.id.in_(session['product_list'])).all()
        for prod in products:
            prod.state = 2
        db.session.commit()
        return redirect(url_for('center_product_products'))
    elif request.form['service'] == 'quickedit':
        return redirect(url_for('center_product_quickedit_step1'))
        #return redirect(url_for('center_product_quickedit_proc_sources'))
    elif request.form['service'] == 'mark_review':
        pcpss = Product_CurrProcStat.query.filter(Product_CurrProcStat.product_id.in_(session['product_list'])).filter(Product_CurrProcStat.proc_user_id==None).all()
        for pcps in pcpss:
            pcps.review = True
            db.session.commit()
        return redirect(url_for('center_product_products'))
    elif request.form['service'] == 'mark_processed':
        pcpss = Product_CurrProcStat.query.filter(Product_CurrProcStat.product_id.in_(session['product_list'])).filter(Product_CurrProcStat.proc_user_id==None).all()
        for pcps in pcpss:
            pcps.proc_user_id = int(session['user_id'])
            pcps.proc_timestamp = datetime.now()
            pcps.review = False
            db.session.commit()
        return redirect(url_for('center_product_products'))
    elif request.form['service'] == 'mark_confirmed':
        if 'Admin' not in session['roles']:
            flash('Unauthorisierter Zugriff.', 'danger')
        else:
            pcpss = Product_CurrProcStat.query.filter(
                Product_CurrProcStat.product_id.in_(session['product_list'])
            ).filter(
                Product_CurrProcStat.conf_user_id == None
            ).filter(
                Product_CurrProcStat.proc_user_id!=None
            ).all()
            for pcps in pcpss:
                pcps.conf_user_id = int(session['user_id'])
                pcps.conf_timestamp = datetime.now()
                db.session.commit()
        return redirect(url_for('center_product_products'))
    elif request.form['service'] == 'mark_processable':
        if 'Admin' not in session['roles']:
            flash('Unauthorisierter Zugriff.', 'danger')
        else:
            pcpss = Product_CurrProcStat.query.filter(Product_CurrProcStat.product_id.in_(session['product_list'])).all()
            pcps_ids = [pcps.product_id for pcps in pcpss]
            products = Product.query.filter(Product.id.in_(session['product_list'])).all()
            for p in products:
                if p.id not in pcps_ids:
                    db.session.add(Product_CurrProcStat(p.id))
                    db.session.commit()
        return redirect(url_for('center_product_products'))


@app.route('/center/product/delete_products/')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_delete_products():
    products = Product.query.filter(Product.id.in_(session['product_list'])).all()
    for product in products:
        marketplace = Marketplace.query.filter_by(name='Idealo').first()
        mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace.id,
                                                             product_id=product.id).first()
        if mpa.uploaded:
            client_id = '54743bc2-5f71-4143-a52a-a9502dcf4587'
            client_pw = 'D2;jS$lnL0Z5,'
            header = {'Content-Type': 'application/x-www-form-urlencoded'}
            auth = requests.post('https://api.idealo.com/mer/businessaccount/api/v1/oauth/token', headers=header,
                                 auth=HTTPBasicAuth(client_id, client_pw), data={'grant_type': 'client_credentials'})
            json_data = auth.json()
            sku = product.internal_id
            shop_id = '318578'
            url = "https://import.idealo.com/shop/" + shop_id + "/offer/" + sku + "/"
            header = {"Authorization": "Bearer " + json_data['access_token'], 'Accept': 'application/json',
                      'Content-Type': 'application/json; charset=UTF-8', 'scope': json_data['scope']}
            requests.delete(url=url, headers=header)
        for picture in product.pictures:
            db.session.delete(picture)
        for action in product.actions:
            action.archived = True
            action.active = False
            for strategy in action.strategies:
                strategy.archived = True
                strategy.active = False
            db.session.commit()
        for offer in product.extoffers:
            db.session.delete(offer)
            db.session.commit()
        for value in product.featurevalues:
            db.session.delete(value)
            db.session.commit()
        for link in product.links:
            db.session.delete(link)
            db.session.commit()
        for marketplace_attribute in product.marketplace_attributes:
            for description in marketplace_attribute.descriptions:
                db.session.delete(description)
                db.session.commit()
            db.session.delete(marketplace_attribute)
            db.session.commit()
        for order in product.orders:
            db.session.delete(order)
            db.session.commit()
        for stock in product.stock:
            db.session.delete(stock)
            db.session.commit()
        db.session.delete(product)
        db.session.commit()
    session['product_list'] = []
    session['product_id_choice'] = False
    return redirect(url_for('center_product_products'))


@app.route('/center/product/update_afterbuy_products/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Marketing')
def center_product_update_afterbuy_products():
    url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"
    product = Product.query.filter_by(id=int(request.form[f'p_id'])).first()
    error = False
    try:
        bigpic = ProductPicture.query.filter_by(product_id=product.id, pic_type=0).first()
        smallpic = ProductPicture.query.filter_by(product_id=product.id, pic_type=1).first()

        marketplace = Marketplace.query.filter_by(name='Ebay').first()
        marketplace_id = Marketplace.query.filter_by(name='Idealo').first()

        mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace.id,
                                                             product_id=product.id).first()
        mpa_id = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace_id.id,
                                                                product_id=product.id).first()

        if len(mpa.descriptions) > 1:
            mpa.descriptions.sort(key=lambda mpa_description: mpa_description.id)
            description_headlist = mpa.descriptions[0].text.splitlines()
            description_list = mpa.descriptions[1].text.splitlines()

            otherdescrpt = []
            for descr in mpa.descriptions[2:]:
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
            otherpics = ProductPicture.query.filter_by(product_id=product.id).filter(ProductPicture.pic_type == 2).all()
            description += '<div align="center"><img src="' + 'https://strikeusifucan.com/' + bigpic.link + '" ' \
                           'float="left" border="0" height="640"><img src="' + 'https://strikeusifucan.com/' \
                           '' + smallpic.link + '" float="left" border="0" height="640"><br>'
            for pic in otherpics:
                description += '<img src="' + 'https://strikeusifucan.com/' + pic.link + '" ' \
                               'float="left" border="0" height="640">'
            description += '</div>'
        elif len(mpa.descriptions) > 0:
            description = mpa.descriptions[0]
        else:
            description = ''

        try:
            seo = (product.category + ' ' + mpa.name).replace(' ', '-')
        except:
            seo = mpa.name.replace(' ', '-')

        info = mpa.name + ' EAN ' + product.hsp_id + ' MPN ' + product.mpn + ' ' + product.brand

        xml = '''<?xml version="1.0" encoding="UTF-8"?>
                    <Request>
                        <AfterbuyGlobal>
                            <PartnerID><![CDATA[1000007048]]></PartnerID>
                            <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                            <UserID><![CDATA[Lotusicafe]]></UserID>
                            <UserPassword><![CDATA[210676After251174]]></UserPassword>
                            <CallName>UpdateShopProducts</CallName>
                            <DetailLevel>0</DetailLevel>
                            <ErrorLanguage>DE</ErrorLanguage>
                        </AfterbuyGlobal>
                        <Products>
                        <Product>
                            <ProductIdent>
                                <ProductInsert>0</ProductInsert>
                                <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                            </ProductIdent>
                            <Anr><![CDATA[''' + product.hsp_id + ''']]></Anr>
                            <EAN><![CDATA[''' + product.hsp_id + ''']]></EAN>
                            <ManufacturerStandardProductIDType><![CDATA[''' + product.hsp_id_type + ''']]></ManufacturerStandardProductIDType>
                            <ManufacturerStandardProductIDValue><![CDATA[''' + product.hsp_id + ''']]></ManufacturerStandardProductIDValue>
                            <Name><![CDATA[''' + mpa.name + ''']]></Name>
                            <SeoName><![CDATA[''' + seo + ''']]></SeoName>
                            <ManufacturerPartNumber><![CDATA[''' + product.mpn + ''']]></ManufacturerPartNumber>
                            <Description><![CDATA[''' + description + ''']]></Description> 
                            <ShortDescription><![CDATA[''' + seo + ''']]></ShortDescription> 
                            <SearchAlias><![CDATA[''' + info + ''']]></SearchAlias>>
                            <SellingPrice>''' + float_to_comma(mpa.selling_price) + '''</SellingPrice>
                            <ScaledDiscounts>
                                <ScaledDiscount>
                                    <ScaledQuantity>0</ScaledQuantity>
                                    <ScaledPrice>''' + float_to_comma(mpa.shipping_dhl_cost) + '''</ScaledPrice>
                                    <ScaledDPrice>''' + float_to_comma(product.shipping_dhl) + '''</ScaledDPrice>
                                </ScaledDiscount>
                                <ScaledDiscount>
                                    <ScaledQuantity>0</ScaledQuantity>
                                    <ScaledPrice>0,00</ScaledPrice>
                                    <ScaledDPrice>0,00</ScaledDPrice>
                                </ScaledDiscount>
                                <ScaledDiscount>
                                    <ScaledQuantity>0</ScaledQuantity>
                                    <ScaledPrice>''' + float_to_comma(mpa_id.shipping_dhl_cost) + '''</ScaledPrice>
                                    <ScaledDPrice>''' + float_to_comma(mpa_id.selling_price) + '''</ScaledDPrice>
                                </ScaledDiscount>
                            </ScaledDiscounts>
                            <Stocklocation_1><![CDATA[''' + product.internal_id + ''']]></Stocklocation_1>
                            <TaxRate>''' + float_to_comma(tax_group[product.tax_group]['national']) + '''</TaxRate>
                            <Stock>1</Stock>
                            <Discontinued>1</Discontinued>
                            <MergeStock>0</MergeStock>
                            <MinimumStock>5</MinimumStock>
                            <TitleReplace>1</TitleReplace>
                            <Weight>''' + float_to_comma(product.weight) + '''</Weight>
                            <FreeValue1><![CDATA[''' + float_to_comma(mpa.commission) + ''']]></FreeValue1>
                            <FreeValue2><![CDATA[''' + float_to_comma(mpa_id.commission) + ''']]></FreeValue2>'''

        i = 3
        for pic in product.pictures:
            if i < 7:
                if pic.pic_type == 2:
                    xml += '''<FreeValue''' + str(i) + '''><![CDATA[''' + 'https://strikeusifucan.com/' + pic.link + ''']]></FreeValue''' + str(i) + '''>'''
                    i += 1
                else:
                    continue
            else:
                break

        mercateo = ProductLinkCategory.query.filter_by(name='Mercateo').first()
        ebay = ProductLinkCategory.query.filter_by(name='Ebay').first()
        idealo = ProductLinkCategory.query.filter_by(name='Idealo').first()

        xml += '''<FreeValue7><![CDATA[<a href="''' + product.productlink(mercateo.id) + '''"><font size="2">MERCATEO</font></a>']]></FreeValue7>
                    <FreeValue8><![CDATA[<a href="''' + product.productlink(ebay.id) + '''"><font size="2">EBAY</font></a>]]></FreeValue8>
                    <FreeValue9><![CDATA[<a href="''' + product.productlink(idealo.id) + '''"><font size="2">IDEALO</font></a>]]></FreeValue9>
                    <ImageSmallURL><![CDATA[''' + 'https://strikeusifucan.com/' + smallpic.link + ''']]></ImageSmallURL>
                    <ImageLargeURL><![CDATA[''' + 'https://strikeusifucan.com/' + bigpic.link + ''']]></ImageLargeURL>
                    <ProductBrand><![CDATA[''' + product.brand + ''']]></ProductBrand>
                </Product>
            </Products>
            </Request>'''
        print(xml)
        xml = xml.encode('utf-8')

        headers = {'Content-Type': 'application/xml; charset=utf-8'}
        r = requests.get(url, data=xml, headers=headers)
        print(r.text)
        status = 'success'
    except:
        status = 'danger'
    return jsonify({'status': status, 'p_id': product.id})


@app.route('/center/product/update_afterbuy_prices/')
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_update_afterbuy_prices():
    if session['product_id_choice']:
        products = Product.query.filter(Product.id.in_(session['product_list'])).all()
    else:
        products = Product.query.all()

    session['product_id_choice'] = False
    session['product_list'] = []

    url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"

    error_message = 'Beim Upload der folgenden Produkte sind Fehler entstanden:\n'
    error = False

    success_message = 'Die Produktpreise der Produkte ID '

    for product in products:
        try:
            marketplace = Marketplace.query.filter_by(name='Ebay').first()
            marketplace_id = Marketplace.query.filter_by(name='Idealo').first()

            mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace.id,
                                                                 product_id=product.id).first()
            mpa_id = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace_id.id,
                                                                    product_id=product.id).first()
            xml = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Request>
                            <AfterbuyGlobal>
                                <PartnerID><![CDATA[1000007048]]></PartnerID>
                                <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                                <UserID><![CDATA[Lotusicafe]]></UserID>
                                <UserPassword><![CDATA[210676After251174]]></UserPassword>
                                <CallName>UpdateShopProducts</CallName>
                                <DetailLevel>0</DetailLevel>
                                <ErrorLanguage>DE</ErrorLanguage>
                            </AfterbuyGlobal>
                            <Products>
                                <Product>
                                    <ProductIdent>
                                        <ProductInsert>0</ProductInsert>
                                        <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                    </ProductIdent>
                                    <SellingPrice>''' + float_to_comma(mpa.selling_price) + '''</SellingPrice>
                                    <ScaledDiscounts>
                                        <ScaledDiscount>
                                            <ScaledQuantity>0</ScaledQuantity>
                                            <ScaledPrice>''' + float_to_comma(mpa.shipping_dhl) + '''</ScaledPrice>
                                            <ScaledDPrice>''' + float_to_comma(product.shipping_dhl) + '''</ScaledDPrice>
                                        </ScaledDiscount>
                                        <ScaledDiscount>
                                            <ScaledQuantity>0</ScaledQuantity>
                                            <ScaledPrice>0,00</ScaledPrice>
                                            <ScaledDPrice>0,00</ScaledDPrice>
                                        </ScaledDiscount>
                                        <ScaledDiscount>
                                            <ScaledQuantity>0</ScaledQuantity>
                                            <ScaledPrice>''' + float_to_comma(mpa_id.shipping_dhl) + '''</ScaledPrice>
                                            <ScaledDPrice>''' + float_to_comma(mpa_id.selling_price) + '''</ScaledDPrice>
                                        </ScaledDiscount>
                                    </ScaledDiscounts>
                                    <FreeValue1><![CDATA[''' + float_to_comma(mpa.comission) + ''']]></FreeValue1>
                                    <FreeValue2><![CDATA[''' + float_to_comma(mpa_id.comission) + ''']]></FreeValue2>
                                    </Product>
                            </Products>
                        </Request>'''

            xml = xml.encode('utf-8')

            headers = {'Content-Type': 'application/xml; charset=utf-8'}
            r = requests.get(url, data=xml, headers=headers)
            tree = ET.fromstring(r.text)
            status = [item.text for item in tree.iter() if item.tag == 'CallStatus'][0]
            if status == 'Error':
                error = True
                error_message += str(product.id) + '(' + [item.text for item in tree.iter() if item.tag == 'ErrorLongDescription'][0] + '), '
            else:
                success_message += str(product.id) + ', '
        except:
            error = True
            error_message += str(product.id) + ', '
        success_message = success_message[:-2] + ' wurden erfolgreich geupdatet.'

        if error:
            flash(error_message[:-2] + '\n' + success_message, 'danger')
        else:
            flash(success_message, 'success')

    return redirect(url_for('center_product_products'))


@app.route('/center/product/mp_export/<marketplace_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_mp_export(marketplace_id):
    if session['product_id_choice']:
        products = Product.query.filter(Product.id.in_(session['product_list'])).all()
    else:
        products = Product.query.all()
    session['product_id_choice'] = False
    session['product_list'] = []
    error_msg = ''
    error = False
    for product in products:
        mp = Marketplace.query.filter_by(id=int(marketplace_id)).first()
        if mp.name == 'Idealo':
            authorization = idealo_offer.get_access_token()
        elif mp.name == 'Ebay':
            authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
        else:
            return jsonify({'msg': f'Marketplace-Upload for {mp.name} not implemented.'})
        mpa = Marketplace_Product_Attributes.query.filter_by(product_id=product.id, marketplace_id=int(marketplace_id)).first()
        try:
            if mpa.uploaded:
                r = product.mp_update(int(marketplace_id), price=True, shipping_cost=True, shipping_time=True, custom_price=mpa.selling_price, authorization=authorization)
            else:
                r = product.mp_upload(int(marketplace_id), features=True, category=True, authorization=authorization)
            if r.status_code >= 300:
                if mpa.marketplace.name == 'Idealo':
                    data = r.json()
                    if 'No offer found' in data['generalErrors'][0]:
                        r = mpa.product.mp_upload(authorization=authorization, marketplace_id=mpa.marketplace_id)
                        if not r.ok:
                            error = True
                            error_msg += f'Fehler für {product.id}: {r.text}'
                    else:
                        error = True
                        error_msg += f'Fehler für {product.id}: {r.text}'
                else:
                    error = True
                    error_msg += f'Fehler für {product.id}: {r.text}'
        except Exception as e:
            error = True
            error_msg += f'Fehler für {product.id}: {str(e)}'
    if error:
        flash(error_msg, 'danger')
    else:
        flash('Die Produkte wurden erfolgreich geupdatet.', 'success')
    return redirect(url_for('center_product_products'))


@app.route('/center/product/mp_delete/<marketplace_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Marketing')
def center_product_mp_delete(marketplace_id):
    if session['product_id_choice']:
        products = Product.query.filter(Product.id.in_(session['product_list'])).all()
    else:
        products = Product.query.all()
    session['product_id_choice'] = False
    session['product_list'] = []
    error_msg = ''
    error = False
    for product in products:
        mp = Marketplace.query.filter_by(id=int(marketplace_id)).first()
        if mp.name == 'Idealo':
            authorization = idealo_offer.get_access_token()
        elif mp.name == 'Ebay':
            authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
        else:
            return jsonify({'msg': f'Marketplace-Upload for {mp.name} not implemented.'})
        mpa = Marketplace_Product_Attributes.query.filter_by(product_id=product.id, marketplace_id=int(marketplace_id)).first()
        try:
            r = product.mp_delete(int(marketplace_id), authorization=authorization)
            if r.status_code < 300:
                mpa.uploaded = False
                db.session.commit()
            else:
                error = True
                error_msg += f'Fehler für {product.id}: {r.text}'
        except Exception as e:
            error = True
            error_msg += f'Fehler für {product.id}: {str(e)}'
    if error:
        flash(error_msg, 'danger')
    else:
        flash('Die Produkte wurden erfolgreich geupdatet.', 'success')
    return redirect(url_for('center_product_products'))

#SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB   DYNAMIC PRICING   SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB#


# noinspection PyComparisonWithNone
@app.route('/center/product/redirect_pricingaction/', methods=['POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_redirect_pricingaction():
    send_all = request.form.getlist('send_all')
    if 'True' in send_all:
        pricing_action_ids = [int(action_id) for action_id in request.form['pricingaction_hidden'].split(',')]
    else:
        pricing_action_ids = [int(x) for x in request.form.getlist('pricingaction')]
    if 'True' not in send_all and len(pricing_action_ids) == 0:
        flash('Bitte wähle mindestens eine Checkbox aus.', 'danger')
    elif request.form['service'] == 'extend':
        start = request.form['service_start']
        end = request.form['service_end']
        name = request.form['service_name']
        pricing_action_query = db.session.query(
            PricingAction
        ).filter(
            PricingAction.id.in_(pricing_action_ids) if pricing_action_ids else True
        ).all()
        for pricing_action in pricing_action_query:
            extension = PricingAction(name, start, end, pricing_action.comment, pricing_action.product_id, [1])
            extension.is_extension = True
            extension.promotion_quantity = pricing_action.promotion_quantity
            if pricing_action.promotion_quantity != None:
                extension.sale_count = 0
            extension.parent_id = pricing_action.id
            db.session.add(extension)
            for supplier in pricing_action.suppliers:
                db.session.add(PricingAction_Supplier(extension.id, supplier.supplier_id))
            for stock in pricing_action.stocks:
                db.session.add(PricingAction_Stock(extension.id, stock.stock_id))
            db.session.commit()
            for pricingstrategy in pricing_action.strategies:
                new_pricingstrategy = PricingStrategy(pricingstrategy.label, pricingstrategy.rank, pricingstrategy.prc_margin, pricingstrategy.promotion_quantity, pricingstrategy.update_factor,
                                                      pricingstrategy.update_rule_hours, pricingstrategy.update_rule_quantity, pricingstrategy.marketplace_id, extension.id)
                if pricingstrategy.promotion_quantity != None:
                    new_pricingstrategy.sale_count = 0
                db.session.add(new_pricingstrategy)
                db.session.commit()
                for seller in pricingstrategy.noncompeting_sellers:
                    db.session.add(ExtSeller_PricingStrategy_NonCompeting(seller.id, new_pricingstrategy.id))
                for platform in pricingstrategy.noncompeting_platforms:
                    db.session.add(ExtPlatform_PricingStrategy_NonCompeting(platform.id, new_pricingstrategy.id))
                db.session.commit()
            if extension.start <= datetime.now() <= extension.end and pricing_action.active:
                for pa in extension.product.actions:
                    pa.active = False
                    for strategy in pa.strategies:
                        strategy.active = False
                extension.active = True
                for strategy in extension.strategies:
                    strategy.active = True
                db.session.commit()
        flash('Die Pricing-Aktionen wurden erfolgreich verlängert.', 'success')
        return redirect(url_for('center_product_dynamic_pricing'))
    elif request.form['service'] == 'activate':
        pricing_action_query = db.session.query(
            PricingAction
        ).filter(
            PricingAction.id.in_(pricing_action_ids) if pricing_action_ids else True
        ).all()
        for pricing_action in pricing_action_query:
            if pricing_action.start <= datetime.now() <= pricing_action.end:
                for pa in pricing_action.product.actions:
                    pa.active = False
                    for strategy in pa.strategies:
                        strategy.active = False
                db.session.commit()
                pricing_action.active = True
                if pricing_action.promotion_quantity != None:
                    pricing_action.sale_count = 0
                for strategy in pricing_action.strategies:
                    strategy.active = True
                    if strategy.promotion_quantity != None:
                        strategy.sale_count = 0
                db.session.commit()
        flash('Die Pricing-Aktionen wurden erfolgreich aktiviert.', 'success')
        return redirect(url_for('center_product_dynamic_pricing'))
    elif request.form['service'] == 'archive':
        pricing_action_query = db.session.query(
            PricingAction
        ).filter(
            PricingAction.id.in_(pricing_action_ids) if pricing_action_ids else True
        ).all()
        for pricing_action in pricing_action_query:
            pricing_action.archived = True
            pricing_action.active = False
            for strategy in pricing_action.strategies:
                strategy.archived = True
                strategy.active = False
            db.session.commit()
        flash('Die Pricing-Aktionen wurden erfolgreich archiviert.', 'success')
        return redirect(url_for('center_product_dynamic_pricing'))
    else:
        flash('Kein valider Service ausgewählt', 'danger')
        return redirect(url_for('center_product_dynamic_pricing'))


@app.route('/center/product/dynamic_pricing/sort/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_dynamic_pricing_sort(val):
    if val == session['dynamic_pricing_filter_infos']['order_by']:
        if session['dynamic_pricing_filter_infos']['order_by_dir'] == 'DESC':
            session['dynamic_pricing_filter_infos']= {}
            session['dynamic_pricing_filter_infos'] = {'marketplace_options': {},
                                                       'resultlimit': 10,
                                                       'except_mp': ['Kuchenboden', 'Leerverkauf'],
                                                       'short_sell_active': None,
                                                       'activity': None,
                                                       'order_by': val,
                                                       'order_by_dir': 'ASC'}
        else:
            session['dynamic_pricing_filter_infos']= {}
            session['dynamic_pricing_filter_infos'] = {'marketplace_options': {},
                                                       'resultlimit': 10,
                                                       'except_mp': ['Kuchenboden', 'Leerverkauf'],
                                                       'short_sell_active': None,
                                                       'activity': None,
                                                       'order_by': val,
                                                       'order_by_dir': 'DESC'}
    else:
        session['dynamic_pricing_filter_infos']= {}
        session['dynamic_pricing_filter_infos'] = {'marketplace_options': {},
                                                   'resultlimit': 10,
                                                   'except_mp': ['Kuchenboden', 'Leerverkauf'],
                                                   'short_sell_active': None,
                                                   'activity': None,
                                                   'order_by': val,
                                                   'order_by_dir': 'ASC'}
    return jsonify({})


@app.route('/center/product/dynamic_pricing', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_dynamic_pricing():
    session['dynamic_pricing_resultlimit'] = 10
    marketplaces = Marketplace.query.order_by(Marketplace.name).all()
    filter_infos = {}
    pricingactions = PricingAction.query.order_by(
        PricingAction.id.desc()
    ).filter_by(
        archived=False
    ).filter(
        PricingAction.name != 'Kuchenboden'
    ).filter(
        PricingAction.name != 'Leerverkauf'
    ).all()
    result_length = len(pricingactions)
    hidden_ids = [str(res.id) for res in pricingactions]
    pricingactions = pricingactions[:session['dynamic_pricing_filter_infos']['resultlimit']]
    if request.method == 'POST':
        if request.form['checker'] == 'filter':
            product_rank_ids = None
            id_type = request.form['id_type']
            session['dynamic_pricing_filter_infos']['product_id_type'] = id_type
            if request.form['product_ids'] != '':
                product_ids = request.form['product_ids']
                product_ids = product_ids.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
                pattern = ';' + '{2,}'
                product_ids = re.sub(pattern, ';', product_ids)
                if product_ids[-1] == ';':
                    product_ids = product_ids[:-1]
                if id_type == 'id':
                    product_ids = [int(product_id) for product_id in product_ids.split(';')]
                    session['dynamic_pricing_filter_infos']['product_ids'] = product_ids
                elif id_type == 'Internal_ID':
                    product_ids = [product_id for product_id in product_ids.split(';')]
                    session['dynamic_pricing_filter_infos']['product_ids'] = product_ids
                    filtered_products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
                    product_ids = [prod.id for prod in filtered_products]
                else:
                    product_ids = [product_id for product_id in product_ids.split(';')]
                    session['dynamic_pricing_filter_infos']['product_ids'] = product_ids
                    filtered_products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
                    product_ids = [prod.id for prod in filtered_products]
            else:
                product_ids = []
                session['dynamic_pricing_filter_infos']['product_ids'] = product_ids
            try:
                own_stock = int(request.form['own_stock'])
            except:
                own_stock = None
            session['dynamic_pricing_filter_infos']['own_stock'] = own_stock
            own_stock_operator = request.form['own_stock-operator']
            session['dynamic_pricing_filter_infos']['own_stock-operator'] = own_stock_operator
            try:
                summed_stock = int(request.form['summed_stock'])
            except:
                summed_stock = None
            session['dynamic_pricing_filter_infos']['summed_stock'] = summed_stock
            summed_stock_operator = request.form['summed_stock-operator']
            session['dynamic_pricing_filter_infos']['summed_stock-operator'] = summed_stock_operator
            try:
                active_start = datetime.strptime(request.form['start'], '%Y-%m-%d')
                session['dynamic_pricing_filter_infos']['active_start'] = active_start.strftime('%Y-%m-%d')
            except:
                active_start = datetime.strptime('2000-01-01', '%Y-%m-%d')
            try:
                active_end = datetime.strptime(request.form['end'], '%Y-%m-%d')
                session['dynamic_pricing_filter_infos']['active_end'] = active_end.strftime('%Y-%m-%d')
            except:
                active_end = datetime.strptime('3000-01-01', '%Y-%m-%d')
            try:
                sales_start = datetime.strptime(request.form['sales_start'], '%Y-%m-%d')
                session['dynamic_pricing_filter_infos']['sales_start'] = sales_start.strftime('%Y-%m-%d')
            except:
                sales_start = datetime.strptime('2000-01-01', '%Y-%m-%d')
            try:
                sales_end = datetime.strptime(request.form['sales_end'], '%Y-%m-%d')
                session['dynamic_pricing_filter_infos']['sales_end'] = sales_end.strftime('%Y-%m-%d')
            except:
                sales_end = datetime.strptime('3000-01-01', '%Y-%m-%d')
            try:
                sales_quantity = int(request.form['sales_quantity'])
            except:
                sales_quantity = None
            session['dynamic_pricing_filter_infos']['sales_quantity'] = sales_quantity
            try:
                actionstart = request.form['actionstart']
                datetime.strptime(request.form['actionstart'], '%Y-%m-%d')
                session['dynamic_pricing_filter_infos']['actionstart'] = actionstart
            except:
                actionstart = None
            try:
                actionend = request.form['actionend']
                datetime.strptime(request.form['actionend'], '%Y-%m-%d')
                session['dynamic_pricing_filter_infos']['actionend'] = actionend
            except:
                actionend = None
            try:
                promotion_quantity = int(request.form['promotion_quantity'])
            except:
                promotion_quantity = None
            session['dynamic_pricing_filter_infos']['promotion_quantity'] = promotion_quantity
            sales_quantity_operator = request.form['sales_quantity-operator']
            session['dynamic_pricing_filter_infos']['sales_quantity-operator'] = sales_quantity_operator
            actionstart_operator = request.form['actionstart-operator']
            session['dynamic_pricing_filter_infos']['actionstart-operator'] = actionstart_operator
            actionend_operator = request.form['actionend-operator']
            session['dynamic_pricing_filter_infos']['actionend-operator'] = actionend_operator
            promotion_quantity_operator = request.form['promotion_quantity-operator']
            session['dynamic_pricing_filter_infos']['promotion_quantity-operator'] = promotion_quantity_operator
            except_mp = request.form.getlist('except_mp')
            session['dynamic_pricing_filter_infos']['except_mp'] = except_mp
            session['dynamic_pricing_filter_infos']['short_sell_active'] = str_to_bool(request.form['short_sell_active'])
            activity = bool(request.form['activity']) if request.form['activity'] != 'None' else None
            session['dynamic_pricing_filter_infos']['activity'] = activity
            try:
                resultlimit = int(request.form['resultlimit'])
            except:
                resultlimit = 10
            session['dynamic_pricing_filter_infos']['resultlimit'] = resultlimit
            marketplace_options = request.form['marketplace_options']
            if marketplace_options == 'all_marketplaces' or marketplace_options == 'one_marketplace':
                if marketplace_options == 'all_marketplaces':
                    session['dynamic_pricing_filter_infos']['marketplace_options'] = {}
                    session['dynamic_pricing_filter_infos']['marketplace_options']['option'] = 'all_marketplaces'
                    query_operator = len(marketplaces)
                    strategy = str_to_float(request.form['strategy_all'])
                    session['dynamic_pricing_filter_infos']['marketplace_options']['strategy_all'] = strategy

                    min_margin = str_to_float(money_to_float(request.form['min_margin_all']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin_all'] = min_margin
                    latest_prc_margin = str_to_float(money_to_float(request.form['latest_prc_margin_all']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin_all'] = latest_prc_margin
                    mean_prc_margin = str_to_float(money_to_float(request.form['mean_prc_margin_all']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin_all'] = mean_prc_margin
                    real_sales = str_to_float(money_to_float(request.form['real_sales_all']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales_all'] = real_sales
                    mean_price = str_to_float(money_to_float(request.form['mean_price_all']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price_all'] = mean_price

                    min_margin_operator = request.form['min_margin_all-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin_all-operator'] = min_margin_operator
                    latest_prc_margin_operator = request.form['latest_prc_margin_all-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin_all-operator'] = latest_prc_margin_operator
                    mean_prc_margin_operator = request.form['mean_prc_margin_all-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin_all-operator'] = mean_prc_margin_operator
                    real_sales_operator = request.form['real_sales_all-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales_all-operator'] = real_sales_operator
                    mean_price_operator = request.form['mean_price_all-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price_all-operator'] = mean_price_operator
                else:
                    session['dynamic_pricing_filter_infos']['marketplace_options'] = {}
                    session['dynamic_pricing_filter_infos']['marketplace_options']['option'] = 'one_marketplace'
                    query_operator = 1
                    strategy = str_to_float(request.form['strategy_one'])
                    session['dynamic_pricing_filter_infos']['marketplace_options']['strategy_one'] = strategy
                    min_margin = str_to_float(money_to_float(request.form['min_margin_one']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin_one'] = min_margin
                    latest_prc_margin = str_to_float(money_to_float(request.form['latest_prc_margin_one']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin_one'] = latest_prc_margin
                    mean_prc_margin = str_to_float(money_to_float(request.form['mean_prc_margin_one']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin_one'] = mean_prc_margin
                    real_sales = str_to_float(money_to_float(request.form['real_sales_one']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales_one'] = real_sales
                    mean_price = str_to_float(money_to_float(request.form['mean_price_one']))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price_one'] = mean_price

                    min_margin_operator = request.form['min_margin_one-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin_one-operator'] = min_margin_operator
                    latest_prc_margin_operator = request.form['latest_prc_margin_one-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin_one-operator'] = latest_prc_margin_operator
                    mean_prc_margin_operator = request.form['mean_prc_margin_one-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin_one-operator'] = mean_prc_margin_operator
                    real_sales_operator = request.form['real_sales_one-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales_one-operator'] = real_sales_operator
                    mean_price_operator = request.form['mean_price_one-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price_one-operator'] = mean_price_operator
                # noinspection PyArgumentList,PyCallByClass
                pricing_strategy_query = db.session.query(
                    PricingStrategy.pricingaction_id, func.count(Marketplace.id)
                ).filter(
                    PricingStrategy.label == strategy if strategy != None else True
                ).filter(
                    sign(PricingStrategy.prc_margin, min_margin, min_margin_operator) if min_margin is not None else True
                ).filter(
                    Marketplace.id == PricingStrategy.marketplace_id
                ).filter(
                    sign(PricingStrategy.get_performance('latest_prc_margin', active_start, active_end), latest_prc_margin, latest_prc_margin_operator)
                    if latest_prc_margin is not None else True
                ).filter(
                    sign(PricingStrategy.get_performance('mean_prc_margin', active_start, active_end), mean_prc_margin, mean_prc_margin_operator)
                    if mean_prc_margin is not None else True
                ).filter(
                    sign(PricingStrategy.get_performance('real_sales', active_start, active_end), real_sales, real_sales_operator)
                    if real_sales is not None else True
                ).filter(
                    sign(PricingStrategy.get_performance('mean_price', active_start, active_end), mean_price, mean_price_operator)
                    if mean_price is not None else True
                ).group_by(
                    PricingStrategy.pricingaction_id
                ).having(
                    func.count(Marketplace.id) >= query_operator
                ).all()

                pricingaction_ids = [res[0] for res in pricing_strategy_query]

            else:
                session['dynamic_pricing_filter_infos']['marketplace_options'] = {}
                session['dynamic_pricing_filter_infos']['marketplace_options']['option'] = 'spec_marketplace'
                pricingaction_ids = []
                marketplace_ids = request.form.getlist('marketplace_filter')
                marketplace_ids = [int(marketplace_id) for marketplace_id in marketplace_ids]
                session['dynamic_pricing_filter_infos']['marketplace_options']['marketplace_ids'] = marketplace_ids
                chosen_marketplaces = Marketplace.query.filter(Marketplace.id.in_(marketplace_ids)).all()
                for marketplace in chosen_marketplaces:
                    strategy = str_to_float(request.form['strategy'+str(marketplace.id)])
                    session['dynamic_pricing_filter_infos']['marketplace_options']['strategy' + str(marketplace.id)] = strategy

                    rank = str_to_float(money_to_float(request.form['rank'+str(marketplace.id)]))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['rank' + str(marketplace.id)] = rank
                    min_margin = str_to_float(money_to_float(request.form['min_margin'+str(marketplace.id)]))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin' + str(marketplace.id)] = min_margin
                    latest_prc_margin = str_to_float(money_to_float(request.form['latest_prc_margin'+str(marketplace.id)]))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin' + str(marketplace.id)] = latest_prc_margin
                    mean_prc_margin = str_to_float(money_to_float(request.form['mean_prc_margin'+str(marketplace.id)]))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin' + str(marketplace.id)] = mean_prc_margin
                    real_sales = str_to_float(money_to_float(request.form['real_sales'+str(marketplace.id)]))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales' + str(marketplace.id)] = real_sales
                    mean_price = str_to_float(money_to_float(request.form['mean_price'+str(marketplace.id)]))
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price'+str(marketplace.id)] = mean_price

                    rank_operator = request.form['rank' + str(marketplace.id) + '-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['rank' + str(marketplace.id) + '-operator'] = rank_operator
                    min_margin_operator = request.form['min_margin' + str(marketplace.id) + '-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin' + str(marketplace.id) + '-operator'] = min_margin_operator
                    latest_prc_margin_operator = request.form['latest_prc_margin' + str(marketplace.id) + '-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin' + str(marketplace.id) + '-operator'] = latest_prc_margin_operator
                    mean_prc_margin_operator = request.form['mean_prc_margin' + str(marketplace.id) + '-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin' + str(marketplace.id) + '-operator'] = mean_prc_margin_operator
                    real_sales_operator = request.form['real_sales' + str(marketplace.id) + '-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales' + str(marketplace.id) + '-operator'] = real_sales_operator
                    mean_price_operator = request.form['mean_price' + str(marketplace.id) + '-operator']
                    session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price' + str(marketplace.id) + '-operator'] = mean_price_operator

                    # noinspection PyArgumentList,PyCallByClass
                    pricing_strategy_query = db.session.query(
                        PricingStrategy.pricingaction_id
                    ).filter(
                        PricingStrategy.label == strategy if strategy != None else True
                    ).filter(
                        sign(PricingStrategy.prc_margin, min_margin, min_margin_operator) if min_margin is not None else True
                    ).filter(
                        marketplace.id == PricingStrategy.marketplace_id
                    ).filter(
                        sign(PricingStrategy.get_performance('latest_prc_margin', active_start, active_end), latest_prc_margin, latest_prc_margin_operator)
                        if latest_prc_margin is not None else True
                    ).filter(
                        sign(PricingStrategy.get_performance('mean_prc_margin', active_start, active_end), mean_prc_margin, mean_prc_margin_operator)
                        if mean_prc_margin is not None else True
                    ).filter(
                        sign(PricingStrategy.get_performance('real_sales', active_start, active_end), real_sales, real_sales_operator)
                        if real_sales is not None else True
                    ).filter(
                        sign(PricingStrategy.get_performance('mean_price', active_start, active_end), mean_price, mean_price_operator)
                        if mean_price is not None else True
                    ).group_by(
                        PricingStrategy.pricingaction_id
                    ).all()

                    if pricingaction_ids:
                        pricingaction_ids = intersection(pricingaction_ids, [res[0] for res in pricing_strategy_query])
                    else:
                        pricingaction_ids = [res[0] for res in pricing_strategy_query]

                    if rank:
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
                        if marketplace.name=='Idealo':
                            product_rank_query = db.session.query(
                                Product.id, func.count(ExtOffer.id), func.count(Marketplace.id)
                            ).filter(
                                Product.id == ExtOffer.product_id
                                if rank is not None else True
                            ).filter(
                                Marketplace.id == ExtOffer.marketplace_id
                                if rank is not None else True
                            ).filter(
                                Marketplace.id == marketplace.id
                                if rank is not None else True
                            ).filter(
                                ExtOffer.extplatform.name=='lotusicafe'
                                if rank is not None else True
                            ).filter(
                                sign(ExtOffer.rank, rank, rank_operator)
                                if rank is not None else True
                            ).filter(
                                supremum > ExtOffer.last_seen
                            ).filter(
                                ExtOffer.last_seen >= minimum
                            ).all()
                        elif marketplace.name=='Ebay':
                            product_rank_query = db.session.query(
                                Product.id, func.count(ExtOffer.id), func.count(Marketplace.id)
                            ).filter(
                                Product.id == ExtOffer.product_id
                                if rank==1 else True
                            ).filter(
                                Marketplace.id == ExtOffer.marketplace_id
                                if rank==1 else True
                            ).filter(
                                Marketplace.name == 'Idealo'
                                if rank==1 else True
                            ).filter(
                                ExtOffer.extseller.name=='lotus-icafe'
                                if rank==1 else True
                            ).filter(
                                sign(ExtOffer.rank, 1, rank_operator)
                                if rank==1 else True
                            ).filter(
                                supremum > ExtOffer.last_seen
                            ).filter(
                                ExtOffer.last_seen >= minimum
                            ).all()
                        else:
                            product_rank_query = []

                        if product_rank_ids:
                            product_rank_ids = intersection(product_rank_ids, [res[0] for res in product_rank_query])
                        else:
                            product_rank_ids = [res[0] for res in product_rank_query]

            owns_stock_ids = []
            if own_stock is not None:
                stocks = Stock.query.filter_by(owned=True).all()
                stock_ids = [stock.id for stock in stocks]

                psas = db.session.query(
                    Product_Stock_Attributes.product_id, func.sum(Product_Stock_Attributes.quantity)
                ).filter(
                    Product_Stock_Attributes.stock_id.in_(stock_ids)
                ).filter(
                    Product_Stock_Attributes.avail_date <= datetime.now()
                ).filter(
                    Product_Stock_Attributes.termination_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                ).group_by(
                    Product_Stock_Attributes.product_id
                ).having(
                    sign(func.sum(Product_Stock_Attributes.quantity), own_stock, own_stock_operator)
                ).all()
                owns_stock_ids = [result[0] for result in psas]

            summed_stock_ids = []
            if summed_stock is not None:
                psas = db.session.query(
                    Product_Stock_Attributes.product_id, func.sum(Product_Stock_Attributes.quantity)
                ).filter(
                    Product_Stock_Attributes.avail_date <= datetime.now()
                ).filter(
                    Product_Stock_Attributes.termination_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                ).group_by(
                    Product_Stock_Attributes.product_id
                ).having(
                    sign(func.sum(Product_Stock_Attributes.quantity), summed_stock, summed_stock_operator)
                ).all()
                summed_stock_ids = [result[0] for result in psas]

            # noinspection PyCallByClass,PyComparisonWithNone
            if session['dynamic_pricing_filter_infos']['order_by'] == 'p_name':
                pricing_action_query = db.session.query(
                    PricingAction, func.count(PricingStrategy.id), func.max(Product.name)
                ).filter(
                    Product.id == PricingAction.product_id
                ).filter(
                    Product.short_sell == session['dynamic_pricing_filter_infos']['short_sell_active'] if session['dynamic_pricing_filter_infos']['short_sell_active'] != None else True
                ).filter(
                    PricingAction.id == PricingStrategy.pricingaction_id
                ).filter(
                    Product.id.in_(product_ids) if len(product_ids)>0 else True
                ).filter(
                    Product.id.in_(product_rank_ids) if product_rank_ids is not None else True
                ).filter(
                    PricingAction.start <= active_end
                ).filter(
                    PricingAction.end >= active_start
                ).filter(
                    sign(PricingAction.start, actionstart, actionstart_operator)
                    if actionstart else True
                ).filter(
                    sign(PricingAction.end, actionend, actionend_operator)
                    if actionend else True
                ).filter(
                    PricingAction.id.in_(pricingaction_ids)
                ).filter(
                    sign(PricingAction.promotion_quantity, promotion_quantity, promotion_quantity_operator)
                    if promotion_quantity is not None else True
                ).filter(
                    Product.id.in_(owns_stock_ids)
                    if own_stock is not None else True
                ).filter(
                    Product.id.in_(summed_stock_ids)
                    if summed_stock is not None else True
                ).filter(
                    sign(PricingAction.get_sales(sales_start, sales_end), sales_quantity, sales_quantity_operator)
                    if sales_quantity is not None else True
                ).filter(
                    PricingAction.name.notin_(except_mp)
                ).filter(
                    PricingAction.active==activity if activity!=None else True
                ).filter_by(
                    archived=False
                ).order_by(
                    func.max(Product.name).asc() if session['dynamic_pricing_filter_infos']['order_by_dir'] == 'ASC'
                    else func.max(Product.name).desc()
                ).group_by(
                    PricingAction.id
                ).all()
            else:
                pricing_action_query = db.session.query(
                    PricingAction, func.count(PricingStrategy.id), func.max(Product.name)
                ).filter(
                    Product.id == PricingAction.product_id
                ).filter(
                    Product.short_sell == session['dynamic_pricing_filter_infos']['short_sell_active'] if session['dynamic_pricing_filter_infos']['short_sell_active'] != None else True
                ).filter(
                    PricingAction.id == PricingStrategy.pricingaction_id
                ).filter(
                    Product.id.in_(product_ids) if len(product_ids)>0 else True
                ).filter(
                    Product.id.in_(product_rank_ids) if product_rank_ids is not None else True
                ).filter(
                    PricingAction.start <= active_end
                ).filter(
                    PricingAction.end >= active_start
                ).filter(
                    sign(PricingAction.start, actionstart, actionstart_operator)
                    if actionstart else True
                ).filter(
                    sign(PricingAction.end, actionend, actionend_operator)
                    if actionend else True
                ).filter(
                    PricingAction.id.in_(pricingaction_ids)
                ).filter(
                    sign(PricingAction.promotion_quantity, promotion_quantity, promotion_quantity_operator)
                    if promotion_quantity is not None else True
                ).filter(
                    Product.id.in_(owns_stock_ids)
                    if own_stock is not None else True
                ).filter(
                    Product.id.in_(summed_stock_ids)
                    if summed_stock is not None else True
                ).filter(
                    sign(PricingAction.get_sales(sales_start, sales_end), sales_quantity, sales_quantity_operator)
                    if sales_quantity is not None else True
                ).filter(
                    PricingAction.name.notin_(except_mp)
                ).filter(
                    PricingAction.active==activity if activity!=None else True
                ).filter_by(
                    archived=False
                ).order_by(
                    getattr(PricingAction, session['dynamic_pricing_filter_infos']['order_by']).asc() if session['dynamic_pricing_filter_infos']['order_by_dir'] == 'ASC'
                    else getattr(PricingAction, session['dynamic_pricing_filter_infos']['order_by']).desc()
                ).group_by(
                    PricingAction.id
                ).all()

            hidden_ids = [str(res[0].id) for res in pricing_action_query]
            pricingactions = [res[0] for res in pricing_action_query[:resultlimit]]
            result_length = len(pricing_action_query)
    return render_template('center/product/dynamic_pricing/index.html', marketplaces=marketplaces, filter_infos=filter_infos, pricingactions=pricingactions, result_length=result_length,
                           now=datetime.now().strftime('%Y-%m-%d'), hidden_ids=hidden_ids)


@app.route('/center/product/dynamic_pricing/add10/<off>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_dynamic_pricing_add10(off):
    marketplaces = Marketplace.query.order_by(Marketplace.name).all()
    if 'product_ids' in session['dynamic_pricing_filter_infos']:
        product_rank_ids = None
        id_type = session['dynamic_pricing_filter_infos']['product_id_type']
        if id_type == 'id':
            product_ids = session['dynamic_pricing_filter_infos']['product_ids']
        elif id_type == 'Internal_ID':
            product_ids = session['dynamic_pricing_filter_infos']['product_ids']
            filtered_products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
            product_ids = [prod.id for prod in filtered_products]
        else:
            product_ids = session['dynamic_pricing_filter_infos']['product_ids']
            filtered_products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
            product_ids = [prod.id for prod in filtered_products]
        own_stock = session['dynamic_pricing_filter_infos']['own_stock']
        own_stock_operator = session['dynamic_pricing_filter_infos']['own_stock-operator']
        summed_stock = session['dynamic_pricing_filter_infos']['summed_stock']
        summed_stock_operator = session['dynamic_pricing_filter_infos']['summed_stock-operator']
        try:
            active_start = session['dynamic_pricing_filter_infos']['active_start']
        except:
            active_start = datetime.strptime('2000-01-01', '%Y-%m-%d')
        try:
            active_end = session['dynamic_pricing_filter_infos']['active_end']
        except:
            active_end = datetime.strptime('3000-01-01', '%Y-%m-%d')
        try:
            sales_start = session['dynamic_pricing_filter_infos']['sales_start']
        except:
            sales_start = datetime.strptime('2000-01-01', '%Y-%m-%d')
        try:
            sales_end = session['dynamic_pricing_filter_infos']['sales_end']
        except:
            sales_end = datetime.strptime('3000-01-01', '%Y-%m-%d')
        sales_quantity = session['dynamic_pricing_filter_infos']['sales_quantity']
        try:
            actionstart = session['dynamic_pricing_filter_infos']['actionstart']
            datetime.strptime(actionstart, '%Y-%m-%d')
        except:
            actionstart = None
        try:
            actionend = session['dynamic_pricing_filter_infos']['actionend']
            datetime.strptime(actionend, '%Y-%m-%d')
        except:
            actionend = None
        promotion_quantity = session['dynamic_pricing_filter_infos']['promotion_quantity']
        sales_quantity_operator = session['dynamic_pricing_filter_infos']['sales_quantity-operator']
        actionstart_operator = session['dynamic_pricing_filter_infos']['actionstart-operator']
        actionend_operator = session['dynamic_pricing_filter_infos']['actionend-operator']
        promotion_quantity_operator = session['dynamic_pricing_filter_infos']['promotion_quantity-operator']
        except_mp = session['dynamic_pricing_filter_infos']['except_mp']
        activity = session['dynamic_pricing_filter_infos']['activity']
        resultlimit = session['dynamic_pricing_filter_infos']['resultlimit']
        marketplace_options = session['dynamic_pricing_filter_infos']['marketplace_options']['option']
        if marketplace_options in {'all_marketplaces', 'one_marketplace'}:
            if marketplace_options == 'all_marketplaces':
                query_operator = len(marketplaces)
                strategy = session['dynamic_pricing_filter_infos']['marketplace_options']['strategy_all']

                min_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin_all']
                latest_prc_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin_all']
                mean_prc_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin_all']
                real_sales = session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales_all']
                mean_price = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price_all']

                min_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin_all-operator']
                latest_prc_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin_all-operator']
                mean_prc_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin_all-operator']
                real_sales_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales_all-operator']
                mean_price_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price_all-operator']
            else:
                query_operator = 1
                strategy = session['dynamic_pricing_filter_infos']['marketplace_options']['strategy_one']

                min_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin_one']
                mean_prc_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin_one']
                latest_prc_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin_one']
                real_sales = session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales_one']
                mean_price = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price_one']

                min_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin_one-operator']
                mean_prc_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin_one-operator']
                latest_prc_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin_one-operator']
                real_sales_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales_one-operator']
                mean_price_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price_one-operator']

            # noinspection PyArgumentList,PyCallByClass
            pricing_strategy_query = db.session.query(
                PricingStrategy.pricingaction_id, func.count(Marketplace.id)
            ).filter(
                PricingStrategy.label == strategy if strategy != None else True
            ).filter(
                sign(PricingStrategy.prc_margin, min_margin, min_margin_operator) if min_margin is not None else True
            ).filter(
                Marketplace.id == PricingStrategy.marketplace_id
            ).filter(
                sign(PricingStrategy.get_performance('latest_prc_margin', active_start, active_end), latest_prc_margin, latest_prc_margin_operator)
                if latest_prc_margin is not None else True
            ).filter(
                sign(PricingStrategy.get_performance('mean_prc_margin', active_start, active_end), mean_prc_margin, mean_prc_margin_operator)
                if mean_prc_margin is not None else True
            ).filter(
                sign(PricingStrategy.get_performance('real_sales', active_start, active_end), real_sales, real_sales_operator)
                if real_sales is not None else True
            ).filter(
                sign(PricingStrategy.get_performance('mean_price', active_start, active_end), mean_price, mean_price_operator)
                if mean_price is not None else True
            ).group_by(
                PricingStrategy.pricingaction_id
            ).having(
                func.count(Marketplace.id) >= query_operator
            ).all()

            pricingaction_ids = [res[0] for res in pricing_strategy_query]

        else:
            pricingaction_ids = []
            marketplace_ids = session['dynamic_pricing_filter_infos']['marketplace_options']['marketplace_ids']
            chosen_marketplaces = Marketplace.query.filter(Marketplace.id.in_(marketplace_ids)).all()
            for marketplace in chosen_marketplaces:
                strategy = session['dynamic_pricing_filter_infos']['marketplace_options']['strategy' + str(marketplace.id)]

                rank = session['dynamic_pricing_filter_infos']['marketplace_options']['rank' + str(marketplace.id)]
                min_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin' + str(marketplace.id)]
                mean_prc_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin' + str(marketplace.id)]
                latest_prc_margin = session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin' + str(marketplace.id)]
                real_sales = session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales' + str(marketplace.id)]
                mean_price = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price' + str(marketplace.id)]

                rank_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['rank' + str(marketplace.id) + '-operator']
                min_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['min_margin' + str(marketplace.id) + '-operator']
                mean_prc_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_prc_margin' + str(marketplace.id) + '-operator']
                latest_prc_margin_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['latest_prc_margin' + str(marketplace.id) + '-operator']
                real_sales_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['real_sales' + str(marketplace.id) + '-operator']
                mean_price_operator = session['dynamic_pricing_filter_infos']['marketplace_options']['mean_price' + str(marketplace.id) + '-operator']

                # noinspection PyArgumentList,PyCallByClass
                pricing_strategy_query = db.session.query(
                    PricingStrategy.pricingaction_id
                ).filter(
                    PricingStrategy.label == strategy if strategy != None else True
                ).filter(
                    sign(PricingStrategy.prc_margin, min_margin, min_margin_operator) if min_margin is not None else True
                ).filter(
                    marketplace.id == PricingStrategy.marketplace_id
                ).filter(
                    sign(PricingStrategy.get_performance('latest_prc_margin', active_start, active_end), latest_prc_margin, latest_prc_margin_operator)
                    if latest_prc_margin is not None else True
                ).filter(
                    sign(PricingStrategy.get_performance('mean_prc_margin', active_start, active_end), mean_prc_margin, mean_prc_margin_operator)
                    if mean_prc_margin is not None else True
                ).filter(
                    sign(PricingStrategy.get_performance('real_sales', active_start, active_end), real_sales, real_sales_operator)
                    if real_sales is not None else True
                ).filter(
                    sign(PricingStrategy.get_performance('mean_price', active_start, active_end), mean_price, mean_price_operator)
                    if mean_price is not None else True
                ).group_by(
                    PricingStrategy.pricingaction_id
                ).all()

                if pricingaction_ids:
                    pricingaction_ids = intersection(pricingaction_ids, [res[0] for res in pricing_strategy_query])
                else:
                    pricingaction_ids = [res[0] for res in pricing_strategy_query]

                if rank:
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
                    if marketplace.name == 'Idealo':
                        product_rank_query = db.session.query(
                            Product.id, func.count(ExtOffer.id), func.count(Marketplace.id)
                        ).filter(
                            Product.id == ExtOffer.product_id
                            if rank is not None else True
                        ).filter(
                            Marketplace.id == ExtOffer.marketplace_id
                            if rank is not None else True
                        ).filter(
                            Marketplace.id == marketplace.id
                            if rank is not None else True
                        ).filter(
                            ExtOffer.platform.name == 'lotusicafe'
                            if rank is not None else True
                        ).filter(
                            sign(ExtOffer.rank, rank, rank_operator)
                            if rank is not None else True
                        ).filter(
                            supremum > ExtOffer.last_seen
                        ).filter(
                            ExtOffer.last_seen >= minimum
                        ).all()
                    elif marketplace.name == 'Ebay':
                        product_rank_query = db.session.query(
                            Product.id, func.count(ExtOffer.id), func.count(Marketplace.id)
                        ).filter(
                            Product.id == ExtOffer.product_id
                            if rank == 1 else True
                        ).filter(
                            Marketplace.id == ExtOffer.marketplace_id
                            if rank == 1 else True
                        ).filter(
                            Marketplace.name == 'Idealo'
                            if rank == 1 else True
                        ).filter(
                            ExtOffer.seller.name == 'lotus-icafe'
                            if rank == 1 else True
                        ).filter(
                            sign(ExtOffer.rank, 1, rank_operator)
                            if rank == 1 else True
                        ).filter(
                            supremum > ExtOffer.last_seen
                        ).filter(
                            ExtOffer.last_seen >= minimum
                        ).all()
                    else:
                        product_rank_query = []

                    if product_rank_ids:
                        product_rank_ids = intersection(product_rank_ids, [res[0] for res in product_rank_query])
                    else:
                        product_rank_ids = [res[0] for res in product_rank_query]

        owns_stock_ids = []
        if own_stock is not None:
            stocks = Stock.query.filter_by(owned=True).all()
            stock_ids = [stock.id for stock in stocks]

            psas = db.session.query(
                Product_Stock_Attributes.product_id, func.sum(Product_Stock_Attributes.quantity)
            ).filter(
                Product_Stock_Attributes.stock_id.in_(stock_ids)
            ).filter(
                Product_Stock_Attributes.avail_date <= datetime.now()
            ).filter(
                Product_Stock_Attributes.termination_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).group_by(
                Product_Stock_Attributes.product_id
            ).having(
                sign(func.sum(Product_Stock_Attributes.quantity), own_stock, own_stock_operator)
            ).all()
            owns_stock_ids = [result[0] for result in psas]

        summed_stock_ids = []
        if summed_stock is not None:
            psas = db.session.query(
                Product_Stock_Attributes.product_id, func.sum(Product_Stock_Attributes.quantity)
            ).filter(
                Product_Stock_Attributes.avail_date <= datetime.now()
            ).filter(
                Product_Stock_Attributes.termination_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).group_by(
                Product_Stock_Attributes.product_id
            ).having(
                sign(func.sum(Product_Stock_Attributes.quantity), summed_stock, summed_stock_operator)
            ).all()
            summed_stock_ids = [result[0] for result in psas]

        if session['dynamic_pricing_filter_infos']['order_by'] == 'p_name':
            pricing_action_query = db.session.query(
                PricingAction, func.count(PricingStrategy.id), func.max(Product.name)
            ).filter(
                Product.id == PricingAction.product_id
            ).filter(
                Product.short_sell == session['dynamic_pricing_filter_infos']['short_sell_active'] if session['dynamic_pricing_filter_infos']['short_sell_active'] != None else True
            ).filter(
                PricingAction.id == PricingStrategy.pricingaction_id
            ).filter(
                Product.id.in_(product_ids) if len(product_ids) > 0 else True
            ).filter(
                Product.id.in_(product_rank_ids) if product_rank_ids is not None else True
            ).filter(
                PricingAction.start <= active_end
            ).filter(
                PricingAction.end >= active_start
            ).filter(
                sign(PricingAction.start, actionstart, actionstart_operator)
                if actionstart else True
            ).filter(
                sign(PricingAction.end, actionend, actionend_operator)
                if actionend else True
            ).filter(
                PricingAction.id.in_(pricingaction_ids)
            ).filter(
                sign(PricingAction.promotion_quantity, promotion_quantity, promotion_quantity_operator)
                if promotion_quantity else True
            ).filter(
                Product.id.in_(owns_stock_ids)
                if own_stock is not None else True
            ).filter(
                Product.id.in_(summed_stock_ids)
                if summed_stock is not None else True
            ).filter(
                sign(PricingAction.get_sales(sales_start, sales_end), sales_quantity, sales_quantity_operator)
                if sales_quantity is not None else True
            ).filter(
                PricingAction.name.notin_(except_mp)
            ).filter(
                PricingAction.active==activity if activity!=None else True
            ).filter_by(
                archived=False
            ).group_by(
                PricingAction.id
            ).order_by(
                func.max(Product.name).asc() if session['dynamic_pricing_filter_infos']['order_by_dir'] == 'ASC'
                else func.max(Product.name).desc()
            ).offset(
                session['dynamic_pricing_filter_infos']['resultlimit']*int(off)
            ).limit(
                resultlimit
            ).all()
            pricingactions = [res[0] for res in pricing_action_query]
        else:
            pricing_action_query = db.session.query(
                PricingAction, func.count(PricingStrategy.id), func.max(Product.name)
            ).filter(
                Product.id == PricingAction.product_id
            ).filter(
                Product.short_sell == session['dynamic_pricing_filter_infos']['short_sell_active'] if session['dynamic_pricing_filter_infos']['short_sell_active'] != None else True
            ).filter(
                PricingAction.id == PricingStrategy.pricingaction_id
            ).filter(
                Product.id.in_(product_ids) if len(product_ids) > 0 else True
            ).filter(
                Product.id.in_(product_rank_ids) if product_rank_ids is not None else True
            ).filter(
                PricingAction.start <= active_end
            ).filter(
                PricingAction.end >= active_start
            ).filter(
                sign(PricingAction.start, actionstart, actionstart_operator)
                if actionstart else True
            ).filter(
                sign(PricingAction.end, actionend, actionend_operator)
                if actionend else True
            ).filter(
                PricingAction.id.in_(pricingaction_ids)
            ).filter(
                sign(PricingAction.promotion_quantity, promotion_quantity, promotion_quantity_operator)
                if promotion_quantity else True
            ).filter(
                Product.id.in_(owns_stock_ids)
                if own_stock is not None else True
            ).filter(
                Product.id.in_(summed_stock_ids)
                if summed_stock is not None else True
            ).filter(
                sign(PricingAction.get_sales(sales_start, sales_end), sales_quantity, sales_quantity_operator)
                if sales_quantity is not None else True
            ).filter(
                PricingAction.name.notin_(except_mp)
            ).filter(
                PricingAction.active==activity if activity!=None else True
            ).filter_by(
                archived=False
            ).group_by(
                PricingAction.id
            ).order_by(
                getattr(PricingAction, session['dynamic_pricing_filter_infos']['order_by']).asc() if session['dynamic_pricing_filter_infos']['order_by_dir'] == 'ASC'
                else getattr(PricingAction, session['dynamic_pricing_filter_infos']['order_by']).desc()
            ).offset(
                session['dynamic_pricing_filter_infos']['resultlimit']*int(off)
            ).limit(
                resultlimit
            ).all()
            pricingactions = [res[0] for res in pricing_action_query]
    else:
        pricingactions = PricingAction.query.order_by(
            PricingAction.id.desc()
        ).filter_by(
            archived=False
        ).offset(
            session['dynamic_pricing_filter_infos']['resultlimit']*int(off)
        ).limit(
            session['dynamic_pricing_filter_infos']['resultlimit']
        ).all()
    rows = ''
    for pricingaction in pricingactions:
        rows+= '<tr class="trclick" onclick="show_pricingaction('+ str(pricingaction.id) +')">' \
               '<td style="position: relative">' \
               '<label for="pricingaction_' + str(pricingaction.id) + '" class="clickable_rowbox" style="width: 50px; height: 50px; padding-top: 14px; position: absolute; top:0; cursor: pointer">' \
               '<input value="' + str(pricingaction.id) + '" type="checkbox" name="pricingaction" class="pricingaction" id="pricingaction_' + str(pricingaction.id) + '" style="cursor: pointer">' \
               '</label>' \
               '</td>' \
               '<td>' \
               '' + pricingaction.product.name + '' \
               '</td>' \
               '<td>' \
               '' + str(pricingaction.id) + '' \
               '</td>' \
               '<td>' \
               '' + pricingaction.name + '' \
               '</td>' \
               '<td>' \
               '' + pricingaction.start.strftime('%d.%m.%Y') + '' \
               '</td>' \
               '<td>' \
               '' + pricingaction.end.strftime('%d.%m.%Y') + '' \
               '</td>' \
               '<td>' \
               '' + str(pricingaction.promotion_quantity) + '' \
               '</td>' \
               '<td>' \
               '<table>' \
               '<tr style="border: None">'
        for strategy in pricingaction.strategies:
            add_link = ''
            if strategy.marketplace.get_productlink(pricingaction.product.id):
                if strategy.marketplace.get_productlink(pricingaction.product.id).link != '' and strategy.marketplace.get_productlink(pricingaction.product.id).link != '-':
                    add_link = 'class="glow" onclick="open_marketplace_link(' + strategy.marketplace.get_productlink(pricingaction.product.id).link + '); event.cancelBubble=true;"'
            rows += '<td style="padding: 0; border: None" ' + add_link + '>' \
                    '<img src="' + url_for('static', filename='images/foreignicons/' + strategy.marketplace.name + '_icon.png') + '" style="height:20px; width: 20px; margin: 0 2px 0 2px">' \
                    '</td>'
        rows += '</tr>' \
                '<tr style="border: None">'
        for strategy in pricingaction.strategies:
            rows += '<td style="border: None; padding: 0; text-align: center">'
            if pricingaction.product.current_rank_by_marketplace(strategy.marketplace_id) is not None:
                rows += str(pricingaction.product.current_rank_by_marketplace(strategy.marketplace_id))
            else:
                rows += '-'
            rows += '</td>'
        rows += '</tr>' \
                '</table>' \
                '</td>' \
                '<td>'
        if pricingaction.active:
            rows += '<div class="tiny five green smallbutton visible" style="cursor: default">' \
                    '<i class="fa fa-thumbs-up" aria-hidden="true"></i> <i>aktiv</i>' \
                    '</div>'
        else:
            rows += '<a href="'+ url_for('center_product_pricingactions_activate_pricingaction', id=pricingaction.id) +'" onclick="event.cancelBubble=true;">' \
                    '<div class="tiny five redbutton smallbutton visible" style="">' \
                    '<i class="fa fa-thumbs-down" aria-hidden="true"></i> <i>inaktiv</i>' \
                    '</div>' \
                    '</a>'
        rows+= '</td>' \
               '</tr>'
    return jsonify({'rows': rows, 'length': len(pricingactions)})


@app.route('/center/product/dynamic_pricing/transform_ids/<ids>,<old_type>,<new_type>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_dynamic_pricing_transform_ids(ids, old_type, new_type):
    ids = ids.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
    pattern = ';' + '{2,}'
    ids = re.sub(pattern, ';', ids)
    if ids[-1] == ';':
        ids = ids[:-1]
    ids = ids.split(';')
    not_found = ''

    if old_type == 'id':
        products = Product.query.filter(Product.id.in_([int(product_id) for product_id in ids])).all()
        if len(ids) != len(products):
            product_ids = [str(product.id) for product in products]
            for product_id in ids:
                if product_id not in product_ids:
                    not_found += product_id + ', '
    elif old_type == 'HSP_ID':
        products = Product.query.filter(Product.hsp_id.in_(ids)).all()
        if len(ids) != len(products):
            product_ids = [product.hsp_id for product in products]
            for product_id in ids:
                if product_id not in product_ids:
                    not_found += product_id + ', '
    else:
        products = Product.query.filter(Product.internal_id.in_(ids)).all()
        if len(ids) != len(products):
            product_ids = [product.internal_id for product in products]
            for product_id in ids:
                if product_id not in product_ids:
                    not_found += product_id + ', '

    if new_type == 'id':
        ids = ';'.join([str(product.id) for product in products])
    elif new_type == 'HSP_ID':
        ids = ';'.join([str(product.hsp_id) for product in products])
    else:
        ids = ';'.join([str(product.internal_id) for product in products])

    if not_found != '':
        not_found = not_found[:-2]

    return jsonify({'ids': ids, 'not_found': not_found})


@app.route('/center/product/dynamic_pricing/activate_pricingaction/<pricingaction_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_dynamic_pricing_activate_pricingaction(pricingaction_id):
    pricing_action = PricingAction.query.filter_by(id=int(pricingaction_id)).first()
    if pricing_action.start <= datetime.now() <= pricing_action.end:
        for pa in pricing_action.product.actions:
            pa.active = False
            for strategy in pa.strategies:
                strategy.active = False
        db.session.commit()
        pricing_action.active = True
        if pricing_action.promotion_quantity != None:
            pricing_action.sale_count = 0
        for strategy in pricing_action.strategies:
            strategy.active = True
            if strategy.promotion_quantity != None:
                strategy.sale_count = 0
        db.session.commit()
        product = pricing_action.product
        for pricing_strategy in pricing_action.strategies:
            if pricing_strategy.marketplace.name == 'Idealo':
                authorization = idealo_offer.get_access_token()
            elif pricing_strategy.marketplace.name == 'Ebay':
                authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
            else:
                flash(f'Marketplace-Upload for {pricing_strategy.marketplace.name} not implemented.', 'danger')
                return redirect(url_for('center_product_dynamic_pricing'))
            product.generate_mp_price(marketplace_id=pricing_strategy.marketplace_id, strategy_label=pricing_strategy.label, strategy_id=pricing_strategy.id,
                                      min_margin=pricing_strategy.prc_margin/100 if pricing_strategy.prc_margin is not None else None, rank=pricing_strategy.rank if pricing_strategy.rank is not None else 0,
                                      ext_offers=product.get_mp_ext_offers(pricing_strategy.marketplace_id), authorization=authorization)
    else:
        flash('Wähle eine Pricing-Aktion im aktuellen Zeitraum aus!', 'danger')
    return redirect(url_for('center_product_dynamic_pricing'))


@app.route('/center/product/dynamic_pricing/add_pricingaction', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_product_dynamic_pricing_add_pricingaction():
    product_id_choices = ''
    marketplaces = Marketplace.query.all()

    if request.method == 'POST':
        if request.form['checker'] == 'redirect':
            send_all = request.form.getlist('send_all')
            if 'True' in send_all:
                pricingaction_ids = [int(action_id) for action_id in request.form['pricingaction_hidden'].split(',')]
            else:
                pricingaction_ids = [int(x) for x in request.form.getlist('pricingaction')]
            pricing_action_query = db.session.query(
                PricingAction.product_id
            ).filter(
                PricingAction.id.in_(pricingaction_ids) if pricingaction_ids else False
            ).group_by(
                PricingAction.product_id
            ).all()
            product_id_choices = ';'.join([str(result[0]) for result in pricing_action_query])
        else:
            checked_marketplace = request.form.getlist('marketplace_checkbox')
            if len(checked_marketplace) > 0:
                id_type = request.form['id_type']
                if request.form['product_ids'] != '':
                    prods = request.form['product_ids']
                    prods = prods.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
                    pattern = ';' + '{2,}'
                    prods = re.sub(pattern, ';', prods)
                    if prods[-1] == ';':
                        prods = prods[:-1]
                    if id_type == 'id':
                        product_ids = [int(product_id) for product_id in prods.replace(' ', '').split(';')]
                        products = Product.query.filter(Product.id.in_(product_ids)).all()
                    elif id_type == 'Internal_ID':
                        product_ids = [product_id for product_id in prods.replace(' ', '').split(';')]
                        products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
                    else:
                        product_ids = [product_id for product_id in prods.replace(' ', '').split(';')]
                        products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
                else:
                    products = Product.query.filter(Product.hsp_id.in_([])).all()
                if products:
                    name = request.form['name']
                    promotion_quantity = request.form['promotion_quantity']
                    start = datetime.strptime(request.form['start'], '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=999999)
                    end = datetime.strptime(request.form['end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
                    comment = request.form['comment']
                    supplier_ids = request.form['supplier_ids'].replace(' ', '').split(';')
                    if supplier_ids[0] == '':
                        supplier_ids = []
                    else:
                        supplier_ids = [int(supplier_id) for supplier_id in supplier_ids]
                    stock_ids = request.form['stock_ids'].replace(' ', '').split(';')
                    if stock_ids[0] == '':
                        stock_ids = []
                    else:
                        stock_ids = [int(stock_id) for stock_id in stock_ids]
                    for product in products:
                        new_pricingaction = PricingAction(name, start, end, comment, product.id, [1])
                        if promotion_quantity != '':
                            new_pricingaction.promotion_quantity = int(promotion_quantity)
                            new_pricingaction.sale_count = 0
                        else:
                            new_pricingaction.promotion_quantity = None
                        for supplier_id in supplier_ids:
                            db.session.add(PricingAction_Supplier(new_pricingaction.id, supplier_id))
                        for stock_id in stock_ids:
                            db.session.add(PricingAction_Stock(new_pricingaction.id, stock_id))
                        db.session.add(new_pricingaction)
                        db.session.commit()
                        for marketplace in checked_marketplace:
                            strategy = request.form['strategy' + marketplace]
                            quantity_share = request.form['quantity_share' + marketplace]
                            if quantity_share != '':
                                quantity_share = str_to_float(money_to_float(quantity_share))
                                if new_pricingaction.promotion_quantity:
                                    quantity_share = quantity_share * new_pricingaction.promotion_quantity // 100
                            else:
                                quantity_share = None
                            rank = request.form['rank' + marketplace]
                            if rank != '':
                                rank = int(rank)
                            else:
                                rank = None
                            prc_margin = str_to_float(prc_to_float(request.form['prc_margin' + marketplace]))
                            update_rule_quantity = request.form['update_rule_quantity' + marketplace]
                            if update_rule_quantity != '':
                                update_rule_quantity = int(update_rule_quantity)
                            else:
                                update_rule_quantity = None
                            update_rule_hours = request.form['update_rule_hours' + marketplace]
                            if update_rule_hours != '':
                                update_rule_hours = int(update_rule_hours)
                            else:
                                update_rule_hours = None
                            update_factor = request.form['update_factor' + marketplace]
                            if update_factor != '':
                                update_factor = str_to_float(money_to_float(update_factor))
                            else:
                                update_factor = None
                            new_pricingstrategy = PricingStrategy(strategy, rank, prc_margin, quantity_share, update_factor, update_rule_hours, update_rule_quantity, marketplace, new_pricingaction.id)
                            if quantity_share:
                                new_pricingstrategy.sale_count = 0
                            db.session.add(new_pricingstrategy)
                            seller_ids = request.form['seller_ids' + marketplace].replace(' ', '').split(';')
                            if seller_ids[0] == '':
                                seller_ids = []
                            else:
                                seller_ids = [int(seller_id) for seller_id in request.form['seller_ids' + marketplace].replace(' ', '').split(';')]
                            for seller_id in seller_ids:
                                db.session.add(ExtSeller_PricingStrategy_NonCompeting(seller_id, new_pricingstrategy.id))
                            platform_ids = request.form['platform_ids' + marketplace].replace(' ', '').split(';')
                            if platform_ids[0] == '':
                                platform_ids = []
                            else:
                                platform_ids = [int(platform_id) for platform_id in request.form['platform_ids' + marketplace].replace(' ', '').split(';')]
                            for platform_id in platform_ids:
                                db.session.add(ExtPlatform_PricingStrategy_NonCompeting(platform_id, new_pricingstrategy.id))
                        db.session.commit()
                        activate = request.form.getlist('activate')
                        if start.date() == datetime.now().date() and 'activate' in activate:
                            for pa in new_pricingaction.product.actions:
                                pa.active = False
                                for strategy in pa.strategies:
                                    strategy.active = False
                            db.session.commit()
                            new_pricingaction.active = True
                            for strategy in new_pricingaction.strategies:
                                strategy.active = True
                            db.session.commit()

                    flash('Pricing-Aktionen erfolgreich hinzugefügt.', 'success')
                else:
                    flash('Wähle mindestens eine Produkt aus!', 'danger')
            else:
                flash('Wähle mindestens einen Marketplace aus!', 'danger')
    next_month = datetime.now().replace(day=28) + timedelta(days=4)
    return render_template('center/product/dynamic_pricing/add_pricingaction.html', marketplaces=marketplaces, product_id_choices=product_id_choices, now=datetime.now().strftime('%Y-%m-%d'),
                           init_end=(next_month - timedelta(days=next_month.day)).strftime('%Y-%m-%d'))


#####################################################################################

#####################################   STOCK   #####################################

#####################################################################################


@app.route('/center/stock', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock():
    stocks = Stock.query.order_by(Stock.id).all()
    suppliers = Supplier.query.order_by(Supplier.id).all()
    now = datetime.now()
    if request.method=='POST':
        if request.form['checker'] == 'add':
            name = request.form['name']
            supplier_id = int(request.form['supplier'])
            lag_days = int(request.form['lag_days'])
            if supplier_id == 0:
                owned = True
                newstock = Stock(name, owned, lag_days)
            else:
                owned = False
                newstock = Stock(name, owned, lag_days)
                newstock.supplier_id = supplier_id
            db.session.add(newstock)
            db.session.commit()
        else:
            try:
                start = datetime.strptime(request.form['start'], '%Y-%m-%d')
                end = datetime.strptime(request.form['end'], '%Y-%m-%d')
            except:
                flash('Fehlerhafte Daten', 'danger')
                return redirect(url_for('center_stock'))
            other_stocks = Stock.query.filter_by(owned=False).all()
            while start <= end:
                for stock in other_stocks:
                    psa = Product_Stock_Attributes.query.filter(
                        Product_Stock_Attributes.stock_id == stock.id
                    ).filter(
                        Product_Stock_Attributes.avail_date == start
                    ).first()
                    if not psa:
                        filename = '/lager/' + str(stock.id) + '_' + start.strftime('%Y_%m_%d') + '.csv'
                        if os.path.exists(filename):
                            with open(filename, encoding='utf-8') as csv_file:
                                csv_reader = csv.reader(csv_file, delimiter=';')
                                i = 0
                                new_products = []
                                for row in csv_reader:
                                    if i == 0:
                                        i += 1
                                        continue
                                    prod_hsp_id = row[0]
                                    prod_name = row[1]

                                    if len(prod_name) > 80:
                                        prod_name = prod_name[:80].rsplit(' ', 1)[0]

                                    prod_quant = int(row[2])
                                    prod_tax = 19
                                    prod_price = float(money_to_float(row[3]))

                                    while len(prod_hsp_id) < 13:
                                        prod_hsp_id = '0' + prod_hsp_id
                                    product = Product.query.filter_by(hsp_id=prod_hsp_id).first()
                                    if not product:
                                        product = Product('EAN', prod_hsp_id, name=prod_name, mpn='nicht zutreffend')
                                        db.session.add(product)
                                        db.session.commit()

                                        psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None,
                                                                       datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                                                       datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, stock.id)
                                        psa.last_seen = datetime.now()
                                        db.session.add(psa)
                                        db.session.commit()

                                        own_stock = Stock.query.filter_by(owned=True).first()

                                        product.add_basic_product_data(own_stock.id)

                                        new_products.append(product)

                                        j = 0

                                        while j <= 1:
                                            file_name = 'generic_pic.jpg'
                                            db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                                            j += 1
                                    else:
                                        psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None,
                                                                       datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                                                       datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, stock.id)
                                        psa.last_seen = datetime.now()
                                        db.session.add(psa)
                                        db.session.commit()

                start += timedelta(days=1)
        return redirect(url_for('center_stock'))
    return render_template('center/stock/index.html', stocks=stocks, suppliers=suppliers, now=now.strftime('%Y-%m-%d'))


@app.route('/center/stock/turnpage/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock_turnpage(val):
    sort_dir = session['stock_filter_infos']['sort_dir']
    sort = session['stock_filter_infos']['sort']
    session['stock_filter_infos'] = {'datalimit_page': 25,
                                     'datalimit_whole': None,
                                     'product_ids': [],
                                     'quantity': None,
                                     'buying_price': None,
                                     'last_update': None,
                                     'lag_days': None,
                                     'shipping_cost': None,
                                     'datalimit_offset': int(val)-1}
    session['stock_filter_infos']['sort_dir'] = sort_dir
    session['stock_filter_infos']['sort'] = sort
    return jsonify({})


@app.route('/center/stock/product_sort/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_stock_product_sort(val):
    if val == session['stock_filter_infos']['sort']:
        if session['stock_filter_infos']['sort_dir'] == 'DESC':
            session['stock_filter_infos'] = {'datalimit_page': 25,
                                             'datalimit_whole': None,
                                             'product_ids': [],
                                             'quantity': None,
                                             'buying_price': None,
                                             'lag_days': None,
                                             'shipping_cost': None,
                                             'datalimit_offset': 0}
            session['stock_filter_infos']['sort_dir'] = 'ASC'
            session['stock_filter_infos']['sort'] = val
        else:
            session['stock_filter_infos'] = {'datalimit_page': 25,
                                             'datalimit_whole': None,
                                             'product_ids': [],
                                             'quantity': None,
                                             'buying_price': None,
                                             'lag_days': None,
                                             'shipping_cost': None,
                                             'datalimit_offset': 0}
            session['stock_filter_infos']['sort_dir'] = 'DESC'
            session['stock_filter_infos']['sort'] = val
    else:
        session['stock_filter_infos'] = {'datalimit_page': 25,
                                         'datalimit_whole': None,
                                         'product_ids': [],
                                         'quantity': None,
                                         'buying_price': None,
                                         'lag_days': None,
                                         'shipping_cost': None,
                                         'datalimit_offset': 0}
        session['stock_filter_infos']['sort_dir'] = 'DESC'
        session['stock_filter_infos']['sort'] = val
    return jsonify({})


@app.route('/center/stock/stock/<stock_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock_stock(stock_id):
    stock = Stock.query.filter_by(id=int(stock_id)).first()
    if session['stock_filter_infos']['sort'] in ['id', 'internal_id', 'hsp_id', 'name']:
        stock_products = db.session.query(
            Product_Stock_Attributes
        ).outerjoin(
            Product
        ).filter(
            Product_Stock_Attributes.product_id==Product.id
        ).filter(
            Product_Stock_Attributes.stock_id==stock.id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).order_by(
            getattr(Product, session['stock_filter_infos']['sort']).desc() if session['stock_filter_infos']['sort_dir'] == 'DESC'
            else getattr(Product, session['stock_filter_infos']['sort']).asc()
        ).all()
    else:
        stock_products = db.session.query(
            Product_Stock_Attributes
        ).outerjoin(
            Product
        ).filter(
            Product_Stock_Attributes.product_id==Product.id
        ).filter(
            Product_Stock_Attributes.stock_id==stock.id
        ).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).order_by(
            getattr(Product_Stock_Attributes, session['stock_filter_infos']['sort']).desc() if session['stock_filter_infos']['sort_dir'] == 'DESC'
            else getattr(Product_Stock_Attributes, session['stock_filter_infos']['sort']).asc()
        ).all()
    orders = [o for o in stock.supplier.orders if o.get_current_shipping_stat_label() in ['Kein Zustand', 'angefragt']] if stock.supplier else []
    display_products = stock_products[:25]
    if request.method == 'POST':
        if request.form['datalimit_page'] != '':
            session['stock_filter_infos']['datalimit_page'] = int(request.form['datalimit_page'])
        else:
            session['stock_filter_infos']['datalimit_page'] = 25
        if request.form['datalimit_whole'] != '':
            session['stock_filter_infos']['datalimit_whole'] = request.form['datalimit_whole']
        else:
            session['stock_filter_infos']['datalimit_whole'] = None
        id_type = request.form['id_type']
        session['stock_filter_infos']['product_id_type'] = id_type
        product_ids = []
        if request.form['product_ids'] != '':
            product_ids = request.form['product_ids']
            product_ids = product_ids.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
            pattern = ';' + '{2,}'
            product_ids = re.sub(pattern, ';', product_ids)
            if product_ids[-1] == ';':
                product_ids = product_ids[:-1]
            if id_type == 'id':
                product_ids = [int(product_id) for product_id in product_ids.split(';')]
                session['stock_filter_infos']['product_ids'] = product_ids
            elif id_type == 'Internal_ID':
                product_ids = [product_id for product_id in product_ids.split(';')]
                session['stock_filter_infos']['product_ids'] = product_ids
                filtered_products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
                product_ids = [product.id for product in filtered_products]
            else:
                product_ids = [product_id for product_id in product_ids.split(';')]
                session['stock_filter_infos']['product_ids'] = product_ids
                filtered_products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
                product_ids = [product.id for product in filtered_products]
        else:
            session['stock_filter_infos']['product_ids'] = []

        quantity_min = str_to_float(money_to_float(request.form['quantity_min']))
        quantity_max = str_to_float(money_to_float(request.form['quantity_max']))
        buying_price = str_to_float(money_to_float(request.form['buying_price']))
        last_update = request.form['last_update']
        lag_days = str_to_float(money_to_float(request.form['lag_days']))
        shipping_cost = str_to_float(money_to_float(request.form['shipping_cost']))
        session['stock_filter_infos']['quantity_min'] = quantity_min
        session['stock_filter_infos']['quantity_max'] = quantity_max
        session['stock_filter_infos']['buying_price'] = buying_price
        session['stock_filter_infos']['last_update'] = last_update
        session['stock_filter_infos']['lag_days'] = lag_days
        session['stock_filter_infos']['shipping_cost'] = shipping_cost
        if last_update:
            last_update = datetime.strptime(last_update, '%Y-%m-%d')
        else:
            last_update = None
        buying_price_operator = request.form['buying_price-operator']
        last_update_operator = request.form['last_update-operator']
        lag_days_operator = request.form['lag_days-operator']
        shipping_cost_operator = request.form['shipping_cost-operator']
        session['stock_filter_infos']['buying_price-operator'] = buying_price_operator
        session['stock_filter_infos']['last_update-operator'] = last_update_operator
        session['stock_filter_infos']['lag_days-operator'] = lag_days_operator
        session['stock_filter_infos']['shipping_cost-operator'] = shipping_cost_operator

        if session['stock_filter_infos']['sort'] in ['id', 'internal_id', 'hsp_id', 'name']:
            stock_products = db.session.query(
                Product_Stock_Attributes
            ).outerjoin(
                Product
            ).filter(
                Product_Stock_Attributes.stock_id==int(stock_id)
            ).filter(
                Product_Stock_Attributes.product_id.in_(product_ids) if product_ids else True
            ).filter(
                sign(Product_Stock_Attributes.quantity, quantity_min, '>=')
                if quantity_min is not None else True
            ).filter(
                sign(Product_Stock_Attributes.quantity, quantity_max, '<=')
                if quantity_max is not None else True
            ).filter(
                sign(Product_Stock_Attributes.buying_price, buying_price, buying_price_operator)
                if buying_price is not None else True
            ).filter(
                sign(Product_Stock_Attributes.shipping_cost, shipping_cost, shipping_cost_operator)
                if shipping_cost is not None else True
            ).filter(
                sign(Product_Stock_Attributes.lag_days, lag_days, lag_days_operator)
                if lag_days is not None else True
            ).filter(
                sign(Product_Stock_Attributes.last_seen, last_update, last_update_operator)
                if last_update is not None else True
            ).filter(
                Product_Stock_Attributes.avail_date <= datetime.now()
            ).filter(
                Product_Stock_Attributes.termination_date >= datetime.now()
            ).order_by(
                getattr(Product, session['stock_filter_infos']['sort']).desc() if session['stock_filter_infos']['sort_dir'] == 'DESC'
                else getattr(Product, session['stock_filter_infos']['sort']).asc()
            ).limit(
                session['stock_filter_infos']['datalimit_whole']
            ).all()
        else:
            stock_products = db.session.query(
                Product_Stock_Attributes
            ).outerjoin(
                Product
            ).filter(
                Product_Stock_Attributes.stock_id==int(stock_id)
            ).filter(
                Product_Stock_Attributes.product_id.in_(product_ids) if product_ids else True
            ).filter(
                sign(Product_Stock_Attributes.quantity, quantity_min, '>=')
                if quantity_min is not None else True
            ).filter(
                sign(Product_Stock_Attributes.quantity, quantity_max, '<=')
                if quantity_max is not None else True
            ).filter(
                sign(Product_Stock_Attributes.buying_price, buying_price, buying_price_operator)
                if buying_price is not None else True
            ).filter(
                sign(Product_Stock_Attributes.shipping_cost, shipping_cost, shipping_cost_operator)
                if shipping_cost is not None else True
            ).filter(
                sign(Product_Stock_Attributes.lag_days, lag_days, lag_days_operator)
                if lag_days is not None else True
            ).filter(
                sign(Product_Stock_Attributes.last_seen, last_update, last_update_operator)
                if last_update is not None else True
            ).filter(
                Product_Stock_Attributes.avail_date <= datetime.now()
            ).filter(
                Product_Stock_Attributes.termination_date >= datetime.now()
            ).order_by(
                getattr(Product_Stock_Attributes, session['stock_filter_infos']['sort']).desc() if session['stock_filter_infos']['sort_dir'] == 'DESC'
                else getattr(Product_Stock_Attributes, session['stock_filter_infos']['sort']).asc()
            ).limit(
                session['stock_filter_infos']['datalimit_whole']
            ).all()

        display_products = stock_products[session['stock_filter_infos']['datalimit_page']*session['stock_filter_infos']['datalimit_offset']:session['stock_filter_infos']['datalimit_page']*(session['stock_filter_infos']['datalimit_offset']+1)]
    return render_template('center/stock/stock.html', stock=stock, display_products=display_products, result_length=len(stock_products), orders=orders, supplier=stock.supplier)


@app.route('/center/stock/products/turnpage/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock_products_turnpage(val):
    sort_dir = session['stock_products_filter_infos']['sort_dir']
    sort = session['stock_products_filter_infos']['sort']
    session['stock_products_filter_infos'] = {'datalimit_page': 25,
                                              'datalimit_whole': None,
                                              'product_ids': [],
                                              'quantity': None,
                                              'buying_price': None,
                                              'lag_days': None,
                                              'shipping_cost': None,
                                              'datalimit_offset': int(val)-1}
    session['stock_products_filter_infos']['sort_dir'] = sort_dir
    session['stock_products_filter_infos']['sort'] = sort
    return jsonify({})


@app.route('/center/stock/stock/worker', methods=['GET', 'POST'])
@is_logged_in
@csrf.exempt
@new_pageload
@roles_required('Produkt-Management')
def center_stock_stock_worker():
    order_id = int(request.form['order_id'])
    supplier = Supplier.query.filter_by(id=int(request.form['supplier_id'])).first()
    if order_id:
        order = Order.query.filter_by(id=order_id).first()
        summed_price = order.price
    else:
        order_time = datetime.now()
        stock_id = 1
        name = supplier.get_name() + '_' + order_time.strftime('%Y_%m_%d')
        payment_method = 6
        delivery_time = None
        comment = None
        summed_price_value = 0
        order = Order(name, order_time, delivery_time, summed_price_value, 0, comment, stock_id, payment_method, supplier.id)
        db.session.add(order)
        db.session.commit()
        summed_price = 0
    max_index = int(request.form['max_index'])
    for i in range(max_index):
        product = Product.query.filter_by(id=request.form[f'p_id_{i}']).first()
        new_connection = Order_Product_Attributes(int(request.form[f'quant_{i}']), 0, float(request.form[f'price_{i}']), tax_group[product.tax_group][supplier.std_tax], order.id, product.id)
        db.session.add(new_connection)
        db.session.commit()
        summed_price += new_connection.ordered * new_connection.price
    order.price = summed_price
    db.session.commit()
    return jsonify({'status_code': 200})


@app.route('/center/stock/add_to_stock/<stock_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_stock_add_to_stock(stock_id):
    stock = Stock.query.filter_by(id=int(stock_id)).first()
    if request.method == 'POST':
        internal_id = request.form['internal_id']
        hsp_id = request.form['hsp_id']
        name = request.form['name']
        idealo_link = request.form['idealo_link']
        release_date = datetime.strptime(request.form['release_date'], '%d.%m.%Y')
        start = datetime.strptime(request.form['start'], '%Y-%m-%d')
        end = datetime.strptime(request.form['end'], '%Y-%m-%d')
        price = str_to_float(money_to_float(request.form['price']))
        quantity = str_to_int(request.form['quantity'])
        while len(hsp_id) < 13:
            hsp_id = '0' + hsp_id
        product = Product.query.filter_by(hsp_id=hsp_id).first()
        if not product:
            product = Product('EAN', hsp_id, name=name, mpn='nicht zutreffend')
            product.release_date = release_date
            db.session.add(product)
            db.session.commit()

            own_stock = Stock.query.filter_by(owned=True).first()

            product.add_basic_product_data(own_stock.id)

            idealo_cat = ProductLinkCategory.query.filter_by(name='Idealo').first()
            db.session.add(ProductLink(idealo_link, idealo_cat.id, product.id))
            db.session.commit()

            j = 0

            while j <= 1:
                file_name = 'generic_pic.jpg'
                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                j += 1

        new_product_stock_attributes = Product_Stock_Attributes('Neu & OVP', quantity, price, None, 19, 0, start, end, product.id, stock.id)
        new_product_stock_attributes.internal_id = internal_id if internal_id else None
        new_product_stock_attributes.user_generated = True
        db.session.add(new_product_stock_attributes)
        product.update_mp = True
        db.session.commit()
        flash('Angebot erfolgreich hinzugefügt!', 'success')
    return render_template('center/stock/add_to_stock.html', stock=stock)


@app.route('/center/stock/manipulate_stock/<stock_attribute_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_stock_manipulate_stock(stock_attribute_id):
    psa = Product_Stock_Attributes.query.filter_by(id=int(stock_attribute_id)).first()
    if psa.user_generated:
        if request.method == 'POST':
            psa.avail_date = datetime.strptime(request.form['start'], '%Y-%m-%d')
            psa.termination_date = datetime.strptime(request.form['end'], '%Y-%m-%d')
            psa.buying_price = str_to_float(money_to_float(request.form['price']))
            psa.quantity = str_to_int(request.form['quantity'])
            psa.product.update_mp = True
            db.session.commit()
            flash('Angebot erfolgreich editiert!', 'success')
        return render_template('center/stock/manipulate_stock.html', stock=psa.stock, psa=psa)
    else:
        flash('Unauthorisirter Zugriff', 'danger')
        return redirect(url_for('center_stock_stock', stock_id=psa.stock_id))


@app.route('/center/stock/products', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock_products():
    product_query = db.session.query(
        Product
    ).filter(
        Product.id.in_(session['stock_products_filter_infos']['product_ids']) if session['stock_products_filter_infos']['product_ids'] else True
    ).order_by(
        Product.id.desc()
    ).all()
    stocks = Stock.query.order_by(Stock.id).all()
    products = [res for res in product_query[:session['stock_products_filter_infos']['datalimit_page']]]
    result_length = len(product_query)
    if request.method == 'POST':
        if request.form['datalimit_page'] != '':
            session['stock_products_filter_infos']['datalimit_page'] = int(request.form['datalimit_page'])
        else:
            session['stock_products_filter_infos']['datalimit_page'] = 25
        if request.form['datalimit_whole'] != '':
            session['stock_products_filter_infos']['datalimit_whole'] = request.form['datalimit_whole']
        else:
            session['stock_products_filter_infos']['datalimit_whole'] = None
        id_type = request.form['id_type']
        session['stock_products_filter_infos']['product_id_type'] = id_type
        product_ids = []
        if request.form['product_ids'] != '':
            product_ids = request.form['product_ids']
            product_ids = product_ids.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
            pattern = ';' + '{2,}'
            product_ids = re.sub(pattern, ';', product_ids)
            if product_ids[-1] == ';':
                product_ids = product_ids[:-1]
            if id_type == 'id':
                product_ids = [int(product_id) for product_id in product_ids.split(';')]
                session['stock_products_filter_infos']['product_ids'] = product_ids
            elif id_type == 'Internal_ID':
                product_ids = [product_id for product_id in product_ids.split(';')]
                session['stock_products_filter_infos']['product_ids'] = product_ids
                filtered_products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
                product_ids = [product.id for product in filtered_products]
            else:
                product_ids = [product_id for product_id in product_ids.split(';')]
                session['stock_products_filter_infos']['product_ids'] = product_ids
                filtered_products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
                product_ids = [product.id for product in filtered_products]
        else:
            session['stock_products_filter_infos']['product_ids'] = []

        product_query = db.session.query(
            Product
        ).filter(
            Product.id.in_(product_ids) if product_ids else True
        ).order_by(
            Product.id.desc()
        ).limit(
            session['stock_products_filter_infos']['datalimit_whole']
        ).all()
        stocks = Stock.query.order_by(Stock.id).all()
        products = [res for res in product_query[session['stock_products_filter_infos']['datalimit_page']*session['stock_products_filter_infos']['datalimit_offset']:session['stock_products_filter_infos']['datalimit_page']*(session['stock_products_filter_infos']['datalimit_offset']+1)]]
        result_length = len(product_query)
    return render_template('center/stock/products.html', products=products, result_length=result_length, stocks=stocks)


@app.route('/center/stock/scan_receipt', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock_scan_receipt():
    suppliers = Supplier.query.all()
    return render_template('center/stock/scan_receipt.html', suppliers=suppliers)


@app.route('/center/stock/scan_receipt/transfer', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Produkt-Management')
def center_stock_scan_receipt_transfer():
    data = request.get_json()
    orders = Order.query.filter(
        Order.order_time >= datetime.now()-timedelta(days=30)
    ).join(ShippingStatus_Log).all()
    order_ids = [order.id for order in orders if order.get_current_shipping_stat().label == 'bestellt']
    query = db.session.query(Supplier, Order, Order_Product_Attributes).filter(
        Supplier.id == Order.supplier_id
    ).filter(
        Order_Product_Attributes.order_id == Order.id
    ).filter(
        Supplier.id==int(data['supplier_id'])
    ).filter(
        Order.id.in_(order_ids)
    ).order_by(
        Order.order_time
    ).all()
    try:
        own_stock = Stock.query.filter_by(owned=True).first()
        supplier = Supplier.query.filter_by(id=int(data['supplier_id'])).first()
        now = datetime.now()
        sr = StockReceipt(f'{supplier.get_name()}_{datetime.now().strftime("%Y_%m_%d-%H_%M")}', now, 0, 0, None, own_stock.id, supplier.id)
        db.session.add(sr)
        db.session.commit()
        scans = data['scans']
        for key in scans:
            scans[key] = int(scans[key])
            p = Product.query.filter_by(hsp_id=key).first()
            if not p:
                p = Product('EAN', key, name='neues Produkt', mpn='nicht zutreffend')
                db.session.add(p)
                db.session.commit()
                p.add_basic_product_data(own_stock.id)
                j = 0
                while j <= 1:
                    file_name = 'generic_pic.jpg'
                    db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                    j += 1
            db.session.add(PSR_Attributes(scans[key], 0, .19, sr.id, p.id))
            db.session.commit()
        for sup, o, opa in query:
            if opa.product.hsp_id in scans:
                diff = opa.ordered - opa.shipped if opa.shipped is not None else opa.ordered
                add = min(diff, scans[opa.product.hsp_id])
                if add > 0:
                    opa.shipped = opa.shipped + add if opa.shipped is not None else add
                    scans[opa.product.hsp_id] -= add
                    if scans[opa.product.hsp_id] == 0:
                        del scans[opa.product.hsp_id]
                    db.session.commit()
        if scans:
            order = Order(f'Wareneingang_{supplier.get_name()}_{datetime.now().strftime("%Y_%m_%d-%H_%M")}', now, None, 0, 0, None, own_stock.id, 6, supplier.id)
            db.session.add(order)
            db.session.commit()
            for key in scans:
                p = Product.query.filter_by(hsp_id=key).first()
                new_connection = Order_Product_Attributes(scans[key], scans[key], 0, tax_group[p.tax_group][supplier.std_tax], order.id, p.id)
                db.session.add(new_connection)
                db.session.commit()
            order.price = order.gross_price()
            db.session.commit()
        return jsonify({'msg': 'success'})
    except Exception as e:
        print(e)
        return jsonify({'msg': str(e)})


@app.route('/center/stock/receipts', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock_receipts():
    srs = StockReceipt.query.order_by(StockReceipt.delivery_time.desc()).all()
    return render_template('center/stock/receipts.html', srs=srs)


@app.route('/center/stock/receipt/delete/<sr_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock_receipt_delete(sr_id):
    sr = StockReceipt.query.filter_by(id=sr_id).first()
    for p in sr.products:
        db.session.delete(p)
    db.session.delete(sr)
    db.session.commit()
    return redirect(url_for('center_stock_receipts'))


@app.route('/center/stock/receipt/<sr_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_stock_receipt(sr_id):
    own_stock = Stock.query.filter_by(owned=True).order_by(Stock.id).first()
    suppliers = Supplier.query.all()
    stocks = Stock.query.all()
    sr = StockReceipt.query.filter_by(id=sr_id).first()
    if request.method == 'POST':
        sr.name = request.form['name']
        try:
            sr.delivery_time = datetime.strptime(request.form['delivery_time'], "%Y-%m-%d")
        except:
            sr.delivery_time = None
        sr.stock_id = int(request.form['stock'])
        sr.supplier_id = int(request.form['supplier'])
        sr.comment = request.form['comment']
        split_additional_cost = request.form['split_additional_cost']
        summed_price_value = str_to_float(money_to_float(request.form['summed_price_value']))
        try:
            if split_additional_cost == '1':
                sr.additional_cost = 0
            else:
                additional_cost = request.form['additional_cost']
                sr.additional_cost = str_to_float(money_to_float(additional_cost))
        except:
            sr.additional_cost = 0
        sr.price = summed_price_value
        db.session.commit()

        counter = int(request.form['counter'])
        print(request.form['removed'])
        removed = [int(removed_article) for removed_article in request.form['removed'].split(',')[-1]] if request.form['removed'] else []

        for product in sr.products:
            db.session.delete(product)
            db.session.commit()

        i = 0
        product_ids = []
        while i < counter:
            if i not in removed:
                p_hsp_id = request.form['hsp_id' + str(i)]
                p_name = request.form['prod_name' + str(i)]
                p_quant = request.form['quant' + str(i)]
                p_tax = float(request.form['tax' + str(i)])/100
                p_price = request.form['net_price' + str(i)]
                while len(p_hsp_id) < 13:
                    p_hsp_id = '0' + p_hsp_id
                product = Product.query.filter_by(hsp_id=p_hsp_id).first()
                if not product:
                    product = Product('EAN', p_hsp_id, name=p_name, mpn='nicht zutreffend')
                    db.session.add(product)
                    db.session.commit()
                    product.add_basic_product_data(own_stock.id)
                    j = 0
                    while j <= 1:
                        file_name = 'generic_pic.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                        j += 1

                new_connection = PSR_Attributes(p_quant, p_price, p_tax, sr.id, product.id)
                db.session.add(new_connection)
                db.session.commit()
                product_ids.append(product.id)
            i += 1
        sr.price = sr.gross_price()
        db.session.commit()

        flash('Bearbeitung abgeschlossen.', 'success')
    return render_template('center/stock/receipt.html', sr=sr, suppliers=suppliers, stocks=stocks)


#####################################################################################

#####################################   ORDER   #####################################

#####################################################################################


@app.route('/center/orders', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders():
    orders = Order.query.order_by(Order.order_time.desc()).all()
    summed_price = sum([order.price for order in orders])
    summed_additional_cost = sum([order.additional_cost for order in orders])
    result_dict = {'num_results': len(orders),
                   'summed_price': summed_price,
                   'summed_additional_cost': summed_additional_cost}
    suppliers = Supplier.query.all()
    names = Order.query.with_entities(func.count(Order.supplier_id), Order.name).group_by(Order.name).all()
    names = [name.name for name in names]
    if request.method == 'POST':
        if request.form['checker'] == 'filter':
            filtered_names = request.form.getlist('name_filter')
            filtered_suppliers = request.form.getlist('supplier_filter')
            filtered_suppliers = [int(supplier_id) for supplier_id in filtered_suppliers]

            start = request.form['start']
            end = request.form['end']
            if start == '':
                start_date = datetime.strptime('2020-01-01', '%Y-%m-%d')
            else:
                start_date = datetime.strptime(start, '%Y-%m-%d')
            if end == '':
                end_date = datetime.strptime('3000-01-01', '%Y-%m-%d')
            else:
                end_date = datetime.strptime(end, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

            if start == '' and end == '':
                orders = Order.query.order_by(Order.order_time.desc()). \
                    filter(Order.name.in_(filtered_names)).\
                    filter(Order.supplier_id.in_(filtered_suppliers)).all()
            else:
                orders = Order.query.order_by(Order.order_time.desc()). \
                    filter(end_date >= Order.order_time). \
                    filter(Order.order_time >= start_date). \
                    filter(Order.name.in_(filtered_names)). \
                    filter(Order.supplier_id.in_(filtered_suppliers)).all()
            summed_price = sum([order.price for order in orders])
            summed_additional_cost = sum([order.additional_cost for order in orders])
            result_dict = {'num_results': len(orders),
                           'summed_price': summed_price,
                           'summed_additional_cost': summed_additional_cost}
            return render_template('center/orders/index.html', orders=orders, result_dict=result_dict,
                                   suppliers=suppliers, filtered_names=filtered_names, names=names,
                                   filtered_suppliers=filtered_suppliers)
    return render_template('center/orders/index.html', orders=orders, result_dict=result_dict, suppliers=suppliers,
                           names=names, filtered_names=names,
                           filtered_suppliers=[supplier.id for supplier in suppliers])


@app.route('/center/orders/upload_system_order/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_upload_system_order():
    supplier = Supplier.query.filter_by(firmname='Lager').first()
    last_system_order = Order.query.filter_by(supplier_id=supplier.id).order_by(Order.order_time.desc()).first()
    order_time = last_system_order.order_time
    f = request.files['csv']
    if not f:
        supplier = Supplier.query.filter_by(firmname='Lager').first()
        own_stock = Stock.query.filter_by(owned=True).first()
        payment_method = PaymentMethod.query.filter_by(name='-').first()
        neworder = Order('Nullbestellung', datetime.now(), datetime.now(), None, 0, None, own_stock.id, payment_method.id, supplier.id)
        db.session.add(neworder)
        db.session.commit()
        summed_cost = 0

        products = Product.query.order_by(Product.id).all()

        url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"
        request_quant = 250
        i = 1
        while i * request_quant < len(products):
            print(i)
            xml = """<?xml version="1.0" encoding="utf-8"?>
                <Request>
                    <AfterbuyGlobal>
                        <PartnerID><![CDATA[1000007048]]></PartnerID>
                        <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                        <UserID><![CDATA[Lotusicafe]]></UserID>
                        <UserPassword><![CDATA[210676After251174]]></UserPassword>
                        <CallName>GetShopProducts</CallName>
                        <DetailLevel>12</DetailLevel>
                        <ErrorLanguage>DE</ErrorLanguage>
                    </AfterbuyGlobal>
                    <MaxShopItems>""" + str(request_quant) + """</MaxShopItems>
                    <DataFilter>
                    <Filter>
                        <FilterName>ProductID</FilterName>
                        <FilterValues>\n"""
            for product in products[(i - 1) * request_quant:i * request_quant]:
                xml += """<FilterValue>""" + product.internal_id + """</FilterValue>\n"""
            xml += """</FilterValues>
                </Filter>
                </DataFilter>
                </Request>
                """
            headers = {'Content-Type': 'application/xml'}
            r = requests.get(url, data=xml, headers=headers)

            tree = ET.fromstring(r.text)

            product_query = [item for item in tree.iter() if item.tag == 'Product']
            for prod in product_query:
                prod_id = [item.text for item in prod.iter() if item.tag == 'ProductID'][0]
                quant = [item.text for item in prod.iter() if item.tag == 'AuctionQuantity'][0]
                oth_quant = [item.text for item in prod.iter() if item.tag == 'Quantity'][0]
                if int(quant)+int(oth_quant)>0:
                    product = Product.query.filter_by(internal_id=prod_id).first()
                    if product:
                        av_bp = product.get_own_buying_price_from(order_time)
                        check_products = Product.query.filter_by(hsp_id=product.hsp_id).order_by(Product.internal_id).all()
                        n = len(check_products)
                        j = 0
                        while av_bp == None and j < n:
                            av_bp = check_products[j].get_own_buying_price_from(order_time)
                            j += 1
                        if av_bp == None:
                            print('Kein Ausweich-Produkt mit gleicher EAN gefunden')
                            print(product.id)
                            print('---------------------')
                        else:
                            product.buying_price = av_bp
                            new_order_product_attributes = Order_Product_Attributes(int(quant)+int(oth_quant), int(quant)+int(oth_quant), av_bp, 19, neworder.id, product.id)
                            summed_cost += (int(quant) + int(oth_quant)) * av_bp
                            db.session.add(new_order_product_attributes)
                            db.session.commit()
            i += 1

        xml = """<?xml version="1.0" encoding="utf-8"?>
                    <Request>
                        <AfterbuyGlobal>
                            <PartnerID><![CDATA[1000007048]]></PartnerID>
                            <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                            <UserID><![CDATA[Lotusicafe]]></UserID>
                            <UserPassword><![CDATA[210676After251174]]></UserPassword>
                            <CallName>GetShopProducts</CallName>
                            <DetailLevel>12</DetailLevel>
                            <ErrorLanguage>DE</ErrorLanguage>
                        </AfterbuyGlobal>
                        <MaxShopItems>""" + str(request_quant) + """</MaxShopItems>
                        <DataFilter>
                        <Filter>
                            <FilterName>ProductID</FilterName>
                            <FilterValues>\n"""
        for product in products[(i - 1) * request_quant:i * request_quant]:
            xml += """<FilterValue>""" + product.internal_id + """</FilterValue>\n"""
        xml += """</FilterValues>
                    </Filter>
                    </DataFilter>
                    </Request>
                    """
        headers = {'Content-Type': 'application/xml'}
        r = requests.get(url, data=xml, headers=headers)

        tree = ET.fromstring(r.text)

        product_query = [item for item in tree.iter() if item.tag == 'Product']
        for prod in product_query:
            prod_id = [item.text for item in prod.iter() if item.tag == 'ProductID'][0]
            quant = [item.text for item in prod.iter() if item.tag == 'AuctionQuantity'][0]
            oth_quant = [item.text for item in prod.iter() if item.tag == 'Quantity'][0]
            if int(quant) + int(oth_quant) > 0:
                product = Product.query.filter_by(internal_id=prod_id).first()
                if product:
                    av_bp = product.get_own_buying_price_from(order_time)
                    check_products = Product.query.filter_by(hsp_id=product.hsp_id).order_by(Product.internal_id).all()
                    n = len(check_products)
                    j = 0
                    while av_bp == None and j < n:
                        av_bp = check_products[j].get_own_buying_price_from(order_time)
                        j += 1
                    if av_bp == None:
                        print('Kein Ausweich-Produkt mit gleicher EAN gefunden')
                        print(product.id)
                        print('---------------------')
                    else:
                        psa = Product_Stock_Attributes.query.filter_by(product_id=product.id, stock_id=1).first()
                        psa.buying_price = av_bp
                        product.buying_price = av_bp
                        new_order_product_attributes = Order_Product_Attributes(int(quant) + int(oth_quant), int(quant) + int(oth_quant), av_bp, 19, neworder.id, product.id)
                        summed_cost += (int(quant) + int(oth_quant)) * av_bp
                        db.session.add(new_order_product_attributes)
                        db.session.commit()

        newlog = ShippingStatus_Log(2, 'abgeschlossen', '', neworder.id)
        newlog.init_date = datetime.now()
        db.session.add(newlog)
        db.session.commit()
        neworder.price = summed_cost
        db.session.commit()

        url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"
        request_quant = 250
        i = 1
        while i * request_quant < len(products):
            xml = '''<?xml version="1.0" encoding="UTF-8"?>
                                        <Request>
                                            <AfterbuyGlobal>
                                                <PartnerID><![CDATA[1000007048]]></PartnerID>
                                                <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                                                <UserID><![CDATA[Lotusicafe]]></UserID>
                                                <UserPassword><![CDATA[210676After251174]]></UserPassword>
                                                <CallName>UpdateShopProducts</CallName>
                                                <DetailLevel>0</DetailLevel>
                                                <ErrorLanguage>DE</ErrorLanguage>
                                            </AfterbuyGlobal>
                                            <Products>\n'''
            for product in products[(i - 1) * request_quant:i * request_quant]:
                try:
                    xml += '''<Product>
                                                <ProductIdent>
                                                    <ProductInsert>0</ProductInsert>
                                                    <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                                </ProductIdent>
                                                <BuyingPrice>''' + float_to_comma(float(("%.2f" % product.get_own_buying_price()))) + '''</BuyingPrice>
                                            </Product>\n'''
                except:
                    pass
            xml += '''</Products>
                                </Request>'''

            xml = xml.encode('utf-8')

            headers = {'Content-Type': 'application/xml; charset=utf-8'}
            requests.get(url, data=xml, headers=headers)

            i += 1

        xml = '''<?xml version="1.0" encoding="UTF-8"?>
                                    <Request>
                                        <AfterbuyGlobal>
                                            <PartnerID><![CDATA[1000007048]]></PartnerID>
                                            <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                                            <UserID><![CDATA[Lotusicafe]]></UserID>
                                            <UserPassword><![CDATA[210676After251174]]></UserPassword>
                                            <CallName>UpdateShopProducts</CallName>
                                            <DetailLevel>0</DetailLevel>
                                            <ErrorLanguage>DE</ErrorLanguage>
                                        </AfterbuyGlobal>
                                        <Products>\n'''
        for product in products[(i - 1) * request_quant:i * request_quant]:
            try:
                xml += '''<Product>
                                            <ProductIdent>
                                                <ProductInsert>0</ProductInsert>
                                                <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                            </ProductIdent>
                                            <BuyingPrice>''' + float_to_comma(float(("%.2f" % product.get_own_buying_price()))) + '''</BuyingPrice>
                                        </Product>\n'''
            except:
                pass
        xml += '''</Products>
                            </Request>'''
        i += 1

        xml = xml.encode('utf-8')

        headers = {'Content-Type': 'application/xml; charset=utf-8'}
        requests.get(url, data=xml, headers=headers)
        flash('Neue Nullbestellung generiert', 'success')
    else:
        if f.name == 'csv':
            stream = io.StringIO(f.stream.read().decode("utf8"))
            csv_input = csv.reader(stream, delimiter=';')
            supplier = Supplier.query.filter_by(firmname='Lager').first()
            own_stock = Stock.query.filter_by(owned=True).first()
            payment_method = PaymentMethod.query.filter_by(name='-').first()
            neworder = Order('Nullbestellung', datetime.now(), datetime.now(), None, 0, None, own_stock.id, payment_method.id, supplier.id)
            db.session.add(neworder)
            db.session.commit()
            summed_cost = 0
            product_ids = []
            for row in csv_input:
                try:
                    internal_id = int(row[0])
                    quant = int(row[1])
                    product = Product.query.filter_by(internal_id=str(internal_id)).first()
                    if product:
                        product_ids.append(product.id)
                        av_bp = product.get_own_buying_price_from(order_time)
                        check_products = Product.query.filter_by(hsp_id=product.hsp_id).order_by(Product.internal_id).all()
                        n = len(check_products)
                        i = 0
                        while av_bp == None and i < n:
                            av_bp = check_products[i].get_own_buying_price_from(order_time)
                            i += 1
                        if av_bp == None:
                            print('Kein Ausweich-Produkt mit gleicher EAN gefunden')
                            print(product.id)
                            print('---------------------')
                        else:
                            psa = Product_Stock_Attributes.query.filter_by(product_id=product.id, stock_id=1).first()
                            psa.buying_price = av_bp
                            product.buying_price = av_bp
                            new_order_product_attributes = Order_Product_Attributes(int(quant), int(quant), av_bp, 19, neworder.id, product.id)
                            summed_cost += int(quant) * av_bp
                            db.session.add(new_order_product_attributes)
                            db.session.commit()
                except:
                    pass
            newlog = ShippingStatus_Log(2, 'abgeschlossen', '', neworder.id)
            newlog.init_date = datetime.now()
            db.session.add(newlog)
            db.session.commit()
            neworder.price = summed_cost
            db.session.commit()

            products = Product.query.filter(Product.id.in_(product_ids)).all()
            url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"
            request_quant = 250
            i = 1
            while i * request_quant < len(products):
                xml = '''<?xml version="1.0" encoding="UTF-8"?>
                                                    <Request>
                                                        <AfterbuyGlobal>
                                                            <PartnerID><![CDATA[1000007048]]></PartnerID>
                                                            <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                                                            <UserID><![CDATA[Lotusicafe]]></UserID>
                                                            <UserPassword><![CDATA[210676After251174]]></UserPassword>
                                                            <CallName>UpdateShopProducts</CallName>
                                                            <DetailLevel>0</DetailLevel>
                                                            <ErrorLanguage>DE</ErrorLanguage>
                                                        </AfterbuyGlobal>
                                                        <Products>\n'''
                for product in products[(i - 1) * request_quant:i * request_quant]:
                    try:
                        xml += '''<Product>
                                                            <ProductIdent>
                                                                <ProductInsert>0</ProductInsert>
                                                                <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                                            </ProductIdent>
                                                            <BuyingPrice>''' + float_to_comma(float(("%.2f" % product.get_own_buying_price()))) + '''</BuyingPrice>
                                                        </Product>\n'''
                    except:
                        pass
                xml += '''</Products>
                                            </Request>'''

                xml = xml.encode('utf-8')

                headers = {'Content-Type': 'application/xml; charset=utf-8'}
                requests.get(url, data=xml, headers=headers)

                i += 1

            xml = '''<?xml version="1.0" encoding="UTF-8"?>
                                                <Request>
                                                    <AfterbuyGlobal>
                                                        <PartnerID><![CDATA[1000007048]]></PartnerID>
                                                        <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                                                        <UserID><![CDATA[Lotusicafe]]></UserID>
                                                        <UserPassword><![CDATA[210676After251174]]></UserPassword>
                                                        <CallName>UpdateShopProducts</CallName>
                                                        <DetailLevel>0</DetailLevel>
                                                        <ErrorLanguage>DE</ErrorLanguage>
                                                    </AfterbuyGlobal>
                                                    <Products>\n'''
            for product in products[(i - 1) * request_quant:i * request_quant]:
                try:
                    xml += '''<Product>
                                                        <ProductIdent>
                                                            <ProductInsert>0</ProductInsert>
                                                            <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                                        </ProductIdent>
                                                        <BuyingPrice>''' + float_to_comma(float(("%.2f" % product.get_own_buying_price()))) + '''</BuyingPrice>
                                                    </Product>\n'''
                except:
                    pass
            xml += '''</Products>
                                        </Request>'''
            i += 1

            xml = xml.encode('utf-8')

            headers = {'Content-Type': 'application/xml; charset=utf-8'}
            requests.get(url, data=xml, headers=headers)

            flash('Neue Nullbestellung generiert', 'success')
        else:
            flash("Bitte wähle eine CSV-Datei aus!", 'danger')
    return redirect(url_for('center_orders'))


@app.route('/center/orders/upload_csv_order/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_upload_csv_order():
    f = request.files['csv']
    error_list = []
    out_rows = [['ID', 'Name', 'Anzahl', 'Steuer', 'Netto-Preis', 'Brutto-Preis', 'Gesamt-Preis', 'Idealo-Link', 'Afterbuy-ID']]
    if not f:
        flash('Keine Datei vorhanden!', 'danger')
    else:
        if f.name == 'csv':
            stream = io.StringIO(f.stream.read().decode("utf8"))
            csv_input = csv.reader(stream, delimiter=';')
            neworder = Order('', datetime.now(), datetime.now(), None, 0, None, None, None, None)
            id_type = request.form['id_type']
            db.session.add(neworder)
            db.session.commit()
            first_row = True
            for row in csv_input:
                if first_row:
                    first_row = False
                    continue
                try:
                    p_id = row[0]
                    if p_id in ['', ' ', '  ']:
                        continue
                    if id_type == 'hsp_id':
                        while len(p_id) < 13:
                            p_id = '0' + p_id
                    name = row[1]
                    quant = str_to_int(row[2])
                    tax = str_to_float(prc_to_float(row[3]))
                    net_price = str_to_float(money_to_float(row[4]))
                    gross_price = str_to_float(money_to_float(row[5]))
                    full_price = str_to_float(money_to_float(row[6]))
                    idealo_link = row[7]
                    if id_type in ['id', 'internal_id', 'hsp_id']:
                        product = Product.query.filter(getattr(Product, id_type)==p_id).first()
                    else:
                        psa = Product_Stock_Attributes.query.filter_by(internal_id=p_id).first()
                        product = psa.product
                    if (quant is None
                    or tax is None
                    or (net_price is None and gross_price is None and full_price is None)):
                        error_list.append(p_id)
                        continue
                    else:
                        if product is None:
                            if id_type in ['id', 'internal_id', 'vitrex_id']:
                                error_list.append(p_id)
                                continue
                            product = Product('EAN', p_id, name=name, mpn='nicht zutreffend')
                            db.session.add(product)
                            db.session.commit()

                            own_stock = Stock.query.filter_by(owned=True).first()

                            product.add_basic_product_data(own_stock.id)

                            if idealo_link:
                                idealo_cat = ProductLinkCategory.query.filter_by(name='Idealo').first()
                                db.session.add(ProductLink(idealo_link, idealo_cat.id, product.id))
                                db.session.commit()

                            j = 0

                            while j <= 1:
                                file_name = 'generic_pic.jpg'
                                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                                j += 1
                        if net_price is None:
                            if gross_price is None:
                                net_price = full_price/quant/(1+tax/100)
                            else:
                                net_price = gross_price/(1+tax/100)
                        new_order_product_attributes = Order_Product_Attributes(int(quant), int(quant), net_price, tax, neworder.id, product.id)
                        db.session.add(new_order_product_attributes)
                        db.session.commit()
                        out_rows.append(row+[product.internal_id])
                except:
                    pass
            neworder.price = neworder.gross_price()
            db.session.commit()
            flash('Neue Bestellung generiert', 'success')

            f = io.StringIO()
            writer = csv.writer(f, delimiter=';')

            for row in out_rows:
                writer.writerow(row)

            response = Response(u'\uFEFF' + f.getvalue(), mimetype='file/csv', )
            response.headers['Content-Disposition'] = 'attachment; filename=order.csv'
            response.headers["Content-type"] = "text/csv"

            return response
        else:
            flash("Bitte wähle eine CSV-Datei aus!", 'danger')
    return redirect(url_for('center_orders'))


@app.route('/center/orders/delete_order/<order_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_delete_order(order_id):
    order = Order.query.filter_by(id=int(order_id)).first()
    if order.get_current_shipping_stat():
        if order.get_current_shipping_stat().label == 'abgeschlossen':
            flash('Abgeschlossene Bestellungen können nicht gelöscht werden', 'danger')
        else:
            for product in order.products:
                db.session.delete(product)
                db.session.commit()
            db.session.delete(order)
            db.session.commit()
    else:
        for product in order.products:
            db.session.delete(product)
            db.session.commit()
        db.session.delete(order)
        db.session.commit()
    return redirect(url_for('center_orders'))


@app.route('/center/orders/split_order/<order_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_split_order(order_id):
    orig_order = Order.query.filter_by(id=int(order_id)).first()
    supplier = Supplier.query.filter_by(id=orig_order.supplier_id).first()
    name = f'Rückstand_{supplier.get_name()}'
    order_time = datetime.now()
    stock_id = 1
    payment_method = 6
    delivery_time = None
    comment = None
    summed_price_value = 0
    order = Order(name, order_time, delivery_time, summed_price_value, 0, comment, stock_id, payment_method, supplier.id)
    db.session.add(order)
    db.session.commit()
    order.price = 0
    db.session.commit()
    one_p = False
    for opa in orig_order.products:
        if opa.ordered - opa.shipped > 0:
            one_p = True
            summed_price_value += opa.ordered * opa.price
            new_connection = Order_Product_Attributes(opa.ordered - opa.shipped, 0, opa.price, tax_group[opa.product.tax_group][supplier.std_tax], order.id, opa.product.id)
            db.session.add(new_connection)
            orig_order.price -= opa.ordered * opa.price * (1 + opa.prc_tax/100)
            opa.ordered = opa.shipped
            if opa.ordered == 0:
                db.session.delete(opa)
            db.session.commit()
    if one_p is False:
        db.session.delete(order)
    else:
        orig_order.name = f'Wareneingang_{supplier.get_name()}_{datetime.now().strftime("%Y_%m_%d-%H_%M")}'
        newlog = ShippingStatus_Log(2, 'geliefert', '', orig_order.id)
        newlog.init_date = datetime.now()
        db.session.add(newlog)
        order.price = summed_price_value
        newlog = ShippingStatus_Log(2, 'bestellt', '', order.id)
        newlog.init_date = datetime.now()
        db.session.add(newlog)
        db.session.commit()
    db.session.commit()
    return redirect(url_for('center_orders'))


@app.route('/center/orders/merge_orders/<order1_id>,<order2_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_merge_orders(order1_id, order2_id):
    # PROBLEM: VERSCHIEDENE EKS!
    order_1 = Order.query.filter_by(id=int(order1_id)).first()
    order_2 = Order.query.filter_by(id=int(order2_id)).first()
    if order_1.supplier_id != order_2.supplier_id:
        flash('Die Lieferanten stimmen nicht überein.', 'danger')
    else:
        order_1_p_ids = [(opa.product_id, opa.price) for opa in order_1.products]
        for opa in order_2.products:
            if (opa.product_id, opa.price) in order_1_p_ids:
                opa_0 = Order_Product_Attributes.query.filter_by(product_id=opa.product_id, order_id=order_1.id, price=opa.price).first()
                opa_0.ordered += opa.ordered
                opa_0.shipped += opa.shipped
                order_1.price += opa.ordered * opa.price * (1 + opa.prc_tax/100)
                db.session.commit()
                db.session.delete(opa)
            else:
                opa.order_id = order_1.id
                order_1.price += opa.ordered * opa.price * (1 + opa.prc_tax/100)
            db.session.commit()
        db.session.delete(order_2)
        db.session.commit()
    return redirect(url_for('center_orders'))


@app.route('/center/orders/allorders', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_allorders():
    products = []
    if request.method == 'POST':
        id_type = request.form['id_type']
        if request.form['product_ids'] != '':
            product_ids = request.form['product_ids']
            product_ids = product_ids.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
            pattern = ';' + '{2,}'
            product_ids = re.sub(pattern, ';', product_ids)
            if product_ids[-1] == ';':
                product_ids = product_ids[:-1]
            if id_type == 'id':
                product_ids = [int(product_id) for product_id in product_ids.replace(' ', '').split(';')]
                products = Product.query.filter(Product.id.in_(product_ids)).all()
            elif id_type == 'Internal_ID':
                product_ids = [product_id for product_id in product_ids.replace(' ', '').split(';')]
                products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
            else:
                product_ids = [product_id for product_id in product_ids.replace(' ', '').split(';')]
                products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
        else:
            session['product_filter_infos']['product_ids'] = []
    return render_template('center/orders/allorders.html', products=products)


@app.route('/center/orders/addorder', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_addorder():
    stocks = Stock.query.filter_by(owned=True).all()
    suppliers = Supplier.query.all()
    payment_methods = PaymentMethod.query.all()
    if request.method == 'POST':
        idealo_cat = ProductLinkCategory.query.filter_by(name='Idealo').first()
        name = request.form['name']
        afterbuy_id = request.form['afterbuy_id']
        order_time = request.form['order_time']
        stock = request.form['stock']
        supplier = request.form['supplier']
        payment_method = request.form['payment_method']
        splitted_additional_cost = request.form['splitted_additional_cost']
        delivery_time = request.form['delivery_time']
        comment = request.form['comment']
        summed_price_value = str_to_float(money_to_float(request.form['summed_price_value']))
        try:
            if splitted_additional_cost == '1':
                additional_cost = 0
            else:
                additional_cost = request.form['additional_cost']
                additional_cost = str_to_float(money_to_float(additional_cost))
        except:
            additional_cost = 0
        try:
            delivery_time = datetime.strptime(delivery_time, "%Y-%m-%d")
        except:
            delivery_time = None
        order = Order(name, order_time, delivery_time, summed_price_value, additional_cost, comment,
                      int(stock), int(payment_method), int(supplier))
        order.afterbuy_id = afterbuy_id if afterbuy_id else None
        db.session.add(order)
        db.session.commit()
        counter = int(request.form['counter'])
        removed = [int(removed_product) for removed_product in request.form['removed'].split(',')]
        i=1
        while i < counter:
            if i not in removed:
                prod_hsp_id = request.form['hsp_id'+str(i)]
                prod_name = request.form['prod_name'+str(i)]
                idealo_link = request.form['idealo_link'+str(i)]
                prod_quant = request.form['quant'+str(i)]
                prod_prc_tax = request.form['prc_tax'+str(i)]
                prod_price = request.form['net_price'+str(i)]
                while len(prod_hsp_id)<13:
                    prod_hsp_id = '0'+prod_hsp_id
                product = Product.query.filter_by(hsp_id=prod_hsp_id).first()
                if not product:
                    product = Product('EAN', prod_hsp_id, name=prod_name, mpn='nicht zutreffend')
                    db.session.add(product)
                    db.session.commit()

                    own_stock = Stock.query.filter_by(owned=True).first()
                    product.add_basic_product_data(own_stock.id)
                    db.session.add(ProductLink(idealo_link, idealo_cat.id, product.id))
                    db.session.commit()
                    j = 0
                    while j <= 1:
                        file_name = 'generic_pic.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                        j += 1

                new_connection = Order_Product_Attributes(prod_quant, 0, prod_price, prod_prc_tax, order.id, product.id)
                db.session.add(new_connection)
                db.session.commit()
            i+=1
        order.price = order.gross_price()
        db.session.commit()
        return redirect(url_for('center_orders_order', order_id=order.id))
    return render_template('center/orders/addorder.html', stocks=stocks, suppliers=suppliers, payment_methods=payment_methods)


@app.route('/center/orders/order/<order_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_order(order_id):
    stocks = Stock.query.filter_by(owned=True).all()
    suppliers = Supplier.query.all()
    payment_methods = PaymentMethod.query.all()
    order = Order.query.filter_by(id=int(order_id)).first()
    os = Order.query.filter_by(supplier_id=order.supplier.id).order_by(Order.id.desc()).all()
    orders = []
    for o in os:
        if o.get_current_shipping_stat():
            if o.get_current_shipping_stat().label != 'abgeschlossen':
                orders.append(o)
        else:
            orders.append(o)
    own_stock = Stock.query.filter_by(owned=True).first()
    i=1
    for product in order.products:
        product.index = i
        i+=1
    if request.method == 'POST':
        supplier = Supplier.query.filter_by(firmname='Lager').first()
        lso = Order.query.filter_by(supplier_id=supplier.id).order_by(Order.order_time.desc()).first()
        lso_p_ids = [p.product_id for p in lso.products]
        name = request.form['name']
        afterbuy_id = request.form['afterbuy_id']
        order_time = request.form['order_time']
        stock = request.form['stock']
        supplier = request.form['supplier']
        payment_method = request.form['payment_method']
        splitted_additional_cost = request.form['splitted_additional_cost']
        payment_status = request.form['payment_status']
        payment_status_comment = request.form['payment_status_comment']
        delivery_time = request.form['delivery_time']
        shipping_status = request.form['shipping_status']
        shipping_status_comment = request.form['shipping_status_comment']
        comment = request.form['comment']
        summed_price_value = str_to_float(money_to_float(request.form['summed_price_value']))

        order.order_time = datetime.strptime(order_time, "%Y-%m-%d")
        order.buyer_id = int(session['user_id'])
        order.stock_id = int(stock)
        order.supplier_id = int(supplier)
        order.payment_method_id = int(payment_method)
        if payment_status != '':
            if order.get_current_payment_stat():
                if payment_status != order.get_current_payment_stat().label:
                    db.session.add(PaymentStatus_Log(session['user_id'], payment_status, payment_status_comment,
                                                     order.id))
            else:
                db.session.add(PaymentStatus_Log(session['user_id'], payment_status, payment_status_comment, order.id))

        add_to_stock = 0
        if shipping_status != '':
            if order.get_current_shipping_stat():
                if shipping_status != order.get_current_shipping_stat().label:
                    if shipping_status == 'abgeschlossen':
                        add_to_stock = 1
                    elif order.get_current_shipping_stat().label == 'abgeschlossen':
                        add_to_stock = -1
                    db.session.add(ShippingStatus_Log(session['user_id'], shipping_status, shipping_status_comment,
                                                      order.id))
            else:
                if shipping_status == 'abgeschlossen':
                    add_to_stock = 1
                db.session.add(ShippingStatus_Log(session['user_id'], shipping_status, shipping_status_comment,
                                                  order.id))

        order.name = name if name != '' else None
        order.afterbuy_id = afterbuy_id if afterbuy_id != '' else None
        order.comment = comment if comment != '' else None
        try:
            if splitted_additional_cost == '1':
                order.additional_cost = 0
            else:
                additional_cost = request.form['additional_cost']
                order.additional_cost = str_to_float(money_to_float(additional_cost))
        except:
            order.additional_cost = 0
        try:
            order.delivery_time = datetime.strptime(delivery_time, "%Y-%m-%d")
        except:
            order.delivery_time = None
        order.price = summed_price_value
        db.session.add(order)
        db.session.commit()

        counter = int(request.form['counter'])
        removed = [int(removed_article) for removed_article in request.form['removed'].split(',')]

        for order_product in order.products:
            db.session.delete(order_product)
            db.session.commit()

        i=1
        product_ids = []
        while i < counter:
            if i not in removed:
                prod_hsp_id = request.form['hsp_id'+str(i)]
                prod_name = request.form['prod_name'+str(i)]
                prod_quant = request.form['quant'+str(i)]
                prod_shipped = request.form['shipped'+str(i)]
                prod_prc_tax = request.form['prc_tax'+str(i)]
                prod_price = request.form['net_price'+str(i)]
                while len(prod_hsp_id)<13:
                    prod_hsp_id = '0'+prod_hsp_id
                product = Product.query.filter_by(hsp_id=prod_hsp_id).first()
                if not product:
                    product = Product('EAN', prod_hsp_id, name=prod_name, mpn='nicht zutreffend')
                    db.session.add(product)
                    db.session.commit()

                    product.add_basic_product_data(own_stock.id)

                    j = 0

                    while j <= 1:
                        file_name = 'generic_pic.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                        j += 1

                new_connection = Order_Product_Attributes(prod_quant, prod_shipped, prod_price, prod_prc_tax, order.id, product.id)
                db.session.add(new_connection)
                db.session.commit()

                product_ids.append(product.id)

                prod_quant = int(prod_quant)

                if add_to_stock != 0:
                    if order.order_time < lso.order_time:
                        opa = Order_Product_Attributes.query.filter_by(product_id=product.id, order_id=lso.id).first()
                        if opa:
                            opa.price = (opa.price * opa.shipped + add_to_stock * prod_shipped * prod_price)/(opa.shipped + add_to_stock * prod_shipped)
                            opa.ordered += add_to_stock * prod_quant
                            opa.shipped += add_to_stock * prod_shipped
                        else:
                            db.session.add(Order_Product_Attributes(prod_quant, prod_shipped, prod_price, prod_prc_tax, lso.id, product.id))
                        db.session.commit()
                    check_product = Product_Stock_Attributes.query.filter_by(product_id=product.id, stock_id=own_stock.id).first()
                    if check_product:
                        check_product.quantity += add_to_stock * int(prod_quant)
                        check_product.last_seen = datetime.now()
                        try:
                            check_product.buying_price = product.get_own_buying_price()
                        except Exception as e:
                            print(e)
                            continue
                    else:
                        db.session.add(Product_Stock_Attributes('Neu & OVP', prod_quant, product.get_own_buying_price(), 0, prod_prc_tax, 0, datetime.now(), datetime.strptime('01.01.3000', '%d.%m.%Y'), product.id, own_stock.id))
                    db.session.commit()
                    db.session.add(PSAUpdateQueue(product.id))
                    db.session.commit()
            i+=1
        if add_to_stock:
            product_list = []
            products = Product.query.filter(
                Product.id.in_(product_ids)
            ).order_by(Product.internal_id.desc()).all()
            url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"

            request_quant = 250
            i = 1
            while i * request_quant < len(products):
                xml = '''<?xml version="1.0" encoding="UTF-8"?>
                                <Request>
                                    <AfterbuyGlobal>
                                        <PartnerID><![CDATA[1000007048]]></PartnerID>
                                        <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                                        <UserID><![CDATA[Lotusicafe]]></UserID>
                                        <UserPassword><![CDATA[210676After251174]]></UserPassword>
                                        <CallName>UpdateShopProducts</CallName>
                                        <DetailLevel>0</DetailLevel>
                                        <ErrorLanguage>DE</ErrorLanguage>
                                    </AfterbuyGlobal>
                                    <Products>\n'''
                for product in products[(i - 1) * request_quant:i * request_quant]:
                    try:
                        product.buying_price = product.get_own_buying_price()
                        db.session.commit()
                        xml += '''<Product>
                                        <ProductIdent>
                                            <ProductInsert>0</ProductInsert>
                                            <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                        </ProductIdent>
                                        <BuyingPrice>''' + float_to_comma(float(("%.2f" % product.buying_price))) + '''</BuyingPrice>
                                    </Product>\n'''
                    except:
                        product_list.append(product.id)
                xml += '''</Products>
                        </Request>'''

                xml = xml.encode('utf-8')

                headers = {'Content-Type': 'application/xml; charset=utf-8'}
                requests.get(url, data=xml, headers=headers)

                i += 1

            xml = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Request>
                                <AfterbuyGlobal>
                                    <PartnerID><![CDATA[1000007048]]></PartnerID>
                                    <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                                    <UserID><![CDATA[Lotusicafe]]></UserID>
                                    <UserPassword><![CDATA[210676After251174]]></UserPassword>
                                    <CallName>UpdateShopProducts</CallName>
                                    <DetailLevel>0</DetailLevel>
                                    <ErrorLanguage>DE</ErrorLanguage>
                                </AfterbuyGlobal>
                                <Products>\n'''
            for product in products[(i - 1) * request_quant:i * request_quant]:
                try:
                    product.buying_price = product.get_own_buying_price()
                    db.session.commit()
                    xml += '''<Product>
                                    <ProductIdent>
                                        <ProductInsert>0</ProductInsert>
                                        <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                    </ProductIdent>
                                    <BuyingPrice>''' + float_to_comma(float(("%.2f" % product.buying_price))) + '''</BuyingPrice>
                                </Product>\n'''
                except:
                    product_list.append(product.id)
            xml += '''</Products>
                    </Request>'''
            i += 1

            xml = xml.encode('utf-8')

            headers = {'Content-Type': 'application/xml; charset=utf-8'}
            requests.get(url, data=xml, headers=headers)
            if product_list:
                msg = 'Eine Nullbestellung muss für die Einkaufspreis-Berechnung angelegt werden. ' \
                      'Die Produkte mit den folgenden Produkt-IDs sind in keiner Bestellung dieses Quartals gefunden worden:\n'
                msg += str(product_list)
                send_email('Preis-Update-Fehler', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de'], msg, msg)
        order.price = order.gross_price()
        db.session.commit()

        flash('Die Bestellung wurde hinzugefügt und die Einkaufspreise wurden an Afterbuy übertragen.', 'success')
        return redirect(url_for('center_orders_order', order_id=order.id))
    return render_template('center/orders/order.html', stocks=stocks, suppliers=suppliers, payment_methods=payment_methods, order=order, orders=orders)


@app.route('/center/orders/order/print_csv/<order_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_order_print_csv(order_id):
    order = Order.query.filter_by(id=order_id).first()
    file = io.StringIO()
    writer = csv.writer(file, delimiter=';')

    first_row = ['order_id', 'id', 'hsp_id', 'internal_id', 'name', 'delivery_date', 'net_price', 'gross_price', 'stock_type', 'order_status', 'order_amount', 'shipped', 'internal_id']
    writer.writerow(first_row)
    for opa in order.products:
        writer.writerow([order.afterbuy_id, opa.product.id, opa.product.hsp_id, opa.product.internal_id, opa.product.name, '', ('%0.2f' % opa.price).replace('.', ','),
                         ('%0.2f' % opa.gross_price()).replace('.', ','), 2, 881, opa.ordered, 0, opa.product.internal_id])
    output = make_response(file.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=order_{order.id}.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/center/orders/send_order', methods=['GET', 'POST'])
@is_logged_in
@csrf.exempt
@new_pageload
@roles_required('Admin')
def center_orders_send_order():
    res = send_order(request.form['order_id'])
    if res["status_code"] == 201:
        order = Order.query.filter_by(id=request.form['order_id']).first()
        order.sent = True
        order.external_id = res['order_id']
        db.session.add(ShippingStatus_Log(session['user_id'], 'bestellt', '', order.id))
        db.session.commit()
    return jsonify(res)


@app.route('/center/orders/get_order_status/<external_id>', methods=['GET', 'POST'])
@is_logged_in
@csrf.exempt
@new_pageload
@roles_required('Admin')
def center_orders_get_order_status(external_id):
    r = get_order(external_id)
    if r.ok:
        return jsonify(r.json())
    else:
        return jsonify({'status': 'danger'})


@app.route('/center/orders/get_hsp_id_name/<value>')
@is_logged_in
@new_pageload
@roles_required('Produkt-Management')
def center_orders_get_hsp_id_name(value):
    if len(value)<7:
        product = Product.query.filter_by(id=value).first()
    else:
        product=None
    value = str(int(value))
    if product is None:
        product = Product.query.filter_by(internal_id=value).first()
    if product is None:
        while len(value)<13:
            value = '0'+value
        product = Product.query.filter_by(hsp_id=value).first()
    if product:
        if product.release_date:
            release_date = product.release_date.strftime('%d.%m.%Y')
        else:
            release_date = ''
        idealo_link_category = ProductLinkCategory.query.filter_by(name='Idealo').first()
        product_link = ProductLink.query.filter_by(category_id=idealo_link_category.id, product_id=product.id).first()
        if product_link:
            link = product_link.link
        else:
            link = ''
        return jsonify({'product_name': product.name, 'link': link, 'release_date': release_date, 'block_release_date': product.block_release_date, 'hsp_id': product.hsp_id})
    else:
        return jsonify({'product_name': 'neues Produkt', 'link': '', 'release_date': '', 'block_release_date': False, 'hsp_id': value})


@app.route('/center/orders/addsupplier', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_addsupplier():
    if request.method == 'POST':
        isfirm = False
        firmname = request.form['firmname']
        salutation = request.form['salutation']
        name = request.form['name']
        firstname = request.form['firstname']
        fon = request.form['fon']
        email = request.form['email']
        address = request.form['address']
        city = request.form['city']
        zipcode = request.form['zipcode']
        country = request.form['country']
        std_tax = request.form['std_tax']
        if name == '' and firstname == '':
            salutation = ''
        if firmname != '-' and firmname != '':
            isfirm = True

        newsupplier = Supplier(isfirm, salutation, firmname, name, fon, email)
        newsupplier.firstname = firstname
        newsupplier.address = address
        newsupplier.zipcode = zipcode
        newsupplier.city = city
        newsupplier.country = country
        newsupplier.std_tax = std_tax
        db.session.add(newsupplier)
        db.session.commit()

    return render_template('center/orders/addsupplier.html')


@app.route('/center/orders/get_suppliers/')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_get_suppliers():
    suppliers = Supplier.query.all()
    out = '<option value=""></option>'
    for supplier in suppliers:
        if supplier.isfirm:
            out += '<option value="'+str(supplier.id)+'">'+supplier.firmname+'</option>'
        else:
            out += '<option value="'+str(supplier.id)+'">'+supplier.salutation + ' ' + supplier.firstname + ' ' + supplier.name + '</option>'
    return jsonify({'out': out})


@app.route('/center/orders/get_paymentmethods/')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_get_paymentmethods():
    payment_methods = PaymentMethod.query.all()
    out = '<option value=""></option>'
    for payment_method in payment_methods:
        out += '<option value="'+str(payment_method.id)+'">'+payment_method.name+'</option>'
    return jsonify({'out': out})


@app.route('/center/orders/add_paymentmethod/<name>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_add_paymentmethod(name):
    check_method = PaymentMethod.query.filter_by(name=name).first()
    if check_method:
        return jsonify({'msg': 'danger'})
    else:
        db.session.add(PaymentMethod(name))
        db.session.commit()
        return jsonify({'msg': 'success'})


@app.route('/center/orders/pre_order', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_pre_order():
    session['preorder_filter_infos'] = {'product_ids': [],
                                        'product_id_type': 'id',
                                        'min_release_date': None,
                                        'max_release_date': None}
    preorders = db.session.query(
        PreOrder, Product
    ).filter(
        PreOrder.product_id == Product.id
    ).order_by(
        Product.release_date
    ).all()
    vitrex = Supplier.query.filter_by(firmname='Vitrex').first()
    gross = Supplier.query.filter_by(firmname='Groß Electronic').first()
    if request.method == 'POST':
        if request.form['checker'] == 'update_preorders':
            for po in preorders:
                v_num = int(request.form[str(po[0].id)+'_vitrex'])
                v_conn = PreOrder_Supplier.query.filter_by(preorder_id=po[0].id, supplier_id=vitrex.id).first()
                if v_conn:
                    v_conn.quantity = v_num
                elif v_num > 0:
                    db.session.add(PreOrder_Supplier(v_num, po[0].id, vitrex.id))
                g_num = int(request.form[str(po[0].id)+'_gross'])
                g_conn = PreOrder_Supplier.query.filter_by(preorder_id=po[0].id, supplier_id=gross.id).first()
                if g_conn:
                    g_conn.quantity = g_num
                elif g_num > 0:
                    db.session.add(PreOrder_Supplier(g_num, po[0].id, gross.id))
                db.session.commit()
        elif request.form['checker'] == 'filter_preorders':
            id_type = request.form['id_type']
            session['preorder_filter_infos']['product_id_type'] = id_type
            product_ids = []
            if request.form['product_ids'] != '':
                product_ids = request.form['product_ids']
                product_ids = product_ids.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
                pattern = ';' + '{2,}'
                product_ids = re.sub(pattern, ';', product_ids)
                if product_ids[-1] == ';':
                    product_ids = product_ids[:-1]
                if id_type == 'id':
                    product_ids = [int(product_id) for product_id in product_ids.split(';')]
                    session['preorder_filter_infos']['product_ids'] = product_ids
                elif id_type == 'Internal_ID':
                    product_ids = [product_id for product_id in product_ids.split(';')]
                    session['preorder_filter_infos']['product_ids'] = product_ids
                    filtered_products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
                    product_ids = [product.id for product in filtered_products]
                else:
                    product_ids = [product_id for product_id in product_ids.split(';')]
                    session['preorder_filter_infos']['product_ids'] = product_ids
                    filtered_products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
                    product_ids = [product.id for product in filtered_products]
            else:
                session['preorder_filter_infos']['product_ids'] = []

            session['preorder_filter_infos']['min_release_date'] = request.form['min_release_date'] if request.form['min_release_date'] else None
            session['preorder_filter_infos']['max_release_date'] = request.form['max_release_date'] if request.form['max_release_date'] else None

            preorders = db.session.query(
                PreOrder, Product
            ).filter(
                PreOrder.product_id == Product.id
            ).filter(
                Product.id.in_(product_ids) if product_ids else True
            ).filter(
                Product.release_date >= datetime.strptime(session['preorder_filter_infos']['min_release_date'], '%Y-%m-%d') if session['preorder_filter_infos']['min_release_date'] else True
            ).filter(
                Product.release_date <= datetime.strptime(session['preorder_filter_infos']['max_release_date'], '%Y-%m-%d') if session['preorder_filter_infos']['min_release_date'] else True
            ).order_by(
                Product.release_date
            ).all()
    return render_template('center/orders/pre_order.html', preorders=preorders, vitrex=vitrex, gross=gross)


@app.route('/center/orders/sales/sort_results/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_orders_sales_sort_results(val):
    if val == session['orders_sales_filter_infos']['sort']:
        if session['orders_sales_filter_infos']['sort_dir'] == 'DESC':
            session['orders_sales_filter_infos'] = {'product_ids': [],
                                                    'product_id_type': 'id',
                                                    'min_sale': None,
                                                    'max_sale': None,
                                                    'min_stock': None,
                                                    'max_stock': None,
                                                    'min_sale_date': (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0),
                                                    'max_sale_date': datetime.now().replace(hour=23, minute=59, second=59),
                                                    'min_release_date': None,
                                                    'max_release_date': None,
                                                    'page': 1,
                                                    'datalimit_page': 25,
                                                    'datalimit_whole': None,
                                                    'sort_dir': 'ASC',
                                                    'sort': val}
            session['orders_sales_filter_infos']['sort'] = val
        else:
            session['orders_sales_filter_infos'] = {'product_ids': [],
                                                    'product_id_type': 'id',
                                                    'min_sale': None,
                                                    'max_sale': None,
                                                    'min_stock': None,
                                                    'max_stock': None,
                                                    'min_sale_date': (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0),
                                                    'max_sale_date': datetime.now().replace(hour=23, minute=59, second=59),
                                                    'min_release_date': None,
                                                    'max_release_date': None,
                                                    'page': 1,
                                                    'datalimit_page': 25,
                                                    'datalimit_whole': None,
                                                    'sort_dir': 'DESC',
                                                    'sort': val}
            session['orders_sales_filter_infos']['sort'] = val
    else:
        session['orders_sales_filter_infos'] = {'product_ids': [],
                                                'product_id_type': 'id',
                                                'min_sale': None,
                                                'max_sale': None,
                                                'min_stock': None,
                                                'max_stock': None,
                                                'min_sale_date': (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0),
                                                'max_sale_date': datetime.now().replace(hour=23, minute=59, second=59),
                                                'min_release_date': None,
                                                'max_release_date': None,
                                                'page': 1,
                                                'datalimit_page': 25,
                                                'datalimit_whole': None,
                                                'sort_dir': 'DESC',
                                                'sort': val}
        session['orders_sales_filter_infos']['sort'] = val
    return jsonify({})


@app.route('/center/orders/get_sales_data', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_get_sales_data():
    product_ids = session['orders_sales_filter_infos']['product_ids']

    sub_sales = db.session.query(
        Product.id.label('prod_id'), func.count(PricingLog.id), func.avg(Sale.selling_price).label('avg_selling_price'), func.sum(Sale.quantity).label('num_sales'),
        func.avg(Sale.shipping_price).label('avg_shipping_price')
    ).filter(
        PricingLog.id == Sale.pricinglog_id
    ).filter(
        Product.id == PricingLog.product_id
    ).filter(
        Sale.timestamp <= session['orders_sales_filter_infos']['max_sale_date'] if session['orders_sales_filter_infos']['max_sale_date'] else True
    ).filter(
        Sale.timestamp >= session['orders_sales_filter_infos']['min_sale_date'] if session['orders_sales_filter_infos']['min_sale_date'] else True
    ).filter(
        Product.id.in_(product_ids) if product_ids else True
    ).group_by(
        Product.id
    ).order_by(
        Product.id
    )

    mps = Marketplace.query.all()

    for mp in mps:
        mp_query = db.session.query(
            PricingLog.product_id.label('product_id'), func.count(PricingLog.id), func.avg(Sale.selling_price), (func.sum(Sale.quantity)).label('this'), func.max(ProductLinkCategory.id),
            func.max(ProductLink.link).label('that')
        ).filter(
            ProductLink.product_id == PricingLog.product_id
        ).filter(
            ProductLink.category_id == ProductLinkCategory.id
        ).filter(
            ProductLinkCategory.id == mp.productlinkcategory_id
        ).filter(
            Sale.pricinglog_id == PricingLog.id
        ).filter(
            Sale.timestamp <= session['orders_sales_filter_infos']['max_sale_date'] if session['orders_sales_filter_infos']['max_sale_date'] else True
        ).filter(
            Sale.timestamp >= session['orders_sales_filter_infos']['min_sale_date'] if session['orders_sales_filter_infos']['min_sale_date'] else True
        ).filter(
            PricingLog.marketplace_id == mp.id
        ).filter(
            PricingLog.product_id.in_(product_ids) if product_ids else True
        ).group_by(
            PricingLog.product_id
        ).order_by(
            PricingLog.product_id
        ).subquery()

        sub_sales = sub_sales.add_columns(func.coalesce(func.max(mp_query.c.this), 0).label(mp.name + '_num'), func.coalesce(func.max(mp_query.c.that), None).label(mp.name + '_link')).outerjoin(
            mp_query, mp_query.c.product_id == Product.id)

    sub_sales = sub_sales.subquery()

    subquery = db.session.query(
        Product_Stock_Attributes.id.label('psa_id'), Product_Stock_Attributes.product_id.label('p_id'),
        Product_Stock_Attributes.buying_price.label('buying_price'),
        Product_Stock_Attributes.quantity.label('quantity'), Stock.id.label('stock_id'),
        func.rank().over(order_by=Product_Stock_Attributes.buying_price.desc(), partition_by=Product_Stock_Attributes.product_id).label('rnk')
    ).filter(
        Product_Stock_Attributes.stock_id == Stock.id
    ).filter(
        Product_Stock_Attributes.avail_date <= datetime.now()
    ).filter(
        Product_Stock_Attributes.termination_date >= datetime.now()
    ).filter(
        Stock.owned == False
    ).order_by(
        Product_Stock_Attributes.buying_price
    ).subquery()

    stock_query = db.session.query(
        Product_Stock_Attributes.product_id.label('product_id'), Product_Stock_Attributes.quantity.label('stock')
    ).filter(
        Product_Stock_Attributes.stock_id == 1
    ).subquery()
    
    orders = Order.query.filter(
        Order.order_time >= datetime.now()-timedelta(days=30)
    ).join(ShippingStatus_Log).all()
    order_ids = [order.id for order in orders if order.get_current_shipping_stat().label == 'bestellt']
    
    order_query = db.session.query(Order_Product_Attributes.product_id.label('product_id'), func.sum(Order_Product_Attributes.ordered).label('ordered')).filter(
        Order_Product_Attributes.order_id == Order.id
    ).filter(
        Order_Product_Attributes.order_id.in_(order_ids)
    ).group_by(
        Order_Product_Attributes.product_id
    ).subquery()

    if session['orders_sales_filter_infos']['sort'] in ['id', 'internal_id', 'hsp_id', 'name']:
        sales = db.session.query(
            Product, Stock, PricingAction
        ).add_columns(
            stock_query.c.stock, subquery.c.psa_id, subquery.c.buying_price, subquery.c.quantity, subquery.c.stock_id, subquery.c.rnk, order_query.c.ordered
        ).add_columns(
            sub_sales
        ).outerjoin(
            subquery, subquery.c.p_id == Product.id
        ).outerjoin(
            sub_sales, sub_sales.c.prod_id == Product.id
        ).outerjoin(
            stock_query, stock_query.c.product_id == Product.id
        ).outerjoin(
            Stock, Stock.id == subquery.c.stock_id
        ).outerjoin(
            order_query, Product.id == order_query.c.product_id
        ).filter(
            or_(subquery.c.rnk <= 3, subquery.c.rnk == None)
        ).filter(
            Product.release_date <= session['orders_sales_filter_infos']['max_release_date'] if session['orders_sales_filter_infos']['max_release_date'] else True
        ).filter(
            Product.release_date >= session['orders_sales_filter_infos']['min_release_date'] if session['orders_sales_filter_infos']['min_release_date'] else True
        ).filter(
            PricingAction.product_id == Product.id
        ).filter(
            PricingAction.active == True
        ).filter(
            sub_sales.c.prod_id != None
        ).filter(
            sub_sales.c.num_sales >= session['orders_sales_filter_infos']['min_sale'] if session['orders_sales_filter_infos']['min_sale'] != None else True
        ).filter(
            sub_sales.c.num_sales <= session['orders_sales_filter_infos']['max_sale'] if session['orders_sales_filter_infos']['max_sale'] != None else True
        ).filter(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100) >= session['orders_sales_filter_infos']['min_stock']
            if session['orders_sales_filter_infos']['min_stock'] != None else True
        ).filter(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100) <= session['orders_sales_filter_infos']['max_stock']
            if session['orders_sales_filter_infos']['max_stock'] != None else True
        ).order_by(
            getattr(Product, session['orders_sales_filter_infos']['sort']).desc()
            if session['orders_sales_filter_infos']['sort_dir'] == 'DESC'
            else getattr(Product, session['orders_sales_filter_infos']['sort'])
        ).all()
    elif session['orders_sales_filter_infos']['sort'] in ['pa_name']:
        sales = db.session.query(
            Product, Stock, PricingAction
        ).add_columns(
            stock_query.c.stock, subquery.c.psa_id, subquery.c.buying_price, subquery.c.quantity, subquery.c.stock_id, subquery.c.rnk, order_query.c.ordered
        ).add_columns(
            sub_sales
        ).outerjoin(
            subquery, subquery.c.p_id == Product.id
        ).outerjoin(
            sub_sales, sub_sales.c.prod_id == Product.id
        ).outerjoin(
            stock_query, stock_query.c.product_id == Product.id
        ).outerjoin(
            Stock, Stock.id == subquery.c.stock_id
        ).outerjoin(
            order_query, Product.id == order_query.c.product_id
        ).filter(
            or_(subquery.c.rnk <= 3, subquery.c.rnk == None)
        ).filter(
            Product.release_date <= session['orders_sales_filter_infos']['max_release_date'] if session['orders_sales_filter_infos']['max_release_date'] else True
        ).filter(
            Product.release_date >= session['orders_sales_filter_infos']['min_release_date'] if session['orders_sales_filter_infos']['min_release_date'] else True
        ).filter(
            PricingAction.product_id == Product.id
        ).filter(
            PricingAction.active == True
        ).filter(
            sub_sales.c.prod_id != None
        ).filter(
            sub_sales.c.num_sales >= session['orders_sales_filter_infos']['min_sale'] if session['orders_sales_filter_infos']['min_sale'] != None else True
        ).filter(
            sub_sales.c.num_sales <= session['orders_sales_filter_infos']['max_sale'] if session['orders_sales_filter_infos']['max_sale'] != None else True
        ).filter(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100) >= session['orders_sales_filter_infos']['min_stock']
            if session['orders_sales_filter_infos']['min_stock'] != None else True
        ).filter(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100) <= session['orders_sales_filter_infos']['max_stock']
            if session['orders_sales_filter_infos']['max_stock'] != None else True
        ).order_by(
            PricingAction.name.desc()
            if session['orders_sales_filter_infos']['sort_dir'] == 'DESC'
            else PricingAction.name
        ).all()
    elif session['orders_sales_filter_infos']['sort'] in ['num_sales']:
        sales = db.session.query(
            Product, Stock, PricingAction
        ).add_columns(
            stock_query.c.stock, subquery.c.psa_id, subquery.c.buying_price, subquery.c.quantity, subquery.c.stock_id, subquery.c.rnk, order_query.c.ordered
        ).add_columns(
            sub_sales
        ).outerjoin(
            subquery, subquery.c.p_id == Product.id
        ).outerjoin(
            sub_sales, sub_sales.c.prod_id == Product.id
        ).outerjoin(
            stock_query, stock_query.c.product_id == Product.id
        ).outerjoin(
            Stock, Stock.id == subquery.c.stock_id
        ).outerjoin(
            order_query, Product.id == order_query.c.product_id
        ).filter(
            or_(subquery.c.rnk <= 3, subquery.c.rnk == None)
        ).filter(
            Product.release_date <= session['orders_sales_filter_infos']['max_release_date'] if session['orders_sales_filter_infos']['max_release_date'] else True
        ).filter(
            Product.release_date >= session['orders_sales_filter_infos']['min_release_date'] if session['orders_sales_filter_infos']['min_release_date'] else True
        ).filter(
            PricingAction.product_id == Product.id
        ).filter(
            PricingAction.active == True
        ).filter(
            sub_sales.c.prod_id != None
        ).filter(
            sub_sales.c.num_sales >= session['orders_sales_filter_infos']['min_sale'] if session['orders_sales_filter_infos']['min_sale'] != None else True
        ).filter(
            sub_sales.c.num_sales <= session['orders_sales_filter_infos']['max_sale'] if session['orders_sales_filter_infos']['max_sale'] != None else True
        ).filter(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100) >= session['orders_sales_filter_infos']['min_stock']
            if session['orders_sales_filter_infos']['min_stock'] != None else True
        ).filter(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100) <= session['orders_sales_filter_infos']['max_stock']
            if session['orders_sales_filter_infos']['max_stock'] != None else True
        ).order_by(
            sub_sales.c.num_sales.desc()
            if session['orders_sales_filter_infos']['sort_dir'] == 'DESC'
            else sub_sales.c.num_sales
        ).all()
    elif session['orders_sales_filter_infos']['sort'] in ['stock']:
        sales = db.session.query(
            Product, Stock, PricingAction
        ).add_columns(
            stock_query.c.stock, subquery.c.psa_id, subquery.c.buying_price, subquery.c.quantity, subquery.c.stock_id, subquery.c.rnk, order_query.c.ordered
        ).add_columns(
            sub_sales
        ).outerjoin(
            subquery, subquery.c.p_id == Product.id
        ).outerjoin(
            sub_sales, sub_sales.c.prod_id == Product.id
        ).outerjoin(
            stock_query, stock_query.c.product_id == Product.id
        ).outerjoin(
            Stock, Stock.id == subquery.c.stock_id
        ).outerjoin(
            order_query, Product.id == order_query.c.product_id
        ).filter(
            or_(subquery.c.rnk <= 3, subquery.c.rnk == None)
        ).filter(
            Product.release_date <= session['orders_sales_filter_infos']['max_release_date'] if session['orders_sales_filter_infos']['max_release_date'] else True
        ).filter(
            Product.release_date >= session['orders_sales_filter_infos']['min_release_date'] if session['orders_sales_filter_infos']['min_release_date'] else True
        ).filter(
            PricingAction.product_id == Product.id
        ).filter(
            PricingAction.active == True
        ).filter(
            sub_sales.c.prod_id != None
        ).filter(
            sub_sales.c.num_sales >= session['orders_sales_filter_infos']['min_sale'] if session['orders_sales_filter_infos']['min_sale'] != None else True
        ).filter(
            sub_sales.c.num_sales <= session['orders_sales_filter_infos']['max_sale'] if session['orders_sales_filter_infos']['max_sale'] != None else True
        ).filter(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100) >= session['orders_sales_filter_infos']['min_stock']
            if session['orders_sales_filter_infos']['min_stock'] != None else True
        ).filter(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100) <= session['orders_sales_filter_infos']['max_stock']
            if session['orders_sales_filter_infos']['max_stock'] != None else True
        ).order_by(
            (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100).desc()
            if session['orders_sales_filter_infos']['sort_dir'] == 'DESC'
            else (stock_query.c.stock - cast(Product.short_sell, sqlalchemy_Integer) * 100)
        ).all()
    result_length = 0

    if sales:
        out = '<tbody style="border-bottom: solid 1px rgb(222, 226, 230);">'
        num = 0
        curr_id = sales[0][0].id
        for s in sales:
            if (session['orders_sales_filter_infos']['page'] - 1) * session['orders_sales_filter_infos']['datalimit_page'] <= result_length < session['orders_sales_filter_infos']['page'] * session['orders_sales_filter_infos']['datalimit_page']:
                if num == 0:
                    result_length += 1
                    out += f'''
                                <tr>
                                    <td>
                                    </td>
                                    <td>
                                        { s[0].id }<br>
                                        { s[0].hsp_id }<br>
                                        { s[0].internal_id }
                                    </td>
                                    <td>
                                        { s[0].name }
                                '''
                    if s[0].release_date:
                        if s[0].release_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                            out += f'''
                                        <span class="fa-layers fa-fw" style="position: relative; margin-right: 4px">
                                            <i class="fa fa-shopping-cart"></i>
                                            <i class="fa fa-clock-o" style="left: 10px; top: -2px; position: absolute; font-size: 10px;"></i>
                                        </span>
                                        '''
                    out += f'''
                                </td>
                                <td>
                                    <div class="smallbutton visible whitebutton" onclick="window.open('{ url_for("center_product_pricingactions", id=s[0].id ) }');event.cancelBubble=true;" style="width: 170px; margin: 2px">
                                        { s[2].name }
                                    </div>
                                </td>
                                <td>
                                    { '%0.2f' % s.avg_selling_price } €
                                </td>
                                <td>
                                    { '%0.2f' % s.avg_shipping_price } €
                                </td>
                                '''
                    sm = 0
                    print('------------------')
                    print(s[0].id)
                    for mp in mps:
                        print(mp.id)
                        print(s.avg_selling_price)
                        print(s.avg_shipping_price)
                        print(getattr(s, mp.name + '_num'))
                        sm += s[0].get_avgmargin_by_mp_sellp_shipp(mp.id, s.avg_selling_price, s.avg_shipping_price, getattr(s, mp.name + '_num'))
                    print(sm)
                    print(s.num_sales)
                    print('------------------')
                    if s.num_sales != 0 and sm != 0:
                        out += f'''
                                    <td { ['','style="background: #fad0cd"'][int(sm < 0)] }>
                                        { '%0.2f' % (sm / s.num_sales) } %
                                    </td>
                                    '''
                    else:
                        out += f'''
                                    <td>
                                        -
                                    </td>
                                    '''
                    out += f'''
                                <td>
                                    <table>
                                        <tr>
                                        '''
                    for mp in mps:
                        out += f'''
                        <td style="padding: 0; border: None" { 'class="glow" onclick="open_marketplace_link(' + "'" + mp.get_productlink(s[0].id).link + "'" + '); event.cancelBubble=true;"' if mp.get_productlink(s[0].id) else '' }>
                        <img src="{ url_for('static', filename='images/foreignicons/' + mp.name + '_icon.png') }" style="height:15px; width: 15px; margin: 2px">
                        </td>
                        '''
                    out += f'''
                                    <td style="padding: 0 5px; border: None;" >
                                        &Sigma;
                                    </td>
                                </tr>
                                <tr>
                                '''
                    for mp in mps:
                        out += f'''
                                    <td style="padding: 0; border: None; text-align: center" >{ getattr(s, mp.name+'_num') }</td>
                                    '''
                    out += f'''
                                    <td style="padding: 0 5px; border: None; font-weight: 500">
                                        { s.num_sales }
                                    </td>
                                </tr>
                            </table>
                        </td>
                        <td>
                            { '%0.2f' % s[0].get_own_buying_price() + ' €' if s[0].get_own_buying_price() else '-' }<br>
                            { s.stock - s[0].short_sell*100 } Stk. { '(L-VK)' if s[0].short_sell else '' }<br>
                            { s.ordered if s.ordered else '' } { 'bestellt' if s.ordered else ''}
                        </td>
                        '''
                    if s[1]:
                        out += f'''
                            <td>
                                { '%0.2f' % s.buying_price } €<br>
                                { s.quantity } Stk.<br>
                                { s[1].supplier.get_name() }<br>
                                <input class="order_field" required min="0" value="0" style="width: 60px;" type="number" name="{ s[1].supplier.id }_{ s[0].id }">
                                <input hidden name="{ s[1].supplier.id }_{ s[0].id }_price" value="{ s.buying_price }">
                            </td>
                            '''
                    else:
                        out += f'''
                            <td>-</td>
                        '''
                    num += 1
                elif num < 3:
                    if s[0].id == curr_id:
                        out += f'''
                                    <td>
                                        { '%0.2f' % s.buying_price } €<br>
                                        { s.quantity } Stk.<br>
                                        { s[1].supplier.get_name() }<br>
                                        <input class="order_field" required min="0" value="0" style="width: 60px;" type="number" name="{ s[1].supplier.id }_{ s[0].id }">
                                        <input hidden name="{ s[1].supplier.id }_{ s[0].id }_price" value="{ s.buying_price }">
                                    </td>
                                    '''
                        num += 1
                    else:
                        curr_id = s[0].id
                        if (session['orders_sales_filter_infos']['page'] - 1) * session['orders_sales_filter_infos']['datalimit_page'] != result_length:
                            for i in range(3 - num):
                                out += f'''
                                            <td>
                                                - <br>
                                            </td>
                                            '''
                        result_length+=1
                        out += f'''
                                    <tr>
                                        <td>
                                        </td>
                                        <td>
                                            { s[0].id }<br>
                                            { s[0].hsp_id }<br>
                                            { s[0].internal_id }
                                        </td>
                                        <td>
                                            { s[0].name }
                                    '''
                        if s[0].release_date:
                            if s[0].release_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                                out += f'''
                                            <span class="fa-layers fa-fw" style="position: relative; margin-right: 4px">
                                                <i class="fa fa-shopping-cart"></i>
                                                <i class="fa fa-clock-o" style="left: 10px; top: -2px; position: absolute; font-size: 10px;"></i>
                                            </span>
                                            '''
                        out += f'''
                                    </td>
                                    <td>
                                        <div class="smallbutton visible whitebutton" onclick="window.open('{ url_for("center_product_pricingactions", id=s[0].id ) }');event.cancelBubble=true;" style="width: 170px; margin: 2px">
                                            { s[2].name }
                                        </div>
                                    </td>
                                    <td>
                                        { '%0.2f' % s.avg_selling_price } €
                                    </td>
                                    <td>
                                        { '%0.2f' % s.avg_shipping_price } €
                                    </td>
                                    '''
                        sm = 0
                        print('------------------')
                        print(s[0].id)
                        for mp in mps:
                            print(mp.id)
                            print(s.avg_selling_price)
                            print(s.avg_shipping_price)
                            print(getattr(s, mp.name + '_num'))
                            sm += s[0].get_avgmargin_by_mp_sellp_shipp(mp.id, s.avg_selling_price, s.avg_shipping_price, getattr(s, mp.name + '_num'))
                        print(sm)
                        print(s.num_sales)
                        print('------------------')
                        if s.num_sales != 0 and sm != 0:
                            out += f'''
                                        <td { ['','style="background: #fad0cd"'][int(sm < 0)] }>
                                            { '%0.2f' % (sm / s.num_sales) } %
                                        </td>
                                        '''
                        else:
                            out += f'''
                                        <td>
                                            -
                                        </td>
                                        '''
                        out += f'''
                                    <td>
                                        <table>
                                            <tr>
                                            '''
                        for mp in mps:
                            out += f'''
                            <td style="padding: 0; border: None" { 'class="glow" onclick="open_marketplace_link(' + "'" + mp.get_productlink(s[0].id).link + "'" + '); event.cancelBubble=true;"' if mp.get_productlink(s[0].id) else ''}>
                            <img src="{ url_for('static', filename='images/foreignicons/' + mp.name + '_icon.png') }" style="height:15px; width: 15px; margin: 2px">
                            </td>
                            '''
                        out += f'''
                                        <td style="padding: 0 5px; border: None;" >
                                            &Sigma;
                                        </td>
                                    </tr>
                                    <tr>
                                    '''
                        for mp in mps:
                            out += f'''
                                        <td style="padding: 0; border: None; text-align: center" >{ getattr(s, mp.name+'_num') }</td>
                                        '''
                        out += f'''
                                        <td style="padding: 0 5px; border: None; font-weight: 500">
                                            { s.num_sales }
                                        </td>
                                    </tr>
                                </table>
                            </td>
                            <td>
                                { '%0.2f' % s[0].get_own_buying_price() + ' €' if s[0].get_own_buying_price() else '-' }<br>
                                { s.stock - s[0].short_sell*100 } Stk. { '(L-VK)' if s[0].short_sell else '' }<br>
                                { s.ordered if s.ordered else '' } { 'bestellt' if s.ordered else ''}
                            </td>
                            '''
                        if s[1]:
                            out += f'''
                                <td>
                                    { '%0.2f' % s.buying_price } €<br>
                                    { s.quantity } Stk.<br>
                                    { s[1].supplier.get_name() }<br>
                                    <input class="order_field" required min="0" value="0" style="width: 60px;" type="number" name="{ s[1].supplier.id }_{ s[0].id }">
                                    <input hidden name="{ s[1].supplier.id }_{ s[0].id }_price" value="{ s.buying_price }">
                                </td>
                                '''
                        else:
                            out += f'''
                                <td>-</td>
                            '''
                        num = 1
                else:
                    num=0
            else:
                if num == 0:
                    result_length += 1
                    num += 1
                elif num < 3:
                    if s[0].id == curr_id:
                        num += 1
                    else:
                        curr_id = s[0].id
                        result_length += 1
                        num = 1
                else:
                    num = 0
        if num < 3:
            for i in range(3 - num):
                out += f'''
                        <td>
                            - <br>
                        </td>
                        '''
        out += f'''
                    </tbody>
                    '''
    else:
        out = ''
    result_box = f'''
            <div class="box100title">
                { result_length } Treffer
            </div>
            <div class="box100title">
                Seite: <input id="page" type="number" max="{ int(math.ceil(result_length/session['orders_sales_filter_infos']['datalimit_page'])) }" min="1" value="{ session['orders_sales_filter_infos']['page'] }" style="width: 50px" onchange="turnpage(this.value)">
                / { int(math.ceil(result_length/session['orders_sales_filter_infos']['datalimit_page'])) }
            </div>'''
    return jsonify({'result': out, 'result_length': result_length, 'result_box': result_box})
    #return jsonify({'taskid': task.id})


@app.route('/center/orders/sales', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_orders_sales():
    stocks = Stock.query.order_by(Stock.id).filter_by(owned=False).all()

    if request.method == 'POST':
        if request.form['checker'] == 'filter_sales':

            session['orders_sales_filter_infos'] = {'product_ids': [],
                                                    'product_id_type': 'id',
                                                    'min_sale': None,
                                                    'max_sale': None,
                                                    'min_stock': None,
                                                    'max_stock': None,
                                                    'min_sale_date': (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0),
                                                    'max_sale_date': datetime.now().replace(hour=23, minute=59, second=59),
                                                    'min_release_date': None,
                                                    'max_release_date': None,
                                                    'page': session['orders_sales_filter_infos']['page'],
                                                    'datalimit_page': 25,
                                                    'datalimit_whole': None,
                                                    'sort_dir': session['orders_sales_filter_infos']['sort_dir'],
                                                    'sort': session['orders_sales_filter_infos']['sort']}
            id_type = request.form['id_type']
            session['orders_sales_filter_infos']['product_id_type'] = id_type
            product_ids = []
            if request.form['product_ids'] != '':
                product_ids = request.form['product_ids']
                product_ids = product_ids.replace(' ', ';').replace('\r', ';').replace('\n', ';').replace(',', ';')
                pattern = ';' + '{2,}'
                product_ids = re.sub(pattern, ';', product_ids)
                if product_ids[-1] == ';':
                    product_ids = product_ids[:-1]
                if id_type == 'id':
                    product_ids = [int(product_id) for product_id in product_ids.split(';')]
                    session['orders_sales_filter_infos']['product_ids'] = product_ids
                elif id_type == 'Internal_ID':
                    product_ids = [product_id for product_id in product_ids.split(';')]
                    session['orders_sales_filter_infos']['product_ids'] = product_ids
                    filtered_products = Product.query.filter(Product.internal_id.in_(product_ids)).all()
                    product_ids = [product.id for product in filtered_products]
                else:
                    product_ids = [product_id for product_id in product_ids.split(';')]
                    session['orders_sales_filter_infos']['product_ids'] = product_ids
                    filtered_products = Product.query.filter(Product.hsp_id.in_(product_ids)).all()
                    product_ids = [product.id for product in filtered_products]
            else:
                session['orders_sales_filter_infos']['product_ids'] = []

            session['orders_sales_filter_infos']['min_sale_date'] = datetime.strptime(request.form['min_sale_date'], '%Y-%m-%d').replace(hour=0, minute=0, second=0) if request.form['min_sale_date'] else None
            session['orders_sales_filter_infos']['max_sale_date'] = datetime.strptime(request.form['max_sale_date'], '%Y-%m-%d').replace(hour=23, minute=59, second=59) if request.form['max_sale_date'] else None

            session['orders_sales_filter_infos']['min_release_date'] = datetime.strptime(request.form['min_release_date'], '%Y-%m-%d').replace(hour=0, minute=0, second=0) if request.form['min_release_date'] else None
            session['orders_sales_filter_infos']['max_release_date'] = datetime.strptime(request.form['max_release_date'], '%Y-%m-%d').replace(hour=23, minute=59, second=59) if request.form['max_release_date'] else None

            session['orders_sales_filter_infos']['min_sale'] = str_to_int(request.form['min_sale'])
            session['orders_sales_filter_infos']['max_sale'] = str_to_int(request.form['max_sale'])

            session['orders_sales_filter_infos']['min_stock'] = str_to_int(request.form['min_stock'])
            session['orders_sales_filter_infos']['max_stock'] = str_to_int(request.form['max_stock'])

            session['orders_sales_filter_infos']['datalimit_page'] = str_to_int(request.form['datalimit_page'])
            return redirect(url_for('center_orders_sales'))
        elif request.form['checker'] == 'order_form':
            orderdict = {}
            active_order_fields = request.form['active_order_fields'].split(',')
            for field in active_order_fields:
                a = field.split('_')
                if a[0] in orderdict:
                    orderdict[a[0]].append({'product_id': a[1], 'price': request.form[field+'_price'], 'quantity': request.form[field]})
                else:
                    orderdict[a[0]] = [{'product_id': a[1], 'price': request.form[field+'_price'], 'quantity': request.form[field]}]
            print(orderdict)
            for key in orderdict:
                order_time = datetime.now()
                stock_id = 1
                supplier_id = int(key)
                supplier = Supplier.query.filter_by(id=key).first()
                name = supplier.get_name() + '_' + order_time.strftime('%Y_%m_%d')
                payment_method = 6
                delivery_time = None
                comment = None
                summed_price_value = 0
                order = Order(name, order_time, delivery_time, summed_price_value, 0, comment, stock_id, payment_method, supplier_id)
                db.session.add(order)
                db.session.commit()
                summed_price = 0
                for product in orderdict[key]:
                    p = Product.query.filter_by(id=product['product_id']).first()
                    new_connection = Order_Product_Attributes(product['quantity'], 0, product['price'], tax_group[p.tax_group][supplier.std_tax], order.id, product['product_id'])
                    db.session.add(new_connection)
                    db.session.commit()
                    summed_price += float(product['quantity']) * float(product['price'])
                order.price = summed_price
                db.session.commit()
    #return render_template('center/orders/sales.html', sales=sales, mps=mps, stocks=stocks, result_length=result_length, task_id=task.id)
    return render_template('center/orders/sales.html', stocks=stocks)


@app.route('/center/orders/sales/turnpage/<val>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_orders_sales_turnpage(val):
    session['orders_sales_filter_infos'] = {'product_ids': [],
                                            'product_id_type': 'id',
                                            'min_sale': None,
                                            'max_sale': None,
                                            'min_stock': None,
                                            'max_stock': None,
                                            'min_sale_date': (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0),
                                            'max_sale_date': datetime.now().replace(hour=23, minute=59, second=59),
                                            'min_release_date': None,
                                            'max_release_date': None,
                                            'page': int(val),
                                            'datalimit_page': 25,
                                            'datalimit_whole': None,
                                            'sort_dir': 'DESC',
                                            'sort': 'id'}
    return jsonify({})


######################################################################################

#####################################   SALES   ######################################

######################################################################################

@app.route('/center/sales', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_sales():
    return render_template('center/sales/index.html')


@app.route('/center/sales/problem_handling', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_sales_problem_handling():
    return render_template('center/sales/problem_handling.html')


@app.route('/center/sales/filter_addresses/<start>,<end>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_sales_filter_addresses(start, end):
    start = datetime.strptime(str(start), '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.strptime(str(end), '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
    if end > start:
        data = correct_addresses(start, end)
        print(data)
        return jsonify(data)
    else:
        return jsonify({'status': 'Error', 'msg': 'Das End-Datum ist kleiner als das Start-Datum.'})

######################################################################################

######################################   USER   ######################################

######################################################################################


@app.route('/center/user')
@is_logged_in
@new_pageload
def center_user():
    workday = Workday.query.filter_by(user_id=session['user_id']).order_by(
        Workday.check_in_datetime.desc()
    ).first()
    week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)-timedelta(days=datetime.now().weekday())
    week_wdays = Workday.query.filter_by(user_id=session['user_id']).filter(Workday.check_in_datetime >= week_start).filter(Workday.check_out_datetime <= datetime.now()).all()
    week_dur = sum([wd.get_duration() for wd in week_wdays], timedelta()).total_seconds()/3600
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_wdays = Workday.query.filter_by(user_id=session['user_id']).filter(Workday.check_in_datetime >= month_start).filter(Workday.check_out_datetime <= datetime.now()).all()
    month_dur = sum([wd.get_duration() for wd in month_wdays], timedelta()).total_seconds()/3600
    return render_template('center/user/index.html', workday=workday, week_dur=week_dur, month_dur=month_dur)


@app.route('/center/user/start_workday', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_user_start_workday():
    try:
        db.session.add(Workday(request.environ['HTTP_X_REAL_IP'], session['user_id']))
        db.session.commit()
        flash('Arbeitstag gestartet.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('center_user'))


@app.route('/center/user/end_workday', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_user_end_workday():
    workday = Workday.query.filter_by(user_id=session['user_id']).filter(
        Workday.check_out_datetime == None
    ).order_by(
        Workday.check_in_datetime.desc()
    ).first()
    if not workday:
        flash('Noch nicht eingecheckt.', 'danger')
        return redirect(url_for('center_user'))
    workday.check_out_datetime = datetime.now()
    workday.check_out_ip = request.environ['HTTP_X_REAL_IP']
    db.session.commit()
    check_po = Payout.query.filter(Payout.start <= workday.check_in_datetime).filter(Payout.end >= workday.check_out_datetime).filter_by(user_id=workday.user_id).first()
    if check_po:
        dur = workday.get_duration().total_seconds()
        check_po.time_balance += dur
        db.session.commit()
        fol_pos = Payout.query.filter(Payout.start > check_po.end).filter_by(user_id=workday.user_id).all()
        for po in fol_pos:
            po.time_balance += dur
            db.session.commit()
    flash('Arbeitstag beendet.', 'success')
    return redirect(url_for('center_user'))


@app.route('/center/user/workdays', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_user_workdays():
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    end = datetime.now()
    if request.method == 'POST':
        start = datetime.strptime(request.form['start'], '%Y-%m-%d')
        end = datetime.strptime(request.form['end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=9999)
    workdays = Workday.query.filter_by(user_id=session['user_id']).filter(Workday.check_in_datetime >= start).filter(Workday.check_out_datetime <= end).order_by(Workday.check_in_datetime).all()
    dur = sum([wd.get_duration() for wd in workdays], timedelta()).total_seconds()/3600
    return render_template('center/user/workdays.html', workdays=workdays, start=start, end=end, dur=dur)


@app.route('/center/user/proc_products', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
def center_user_proc_products():
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    end = datetime.now()
    if request.method == 'POST':
        start = datetime.strptime(request.form['start'], '%Y-%m-%d')
        end = datetime.strptime(request.form['end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=9999)
    proc_ps = Product_CurrProcStat.query.filter_by(proc_user_id=session['user_id']).filter(
        Product_CurrProcStat.proc_timestamp >= start
    ).filter(
        Product_CurrProcStat.proc_timestamp <= end + timedelta(days=1)
    ).all()
    return render_template('center/user/proc_products.html', proc_ps=proc_ps, start=start, end=end)


@app.route('/center/user/users')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_user_users():
    users = User.query.filter_by(confirmed=True).all()
    return render_template('center/user/users.html', users=users)


@app.route('/center/user/activate_user/<user_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_user_activate_user(user_id):
    User.query.filter_by(id=int(user_id)).first().active = True
    db.session.commit()
    return redirect(url_for('center_users'))


@app.route('/center/user/deactivate_user/<user_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_user_deactivate_user(user_id):
    User.query.filter_by(id=int(user_id)).first().active = False
    db.session.commit()
    return redirect(url_for('center_users'))


@app.route('/center/user/user/<user_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_user_user(user_id):
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    end = datetime.now()
    po_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365)
    po_end = datetime.now()
    if request.method == 'POST':
        if request.form['form_type'] == 'filter_days':
            start = datetime.strptime(request.form['start'], '%Y-%m-%d')
            end = datetime.strptime(request.form['end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=9999)
        elif request.form['form_type'] == 'add_days':
            first_day = datetime.strptime(request.form['add_d_start'], '%Y-%m-%d')
            last_day = datetime.strptime(request.form['add_d_end'], '%Y-%m-%d')
            hours = request.form['hours']
            if '.' in hours:
                hours = int(hours.split('.')[0])
                minutes = 30
            else:
                hours = int(hours)
                minutes = 0
            wd_type = request.form['wd_type']
            wdays = request.form.getlist('weekday')
            for i in range((last_day-first_day).days+1):
                d = first_day + timedelta(days=i)
                if str(d.weekday()) in wdays:
                    d = d.replace(hour=8, minute=0, second=0, microsecond=0)
                    db.session.add(Workday(check_in_ip='-', user_id=int(user_id), check_in_datetime=d, check_out_datetime=d+timedelta(hours=hours, minutes=minutes), check_out_ip='-', sick_leave=wd_type=='sick_leave',
                                           vaca_leave=wd_type=='vaca_leave', holiday=wd_type=='holiday'))
                    db.session.commit()
        elif request.form['form_type'] == 'po_filter_days':
            po_start = datetime.strptime(request.form['po_start'], '%Y-%m-%d')
            po_end = datetime.strptime(request.form['po_end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=9999)
        elif request.form['form_type'] == 'add_payout':
            try:
                add_po_start = datetime.strptime(request.form['add_po_start'], '%Y-%m-%d')
                add_po_end = datetime.strptime(request.form['add_po_end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=9999)
                add_po_hours = request.form['add_po_hours']
                if '.' in add_po_hours:
                    add_po_hours = float(add_po_hours.split('.')[0])+0.5
                else:
                    add_po_hours = float(add_po_hours)
                db.session.add(Payout(add_po_hours, add_po_start, add_po_end, int(user_id)))
                db.session.commit()
            except Exception as e:
                flash(str(e), 'danger')
                return redirect(url_for('center_user_user', user_id=user_id))
    workdays = Workday.query.filter_by(user_id=user_id).filter(Workday.check_in_datetime >= start).filter(Workday.check_out_datetime <= end).order_by(Workday.check_in_datetime).all()
    payouts = Payout.query.filter_by(user_id=user_id).filter(Payout.start >= po_start).filter(Payout.end <= po_end).order_by(Payout.start.desc()).all()
    dur = sum([wd.get_duration() for wd in workdays], timedelta()).total_seconds()/3600
    user = User.query.filter_by(id=int(user_id)).first()
    roles = Role.query.all()
    return render_template('center/user/user.html', user=user, roles=roles, workdays=workdays, payouts=payouts, po_start=po_start, po_end=po_end, start=start, end=end, dur=dur)


@app.route('/center/user/user/update_wd', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@csrf.exempt
@roles_required('Admin')
def center_user_user_update_wd():
    wd = Workday.query.filter_by(id=int(request.form['wd_id'])).first()
    old_dur = wd.get_duration().total_seconds()
    if request.form['update'] == 'ci':
        wd.check_in_datetime = datetime.strptime(request.form['value'], '%d.%m.%Y - %H:%M:%S')
    if request.form['update'] == 'co':
        wd.check_out_datetime = datetime.strptime(request.form['value'], '%d.%m.%Y - %H:%M:%S')
    db.session.commit()
    new_dur = wd.get_duration().total_seconds()
    check_po = Payout.query.filter(Payout.start <= wd.check_in_datetime).filter(Payout.end >= wd.check_out_datetime).filter_by(user_id=wd.user_id).first()
    if check_po:
        check_po.time_balance += new_dur-old_dur
        db.session.commit()
        fol_pos = Payout.query.filter(Payout.start > check_po.end).filter_by(user_id=wd.user_id).all()
        for po in fol_pos:
            po.time_balance += new_dur-old_dur
            db.session.commit()
    workdays = Workday.query.filter_by(user_id=wd.user_id).filter(
        Workday.check_in_datetime >= datetime.strptime(request.form['filter_start'], '%Y-%m-%d')
    ).filter(
        Workday.check_out_datetime <= datetime.strptime(request.form['filter_end'], '%Y-%m-%d')
    ).order_by(Workday.check_in_datetime).all()
    dur = sum([wd.get_duration() for wd in workdays], timedelta()).total_seconds()/3600
    return jsonify({'response': 200, 'dur': '%.2f' % dur,
                    'wd_dur': f'{ "%02d" % (wd.get_duration().seconds//3600) }:{ "%02d" % ((wd.get_duration().seconds//60)%60) }:{ "%02d" % (wd.get_duration().seconds%60) }'})


@app.route('/center/user/user/delete_wday/<wday_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_user_user_delete_wday(wday_id):
    wd = Workday.query.filter_by(id=int(wday_id)).first()
    user_id = wd.user_id
    db.session.delete(wd)
    db.session.commit()
    return redirect(url_for('center_user_user', user_id=user_id))


@app.route('/center/user/activate_role/<user_id>,<role_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_user_activate_role(user_id, role_id):
    db.session.add(Role_User_Attributes(role_id, user_id))
    db.session.commit()
    return redirect(url_for('center_user_user', user_id=user_id))


@app.route('/center/user/deactivate_role/<user_id>,<role_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_user_deactivate_role(user_id, role_id):
    role = Role.query.filter_by(id=int(role_id)).first()
    if role.name == 'Admin' and len(role.users) == 1:
        flash('Es muss mindestens ein Admin existieren.', 'danger')
        return redirect(url_for('center_user_user', user_id=user_id))
    else:
        db.session.delete(Role_User_Attributes.query.filter_by(role_id=int(role_id), user_id=int(user_id)).first())
        db.session.commit()
        return redirect(url_for('center_user_user', user_id=user_id))


######################################################################################

####################################   SETTINGS   ####################################

######################################################################################


@app.route('/center/settings', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings():
    return render_template('center/settings/index.html')

#SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB   PRODUCT   SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB#


@app.route('/center/settings/products/categories', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_categories():
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
    return render_template('center/settings/products/categories.html', product_categories=product_categories)


@app.route('/center/settings/products/category/<category_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_category(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    orphans = ProductCategory.query.filter(ProductCategory.parent_id == None).filter(ProductCategory.id!=category_id).all()
    successor_ids = [successor.id for successor in category.get_successors()]
    adopt_parents = ProductCategory.query.filter(ProductCategory.id.notin_(successor_ids)).all()
    family_ids = [member.id for member in category.get_family()]
    other_cats = ProductCategory.query.filter(ProductCategory.id.notin_(family_ids)).all()
    subquery = db.session.query(ProductCategory_ProductFeature.productfeature_id).filter(
        ProductCategory_ProductFeature.productcategory_id==int(category_id)
    ).all()
    poss_features = ProductFeature.query.filter(ProductFeature.id.notin_(subquery)).filter_by(source='lotus').order_by(ProductFeature.name).all()
    main_cats = ProductCategory.query.filter(ProductCategory.parent_id == None).all()
    mps = Marketplace.query.all()
    return render_template('center/settings/products/category.html', category=category, orphans=orphans, adopt_parents=adopt_parents, other_cats=other_cats, poss_features=poss_features,
                           main_cats=main_cats, mps=mps)


@app.route('/center/settings/products/category/update_mp_codes/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@csrf.exempt
@new_pageload
@roles_required('Admin')
def center_settings_products_category_update_mp_codes(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    mps = Marketplace.query.all()
    try:
        for mp in mps:
            mpc = Marketplace_ProductCategory.query.filter_by(marketplace_id=mp.id, productcategory_id=category.id).first()
            if mpc is None:
                db.session.add(Marketplace_ProductCategory(request.form[f'mp_code_{ mp.id }'], mp.id, category.id))
            else:
                mpc.marketplace_system_id = request.form[f'mp_code_{ mp.id }']
            db.session.commit()
            mpc = Marketplace_ProductCategory.query.filter_by(marketplace_id=mp.id, productcategory_id=category.id).first()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': str(e)})



@app.route('/center/settings/products/category/change_category/<category_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_category_change_category(category_id):
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


@app.route('/center/settings/products/category/edit_name/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_edit_category_name(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    category.name = request.form['name'].strip() if request.form['name'] else category.name
    db.session.commit()
    return redirect(url_for('center_settings_products_category', category_id=category_id))


@app.route('/center/settings/products/category/detach/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_detach_category(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    redirect_id = category.parent_id
    category.parent_id = None
    db.session.commit()
    return redirect(url_for('center_settings_products_category', category_id=redirect_id))


@app.route('/center/settings/products/category/detach_successors/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_detach_successors(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    redirect_id = category.parent_id
    for successor in category.get_successors():
        successor.parent_id = None
        db.session.commit()
    category.parent_id = None
    db.session.commit()
    return redirect(url_for('center_settings_products_category', category_id=redirect_id))


@app.route('/center/settings/products/category/adopt_child/<category_id>,<child_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_category_adopt_child(category_id, child_id):
    child = ProductCategory.query.filter_by(id=int(child_id)).first()
    child.parent_id = category_id
    db.session.commit()
    return redirect(url_for('center_settings_products_category', category_id=category_id))


@app.route('/center/settings/products/category/edit_parent/<category_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_edit_category_parent(category_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    category.parent_id = int(request.form['category']) if request.form['category'] else category.parent_id
    db.session.commit()
    return redirect(url_for('center_settings_products_category', category_id=category_id))


@app.route('/center/settings/products/category/transfer_features/<category_id>,<transfer_cat_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_category_transfer_features(category_id, transfer_cat_id):
    category = ProductCategory.query.filter_by(id=int(category_id)).first()
    for feat in category.productfeatures:
        db.session.delete(feat)
        db.session.commit()
    cfs = ProductCategory_ProductFeature.query.filter_by(productcategory_id=int(transfer_cat_id)).all()
    for cf in cfs:
        db.session.add(ProductCategory_ProductFeature(category.id, cf.productfeature_id))
        db.session.commit()
    return redirect(url_for('center_settings_products_category', category_id=category_id))


@app.route('/center/settings/products/category/detach_feature/<category_id>,<feature_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_category_detach_feature(category_id, feature_id):
    feature = ProductFeature.query.filter_by(id=int(feature_id)).first()
    check_cf = ProductCategory_ProductFeature.query.filter_by(productcategory_id=int(category_id), productfeature_id=int(feature_id)).first()
    if check_cf:
        db.session.delete(check_cf)
        db.session.commit()
    return jsonify({
        'status_code': 200,
        'feature_name': feature.name,
        'add_url': url_for('center_settings_products_category_add_feature', category_id=category_id, feature_id=feature_id)
    })


@app.route('/center/settings/products/category/add_feature/<category_id>,<feature_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_category_add_feature(category_id, feature_id):
    check_cf = ProductCategory_ProductFeature.query.filter_by(productcategory_id=int(category_id), productfeature_id=int(feature_id)).first()
    if not check_cf:
        new_cf = ProductCategory_ProductFeature(category_id, feature_id)
        db.session.add(new_cf)
        db.session.commit()
    return jsonify({
        'status_code': 200,
        'feature_name': new_cf.productfeature.name,
        'detach_url': url_for('center_settings_products_category_detach_feature', category_id=category_id, feature_id=feature_id)
    })


@app.route('/center/settings/products/features', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_features():
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
    return render_template('center/settings/products/features.html', product_features=product_features)


@app.route('/center/settings/products/links', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_links():
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
    return render_template('center/settings/products/links.html', product_link_categories=product_link_categories)

@app.route('/center/settings/products/change_cat_feature/<cat_id>,<feature_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_change_cat_feature(cat_id, feature_id):
    cat_feature = ProductCategory_ProductFeature.query.filter_by(productcategory_id=int(cat_id), productfeature_id=int(feature_id)).first()
    if cat_feature:
        db.session.delete(cat_feature)
    else:
        db.session.add(ProductCategory_ProductFeature(cat_id, feature_id))
    db.session.commit()
    return jsonify({})


@app.route('/center/settings/products/change_feature_active/<feature_id>')
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


@app.route('/center/settings/products/change_feature_fixed/<feature_id>')
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


@app.route('/center/settings/products/delete_feature/<feature_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_delete_feature(feature_id):
    feature = ProductFeature.query.filter_by(id=int(feature_id)).first()
    for entry in feature.values:
        db.session.delete(entry)
    db.session.delete(feature)
    db.session.commit()
    return redirect(url_for('center_product_settings'))


@app.route('/center/settings/products/delete_linkcategory/<linkcategory_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_delete_linkcategory(linkcategory_id):
    category = ProductLinkCategory.query.filter_by(id=int(linkcategory_id)).first()
    for link in category.links:
        db.session.delete(link)
        db.session.commit()
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('center_product_settings'))


@app.route('/center/settings/products/activate_category/<productcategory_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_activate_category(productcategory_id):
    ProductCategory.query.filter_by(id=int(productcategory_id)).first().active = True
    db.session.commit()
    return redirect(url_for('center_product_settings'))


@app.route('/center/settings/products/deactivate_category/<productcategory_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_deactivate_category(productcategory_id):
    ProductCategory.query.filter_by(id=int(productcategory_id)).first().active = False
    db.session.commit()
    return redirect(url_for('center_product_settings'))


@app.route('/center/settings/products/featurevalues/<id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_featurevalues(id):
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
                return redirect(url_for('center_settings_products_featurevalues', id=id))
        else:
            flash('Bitte gib einen Namen an.', 'danger')
    return render_template('center/settings/products/featurevalues.html', feature=feature, values=values)


@app.route('/center/settings/products/edit_featurename/<id>', methods=['POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_edit_featurename(id):
    feature = ProductFeature.query.filter_by(id=int(id)).first()
    feature.name = request.form['name']
    db.session.commit()
    return redirect(url_for('center_settings_products_featurevalues', id=id))


@app.route('/center/settings/products/activate_featurevalue/<id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_activate_featurevalue(id):
    ProductFeatureValue.query.filter_by(id=int(id)).first().active = True
    db.session.commit()
    return redirect(url_for('center_settings_products_featurevalues', id=ProductFeatureValue.query.filter_by(id=int(id)).first().productfeature_id))


@app.route('/center/settings/products//deactivate_featurevalue/<id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_deactivate_featurevalue(id):
    ProductFeatureValue.query.filter_by(id=int(id)).first().active = False
    db.session.commit()
    return redirect(url_for('center_settings_products_featurevalues', id=ProductFeatureValue.query.filter_by(id=int(id)).first().productfeature_id))


@app.route('/center/settings/products/delete_featurevalue/<id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_delete_featurevalue(id):
    value = ProductFeatureValue.query.filter_by(id=int(id)).first()
    back_id = value.productfeature_id
    db.session.delete(value)
    db.session.commit()
    return redirect(url_for('center_settings_products_featurevalues', id=back_id))


@app.route('/center/settings/products/featurevalue/<value_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_featurevalue(value_id):
    value = ProductFeatureValue.query.filter_by(id=int(value_id)).first()
    '''
    feature_values = ProductFeatureValue.query.outerjoin(
        Product_ProductFeatureValue
    ).filter(
        ProductFeatureValue.productfeature_id.in_(features)
    ).having(
        func.count(Product_ProductFeatureValue.id) >= 25
    ).group_by(
        ProductFeatureValue.id
    ).all()
    feature_ids = [fv.productfeature_id for fv in feature_values]
    ext_features = ProductFeature.query.filter(ProductFeature.id.in_(feature_ids)).order_by(ProductFeature.name).all()
    '''
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
    print('HI')
    return render_template('center/settings/products/featurevalue.html', value=value, ext_features=ext_features, first_id=ext_features[0][0].id)


@app.route('/center/settings/products/edit_featurevalue/<value_id>', methods=['POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_products_edit_featurevalue(value_id):
    feature = ProductFeatureValue.query.filter_by(id=int(value_id)).first()
    feature.value = request.form['value']
    db.session.commit()
    return redirect(url_for('center_settings_products_featurevalue', value_id=value_id))


@app.route('/center/settings/products/connect_ext_featurevalues/<value_id>,<ext_value_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_connect_ext_featurevalues(value_id, ext_value_id):
    ext_value = ProductFeatureValue.query.filter_by(id=int(ext_value_id)).first()
    ext_value.int_value_id = int(value_id)
    db.session.commit()
    return jsonify({'featurevalue': ext_value.value, 'feature': ext_value.productfeature.name})


@app.route('/center/settings/products/disconnect_ext_featurevalues/<ext_value_id>')
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_disconnect_ext_featurevalues(ext_value_id):
    ext_value = ProductFeatureValue.query.filter_by(id=int(ext_value_id)).first()
    ext_value.int_value_id = None
    db.session.commit()
    return jsonify({'featurevalue': ext_value.value, 'feature': ext_value.productfeature.name})


#SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB   MARKETPLACE   SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB#


@app.route('/center/settings/marketplaces', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_marketplaces():
    marketplaces = Marketplace.query.all()
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
    return render_template('center/settings/marketplaces/index.html', marketplaces=marketplaces,
                           productlinkcategories=productlinkcategories)


#SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB   SHIPPING   SUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUBSUB#


@app.route('/center/settings/shipping', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_shipping():
    shipping_services = ShippingService.query.order_by(ShippingService.international, ShippingService.name).all()
    shipping_providers = ShippingProvider.query.all()
    if request.method == 'POST':
        provider = request.form['provider'].strip()
        shipping_type = request.form['shipping_type'].strip()
        min_days = int(request.form['min_days'])
        max_days = int(request.form['max_days'])
        weight_g = int(request.form['weight_g'])
        height_cm = int(request.form['height_cm'])
        width_cm = int(request.form['width_cm'])
        depth_cm = int(request.form['depth_cm'])
        name = request.form['name'].strip()
        price = request.form['price']
        try:
            db.session.add(ShippingService(shipping_type, min_days, max_days, name, price, provider, weight_g, height_cm, width_cm, depth_cm))
        except Exception as e:
            flash(str(e), 'danger')
        db.session.commit()
        flash('Änderungen gespeichert.', 'success')
        return redirect(url_for('center_settings_shipping'))
    return render_template('center/settings/shipping.html', shipping_services=shipping_services, shipping_providers=shipping_providers)


@app.route('/center/settings/shipping/service/<service_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_shipping_service(service_id):
    shipping_service = ShippingService.query.filter_by(id=service_id).first()
    shipping_providers = ShippingProvider.query.all()
    marketplaces = Marketplace.query.all()
    mp_shipping_services = MPShippingService.query.filter_by(shipping_service_id=shipping_service.id).all()
    labels = dict((mps.marketplace_id, mps.code) for mps in mp_shipping_services)
    if request.method == 'POST':
        try:
            price = float(request.form['price'])
            if price != shipping_service.price:
                rep_datetime = datetime.now()
                shipping_service.serial_data.sort(key=lambda x: x.init_datetime, reverse=True)
                shipping_service.serial_data[-1].rep_datetime = rep_datetime
                db.session.add(ShippingServiceSD(price, service_id=shipping_service.id))
                shipping_service.price = price
                db.session.commit()
            for marketplace in marketplaces:
                code = request.form[f'code_{ marketplace.id }'].strip()
                if not code:
                    flash('Bitte gib für jeden Marketplace einen Code an.', 'danger')
                else:
                    mps = MPShippingService.query.filter_by(shipping_service_id=shipping_service.id, marketplace_id=marketplace.id).first()
                    if mps:
                        mps.code = code
                    else:
                        db.session.add(MPShippingService(code, marketplace.id, shipping_service.id))
            shipping_service.international = request.form['shipping_type'].strip()=='international'
            provider = request.form['provider'].strip()
            if provider != shipping_service.provider.name:
                check_provider = ShippingProvider.query.filter_by(name=provider).first()
                if not check_provider:
                    check_provider = ShippingProvider(provider)
                    db.session.add(check_provider)
                    db.session.commit()
                shipping_service.provider_id = check_provider.id
            min_days = int(request.form['min_days']) if request.form['min_days'] else None
            max_days = int(request.form['max_days']) if request.form['max_days'] else None
            weight_g = int(request.form['weight_g']) if request.form['weight_g'] else None
            height_cm = int(request.form['height_cm']) if request.form['height_cm'] else None
            width_cm = int(request.form['width_cm']) if request.form['width_cm'] else None
            depth_cm = int(request.form['depth_cm']) if request.form['depth_cm'] else None
            shipping_service.min_days = min_days if min_days is not None else shipping_service.min_days
            shipping_service.max_days = max_days if max_days is not None else shipping_service.max_days
            shipping_service.weight_g = weight_g if weight_g is not None else shipping_service.weight_g
            shipping_service.height_cm = height_cm if height_cm is not None else shipping_service.height_cm
            shipping_service.width_cm = width_cm if width_cm is not None else shipping_service.width_cm
            shipping_service.depth_cm = depth_cm if depth_cm is not None else shipping_service.depth_cm
            db.session.commit()
            flash('Änderungen gespeichert.', 'success')
        except Exception as e:
            print(e)
            flash(str(e), 'danger')
        return redirect(url_for('center_settings_shipping_service', service_id=service_id))
    return render_template('center/settings/shipping_service.html', shipping_service=shipping_service, marketplaces=marketplaces, labels=labels, shipping_providers=shipping_providers)


@app.route('/center/settings/shipping_profiles', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_shipping_profiles():
    shipping_profiles = ShippingProfile.query.all()
    shipping_services = ShippingService.query.all()
    marketplaces = Marketplace.query.all()
    mp_shipping_services = MPShippingService.query.all()
    mps_list = [f'{mps.marketplace_id}_{mps.shipping_service_id}' for mps in mp_shipping_services]
    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            service_dict = {}
            for mps in mp_shipping_services:
                price = request.form[f'price_{ mps.marketplace_id }_{ mps.shipping_service_id }']
                if not price:
                    flash('Bitte fülle alle möglichen Felder aus.', 'danger')
                    return redirect(url_for('center_settings_shipping_profiles'))
                service_dict[mps.id] = request.form[f'price_{ mps.marketplace_id }_{ mps.shipping_service_id }']
            db.session.add(ShippingProfile(name, service_dict))
            db.session.commit()
        except Exception as e:
            print(e)
            flash(str(e), 'danger')
        flash('Profil hinzugefügt.', 'success')
        return redirect(url_for('center_settings_shipping_profiles'))
    return render_template('center/settings/shipping_profiles.html', shipping_profiles=shipping_profiles, shipping_services=shipping_services, marketplaces=marketplaces, mps_list=mps_list)


@app.route('/center/settings/shipping_profile/<shipping_profile_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def center_settings_shipping_profile(shipping_profile_id):
    shipping_profile = ShippingProfile.query.filter_by(id=shipping_profile_id).first()
    shipping_services = ShippingService.query.all()
    marketplaces = Marketplace.query.all()
    mp_shipping_services = MPShippingService.query.all()
    mps_list = [f'{mps.marketplace_id}_{mps.shipping_service_id}' for mps in mp_shipping_services]
    price_dict = dict((f'{price.mp_service.marketplace_id}_{price.mp_service.shipping_service_id}', price.price) for price in shipping_profile.mp_services)
    if request.method == 'POST':
        shipping_profile.name = request.form['name'].strip()
        for mps in mp_shipping_services:
            price = request.form[f'price_{ mps.marketplace_id }_{ mps.shipping_service_id }']
            if not price:
                flash('Bitte fülle alle möglichen Felder aus.', 'danger')
                return redirect(url_for('center_settings_shipping_profile', shipping_profile_id=shipping_profile_id))
            spp = ShippingProfilePrice.query.filter_by(mp_service_id=mps.id, profile_id=shipping_profile.id).first()
            if not spp:
                db.session.add(ShippingProfilePrice(price, mps.id, shipping_profile.id))
            else:
                spp.update_price(price)
        db.session.commit()
        flash('Änderungen gespeichert.', 'success')
        return redirect(url_for('center_settings_shipping_profile', shipping_profile_id=shipping_profile_id))
    return render_template('center/settings/shipping_profile.html', shipping_profile=shipping_profile, shipping_services=shipping_services, marketplaces=marketplaces, mps_list=mps_list,
                           price_dict=price_dict)
