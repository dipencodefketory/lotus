# -*- coding: utf-8 -*-

from lotus import db, env_vars_path, send_email, tax_group
from basismodels import (Product, Marketplace_Product_Attributes, Marketplace, Sale, PricingLog, Stock, Product_Stock_Attributes, PricingAction, PreOrder, ShippingService, MPShippingService,
                         ShippingProfilePrice, PricingRule, PPrRule, StockUpdateQueue)
from functions import str_to_float, money_to_float, marketplace_price_performance_measure, add_business_days
import afterbuy_api
import idealo_offer

from ebaysdk.trading import Connection as Trading_Connection
import os
from os import environ
from dotenv import load_dotenv
import xml.etree.ElementTree as ETree
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, case


load_dotenv(env_vars_path)

headers = {'Content-Type': 'application/xml'}
r = afterbuy_api.get_sold_items({'DateFilter': ['AuctionEndDate', (datetime.now()-timedelta(hours=6)).strftime('%d.%m.%Y %H:%M:%S'), datetime.now().strftime('%d.%m.%Y %H:%M:%S')]})
tree = ETree.fromstring(r.text)
orders = []
own_stock = Stock.query.filter_by(owned=True).order_by(Stock.id).first()
for order in tree.findall('.//Order'):
    print('-----------------')
    platform = order.find('.//ItemPlatformName')
    customer_uname = order.find('.//UserIDPlattform')
    if platform.text=='105168_lotusicafe' or '105168_lotusicafe' in customer_uname.text:
        print('Idealo')
        marketplace = Marketplace.query.filter_by(name='Idealo').first()
        authorization = idealo_offer.get_access_token()
    else:
        print('Ebay')
        marketplace = Marketplace.query.filter_by(name='Ebay').first()
        authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", escape_xml=True, siteid='77')
    try:
        order_date = datetime.strptime(order.find('.//OrderDate').text, '%d.%m.%Y %H:%M:%S')
    except Exception as e:
        print(e)
        try:
            order_date = datetime.strptime(order.find('.//OrderDate').text, '%d.%m.%Y')
        except Exception as e:
            print(e)
            continue
    order_id = order.find('.//OrderID').text
    mp_order_id = order.find('.//OrderIDAlt').text
    mp_order_id = order.find('.//PlatformSpecificOrderId').text if mp_order_id is None else mp_order_id
    mp_order_id = order.find('.//AlternativeItemNumber1').text if mp_order_id is None else mp_order_id
    shipping_total = str_to_float(money_to_float(order.find('.//ShippingTotalCost').text))
    print(order_date)
    print(order_id)
    print(shipping_total)
    check_sale = Sale.query.filter_by(order_number=order_id).first()
    if check_sale is None:
        sh_info = order.find('.//ShippingAddress')
        if sh_info is not None:
            country = sh_info.find('.//Country').text if sh_info.find('.//Country').text is not None else ''
            international = False if country == 'D' else True
        else:
            international = False if order.find('.//Country').text == 'D' else True
        for item in order.findall('.//SoldItem'):
            from_own_stock = True
            short_sell = False
            pre_order = False
            internal_id = item.find('.//ProductID')
            product = None
            if internal_id is not None:
                product = Product.query.filter_by(internal_id=internal_id.text).first()
            elif marketplace.name == 'Ebay':
                ebay_id = item.find('.//Anr')
                if ebay_id is not None:
                    mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_system_id=ebay_id.text, marketplace_id=marketplace.id).first()
                    if mpa:
                        product = mpa.product
                    else:
                        continue
            if product is None:
                print('FAILED')
                continue
            tags = []
            own_real_stock = product.get_own_real_stock()
            if own_real_stock <= 0:
                tags.append('LVK')
                from_own_stock = False
                short_sell = True
                sendable_by = None
            else:
                sendable_by = datetime.now()
            if product.release_date:
                if product.release_date > datetime.now():
                    tags.append('PRE ORDER')
                    pre_order = True
            if tags:
                orders.append({'order_id': order_id, 'tags': tags})
            psa = Product_Stock_Attributes.query.filter_by(stock_id=own_stock.id, product_id=product.id).first()
            quantity = int(item.find('.//ItemQuantity').text)
            selling_price = str_to_float(money_to_float(item.find('.//ItemPrice').text))
            if selling_price < 0:
                quantity *= -1
                selling_price *= -1
                shipping_total *= -1
                cancelled_sale = Sale.query.filter_by(mp_order_id=mp_order_id).filter(and_(Sale.quantity > 0, Sale.selling_price > 0)).first()
                if cancelled_sale:
                    cancelled_sale.cancelled = True
                    db.session.commit()
            print(product.internal_id)
            print(quantity)
            print(selling_price)
            t_mpa = None
            for mpa in product.marketplace_attributes:
                if mpa.marketplace_id == marketplace.id:
                    t_mpa = mpa
                mpa.curr_stock -= quantity
                if mpa.curr_stock < mpa.min_stock or mpa.curr_stock > mpa.max_stock:
                    mpa.curr_stock = min(max(0, product.get_own_stock() - mpa.quantity_delta - quantity if mpa.quantity_delta else product.get_own_stock() - quantity), mpa.max_stock)
                if mpa.uploaded:
                    mpa.update_quantity = mpa.curr_stock
                    mpa.update = True
                db.session.commit()
            log = PricingLog.query.filter(
                PricingLog.product_id == product.id
            ).filter(
                PricingLog.set_date <= order_date
            ).filter(
                PricingLog.marketplace_id == marketplace.id
            ).order_by(
                PricingLog.set_date.desc()
            ).first()
            print(f'LOG-QUERY:{log}')
            if log is None:
                log = product.add_pricing_log(marketplace.id, selling_price, psa.id)
            else:
                if log.pricingstrategy:
                    if log.pricingstrategy.pricingaction.sale_count:
                        log.pricingstrategy.pricingaction.sale_count += quantity
                    else:
                        log.pricingstrategy.pricingaction.sale_count = quantity
                    if log.pricingstrategy.sale_count:
                        log.pricingstrategy.sale_count+=quantity
                    else:
                        log.pricingstrategy.sale_count=quantity
                    if log.pricingstrategy.pricingaction.promotion_quantity!=None:
                        activate = False
                        if log.pricingstrategy.pricingaction.sale_count >= log.pricingstrategy.pricingaction.promotion_quantity:
                            log.pricingstrategy.pricingaction.active = False
                            for strategy in log.pricingstrategy.pricingaction.strategies:
                                strategy.active = False
                            activate = True
                        db.session.commit()

                        if activate:
                            # noinspection PyComparisonWithNone
                            query = db.session.query(
                                PricingAction
                            ).filter(
                                PricingAction.product_id == product.id
                            ).filter(
                                PricingAction.promotion_quantity != None
                            ).filter(
                                PricingAction.sale_count != None
                            ).all()

                            ids = [item.id for item in query if item.sale_count >= item.promotion_quantity]

                            pa = db.session.query(
                                PricingAction
                            ).filter(
                                PricingAction.start <= datetime.now()
                            ).filter(
                                PricingAction.end >= datetime.now()
                            ).filter(
                                PricingAction.product_id == product.id
                            ).filter(
                                PricingAction.archived == False
                            ).filter(
                                PricingAction.id.notin_(ids)
                            ).order_by(
                                PricingAction.id.desc()
                            ).first()

                            if pa:
                                pa.active = True
                                for strategy in pa.strategies:
                                    strategy.active = True       
                                    db.session.commit()     
                                    if strategy.marketplace.name == 'Idealo':
                                        authorization = idealo_offer.get_access_token()
                                    elif strategy.marketplace.name == 'Ebay':
                                        authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_ROOT')), domain="api.ebay.com", escape_xml=True, siteid='77')
                                    else:
                                        print(f'Marketplace-Upload for {strategy.marketplace.name} not implemented.', 'danger')
                                        continue
                                    product.generate_mp_price(marketplace_id=strategy.marketplace_id, strategy_label=strategy.label, min_margin=strategy.prc_margin/100 if strategy.prc_margin is not None else None,
                                                              max_margin=strategy.prc_max_margin/100 if strategy.prc_max_margin is not None else None, rank=strategy.rank if strategy.rank else 0,
                                                              ext_offers=product.get_mp_ext_offers(strategy.marketplace_id), authorization=authorization)
            print('ADDED')
            query = db.session.query(ShippingService, MPShippingService, ShippingProfilePrice).filter(
                or_(ShippingService.id == product.nat_shipping_1_id,
                    ShippingService.id == product.nat_shipping_2_id,
                    ShippingService.id == product.nat_shipping_3_id,
                    ShippingService.id == product.nat_shipping_4_id)
            ).filter(
                MPShippingService.shipping_service_id == ShippingService.id
            ).filter(
                MPShippingService.marketplace_id == marketplace.id
            ).filter(
                ShippingProfilePrice.profile_id == product.shipping_profile_id
            ).filter(
                ShippingProfilePrice.mp_service_id == MPShippingService.id
            ).all()
            if not query:
                raise SystemError('Shipping needs to be configured for this Product.')
            _, i = min((row[2].price - row[0].price, i) for (i, row) in enumerate(query))
            own_shipping = query[i][0].price
            chp_margin = marketplace_price_performance_measure(marketplace.name, selling_price, shipping_total, own_shipping, product.cheapest_buying_price, t_mpa.commission,
                                                               tax_group[product.tax_group]['national' if not international else 'international'])['prc_margin']
            own_margin = marketplace_price_performance_measure(marketplace.name, selling_price, shipping_total, own_shipping, product.buying_price, t_mpa.commission,
                                                               tax_group[product.tax_group]['national' if not international else 'international'])['prc_margin']
            delta = log.product_stock_attributes.stock.lag_days * int(own_real_stock <= 0) + int(order_date.hour >= 9) * 1
            delta += product.productcategory.get_stock_ship_days(log.product_stock_attributes.stock_id) * int(own_real_stock <= 0) if product.productcategory else 0
            new_sale = Sale(order_id, order_date, quantity, product.cheapest_buying_price, product.buying_price, selling_price, shipping_total, chp_margin, own_margin, marketplace.id, log.id, from_own_stock,
                            short_sell, pre_order, international)
            new_sale.mp_order_id = mp_order_id
            new_sale.sendable_by = sendable_by
            if quantity > 0:
                new_sale.send_by = add_business_days(datetime.now().replace(hour=16, minute=0, second=0, microsecond=0), delta)
                if product.release_date:
                    if product.release_date > datetime.now():
                        new_sale.send_by = add_business_days(product.release_date.replace(hour=16, minute=0, second=0, microsecond=0), delta)
                new_sale.deliver_by = add_business_days(new_sale.send_by, 3)
            db.session.add(new_sale)
            db.session.commit()
            db.session.add(StockUpdateQueue(-1 * quantity, psa.id, curr_stock=psa.quantity))
            db.session.commit()

            if product.release_date:
                if product.release_date >= datetime.now() - timedelta(days=5):
                    print('--------PreOrder--------')
                    print(product.id)
                    preorder = PreOrder.query.filter_by(product_id=product.id).first()
                    if not preorder:
                        print('NEW')
                        print(quantity)
                        db.session.add(PreOrder(quantity, product.id))
                    else:
                        print('ADD')
                        print(preorder.sales)
                        print(quantity)
                        preorder.sales += quantity
                    db.session.commit()
                    print('-------------------------')

            num, p_id = db.session.query(
                func.sum(Sale.quantity), PricingLog.product_id
            ).filter(
                Sale.pricinglog_id == PricingLog.id
            ).filter(
                PricingLog.product_id == product.id
            ).filter(
                Sale.timestamp > datetime.now()-timedelta(hours=24)
            ).group_by(
                PricingLog.product_id
            ).first()
            for mpa in product.marketplace_attributes:
                if num > mpa.max_stock != 0:
                    old_max_stock = mpa.max_stock
                    mpa.min_stock = 0
                    mpa.max_stock = 0
                    mpa.curr_stock = 0
                    if mpa.uploaded:
                        product.mp_prq_update(marketplace_id=mpa.marketplace_id, shipping_time=False, quantity=True, price=False, shipping_cost=False, custom_quantity=mpa.curr_stock, authorization=authorization, check_clearance=False)
                    db.session.commit()
                    msg = f'Das Produkt\n\n{product.id} - {product.name}\n\nwurde in den letzten 24 Stunden auf {mpa.marketplace.name} mehr als {old_max_stock} verkauft und sein Marketplace-Bestand daher auf Null gesetzt.'
                    send_email(f'Sale-Alarm - {product.id} - {product.name}', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de', 'benjamin.hahn@lotusicafe.de'], msg, msg)
            try:
                if product.pricing_bundle_id:
                    subquery = db.session.query(
                        PricingAction.name.label('name')
                    ).filter(
                        and_(
                            PricingAction.active == True,
                            PricingAction.product_id == product.id
                        )
                    ).subquery()
                    query = db.session.query(
                        PricingAction, PricingRule.if_sale_suc_h, PricingRule.if_sale_num, PricingRule.if_sale_rev
                    ).join(
                        PricingRule, PricingRule.then_strategy == PricingAction.name
                    ).join(
                        subquery, PricingRule.if_strategy == subquery.c.name
                    ).filter(
                        and_(
                            PricingRule.pricing_bundle_id == product.pricing_bundle_id,
                            PricingAction.product_id == product.id,
                            PricingRule.if_sale_suc_h != None
                        )
                    ).order_by(
                        case([(PricingAction.name == PricingRule.if_strategy, 'if')], else_='then')
                    ).first()
                    if query:
                        new_pa, suc_h, num, rev = query
                        sales = db.session.query(
                            PricingLog.product_id, func.sum(Sale.quantity), func.sum(Sale.selling_price + Sale.shipping_price)
                        ).join(
                            PricingLog, PricingLog.id == Sale.pricinglog_id
                        ).filter(
                            and_(
                                PricingLog.product_id == product.id,
                                Sale.timestamp >= datetime.now() - timedelta(suc_h),
                                Sale.quantity > 0
                            )
                        ).group_by(
                            PricingLog.product_id
                        ).having(
                            and_(
                                func.sum(Sale.quantity) >= num if num is not None else True,
                                func.sum(Sale.selling_price + Sale.shipping_price) >= rev if rev is not None else True,
                            )
                        ).first()
                        if sales:
                            for pa in new_pa.product.actions:
                                for strategy in pa.strategies:
                                    strategy.active = False
                                pa.active = False
                                db.session.commit()
                            pa = new_pa
                            pa.active = True
                            for strategy in pa.strategies:
                                strategy.active = True
                            db.session.commit()
                            for strategy in pa.strategies:
                                if strategy.marketplace.name == 'Idealo':
                                    authorization = idealo_offer.get_access_token()
                                elif strategy.marketplace.name == 'Ebay':
                                    authorization = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_ROOT')), domain="api.ebay.com", escape_xml=True, siteid='77')
                                else:
                                    print(f'Marketplace-Upload for {strategy.marketplace.name} not implemented.', 'danger')
                                    continue
                                product.generate_mp_price(marketplace_id=strategy.marketplace_id, strategy_label=strategy.label, min_margin=strategy.prc_margin / 100 if strategy.prc_margin is not None else None,
                                                          max_margin=strategy.prc_max_margin / 100 if strategy.prc_max_margin is not None else None, rank=strategy.rank if strategy.rank else 0,
                                                          ext_offers=product.get_mp_ext_offers(strategy.marketplace_id), authorization=authorization)
            except Exception as e:
                print(e)
if orders:
    print(orders)
    result = afterbuy_api.update_sold_items(orders)
    print(result.status_code)
    print(result.text)
