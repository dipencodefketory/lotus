# -*- coding: utf-8 -*-

from lotus import *
import requests
from requests.auth import HTTPBasicAuth
import csv
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


username = 'lotusicafe-de'
password = 'GWle==-**^lX'

r = requests.get('https://feeds.entertainment-trading.com/3728900-lotusicafe.csv', auth=HTTPBasicAuth(username, password))
r.encoding = 'utf-8'
csv_reader = csv.DictReader(r.text.strip().split('\n'), delimiter=';', dialect=csv.excel)

h = html2text.HTML2Text()
h.body_width = 0

avail_ts = datetime.now().replace(hour=3, minute=0, second=0, microsecond=0)
term_ts = avail_ts+timedelta(days=1)
check_term_ts = avail_ts-timedelta(hours=1)
et_ws = Wholesaler.query.filter_by(name='Entertainment-Trading').first()
et = Stock.query.filter_by(id=6).first()
et_link_cat = ProductLinkCategory.query.filter_by(id=13).first()
prc_tax = 19

region_dict = {'German': 'USK', 'English': 'UK', 'Nordic': 'Nordic', 'Finnish': 'Nordic', 'Danish': 'Nordic', 'Norwegian': 'Nordic', 'Swedish': 'Nordic', 'French': 'EU', 'Italian': 'EU',
               'Import': 'PEGI', 'Export': 'PEGI', '': 'PEGI', 'Australia': 'AUS', 'Spanish': 'PEGI'}

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

toy_cat = ProductCategory.query.filter_by(id=27).first()
toy_cats = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]
dino_cat = ProductCategory.query.filter_by(name='Tiere & Dinosaurier').first()
other_action_cat = ProductCategory.query.filter_by(name='Andere Action-Figuren').first()
fantasy_cat = ProductCategory.query.filter_by(name='Fantasy-Figuren').first()
tv_gaming_cat = ProductCategory.query.filter_by(name='TV- & Videospiel-Figuren').first()
hist_cat = ProductCategory.query.filter_by(name='Historische Figuren').first()
military_cat = ProductCategory.query.filter_by(name='Militär-Figuren').first()
comic_cat = ProductCategory.query.filter_by(name='Comic-Figuren').first()
lego_cat = ProductCategory.query.filter_by(name='LEGO Baukästen & Sets').first()
mega_cat = ProductCategory.query.filter_by(name='MEGA Bloks Bau- & Konstruktionsspielzeug').first()
building_cat = ProductCategory.query.filter_by(name='Bau- & Konstruktionsspielzeug').first()
baby_doll_cat = ProductCategory.query.filter_by(name='Baby-Spielpuppen').first()
fashion_doll_cat = ProductCategory.query.filter_by(name='Mode-Spielpuppen').first()
other_doll_cat = ProductCategory.query.filter_by(name='Andere Spielpuppen').first()
joystick_cat = ProductCategory.query.filter_by(name='Joysticks').first()
key_mouse_cat = ProductCategory.query.filter_by(name='Tastatur-Maus-Sets').first()
key_cat = ProductCategory.query.filter_by(name='Tastaturen').first()
mice_cat = ProductCategory.query.filter_by(name='Computermäuse').first()
headphone_acc_cat = ProductCategory.query.filter_by(name='Kopfhörer-Zubehör').first()
in_ear_cat = ProductCategory.query.filter_by(name='In-Ear-Kopfhörer').first()
on_ear_cat = ProductCategory.query.filter_by(name='On-Ear-Kopfhörer').first()
over_ear_cat = ProductCategory.query.filter_by(name='Over-Ear-Kopfhörer').first()
media_str_cat = ProductCategory.query.filter_by(name='Medien-Streamer').first()
comp_audio_cat = ProductCategory.query.filter_by(name='Kompakt-Audio-Systeme').first()
audio_comp_cat = ProductCategory.query.filter_by(name='Audio-Komponenten').first()
speaker_cat = ProductCategory.query.filter_by(name='Lautsprecher').first()
port_speaker_cat = ProductCategory.query.filter_by(name='Tragbare Lautsprecher').first()
sm_speaker_cat = ProductCategory.query.filter_by(name='Smart-Speaker').first()
tooth_br_cat = ProductCategory.query.filter_by(name='Zahnbürsten').first()
mens_sh_cat = ProductCategory.query.filter_by(name='Herren-Elektrorasierer').first()
wmns_sh_cat = ProductCategory.query.filter_by(name='Damen-Elektrorasierer').first()
epil_cat = ProductCategory.query.filter_by(name='Epilierer').first()
clip_cat = ProductCategory.query.filter_by(name='Haar-, Bartschneidegeräte & Trimmer').first()
massage_cat = ProductCategory.query.filter_by(name='Massage-Geräte').first()
kids_cat = ProductCategory.query.filter_by(name='Kinder').first()
hc_cat = ProductCategory.query.filter_by(name='Haushalt & Küche').first()
garden_cat = ProductCategory.query.filter_by(name='Garten & Outdoor').first()
beauty_cat = ProductCategory.query.filter_by(name='Beauty').first()
num_all = 0
num_pos_stock = 0
num_pre_order = 0
num_imp = 0
num_imp_pos_stock = 0
num_imp_pre_order = 0

