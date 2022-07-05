# -*- coding: utf-8 -*-

from lotus import *
import requests
from requests.auth import HTTPBasicAuth
import csv
from lookup import comma_split_features
import html2text
from PIL import Image

h = html2text.HTML2Text()
h.body_width = 0

username = 'lotusicafe-de'
password = 'GWle==-**^lX'

r = requests.get('https://feeds.entertainment-trading.com/3728900-lotusicafe.csv', auth=HTTPBasicAuth(username, password))
r.encoding = 'utf-8'
csv_reader = csv.DictReader(r.text.strip().split('\n'), delimiter=';', dialect=csv.excel)

et = Stock.query.filter_by(id=6).first()
et_link_cat = ProductLinkCategory.query.filter_by(id=13).first()
prc_tax = 19

region_dict = {'German': 'USK', 'English': 'UK', 'Nordic': 'Nordic', 'Finnish': 'Nordic', 'Danish': 'Nordic', 'Norwegian': 'Nordic', 'Swedish': 'Nordic', 'French': 'EU', 'Italian': 'EU',
               'Import': 'PEGI', '': 'PEGI', 'Australia': 'AUS', 'Spanish': 'PEGI'}
i=0
write_filename = '/home/lotus/lager/Enttrading_' + datetime.now().strftime('%Y_%m_%d') + '.csv'
found = False
with open(write_filename, 'w', newline='') as csvfile:
    for row in csv_reader:
        spamwriter = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        if i==0:
            spamwriter.writerow([key for key in row])
            i+=1
            for key in row:
                print(key)
            print('-----------')
        spamwriter.writerow([row[key] for key in row])
        if row['platform'] in ['Xbox One', 'Nintendo Switch', 'Xbox Series X', 'Nintendo 3DS', 'PC', 'PlayStation 4', 'PlayStation 5']:
            region = region_dict[row['Region']]
            name = f'{row["title"]} - {row["platform"]}'
            name += f' - {region}' if region else ''
            hsp_id = row['ean']
            if hsp_id:
                while len(hsp_id) < 13:
                    hsp_id = '0' + hsp_id
            else:
                continue
            if not found:
                if hsp_id == '5030948122422':
                    found = True
                continue
            else:
                found = True
            product = Product.query.filter_by(hsp_id=hsp_id).first()
            if not product:
                release_date = datetime.strptime(row["release_date"], '%Y-%m-%d') if row["release_date"] else None
                product = Product('EAN', hsp_id, name=name, brand=row["brand"], mpn='nicht zutreffend', release_date=release_date)
                product.measurements = row["Length (cm)"] + 'x' + row["Width (cm)"] + 'x' + row["Height (cm)"]
                product.category_id = 1
                db.session.add(product)
                db.session.commit()
                psa = Product_Stock_Attributes('Neu & OVP', str_to_int(row["stock"]), str_to_float(row["price"]), None, prc_tax, None, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                               datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, et.id, internal_id=row['id'], sku=row['sku'])
                psa.last_seen = datetime.now()
                db.session.add(psa)
                db.session.commit()

                own_stock = Stock.query.filter_by(owned=True).first()

                psa = Product_Stock_Attributes('Neu & OVP', 0, None, None, None, None,
                                               datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                               datetime.now().replace(year=2100, month=1, day=1, hour=23, minute=59, second=59, microsecond=999999), product.id, own_stock.id)

                psa.last_seen = datetime.now()
                db.session.add(psa)
                db.session.commit()

                if row['usk_on_disc'] in ['0+', '6+', '12+', '15+', '16+']:
                    lotus_shipping_dhl = 3.55
                    shipping_dhl_cost = 2.99
                else:
                    lotus_shipping_dhl = 4.54
                    shipping_dhl_cost = 4.99

                product.add_basic_product_data(own_stock.id, lotus_shipping_dhl=lotus_shipping_dhl, shipping_dhl_cost=shipping_dhl_cost, dscrpt=h.handle(row["description"]))


                db.session.add(ProductLink(f'https://business.coolshop.co.uk/video-games-and-consoles/?q={product.hsp_id}', et_link_cat.id, product.id))

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
                j = 0
                session = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')
                try:
                    product_id = row['image'].split('/')[-1].split('.')[0]

                    page = requests.get(row['image'])
                    file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(name)) + str(j+1) + '.jpg'
                    db.session.add(ProductPicture(min(j, 2), file_name, product.id))
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
                    while j<=1:
                        file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(name)) + str(j+1) + '.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                        j += 1

                else:
                    while j<=1:
                        file_name = 'generic_pic.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                        j += 1
                db.session.commit()

            else:
                checklink = ProductLink.query.filter_by(product_id=product.id, category_id=et_link_cat.id).first()
                if checklink:
                    if checklink.link == '':
                        checklink.link = f'https://business.coolshop.co.uk/video-games-and-consoles/?q={product.hsp_id}'
                        db.session.commit()
                else:
                    db.session.add(ProductLink(f'https://business.coolshop.co.uk/video-games-and-consoles/?q={product.hsp_id}', et_link_cat.id, product.id))
                    db.session.commit()
                if row["release_date"]:
                    release_date = datetime.strptime(row["release_date"], '%Y-%m-%d') if row["release_date"] else None
                    product.release_date = release_date
                check_psa = Product_Stock_Attributes.query.filter_by(
                    product_id=product.id, stock_id=et.id, user_generated=True
                ).filter(
                    Product_Stock_Attributes.avail_date < datetime.now()
                ).filter(
                    Product_Stock_Attributes.termination_date > datetime.now()
                ).first()

                if check_psa:
                    db.session.delete(check_psa)
                    db.session.commit()

                psa = Product_Stock_Attributes('Neu & OVP', str_to_int(row["stock"]), str_to_float(row["price"]), None, prc_tax, None, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                               datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, et.id, internal_id=row['id'], sku=row['sku'])
                psa.last_seen = datetime.now()
                db.session.add(psa)
                db.session.commit()
