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


load_dotenv(env_vars_path)

dt = datetime.now()
ebay_tr_auth = Trading_Connection(https=True, config_file=os.path.abspath(os.environ.get('EBAY_API_PATH')), domain="api.ebay.com", siteid='77')
idealo_auth = idealo_offer.get_access_token()
idealo = Marketplace.query.filter_by(name='Idealo').first()
ebay = Marketplace.query.filter_by(name='Ebay').first()

h = html2text.HTML2Text()
h.body_width = 0

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


filename = 'Vitrex_Artikelstamm_Bilder.csv'
write_filename = '/home/lotus/lager/Vitrex_' + datetime.now().strftime('%Y_%m_%d') + '.csv'
#write_filename = '/home/lotus/lager/Vitrex_2021_09_08.csv'

ftp = ftplib.FTP("80.147.95.142")
ftp.login("40790", "vtyh3VJD")
ftp.retrbinary("RETR " + filename, open(write_filename, 'wb').write)
ftp.quit()

req_response = ''
error_message = 'Beim Upload der folgenden Produkte sind Fehler entstanden:\n'
error = False

success_message = 'Die Produkte mit den IDs '

vitrex_link_cat = ProductLinkCategory.query.filter_by(id=5).first()
supplier = Supplier.query.filter_by(firmname='Vitrex').first()
vitrex = Stock.query.filter_by(supplier_id=supplier.id, name='Angebote').first()
vitrex_ws = Wholesaler.query.filter_by(name='Vitrex').first()
own_stock = Stock.query.filter_by(owned=True).first()
avail_ts = datetime.now().replace(hour=3, minute=0, second=0, microsecond=0)
term_ts = avail_ts+timedelta(days=1)
check_term_ts = avail_ts-timedelta(hours=1)
cont = True
num_all = 0
num_pos_stock = 0
num_pre_order = 0
num_imp = 0
num_imp_pos_stock = 0
num_imp_pre_order = 0
error_rows = []
with open(write_filename, encoding='utf-8') as csv_file:
    if datetime.now() - timedelta(minutes=50) > dt:
        dt = datetime.now()
        idealo_auth = idealo_offer.get_access_token()
    csv_reader = csv.DictReader(csv_file, delimiter=';', dialect=csv.excel)
    i=0
    new_products = []
    new_release = []
    keys = []
    for row in csv_reader:
        if i==0:
            for key in row:
                keys.append(key)
                print(key)
            print('-----------')
        num_all += 1
        prod_quant = max(0, int(float(row['Bestand'].replace(',', '')[:-2])))
        num_pos_stock += int(prod_quant > 0)
        release_date = row['VÖ-Datum']
        try:
            release_date = datetime.strptime(release_date, '%d.%m.%Y') if release_date else None
        except Exception as e:
            release_date = None
        if release_date is not None:
            if release_date > datetime.now():
                num_pre_order += 1
        if row['Warengruppe'] in ['3DS Konsole', '3DS Software', '3DS Zubehör', 'PC Software', 'PC Zubehör', 'PS4 Konsole', 'PS4 Software', 'PS4 Zubehör', 'PS5 Konsole', 'PS5 Software', 'PS5 Zubehör',
                                  'Switch Konsole', 'Switch Software', 'Switch Zubehör', 'XB-ONE Konsole', 'XB-ONE Software', 'XB-ONE Zubehör', 'XBSX Konsole', 'XBSX Software', 'XBSX Zubehör', 'Spielzeug', 'Merchandise']:
            num_imp += 1
            num_imp_pos_stock += int(prod_quant > 0)
            if release_date is not None:
                if release_date > datetime.now():
                    num_imp_pre_order += 1
            print(i)
            i+=1
            internal_id = row[keys[0]]
            prod_hsp_id = row['EAN'].strip()
            prod_name = row['Titel'].strip().replace('    ', ' - ').replace('   ', ' - ').replace('  ', ' - ')
            try:
                no_hsp_id = False
                if prod_hsp_id == '' or prod_hsp_id.isnumeric()==False:
                    no_hsp_id = True
                    prod_hsp_id = internal_id
                while len(prod_hsp_id) < 13:
                    prod_hsp_id = '0' + prod_hsp_id
                if len(prod_name)>70:
                    prod_name = prod_name[:70].rsplit(' ', 1)[0]
                prod_brand = row['Label'].replace('    ', ' - ').replace('   ', ' - ').replace('  ', ' - ')
                prod_tax = 19
                prod_price = float(row['EK-Preis'].replace(',', '.'))
                if prod_price <= 0:
                    continue
                usk = row['FSK']
                if usk == 'indiziert':
                    continue
                category = row['Genre']
                if usk in ['o.A.', '6', '12', '16'] or category=='Zubehör':
                    shipping_service = ShippingService.query.filter_by(name='DHL Paket').first()
                else:
                    shipping_service = ShippingService.query.filter_by(name='DHL Paket 18').first()

                dscrpt = row['Beschreibung']

                dscrpt = h.handle(dscrpt.replace('<BR>', ' ').replace('<BR><BR>', '\n'))
                k=0
                while len(prod_hsp_id) > 13 and prod_hsp_id[0]=='0' and k<10:
                    prod_hsp_id = prod_hsp_id[1:]
                    k+=1
                product = Product.query.filter_by(hsp_id=prod_hsp_id).first()
                if product is None and no_hsp_id is False:
                    global_id = PrdGlobalID.query.filter_by(global_id_type='EAN', global_id=prod_hsp_id).first()
                    product = Product.query.filter_by(id=global_id.product_id).first() if global_id is not None else None
                if not product:
                    psa = Product_Stock_Attributes.query.filter_by(stock_id=vitrex.id, internal_id=internal_id).order_by(Product_Stock_Attributes.termination_date).first()
                    if psa:
                        product = psa.product
                        if no_hsp_id is False:
                            ch_global_id = PrdGlobalID.query.filter_by(global_id_type='EAN', global_id=product.hsp_id, product_id=product.id).first()
                            if ch_global_id is None:
                                db.session.add(PrdGlobalID('EAN', product.hsp_id, product.id))
                                db.session.commit()
                            product.hsp_id = prod_hsp_id
                            for mpa in product.marketplace_attributes:
                                mpa.search_term = prod_hsp_id
                                mpa.mp_hsp_id = prod_hsp_id
                                if mpa.uploaded is True:
                                    if mpa.marketplace.name == 'Idealo':
                                        product.mp_update(marketplace_id=mpa.marketplace_id, authorization=idealo_auth, ean=True)
                                    elif mpa.marketplace.name == 'Ebay':
                                        product.mp_update(marketplace_id=mpa.marketplace_id, authorization=ebay_tr_auth, ean=True)
                        product.release_date = release_date
                        db.session.commit()
                        psa.self_update(termination_date=term_ts, quantity=prod_quant, buying_price=prod_price)
                    else:
                        try:
                            release_date = release_date if release_date is not None else None
                        except Exception as e:
                            release_date = None
                        product = Product('EAN', prod_hsp_id, name=prod_name, brand=prod_brand, mpn='nicht zutreffend', release_date=release_date, shipping_service_id=shipping_service.id)
                        if row['Warengruppe'] in ['Spielzeug', 'Merchandise']:
                            product.category_id = 45
                        else:
                            product.category_id = 1
                        product.cheapest_stock_id = vitrex.id
                        product.cheapest_buying_price = str_to_float(prod_price)
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

                        psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None, avail_ts, term_ts, product.id, vitrex.id, internal_id=internal_id)
                        psa.last_seen = datetime.now()
                        db.session.add(psa)
                        db.session.commit()

                        product.add_basic_product_data(own_stock.id, dscrpt=dscrpt.replace('<BR>', '\n'))
                        db.session.add(PSAUpdateQueue(product.id))
                        db.session.commit()
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
                    if product.id in val_p_ids:
                        msg_p_ids.append(product.id)
                    checklink = ProductLink.query.filter_by(product_id=product.id, category_id=vitrex_link_cat.id).first()
                    if checklink:
                        if checklink.link == '':
                            checklink.link = f'https://www.vitrex-shop.de/de/erweiterte-suche__13/?quicksearch={product.hsp_id}&search_button=1&vtx_detail={internal_id}'
                            db.session.commit()
                    else:
                        db.session.add(ProductLink(f'https://www.vitrex-shop.de/de/erweiterte-suche__13/?quicksearch={product.hsp_id}&search_button=1&vtx_detail={internal_id}', vitrex_link_cat.id, product.id))
                        db.session.commit()
                    if release_date is not None and product.block_release_date == False:
                        try:
                            if product.release_date != release_date:
                                print('----------------------')
                                print('RELEASE_UPDATE')
                                print(product.release_date)
                                print(release_date)
                                product.release_date = release_date
                                db.session.add(PSAUpdateQueue(product.id))
                                db.session.commit()
                                new_release.append(product)
                                if product.release_date > datetime.now():
                                    for mpa in product.marketplace_attributes:
                                        if mpa.marketplace.name == 'Ebay':
                                            dscrpt = Marketplace_Product_Attributes_Description.query.filter_by(
                                                marketplace_product_attributes_id=mpa.id
                                            ).filter(
                                                Marketplace_Product_Attributes_Description.text.like("%WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN%")
                                            ).first()

                                            dscrpt_list = dscrpt.text.split('\n')
                                            if product.release_date > datetime.now():
                                                dscrpt.text += '\nUpdate: Neues Release-Datum: ' + datetime.strftime(product.release_date, '%d.%m.%Y')
                                            else:
                                                dscrpt.text = '\n'.join(dscrpt_list[:-1])
                                            if mpa.uploaded is True:
                                                try:
                                                    product.mp_update(marketplace_id=ebay.id, authorization=ebay_tr_auth, description=True, description_revise_mode='Replace')
                                                except Exception as e:
                                                    print(e)
                                        elif mpa.marketplace.name == 'Idealo':
                                            new_name = mpa.name + f' - Update: Neues Release-Datum: {datetime.strftime(product.release_date, "%d.%m.%Y")}'
                                            if len(new_name) <= 255:
                                                mpa.name = new_name
                                                if mpa.uploaded is True:
                                                    try:
                                                        product.mp_update(marketplace_id=idealo.id, authorization=idealo_auth, title=True)
                                                    except Exception as e:
                                                        print(e)
                                db.session.commit()
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

                    avail_psa = Product_Stock_Attributes.query.filter_by(
                        product_id=product.id, stock_id=vitrex.id
                    ).filter(
                        Product_Stock_Attributes.avail_date < datetime.now()
                    ).filter(
                        Product_Stock_Attributes.termination_date > check_term_ts
                    ).first()

                    if avail_psa:
                        avail_psa.self_update(termination_date=term_ts, quantity=prod_quant, buying_price=prod_price)
                    else:
                        psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None, avail_ts, term_ts, product.id, vitrex.id, internal_id=internal_id)
                        psa.last_seen = datetime.now()
                        db.session.add(psa)
                        db.session.add(PSAUpdateQueue(product.id))
                        db.session.commit()
            except Exception as e:
                print(e)
                error_rows.append(internal_id)

