# -*- coding: utf-8 -*-

from lotus import db, env_vars_path
from basismodels import Marketplace_Product_Attributes_Description, ProductPicture, Marketplace, ProductFeatureValue, ProductFeature, Product_ProductFeatureValue, Product, ProductCategory, ImageProcJob, IPJResults, ProductGroup, PrGrTokens, PrGrToken
from lookup import version_normalizer_dict
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ETree
import afterbuy_api
from PIL import Image, ImageEnhance
import other_apis
import time as t
import cv2
import ftplib
from pyzbar import pyzbar
import os
from dotenv import load_dotenv
import numpy as np
from sqlalchemy import func
from flask import jsonify, make_response

load_dotenv(env_vars_path)


def ebay_description_generator(product, description: str, usk: bool, usk_val: str, suppress_mid: bool = False) -> int:
    toy_cat = ProductCategory.query.filter_by(name='Spielzeug').first()
    toy_cat_ids = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]
    feat = ProductFeature.query.filter_by(name='Datenträger', source='lotus').first()
    cib_vals = db.session.query(ProductFeatureValue.id).filter(ProductFeatureValue.value.like("%Code in a Box%")).filter(ProductFeatureValue.productfeature_id==feat.id)
    p_pfv = Product_ProductFeatureValue.query.filter_by(product_id=product.id).filter(Product_ProductFeatureValue.productfeaturevalue_id.in_(cib_vals)).first()
    ebay = Marketplace.query.filter_by(name='Ebay').first()
    dscrpts = Marketplace_Product_Attributes_Description.query.filter_by(
        marketplace_product_attributes_id=product.get_marketplace_attributes(ebay.id).id
    ).order_by(
        Marketplace_Product_Attributes_Description.position
    ).all()
    d_list = []
    for i, d in enumerate(dscrpts):
        if suppress_mid and i>0:
            d_list.append(d.text)
        db.session.delete(d)
    if d_list:
        d_list.pop()

    if product.spec_trait_3:
        if product.spec_trait_3 in version_normalizer_dict:
            if version_normalizer_dict[product.spec_trait_3] == 'Deutsche Version':
                version_ext = 'Deutsche Version mit USK ' + usk_val + ' Kennzeichnung' if usk_val else 'Deutsche Version mit USK Kennzeichnung'
            else:
                version_ext = 'Europäische Verkaufsversion'
        else:
            if usk:
                version_ext = 'Deutsche Version mit USK ' + usk_val + ' Kennzeichnung' if usk_val else 'Deutsche Version mit USK Kennzeichnung'
            else:
                version_ext = 'Deutsche Version mit USK Kennzeichnung\nEuropäische Verkaufsversion'
    else:
        version_ext = 'Deutsche Version mit USK Kennzeichnung\nEuropäische Verkaufsversion'
    description_1 = product.spec_trait_0 if product.spec_trait_0 else product.name
    description_1 += f'\n{product.spec_trait_1}' if product.spec_trait_1 else ''
    description_1 += f'\n{product.spec_trait_2}' if product.spec_trait_2 else f'\nPS4 / PlayStation 4 PS5 / PlayStation 5 Xbox ONE Xbox Series X PC'
    db.session.add(Marketplace_Product_Attributes_Description(1, description_1, product.get_marketplace_attributes(ebay.id).id))
    db.session.commit()
    if not suppress_mid:
        description_2 = description
        description_3 = 'FEATURES\n\nWAS BEINHALTET DIESE EDITION?'
        db.session.add(Marketplace_Product_Attributes_Description(2, description_2, product.get_marketplace_attributes(ebay.id).id))
        db.session.commit()
        db.session.add(Marketplace_Product_Attributes_Description(3, description_3, product.get_marketplace_attributes(ebay.id).id))
        db.session.commit()
        max_pos = 4
    else:
        for i, d in enumerate(d_list):
            db.session.add(Marketplace_Product_Attributes_Description(i+2, d, product.get_marketplace_attributes(ebay.id).id))
        max_pos = len(d_list)+2
    description_4 = f'WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN\nNeu und originalverpackt'
    if product.category_id == 1:
        description_4 += f'\n{version_ext}'
        if p_pfv:
            description_4 += '\nDie Spielhülle beinhaltet nur einen Download-Code, Speicherkarte nicht vorhanden'
        feat = ProductFeature.query.filter_by(name='Sprachausgabe / Ingame language').first()
        description_4 += f'\nSpielsprache: {", ".join(feat.get_value_product_values(product.id))}'
        feat = ProductFeature.query.filter_by(name='Textsprache im Spiel / Subtitles').first()
        description_4 += f'\nTexte: {", ".join(feat.get_value_product_values(product.id))}'
    if product.release_date:
        if product.release_date > datetime.now():
            description_4 += '\nRelease-Datum: ' + datetime.strftime(product.release_date, '%d.%m.%Y') + ' / Voraussichtlicher Versand am ' + datetime.strftime(
                product.release_date - timedelta(days=1), '%d.%m.%Y')
    if product.category_id in toy_cat_ids:
        query = db.session.query(
            ProductFeature, ProductFeatureValue, Product_ProductFeatureValue
        ).filter(
            ProductFeature.id == ProductFeatureValue.productfeature_id
        ).filter(
            ProductFeatureValue.id == Product_ProductFeatureValue.productfeaturevalue_id
        ).filter(
            Product_ProductFeatureValue.product_id == product.id
        ).filter(
            ProductFeature.name == 'Warnhinweise'
        ).filter(
            ProductFeature.source == 'lotus'
        ).all()
        warnings = [pfv.value for _, pfv, _ in query]
        description_4 += f'\nACHTUNG: {" ".join(warnings)}'
    db.session.add(Marketplace_Product_Attributes_Description(max_pos, description_4, product.get_marketplace_attributes(ebay.id).id))
    db.session.commit()
    return 200


