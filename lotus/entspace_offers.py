# -*- coding: utf-8 -*-

from lotus import db, send_email
from basismodels import Product, ShippingService, Product_Stock_Attributes, PSAUpdateQueue, PricingAction, Stock, PrdGlobalID, PricingBundle
from datetime import datetime, timedelta
import pandas as pd
from functions import str_to_float, str_to_int
from sqlalchemy import or_, and_


url = 'https://powerplay.us19.list-manage.com/track/click?u=dfbeb5d8b215da6c579482771&id=cdab3c510c&e=1e7b2e4370'
df = pd.read_excel(url, engine='openpyxl', skiprows=6)
df.rename(columns={'ID:': 'PID'}, inplace=True)
df.rename(columns={'Product:': 'Product'}, inplace=True)
df.rename(columns={'Qty:': 'Qty'}, inplace=True)
df.rename(columns={'Euro price:': 'Price'}, inplace=True)
df.rename(columns={'Details:': 'Details'}, inplace=True)
df = df[df.PID.apply(lambda x: str(x).isnumeric())]
print(df)

rare_bundle = PricingBundle.query.filter_by(name='Rare').first()

query = db.session.query(
    Product, PricingAction
).filter(
    Product.id == PricingAction.product_id,
    or_(
        and_(
            PricingAction.active == True,
            PricingAction.name.in_(['Marktpreis 20%', 'Marktpreis 25%', 'Marktpreis 30%', 'Marktpreis 35%', 'Marktpreis 40%', 'Marktpreis 45%', 'Marktpreis 50%', 'Marktpreis 55%', 'Kuchenboden', 'Fix Preis'])
        ),
        Product.pricing_bundle_id == rare_bundle.id if rare_bundle is not None else True
    )
).all()

val_p_ids = [p.id for p, _ in query]
msg_p_ids = []

platform_dict = {'XONE/X360': 'Xbox ONE', 'X360/XONE': 'Xbox ONE', 'XONE': 'Xbox ONE', 'XSX/XONE': 'Xbox Series X', 'XONE/XSX': 'Xbox Series X', 'XSX': 'Xbox Series X', 'SWITCH': 'Nintendo Switch', '3DS': 'Nintendo 3DS',
                 'PC': 'PC', 'PS4': 'PS4 / PlayStation 4', 'PS5': 'PS5 / PlayStation 5', 'PS4/PS5': 'PS5 / PlayStation 5', 'PS5/PS4': 'PS5 / PlayStation 5', 'HW': 'Hardware', 'HWC': 'Hardware', 'MERCH': 'Merchandise'}
es = Stock.query.filter_by(id=8).first()
prc_tax = 19
avail_ts = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
term_ts = avail_ts+timedelta(days=1)
check_term_ts = avail_ts-timedelta(hours=1)
write_filename = 'Entspace_' + datetime.now().strftime('%Y_%m_%d') + '.csv'#/home/lotus/lager/
other_platforms = []
with open(write_filename, 'w', newline='') as csvfile:
    for row in df.itertuples():
        platform, name = row.Product.split(" ", 1)
        if platform in ['XONE/X360', 'X360/XONE', 'XONE', 'XONE/XSX', 'XSX/XONE', 'XSX', 'SWITCH', '3DS', 'PC', 'PS4', 'PS4/PS5', 'PS5/PS4', 'PS5', 'HW', 'HWC', 'MERCH']:
            hsp_id = str(row.PID)
            quant = str_to_int(row.Qty)
            price = (100 * row.Price) // 1 / 100
            if price <= 0:
                continue
            details = row.Details
            if hsp_id:
                while len(hsp_id) < 13:
                    hsp_id = '0' + hsp_id
            else:
                continue
            print(hsp_id)
            print(quant)
            print(price)
            print(details)
            print(platform)
            print(name)
            product = Product.query.filter_by(hsp_id=hsp_id).first()
            if product is None:
                global_id = PrdGlobalID.query.filter_by(global_id_type='EAN', global_id=hsp_id).first()
                product = Product.query.filter_by(id=global_id.product_id).first() if global_id is not None else None
            if not product:
                print('NEW')
                print(hsp_id)
                print(name)
                print('------------')
                shipping_service = ShippingService.query.filter_by(name='DHL Paket 18').first()
                product = Product('EAN', hsp_id, name=f'{name} - {platform_dict[platform]}', mpn='nicht zutreffend', shipping_service_id=shipping_service.id)
                product.cheapest_stock_id = es.id
                product.cheapest_buying_price = price
                db.session.add(product)
                db.session.commit()
                psa = Product_Stock_Attributes('Neu & OVP', quant, price, None, prc_tax, None, avail_ts, term_ts, product.id, es.id, internal_id=hsp_id, sku=None)
                psa.last_seen = datetime.now()
                db.session.add(psa)
                db.session.commit()
                own_stock = Stock.query.filter_by(owned=True).first()
                product.add_basic_product_data(own_stock.id, dscrpt=details, mpa_name=f'{name} - {platform_dict[platform]} - Neu & OVP')
                db.session.add(PSAUpdateQueue(product.id))
                db.session.commit()
            else:
                if product.id in val_p_ids:
                    msg_p_ids.append(product.id)
                check_psa = Product_Stock_Attributes.query.filter_by(
                    product_id=product.id, stock_id=es.id, user_generated=True
                ).filter(
                    Product_Stock_Attributes.avail_date < datetime.now()
                ).filter(
                    Product_Stock_Attributes.termination_date > datetime.now()
                ).first()
                if check_psa:
                    db.session.delete(check_psa)
                    db.session.commit()

                avail_psa = Product_Stock_Attributes.query.filter_by(
                    product_id=product.id, stock_id=es.id
                ).filter(
                    Product_Stock_Attributes.avail_date < datetime.now()
                ).filter(
                    Product_Stock_Attributes.termination_date > check_term_ts
                ).first()
                if avail_psa:
                    avail_psa.self_update(termination_date=term_ts, quantity=quant, buying_price=price)
                else:
                    psa = Product_Stock_Attributes('Neu & OVP', quant, price, None, prc_tax, None, avail_ts, term_ts, product.id, es.id, internal_id=hsp_id, sku=None)
                    psa.last_seen = datetime.now()
                    db.session.add(psa)
                    db.session.add(PSAUpdateQueue(product.id))
                    db.session.commit()
        else:
            other_platforms.append(platform) if platform not in other_platforms else None
print(other_platforms)
if msg_p_ids:
    msg = 'Folgende wertvolle Produkte sind bei EntSpace verfügbar:<br>'
    i = 0
    while i * 25 < len(msg_p_ids):
        msg += ','.join([str(p_id) for p_id in msg_p_ids[i * 25:(i + 1) * 25]]) + '<br>'
        i += 1
    send_email('Wertvolle Produkte bei EntSpace verfügbar!', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de'], msg, msg)