write_filename = '/home/lotus/lager/Enttrading_' + datetime.now().strftime('%Y_%m_%d') + '.csv'
with open(write_filename, 'w', newline='') as csvfile:
    i=0
    new_products = []
    new_release = []
    for row in csv_reader:
        num_all +=1
        quant = str_to_int(row["stock"])
        if quant is not None:
            num_pos_stock += int(quant > 0)
        release_date = datetime.strptime(row["release_date"], '%Y-%m-%d') if row["release_date"] else None
        if release_date is not None:
            num_pre_order += int(release_date > datetime.now())
        try:
            spamwriter = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            if i==0:
                spamwriter.writerow([key for key in row])
                i+=1
                for key in row:
                    print(key)
                print('-----------')
            spamwriter.writerow([row[key] for key in row])
            for key in row:
                row[key] = row[key].replace('®', '').replace(
                    'LEGO', 'LEGO®'
                ).replace(
                    'lego', 'LEGO®'
                ).replace(
                    'Lego', 'LEGO®'
                ).replace(
                    'DUPLO', 'DUPLO®'
                ).replace(
                    'duplo', 'DUPLO®'
                ).replace(
                    'Duplo', 'DUPLO®'
                ).replace(
                    'Schleich', 'Schleich®'
                ).replace(
                    'schleich', 'Schleich®'
                ).replace(
                    'SCHLEICH', 'Schleich®'
                ).replace(
                    'Playmobil', 'Playmobil®'
                ).replace(
                    'playmobil', 'Playmobil®'
                ).replace(
                    'PLAYMOBIL', 'Playmobil®'
                )
            if row['category'] != 'Health and Personal Care - Personal Care - Shaving and hair removal - Hair removal - Waxing' and (
                'Computers - Keyboards, Mice & Other Input Devices' in row['category']
                or 'Electronics - Audio & HiFi' in row['category']
                or 'Health and Personal Care - Personal Care - Oral care - Toothbrushes - Electric Toothbrushes' in row['category']
                or 'Health and Personal Care - Personal Care - Oral care - Toothbrushes - Toothbrush Replacement Heads' in row['category']
                or 'Health and Personal Care - Personal Care - Shaving and hair removal - Electric Shavers' in row['category']
                or 'Health and Personal Care - Personal Care - Shaving and hair removal - Hair removal' in row['category']
                or 'Health and Personal Care - Personal Care - Shaving and hair removal - Trimmers, Clippers & Body Groomers' in row['category']
                or 'Health and Personal Care - Wellness - Electric Massagers' in row['category']
                or row['platform'] in ['Xbox One', 'Nintendo Switch', 'Xbox Series X', 'Nintendo 3DS', 'PC', 'PlayStation 4', 'PlayStation 5']
                or 'Toys' in row['category']
                or 'Baby and Children - ' in row['category']
                or 'Home and Kitchen - ' in row['category']
                or 'Garden, Patio and Outdoor - ' in row['category']
                or 'Beauty - ' in row['category']
            ):
                if str_to_float(row["price"]) <= 0:
                    continue
                num_imp +=1
                print(i)
                i+=1
                mpa_name = row["title"]
                name = row["title"]
                if row['platform']:
                    region = region_dict[row['Region']] if row['Region'] in region_dict else ''
                    mpa_name = f'{row["title"].replace("(Nordic)", "").strip()} - {row["platform"]} - EU Version' if row["platform"] else row["title"]
                    name = mpa_name + f' - {region}' if region else mpa_name
                hsp_id = row['ean']
                if hsp_id:
                    while len(hsp_id) < 13:
                        hsp_id = '0' + hsp_id
                else:
                    continue
                product = Product.query.filter_by(hsp_id=hsp_id).first()
                if quant:
                    if quant > 0:
                        release_date = datetime.now() - timedelta(days=1) if release_date == None else release_date
                        num_imp_pos_stock += 1
                if release_date is not None:
                    num_imp_pre_order += int(release_date > datetime.now())
                if product is None:
                    global_id = PrdGlobalID.query.filter_by(global_id_type='EAN', global_id=hsp_id).first()
                    product = Product.query.filter_by(id=global_id.product_id).first() if global_id is not None else None
                if not product:
                    print('NEW')
                    print(hsp_id)
                    print(name)
                    print('------------')
                    if row['platform']:
                        if row['usk_on_disc'] in ['0+', '6+', '12+', '15+', '16+']:
                            shipping_service = ShippingService.query.filter_by(name='DHL Paket').first()
                        else:
                            shipping_service = ShippingService.query.filter_by(name='DHL Paket 18').first()
                    else:
                        shipping_service = ShippingService.query.filter_by(name='DHL Paket').first()
                    product = Product('EAN', hsp_id, name=name, brand=row["brand"], mpn='nicht zutreffend', release_date=release_date, shipping_service_id=shipping_service.id)
                    product.measurements = row["Length (cm)"] + 'x' + row["Width (cm)"] + 'x' + row["Height (cm)"]
                    main_cat = row['category'].split('-')[0].strip()
                    if 'Beauty -' in row['category']:
                        product.category_id = beauty_cat.id
                    elif 'Garden, Patio and Outdoor - ' in row['category']:
                        product.category_id = garden_cat.id
                    elif 'Home and Kitchen - ' in row['category']:
                        product.category_id = hc_cat.id
                    elif 'Baby and Children - ' in row['category']:
                        product.category_id = kids_cat.id
                    elif row['category'] == 'Computers - Keyboards, Mice & Other Input Devices - Joysticks':
                        product.category_id = joystick_cat.id
                    elif row['category'] == 'Computers - Keyboards, Mice & Other Input Devices - Keyboard & Mouse Sets':
                        product.category_id = key_mouse_cat.id
                    elif row['category'] in ['Computers - Keyboards, Mice & Other Input Devices - Keyboards', 'Computers - Keyboards, Mice & Other Input Devices - Tablet Keyboards']:
                        product.category_id = key_cat.id
                    elif row['category'] in ['Computers - Keyboards, Mice & Other Input Devices - Mice', 'Computers - Keyboards, Mice & Other Input Devices - Trackballs']:
                        product.category_id = mice_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Headphones & Headsets - Headphones Accessories':
                        product.category_id = headphone_acc_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Headphones & Headsets - In-Ear':
                        product.category_id = in_ear_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Headphones & Headsets - On Ear':
                        product.category_id = on_ear_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Headphones & Headsets - Over Ear':
                        product.category_id = over_ear_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Media Streaming Devices':
                        product.category_id = media_str_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Music Systems':
                        product.category_id = comp_audio_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Radios & Boomboxes':
                        product.category_id = comp_audio_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Receivers & Separates - LP/Record Players':
                        product.category_id = audio_comp_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Speakers - Portable Bluetooth Speakers':
                        product.category_id = port_speaker_cat.id
                    elif row['category'] == 'Electronics - Audio & HiFi - Speakers - Smart Speakers':
                        product.category_id = sm_speaker_cat.id
                    elif row['category'] in ['Electronics - Audio & HiFi - Speakers - Subwoofers', 'Electronics - Audio & HiFi - Speakers - Wireless Multiroom Systems']:
                        product.category_id = speaker_cat.id
                    elif row['category'] in ['Health and Personal Care - Personal Care - Oral care - Toothbrushes - Electric Toothbrushes', 'Health and Personal Care - Personal Care - Oral care - Toothbrushes - Toothbrush Replacement Heads']:
                        product.category_id = tooth_br_cat.id
                    elif 'Health and Personal Care - Personal Care - Shaving and hair removal - Electric Shavers - Mens' in row['category']:
                        product.category_id = mens_sh_cat.id
                    elif 'Health and Personal Care - Personal Care - Shaving and hair removal - Hair removal' in row['category']:
                        product.category_id = epil_cat.id
                    elif row['category'] == 'Health and Personal Care - Personal Care - Shaving and hair removal - Trimmers, Clippers & Body Groomers':
                        product.category_id = clip_cat.id
                    elif 'Health and Personal Care - Wellness - Electric Massagers' in row['category']:
                        product.category_id = massage_cat.id
                    elif row['category'] in ['Toys - Figures - Dinosaurs'] or 'Toys - Figures - Farm and Animals' in row['category']:
                        product.category_id = dino_cat.id
                    elif row['category'] in ['Toys - Figures - Elves & Fairies', 'Toys - Figures - Dragons', 'Toys - Figures - Zombies and monsters']:
                        product.category_id = fantasy_cat.id
                    elif row['category'] in ['Toys - Figures - Knights & Castles', 'Toys - Figures - Princesses']:
                        product.category_id = hist_cat.id
                    elif row['category'] in ['Toys - Figures - Military', 'Toys - Figures - Pirates']:
                        product.category_id = military_cat.id
                    elif row['category'] in ['Toys - Figures - Superheroes', 'Toys - Figures - Action Figures']:
                        product.category_id = comic_cat.id
                    elif row['category'] in ['Toys - Figures - Kids TV and Movie Characters', 'Toys - Figures - Gaming Figures'] or 'Video Games and Consoles - Toys for games' in row['category']:
                        product.category_id = tv_gaming_cat.id
                    elif row['category'] in ['Toys - Figures - Doctor and Hospital', 'Toys - Figures - Emergency Services', 'Toys - Figures - Urban & Village Life', 'Toys - Figures - Transportation & Traffic',
                                             'Toys - Figures - Collectibles']:
                        product.category_id = other_action_cat.id
                    elif 'LEGO' in row["brand"]:
                        product.category_id = lego_cat.id
                    elif 'MEGA Construx' in row["title"]:
                        product.category_id = mega_cat.id
                    elif 'Toys - Building and Construction Toys' in row['category']:
                        product.category_id = building_cat.id
                    elif 'Toys - Dolls and Dollhouses' in row['category']:
                        if row['brand'].lower() in ['baby annabell', 'baby born', 'tiny treasure', 'smoby', 'smallstuff', 'rubens barn', 'happy friend', 'bayer']:
                            product.category_id = baby_doll_cat.id
                        elif row['brand'].lower() in ['barbie', 'sparkle girlz', 'rainbow high', 'love diana', 'l.o.l.'] or 'barbie' in row['title'].lower() or 'disney' in row['brand'].lower():
                            product.category_id = fashion_doll_cat.id
                        else:
                            product.category_id = fashion_doll_cat.id
                    elif main_cat in ['Toys']:
                        product.category_id = 27
                    else:
                        product.category_id = 1
                    product.cheapest_stock_id = et.id
                    product.cheapest_buying_price = str_to_float(row["price"])
                    product.length = str_to_float(money_to_float(row['length_mm']))
                    product.width = str_to_float(money_to_float(row['width_mm']))
                    product.height = str_to_float(money_to_float(row['height_mm']))
                    product.weight = str_to_float(money_to_float(row['weight_g'])) / 1000
                    db.session.add(product)
                    db.session.commit()
                    print(row["price"])
                    print(str_to_float(row["price"]))
                    print(product.cheapest_buying_price)
                    psa = Product_Stock_Attributes('Neu & OVP', str_to_int(row["stock"]), str_to_float(row["price"]), None, prc_tax, None, avail_ts, term_ts, product.id, et.id, internal_id=row['id'], sku=row['sku'])
                    psa.last_seen = datetime.now()
                    db.session.add(psa)
                    db.session.commit()

                    own_stock = Stock.query.filter_by(owned=True).first()

                    product.add_basic_product_data(own_stock.id, dscrpt=h.handle(row["description"]), mpa_name=mpa_name)
                    db.session.add(PSAUpdateQueue(product.id))
                    db.session.commit()

                    db.session.add(ProductLink(f'https://business.coolshop.co.uk/video-games-and-consoles/?q={product.hsp_id}', et_link_cat.id, product.id))

                    for key in row:
                        product_feature_name = key
                        value = row[key]
                        if value != '':
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
                    if product.category_id not in toy_cats:
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
                    if product.id in val_p_ids:
                        msg_p_ids.append(product.id)
                    if release_date is not None and product.block_release_date == False:
                        try:
                            if product.release_date != release_date:
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
                                                dscrpt.text += f'\nUpdate: Neues Release-Datum: {datetime.strftime(product.release_date, "%d.%m.%Y")}'
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
                        product_id=product.id, stock_id=et.id, user_generated=True
                    ).filter(
                        Product_Stock_Attributes.avail_date < datetime.now()
                    ).filter(
                        Product_Stock_Attributes.termination_date > datetime.now()
                    ).first()
                    if check_psa:
                        db.session.delete(check_psa)
                        db.session.commit()

                    avail_psa = Product_Stock_Attributes.query.filter_by(
                        product_id=product.id, stock_id=et.id
                    ).filter(
                        Product_Stock_Attributes.avail_date < datetime.now()
                    ).filter(
                        Product_Stock_Attributes.termination_date > check_term_ts
                    ).first()
                    if avail_psa:
                        avail_psa.self_update(termination_date=term_ts, quantity=str_to_int(row["stock"]), buying_price=str_to_float(row["price"]) * 1.15 if str_to_int(row["stock"]) == 2 else str_to_float(row["price"]))
                    else:
                        psa = Product_Stock_Attributes('Neu & OVP', str_to_int(row["stock"]), str_to_float(row["price"]) * 1.15 if str_to_int(row["stock"]) == 2 else str_to_float(row["price"]),
                                                       None, prc_tax, None, avail_ts, term_ts, product.id, et.id, internal_id=row['id'], sku=row['sku'])
                        psa.last_seen = datetime.now()
                        db.session.add(psa)
                        db.session.add(PSAUpdateQueue(product.id))
                        db.session.commit()
        except Exception as e:
            print(e)
db.session.add(WSReport(num_all, num_pos_stock, num_pre_order, num_imp, num_imp_pos_stock, num_imp_pre_order, et_ws.id))
db.session.commit()

if msg_p_ids:
    msg = 'Folgende wertvolle Produkte sind bei Entertainment-Trading verfügbar:<br>'
    i = 0
    while i * 25 < len(msg_p_ids):
        msg += ','.join([str(p_id) for p_id in msg_p_ids[i * 25:(i + 1) * 25]]) + '<br>'
        i += 1
    send_email('Wertvolle Produkte bei Entertainment-Trading verfügbar!', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de'], msg, msg)
