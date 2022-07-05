# -*- coding: utf-8 -*-

from lotus import db, env_vars_path
from basismodels import Product, ProductPicture, Marketplace, Marketplace_Product_Attributes, ProductCategory
from ebaysdk.trading import Connection as Trading_Connection
from datetime import datetime
import csv
import ftplib
import requests
import re
from functions import deumlaut
import os
from PIL import Image
import os
from os import environ
from dotenv import load_dotenv

load_dotenv(env_vars_path)

trading_api = Trading_Connection(https=True, config_file=os.path.abspath(environ.get('EBAY_API_PATH')), domain="api.ebay.com", siteid='77')

toy_cat = ProductCategory.query.filter_by(id=27).first()
toy_cats = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]
ps = Product.query.all()
update_hsp_ids = []
for p in ps:
    update_pictures = False
    if len(p.pictures)<2:
        update_pictures = True
    for pic in p.pictures:
        if 'generic' in pic.link:
            update_pictures = True
            break
    if update_pictures:
        update_hsp_ids.append(p.hsp_id)
print('Products found')
print('Starting Vitrex')
vitrex_csv = '/home/lotus/lager/Vitrex_' + datetime.now().strftime('%Y_%m_%d') + '.csv'
with open(vitrex_csv, encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';', dialect=csv.excel)
    keys = []
    i=0
    for row in csv_reader:
        if i==0:
            for key in row:
                keys.append(key)
                print(key)
            print('-----------')
            i+=1
        internal_id = row[keys[0]].strip()
        hsp_id = row['EAN'].strip()
        if hsp_id == '' or hsp_id.isnumeric()==False:
            hsp_id = internal_id
        while len(hsp_id) < 13:
            hsp_id = '0' + hsp_id
        if hsp_id in update_hsp_ids and row['Jpg-Pfad']:
            p = Product.query.filter_by(hsp_id=hsp_id).first()
            print(p.id)
            for picture in p.pictures:
                db.session.delete(picture)
                db.session.commit()
            j=0
            if p.category_id not in toy_cats:
                session = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')
                try:
                    pic_link = row['Jpg-Pfad']
                    product_id = pic_link.split('/')[-1].split('.')[0]
                    page = requests.get(pic_link)
                    while page.status_code == 200:
                        file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(p.name)) + str(j + 1) + '.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                        with open(file_name, 'wb') as f:
                            f.write(page.content)
                        with Image.open(file_name) as img:
                            width, height = img.size
                            if width < 500 and height < 500:
                                if width < height:
                                    new_width = 500
                                    new_height = 500 * height // width
                                else:
                                    new_height = 500
                                    new_width = 500 * width // height
                                new_img = img.resize((new_width, new_height))
                                new_img = new_img.convert('RGB')
                                new_img.save(f'{file_name}', 'JPEG')
                        file = open(f'{file_name}', 'rb')
                        session.storbinary('STOR ' + file_name, file)
                        file.close()
                        os.remove(file_name)
                        j += 1
                        file_name = product_id + '_' + str(j) + '.jpg'
                        url = 'https://bilderserver.vitrex.de/' + file_name
                        page = requests.get(url)
                except:
                    pass
                session.quit()
            if j == 1:
                while j <= 1:
                    file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(p.name)) + str(j + 1) + '.jpg'
                    db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                    j += 1
            elif j==0:
                while j <= 1:
                    file_name = 'generic_pic.jpg'
                    db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                    j += 1
            if j >= 1:
                marketplace = Marketplace.query.filter_by(name='Ebay').first()
                mpa = Marketplace_Product_Attributes.query.filter_by(marketplace_id=marketplace.id,
                                                                     product_id=p.id).first()
                if mpa.uploaded and len(mpa.descriptions) > 1:
                    try:
                        r = p.mp_update(int(marketplace.id), title=True, price=True, shipping_cost=True, shipping_time=True, brand=True, ean=True, mpn=True, quantity=True, images=True,
                                        description=True, features=True, category=True)
                    except Exception as e:
                        print(e)
            db.session.commit()
print('Vitrex done')
print('Starting Entertainment-Trading')
ent_trading_csv = '/home/lotus/lager/Enttrading_' + datetime.now().strftime('%Y_%m_%d') + '.csv'
with open(ent_trading_csv, encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';', dialect=csv.excel)
    for row in csv_reader:
        hsp_id = row['ean'].strip()
        if hsp_id:
            while len(hsp_id) < 13:
                hsp_id = '0' + hsp_id
            if hsp_id in update_hsp_ids and row['image']:
                p = Product.query.filter_by(hsp_id=hsp_id).first()
                print(p.id)
                for picture in p.pictures:
                    db.session.delete(picture)
                    db.session.commit()
                j = 0
                if p.category_id not in toy_cats:
                    session = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')
                    try:
                        product_id = row['image'].split('/')[-1].split('.')[0]
                        page = requests.get(row['image'])
                        file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(p.name)) + str(j + 1) + '.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                        with open(file_name, 'wb') as f:
                            f.write(page.content)
                        with Image.open(file_name) as img:
                            width, height = img.size
                            if width < 500 and height < 500:
                                if width < height:
                                    new_width = 500
                                    new_height = 500 * height // width
                                else:
                                    new_height = 500
                                    new_width = 500 * width // height
                                new_img = img.resize((new_width, new_height))
                                new_img = new_img.convert('RGB')
                                new_img.save(f'{file_name}', 'JPEG')
                        file = open(f'{file_name}', 'rb')
                        session.storbinary('STOR ' + file_name, file)
                        file.close()
                        os.remove(file_name)
                        j += 1
                    except:
                        pass
                    session.quit()
                if j == 1:
                    while j <= 1:
                        file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(p.name)) + str(j + 1) + '.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                        j += 1
                else:
                    while j <= 1:
                        file_name = 'generic_pic.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, p.id))
                        j += 1
                db.session.commit()
