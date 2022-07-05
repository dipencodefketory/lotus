from lotus import *
import ftplib
from datetime import *
import os
from typing import List
from lookup import comma_split_features
import html2text

h = html2text.HTML2Text()
h.body_width = 0


def feature_value_adder(product, feature_name: str, feature_values: List[str], source: str):
    if feature_name and feature_values:
        feature = ProductFeature.query.filter_by(name=feature_name, source=source).first()
        if feature is None:
            feature = ProductFeature(None, feature_name, False)
            feature.source = source
            db.session.add(feature)
            db.session.commit()
        for value in feature_values:
            value = value.strip()
            if value:
                feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                if feature_value is None:
                    feature_value = ProductFeatureValue(value, feature.id)
                    db.session.add(feature_value)
                    db.session.commit()

                if product not in feature_value.get_products():
                    db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                    db.session.commit()
        return 200
    else:
        return 400


write_filename = '/home/lotus/lager/Vitrex_' + datetime.now().strftime('%Y_%m_%d') + '.csv'

req_response = ''
error_message = 'Beim Upload der folgenden Produkte sind Fehler entstanden:\n'
error = False

success_message = 'Die Produkte mit den IDs '

vitrex_link_cat = ProductLinkCategory.query.filter_by(id=5).first()

counter = 0
error_rows = []
with open(write_filename, encoding='cp1252') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';', dialect=csv.excel)
    i=0
    new_products = []
    new_release = []
    for row in csv_reader:
        if i==0:
            i+=1
            continue
        if row['Genre'] in ['BuchHeft', 'Code-Card', 'Guthaben Karte Online', 'Merchandise', 'Spielzeug', '']:
            counter +=1
            print('continued')
            continue

        internal_id = row['Art.Nr']
        prod_hsp_id = row['EAN'].strip()
        prod_name = row['Titel'].strip().replace('    ',' - ').replace('   ',' - ').replace('  ',' - ')
        try:
            if prod_hsp_id == '' or prod_hsp_id.isnumeric()==False:
                prod_hsp_id = internal_id
            while len(prod_hsp_id) < 13:
                prod_hsp_id = '0' + prod_hsp_id
            if prod_hsp_id not in ['0000000436866']:
                continue
            if len(prod_name)>70:
                prod_name = prod_name[:70].rsplit(' ',1)[0]
            prod_brand = row['Label'].replace('    ',' - ').replace('   ',' - ').replace('  ',' - ')

            prod_quant = int(row['Bestand'])
            prod_tax = 19
            prod_price = float(row['EK-Preis'].replace(',','.'))
            usk = row['FSK']
            if usk == 'indiziert':
                continue
            category = row['Genre']
            if usk in ['o.A.', '6', '12', '16'] or category=='Zubehör':
                lotus_shipping_dhl = 3.55
                shipping_dhl_cost = 2.99
            else:
                lotus_shipping_dhl = 4.54
                shipping_dhl_cost = 4.99

            dscrpt = row['Beschreibung']

            dscrpt = h.handle(dscrpt.replace('<BR>', ' ').replace('<BR><BR>', '\n'))

            release_date = row['VÖ-Datum']

            print(prod_hsp_id)
            print(prod_name)
            print(prod_brand)
            k=0
            while len(prod_hsp_id) > 13 and prod_hsp_id[0]=='0' and k<10:
                prod_hsp_id = prod_hsp_id[1:]
                k+=1
            product = Product.query.filter_by(hsp_id=prod_hsp_id).first()
            supplier = Supplier.query.filter_by(firmname='Vitrex').first()
            vitrex = Stock.query.filter_by(supplier_id=supplier.id, name='Angebote').first()
            if not product:
                product = Product('EAN', prod_hsp_id, name=prod_name, brand=prod_brand, mpn='nicht zutreffend', release_date=release_date)
                product.category_id = 1
                db.session.add(product)
                db.session.commit()

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

                psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                               datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, vitrex.id, internal_id=internal_id)
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

                product.add_basic_product_data(own_stock.id, lotus_shipping_dhl=lotus_shipping_dhl, shipping_dhl_cost=shipping_dhl_cost, dscrpt=dscrpt.replace('<BR>', '\n'))

                new_products.append(product)

                j=0

                session = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')
                try:

                    pic_link = row['Jpg-Pfad']
                    product_id = pic_link.split('/')[-1].split('.')[0]

                    page = requests.get(pic_link)

                    while page.status_code == 200:
                        file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(prod_name)) + str(j+1) + '.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                        with open(file_name, 'wb') as f:
                            f.write(page.content)
                        file = open(file_name, 'rb')
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
                    while j<=1:
                        file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(prod_name)) + str(j+1) + '.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                        j += 1

                else:
                    while j<=1:
                        file_name = 'generic_pic.jpg'
                        db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                        j += 1
                db.session.commit()
            else:
                checklink = ProductLink.query.filter_by(product_id=product.id, category_id=vitrex_link_cat.id).first()
                if checklink:
                    if checklink.link == '':
                        checklink.link = f'https://www.vitrex-shop.de/de/erweiterte-suche__13/?quicksearch={product.hsp_id}&search_button=1&vtx_detail={internal_id}'
                        db.session.commit()
                else:
                    db.session.add(ProductLink(f'https://www.vitrex-shop.de/de/erweiterte-suche__13/?quicksearch={product.hsp_id}&search_button=1&vtx_detail={internal_id}', vitrex_link_cat.id, product.id))
                    db.session.commit()
                if release_date != '' and product.block_release_date == False:
                    try:
                        release_date = datetime.strptime(release_date, '%d.%m.%Y')
                        if product.release_date != release_date:
                            product.release_date = release_date
                            new_release.append(product)
                            if product.release_date > datetime.now():
                                ebay = Marketplace.query.filter_by(name='Ebay').first()
                                dscrpt = Marketplace_Product_Attributes_Description.query.filter_by(
                                    marketplace_product_attributes_id=product.get_marketplace_attributes(ebay.id).id
                                ).filter(
                                    Marketplace_Product_Attributes_Description.text.like("%WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN%")
                                ).first()

                                dscrpt_list = dscrpt.text.split('\n')
                                if product.release_date > datetime.now():
                                    dscrpt.text = '\n'.join(dscrpt_list[:-1]) + '\nRelease-Datum: ' + datetime.strftime(product.release_date, '%d.%m.%Y') + ' / Voraussichtlicher Versand am ' + datetime.strftime(
                                        product.release_date - timedelta(days=1), '%d.%m.%Y')
                                else:
                                    dscrpt.text = '\n'.join(dscrpt_list[:-1])
                    except:
                        pass

                check_psa = Product_Stock_Attributes.query.filter_by(
                    product_id=product.id, stock_id=vitrex.id, user_generated=True
                ).filter(
                    Product_Stock_Attributes.avail_date < datetime.now()
                ).filter(
                    Product_Stock_Attributes.termination_date > datetime.now()
                ).first()

                if check_psa:
                    db.session.delete(check_psa)
                    db.session.commit()

                psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                               datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, vitrex.id, internal_id=internal_id)
                psa.last_seen = datetime.now()
                db.session.add(psa)
                db.session.commit()
        except:
            error_rows.append(internal_id)