def store_image(ftp_session, product, url: str, file_name: str):
    page = requests.get(url)
    if page.status_code == 200:
        db.session.add(ProductPicture(0, file_name, product.id))
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
        ftp_session.storbinary('STOR ' + file_name, file)
        file.close()
        os.remove(file_name)
        return True
    else:
        return False


def ab_product_update(product_ids: list, insert: bool = False, ean: bool = False, mpn: bool = False, name: bool = False, descriptions: bool = False, search_optimization: bool = False, buying_price: bool = False,
                      selling_price: bool = False, stock_update: dict = None, tags: dict = None, weight: bool = False, images: bool = False, brand: bool = False, features: bool = False, stock_location_1: bool = False):
    if tags is None:
        tags = {}
    if stock_update is None:
        stock_update = {}
    ps = Product.query.filter(Product.id.in_(product_ids)).all()
    product_tree = ETree.Element('Products')
    for p in ps:
        product_tree = p.ab_upload_xml_gen(product_tree, insert=insert, ean=ean, mpn=mpn, name=name, descriptions=descriptions, search_optimization=search_optimization, buying_price=buying_price, selling_price=selling_price,
                                           stock_update=stock_update[p.id] if p.id in stock_update else None, tags=tags[p.id] if p.id in tags else None, weight=weight, images=images, brand=brand,
                                           stock_location_1=stock_location_1)
    r = afterbuy_api.update_shop_products(product_tree)
    return r