db.session.add(WSReport(num_all, num_pos_stock, num_pre_order, num_imp, num_imp_pos_stock, num_imp_pre_order, vitrex_ws.id))
db.session.commit()

msg = ''
if new_products or new_release or error_rows or msg_p_ids:
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
    if new_products and (new_release or msg_p_ids or error_rows):
        msg += '<br>-----------------------<br><br>'
    if new_release:
        msg += 'Zu folgenden Produkt-IDs hat sich das Release-Datum geändert:<br>'
        i=0
        while i*25<len(new_release):
            msg += ','.join([str(p.id) for p in new_release[i*25:(i+1)*25]]) + '<br>'
            i+=1
    if new_release and (error_rows or msg_p_ids):
        msg += '<br>-----------------------<br><br>'
    if error_rows:
        msg += 'Für folgenden Vitrex-IDs ist ein Fehler entstanden:<br>'
        i=0
        while i*25<len(error_rows):
            msg += ','.join([internal_id for p in error_rows[i*25:(i+1)*25]]) + '<br>'
            i+=1
    if error_rows and msg_p_ids:
        msg += '<br>-----------------------<br><br>'
    if msg_p_ids:
        msg += 'Folgende wertvolle Produkte sind bei Vitrex verfügbar:<br>'
        i=0
        while i*25<len(msg_p_ids):
            msg += ','.join([str(p_id) for p_id in msg_p_ids[i*25:(i+1)*25]]) + '<br>'
            i+=1
    send_email('Neue Vitrex-Produkte', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de', 'benjamin.hahn@lotusicafe.de'], msg, msg)