msg = ''
if new_products or new_release:
    if new_products:
        msg += 'Die Produkte mit den folgenden IDs sind heute durch die Vitrex-CSV generiert worden:<br>'
        i=0
        while i*25<len(new_products):
            msg += ','.join([str(p.id) for p in new_products[i*25:(i+1)*25]]) + '<br>'
            i+=1
        msg += '<br>-----------------------<br><br>'
        for product in new_products:
            if product.release_date != None:
                msg += str(product.id) + ' - ' + product.name + ' - ' + product.release_date.strftime('%d.%m.%Y') + '<br>'
            else:
                msg += str(product.id) + ' - ' + product.name + '<br>'
    if new_products and new_release:
        msg += '<br>-----------------------<br><br>'
    if new_release:
        msg += 'Zu folgenden Produkt-IDs hat sich das Release-Datum geändert:<br>'
        i=0
        while i*25<len(new_release):
            msg += ','.join([str(p.id) for p in new_release[i*25:(i+1)*25]]) + '<br>'
            i+=1
    if (new_products and error_rows) or (new_release and error_rows):
        msg += '<br>-----------------------<br><br>'
    if error_rows:
        msg += 'Für folgenden Vitrex-IDs ist ein Fehler entstanden:<br>'
        i=0
        while i*25<len(error_rows):
            msg += ','.join([str(p.id) for p in error_rows[i*25:(i+1)*25]]) + '<br>'
            i+=1
    send_email('Neue Vitrex-Produkte', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de'], msg, msg)