def r_ify_product(p):
    for rep_name_1, rep_name_2, fin_name in [('ninjago', 'Ninjago', 'NINJAGO'), ('lego', 'Lego', 'LEGO'), ('duplo', 'Duplo', 'DUPLO'), ('minecraft', 'MINECRAFT', 'Minecraft'), ('mindstorms', 'Mindstorms', 'MINDSTORMS'),
                                             ('serious_play', 'Serious Play', 'SERIOUS_PLAY'), ('schleich', 'SCHLEICH', 'Schleich'), ('playmobil', 'PLAYMOBIL', 'Playmobil')]:
        p.name = f'{p.name.replace(f"{rep_name_1}™", f"{fin_name}").replace(f"{fin_name}™", f"{fin_name}").replace(f"{rep_name_2}™", f"{fin_name}").replace(f"{rep_name_1}®", f"{fin_name}").replace(f"{fin_name}®", f"{fin_name}").replace(f"{rep_name_2}®", f"{fin_name}").replace(f"{fin_name}", f"{fin_name}®").replace(f"{rep_name_1}", f"{fin_name}®").replace(f"{rep_name_2}", f"{fin_name}®")}'
        db.session.commit()
        if p.spec_trait_0 is not None:
            p.spec_trait_0 = f'{p.spec_trait_0.replace(f"{rep_name_1}™", f"{fin_name}").replace(f"{fin_name}™", f"{fin_name}").replace(f"{rep_name_2}™", f"{fin_name}").replace(f"{rep_name_1}®", f"{fin_name}").replace(f"{fin_name}®", f"{fin_name}").replace(f"{rep_name_2}®", f"{fin_name}").replace(f"{fin_name}", f"{fin_name}®").replace(f"{rep_name_1}", f"{fin_name}®").replace(f"{rep_name_2}", f"{fin_name}®")}'
            db.session.commit()
        if p.spec_trait_1 is not None:
            p.spec_trait_1 = f'{p.spec_trait_1.replace(f"{rep_name_1}™", f"{fin_name}").replace(f"{fin_name}™", f"{fin_name}").replace(f"{rep_name_2}™", f"{fin_name}").replace(f"{rep_name_1}®", f"{fin_name}").replace(f"{fin_name}®", f"{fin_name}").replace(f"{rep_name_2}®", f"{fin_name}").replace(f"{fin_name}", f"{fin_name}®").replace(f"{rep_name_1}", f"{fin_name}®").replace(f"{rep_name_2}", f"{fin_name}®")}'
            db.session.commit()
        if p.spec_trait_2 is not None:
            p.spec_trait_2 = f'{p.spec_trait_2.replace(f"{rep_name_1}™", f"{fin_name}").replace(f"{fin_name}™", f"{fin_name}").replace(f"{rep_name_2}™", f"{fin_name}").replace(f"{rep_name_1}®", f"{fin_name}").replace(f"{fin_name}®", f"{fin_name}").replace(f"{rep_name_2}®", f"{fin_name}").replace(f"{fin_name}", f"{fin_name}®").replace(f"{rep_name_1}", f"{fin_name}®").replace(f"{rep_name_2}", f"{fin_name}®")}'
            db.session.commit()
        if p.spec_trait_3 is not None:
            p.spec_trait_3 = f'{p.spec_trait_3.replace(f"{rep_name_1}™", f"{fin_name}").replace(f"{fin_name}™", f"{fin_name}").replace(f"{rep_name_2}™", f"{fin_name}").replace(f"{rep_name_1}®", f"{fin_name}").replace(f"{fin_name}®", f"{fin_name}").replace(f"{rep_name_2}®", f"{fin_name}").replace(f"{fin_name}", f"{fin_name}®").replace(f"{rep_name_1}", f"{fin_name}®").replace(f"{rep_name_2}", f"{fin_name}®")}'
            db.session.commit()
        if p.brand is not None:
            p.brand = f'{p.brand.replace(f"{rep_name_1}™", f"{fin_name}").replace(f"{fin_name}™", f"{fin_name}").replace(f"{rep_name_2}™", f"{fin_name}").replace(f"{rep_name_1}®", f"{fin_name}").replace(f"{fin_name}®", f"{fin_name}").replace(f"{rep_name_2}®", f"{fin_name}").replace(f"{fin_name}", f"{fin_name}®").replace(f"{rep_name_1}", f"{fin_name}®").replace(f"{rep_name_2}", f"{fin_name}®")}'
            db.session.commit()
        for mpa in p.marketplace_attributes:
            mpa.name = f'{mpa.name.replace(f"{rep_name_1}™", f"{fin_name}").replace(f"{fin_name}™", f"{fin_name}").replace(f"{rep_name_2}™", f"{fin_name}").replace(f"{rep_name_1}®", f"{fin_name}").replace(f"{fin_name}®", f"{fin_name}").replace(f"{rep_name_2}®", f"{fin_name}").replace(f"{fin_name}", f"{fin_name}®").replace(f"{rep_name_1}", f"{fin_name}®").replace(f"{rep_name_2}", f"{fin_name}®")}'
            db.session.commit()
            for mpa_d in mpa.descriptions:
                mpa_d.text = f'{mpa_d.text.replace(f"{rep_name_1}™", f"{fin_name}").replace(f"{fin_name}™", f"{fin_name}").replace(f"{rep_name_2}™", f"{fin_name}").replace(f"{rep_name_1}®", f"{fin_name}").replace(f"{fin_name}®", f"{fin_name}").replace(f"{rep_name_2}®", f"{fin_name}").replace(f"{fin_name}", f"{fin_name}®").replace(f"{rep_name_1}", f"{fin_name}®").replace(f"{rep_name_2}", f"{fin_name}®")}'
                db.session.commit()


