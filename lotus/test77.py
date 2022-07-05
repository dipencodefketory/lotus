from lotus import *
import ftplib
from datetime import *
from typing import List
from lookup import comma_split_features
import html2text
from PIL import Image
import idealo_offer
from ebaysdk.trading import Connection as Trading_Connection
import os
from dotenv import load_dotenv
from sqlalchemy import or_, and_
import pandas as pd

# import sys
# sys.path.append("/home")

# from lotus2.webapp.db.models import Category


print('hellllo test 77 gets executed')


category=['Sony PlayStation 5','Sony PlayStation 4','Xbox Series X','Xbox One','Nintendo Switch','Nintendo','Board games','Electronics & Household Supplies','Blu-ray','Audio','Xbox (XSX&X1)','Nintendo Switch 1st party']
product={'Spiele': [],'Gaming' : [],
        'Konsolen' : [],
        'Spielzeug' : [],
        'Electronics_Household_Supplies' : [],
        'DVDs_Blu_Rays' : [],
        'Gaming_Headsets' : [],
        'Kopfhörer' : [],
        'In_Ear_Kopfhörer' : []}

df = pd.read_excel('/home/lotus2/Price List Evergame (DE).xlsx', engine='openpyxl', skiprows=5)
df.pop('Region')
df.pop('Languages')
df.pop('Condition')
df.pop('GBP')
df.pop('USD')
df.pop('HKD')
df.columns = ['Category', 'Product', 'PID', 'QTY','Price']
df = df[df.PID.apply(lambda x: str(x).isnumeric())]
print(df)
spiele = ProductCategory.query.filter_by(name='Spiele').first()
print('spiele', spiele)
gaming = ProductCategory.query.filter_by(name='Gaming').first()
konsolen = ProductCategory.query.filter_by(name='Konsolen').first()
spielzeug = ProductCategory.query.filter_by(name='Spielzeug').first()
electronics_household_supplies = ProductCategory.query.filter_by(name='Electronics & Household Supplies').first()
dVDs_blu_rays = ProductCategory.query.filter_by(name='DVDs & Blu-Rays').first()
gaming_headsets = ProductCategory.query.filter_by(name='Gaming Headsets').first()
kopfhorer = ProductCategory.query.filter_by(name='Kopfhörer').first()
in_ear_kopfhoer = ProductCategory.query.filter_by(name='In-Ear-Kopfhörer').first()
rare_bundle = PricingBundle.query.filter_by(name='Standard-Bundle').first()
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
es = Stock.query.filter_by(id=12).first()
prc_tax = 19
avail_ts = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
term_ts = avail_ts+timedelta(days=1)
check_term_ts = avail_ts-timedelta(hours=1)
# write_filename = '/home/webapp/ws_data/Entspace_' + datetime.now().strftime('%Y_%m_%d') + '.csv'
for row in df.itertuples():
    hsp_id = str(row.PID)
    quant = str_to_int(row.QTY)
    price=row.Price
    if hsp_id:
        while len(hsp_id) < 13:
            hsp_id = '0' + hsp_id
    else:
        continue
    print('hsp_id\n',hsp_id)
    print(quant)
    print(str_to_float(price))
    p_name = row.Product
    product = Product.query.filter_by(hsp_id=hsp_id).first()
    if product is None:
        global_id = PrdGlobalID.query.filter_by(global_id_type='EAN', global_id=hsp_id).first()
        product = Product.query.filter_by(id=global_id.product_id).first() if global_id is not None else None
    if not product:
        print('------------')
        shipping_service = ShippingService.query.filter_by(name='DHL Paket').first()
        product = Product('EAN', hsp_id, name=p_name, mpn='nicht zutreffend', shipping_service_id=shipping_service.id)
        product.cheapest_stock_id = es.id
        product.cheapest_buying_price = price
        if row.Category in ['PS5 Games','PS4 Games','Xbox SX Games','Xbox One Games','Nintendo Switch Games','Wii U Games','Xbox (XSX&X1)','Nintendo Switch 1st party']:
            product.category_id = spiele.id
        elif row.Category in ['PS5 Accessories','PS4 Accessories','Xbox SX  Accessories','XBOXONE Accessories','NSW Accessories']:
            product.category_id = gaming.id
        elif row.Category in ['XBOXONE Hardware','NSW Hardware']:
            product.category_id = konsolen.id
        elif row.Category in ['Other','Accessories','Toys&Figures','Light Merchandise','Advent Calendar']:
            product.category_id = electronics_household_supplies.id
        elif row.Category in ['Blu-Ray']:
            product.category_id = dVDs_blu_rays.id
        elif row.Category in ['Headphones']:
            product.category_id = kopfhorer.id
        elif row.Category in ['Earbuds']:
            product.category_id = in_ear_kopfhoer.id
        elif row.Category in ['Board Games']:
            product.category_id = spielzeug.id
        elif row.Category in ['Headset']:
            product.category_id = gaming_headsets.id
        else:
            product.category_id = 1
        db.session.add(product)
        db.session.commit()
        psa = Product_Stock_Attributes('Neu & OVP', quant, price, None, prc_tax, None, avail_ts, term_ts, product.id, es.id, internal_id=hsp_id, sku=None)
        psa.last_seen = datetime.now()
        db.session.add(psa)
        db.session.commit()
        own_stock = Stock.query.filter_by(owned=True).first()
        product.add_basic_product_data(own_stock.id, dscrpt='', mpa_name=p_name,idealo_action=False)
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

# New project             
# if msg_p_ids:
#     msg = 'Folgende wertvolle Produkte sind bei EntSpace verfügbar:<br>'
#     i = 0
#     while i * 25 < len(msg_p_ids):
#         msg += ','.join([str(p_id) for p_id in msg_p_ids[i * 25:(i + 1) * 25]]) + '<br>'
#         i += 1
#     send_email(msg, 'Wertvolle Produkte bei EntSpace verfügbar!','system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de','developer@lotusicafe.de'])

# old project 

print('msg_p_ids',msg_p_ids)
if msg_p_ids:
    msg = 'Folgende wertvolle Produkte sind bei Evergame:<br>'
    i = 0
    while i * 25 < len(msg_p_ids):
        msg += ','.join([str(p_id) for p_id in msg_p_ids[i * 25:(i + 1) * 25]]) + '<br>'
        i += 1
    send_email('Wertvolle Produkte bei Evergame verfügbar!', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de','developer@lotusicafe.de'], msg, msg)
print('hellllo test 77 completed')