def image_processor(image: str, filename: str, ftp_session, remove_bg: bool = True, url: str = ''):
    if remove_bg:
        file = open(os.environ.get('BASE_PATH_2') + url + image, 'rb')
        ftp_session.storbinary(f'STOR {image}', file)
        file.close()
        img = other_apis.remove_background(image)
    else:
        Image.open(os.environ.get('BASE_PATH_2') + url + image).save(f'{os.environ.get("BASE_PATH")}{image}')
        img = image
    if img != 'ERROR':
        img_a = Image.open(img)
        enhancer = ImageEnhance.Brightness(img_a)
        img_a = enhancer.enhance(1.175)
        enhancer = ImageEnhance.Contrast(img_a)
        img_a = enhancer.enhance(1.125)
        enhancer = ImageEnhance.Color(img_a)
        img_a = enhancer.enhance(1.25)
        img_a.save(f'{image}', 'JPEG')
        file = open(f'{image}', 'rb')
        ftp_session.storbinary(f'STOR {filename}', file)
        file.close()
        os.remove(image)
        if remove_bg:
            os.remove(f'{image.split(".")[0]}_a.png')
        return True
    else:
        return False


def decode(image: str):
    decoded_objects = pyzbar.decode(image, symbols=[pyzbar.ZBarSymbol.EAN13])
    for obj in decoded_objects:
        return obj.data.decode("utf-8"), obj.rect
    return None, None


def is_barcode(image: str, w_ratio: float = .09, h_ratio: float = .09, url: str = os.environ.get('IMAGE_SERVER')):
    if 'http' in url:
        page = requests.get(url + image)
        with open(image, 'wb') as f:
            f.write(page.content)
        img = cv2.imread(image)
    else:
        img = cv2.imread(os.environ.get('BASE_PATH_2') + os.environ.get('IMAGE_PROC_PATH') + image)
    height, width, channels = img.shape
    if 'http' in url:
        os.remove(image)
    data, rect = decode(img)
    if rect:
        print(rect.width/width)
        print(rect.height/height)
        if rect.width/width > w_ratio and rect.height/height > h_ratio:
            return True, data
        else:
            return False, data
    return False, None


def add_images(ipj: ImageProcJob):
    all_ok = True
    ftp_session = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')
    product = None
    num = 0
    images = [f'DSC0{i}.JPG' if i-10000<0 else f'DSC{i}.JPG' for i in range(ipj.min_int, ipj.max_int + 1)]
    for image in images:
        msg = ''
        try:
            page = requests.get(os.environ.get('IMAGE_SERVER') + image)
            if not page.status_code == 200:
                continue
            barcode, hsp_id = is_barcode(image)
            if barcode is True:
                print('------------------------------')
                print(f'{image} - BARCODE')
                print('------------------------------')
            '''
                msg = f'BARCODE - {hsp_id}'
                if product is not None and num < 2:
                    while num < 2:
                        print('GP ADDED')
                        db.session.add(ProductPicture(min(num, 2), 'generic_pic.jpg', product.id))
                        num += 1
                    db.session.commit()
                    print('------------------------------')
                while len(hsp_id) < 13:
                    hsp_id = '0' + hsp_id
                product = Product.query.filter_by(hsp_id=hsp_id).first()
                num = 0
                if product is not None:
                    msg += ' - FOUND'
                    ok = True
                    print(f'{product.id}\t{product.name}')
                    ProductPicture.query.filter_by(product_id=product.id).delete()
                    db.session.commit()
                else:
                    msg += ' - NOT FOUND'
                    ok = False
                    all_ok = False
                db.session.add(IPJResults(image, msg, ok, ipj.id))
                db.session.commit()
            else:
                if product is not None:
                    filename = f'{product.internal_id}_{num}.jpg'
                    print(filename)
                    proc = image_processor(image, filename, ftp_session)
                    if proc is True:
                        db.session.add(ProductPicture(min(num, 2), filename, product.id))
                        product.images_taken = True
                        db.session.commit()
                        print(f'{image} - DONE')
                        db.session.add(IPJResults(image, f'IMAGE - {product.hsp_id} - DONE', True, ipj.id))
                        db.session.commit()
                        num += 1
                    else:
                        print(f'{image} - ERROR')
                        all_ok = False
                        db.session.add(IPJResults(image, f'IMAGE - {product.hsp_id} - ERROR', False, ipj.id))
                        db.session.commit()
            '''
        except Exception as e:
            print(e)
            msg = f'{msg}\n{str(e)}' if msg else str(e)
            db.session.add(IPJResults(image, msg, False, ipj.id))
            db.session.commit()
            num += 1
    ftp_session.quit()
    '''
    ipj.ok = all_ok
    ipj.proc_dt = datetime.now()
    db.session.commit()
    '''


def calc_opt_ratio(min_num: int, max_num: int, w_ratio: float = .15, h_ratio: float = .22):
    images = [f'DSC0{i}.JPG' if i-10000<0 else f'DSC{i}.JPG' for i in range(min_num, max_num + 1)]
    barcode_ws = []
    barcode_hs = []
    p_image_ws = []
    p_image_hs = []
    for image in images:
        page = requests.get(os.environ.get('IMAGE_SERVER') + image)
        if not page.status_code == 200:
            continue
        with open(image, 'wb') as f:
            f.write(page.content)
        img = cv2.imread(image)
        height, width, channels = img.shape
        os.remove(image)
        data, rect = decode(img)
        if rect:
            print(rect.width / width)
            print(rect.height / height)
            if rect.width / width > w_ratio and rect.height / height > h_ratio:
                barcode_ws.append(rect.width / width)
                barcode_hs.append(rect.height / height)
            else:
                p_image_ws.append(rect.width / width)
                p_image_hs.append(rect.height / height)
    print(barcode_ws)
    print(p_image_ws)
    print(barcode_hs)
    print(p_image_hs)
    print(f'W_R:\t{(min(barcode_ws)+max(p_image_ws))/2}')
    print(f'H_R:\t{(min(barcode_hs)+max(p_image_hs))/2}')


def proc_images():
    jobs = ImageProcJob.query.filter(ImageProcJob.id >= 19).filter(ImageProcJob.ok == None).all()
    for job in jobs:
        add_images(job)


def find_product_group(product: Product):
    et_title = ProductFeature.query.filter_by(name='title', source='Entertainment Trading').first()
    vi_title = ProductFeature.query.filter_by(name='Titel', source='Vitrex').first()
    id_title = ProductFeature.query.filter_by(name='title', source='Idealo').first()
    p_ts = product.name.replace(':', '').replace(' / ', '/').replace(' - ', ' ').lower().split(' ')
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
        Product.id == product.id
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
