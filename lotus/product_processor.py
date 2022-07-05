# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, ProductFeature, ProductFeatureValue, Product_ProductFeatureValue, ProductPicture, ProductCategory, ProductLink, ProductLinkCategory, Marketplace, Marketplace_Product_Attributes, Marketplace_Product_Attributes_Description
from bs4 import BeautifulSoup
from functions import replacer, deumlaut
from lookup import platform_dict, version_normalizer_dict, region_dict
import routines
from selenium import webdriver
import ftplib
from datetime import datetime
import time
from typing import List
import html2text
import re

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


def get_ext_feature_dict(product_id: int, source: str):
    query = db.session.query(Product_ProductFeatureValue, ProductFeatureValue, ProductFeature).filter(
        Product_ProductFeatureValue.product_id == product_id
    ).filter(
        Product_ProductFeatureValue.productfeaturevalue_id == ProductFeatureValue.id
    ).filter(
        ProductFeatureValue.productfeature_id == ProductFeature.id
    ).filter(
        ProductFeature.source == source
    ).all()
    return {el[2].name: el[1].value for el in query}


def idealo_data_extractor(product_id: int, idealo_source: str):
    product = Product.query.filter_by(id=product_id).first()
    soup = BeautifulSoup(idealo_source, 'html.parser')
    data_list = soup.findAll("li", {"class": "datasheet-listItem datasheet-listItem--properties"})
    for data in data_list:
        product_feature_name = data.find_all(recursive=False)[0].text.replace('\n', '').replace('\t', '').replace('\xa0', ' ').strip()
        values = data.find_all(recursive=False)[1].text.replace('\n', '').replace('\t', '').replace('\xa0', ' ').replace(' / ', ', ').split(', ')
        feature_value_adder(product, product_feature_name, values, 'Idealo')
    cat_path = soup.find_all("span", {"class": "breadcrumb-linkText"})
    value = ' > '.join([obj.text for obj in cat_path])
    feature_value_adder(product, 'category_path', [value], 'Idealo')
    title = soup.find("h1", {"class": "oopStage-title"})
    new_name = replacer(' - '.join([obj.text for obj in title.findAll("span")]))
    feature_value_adder(product, 'title', [new_name], 'Idealo')
    return 200


def gen_product_links(product_id):
    product = Product.query.filter_by(id=product_id).first()
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)

    # EBAY
    plc = ProductLinkCategory.query.filter_by(name='Ebay').first()
    no_link = False
    check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
    if check_link:
        if 'http' not in check_link.link:
            db.session.delete(check_link)
            no_link = True
    else:
        no_link = True
    if no_link:
        ebay_link = 'https://www.ebay.de/sch/i.html?_nkw=' + product.hsp_id + '&LH_ItemCondition=3&rt=nc&LH_BIN=1'
        db.session.add(ProductLink(ebay_link, plc.id, product.id))
        db.session.commit()

    # MERCATEO
    plc = ProductLinkCategory.query.filter_by(name='Mercateo').first()
    no_link = False
    check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
    if check_link:
        if 'http' not in check_link.link:
            db.session.delete(check_link)
            no_link = True
    else:
        no_link = True
    if no_link:
        try:
            driver.get("http://www.mercateo.com/")
            driver.find_element_by_id('query').send_keys(product.hsp_id)
            driver.find_element_by_id("searchbutton").click()
            db.session.add(ProductLink(driver.current_url, plc.id, product.id))
            db.session.commit()
        except:
            pass

    # OGDB

    plc = ProductLinkCategory.query.filter_by(name='OGDB').first()
    no_link = False
    check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
    if check_link:
        if 'http' not in check_link.link:
            db.session.delete(check_link)
            no_link = True
    else:
        no_link = True
    if no_link:
        try:
            driver.get("https://ogdb.eu/")
            driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[1]/table/tbody/tr/td/div/form/div/input[1]').send_keys(product.hsp_id)
            driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[1]/table/tbody/tr/td/div/form/div/input[2]').click()
            time.sleep(1)
            driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[3]/table[2]/tbody/tr[2]/td/span/a').click()
            db.session.add(ProductLink(driver.current_url, plc.id, product.id))
            db.session.commit()
        except:
            pass

    # VITREX
    plc = ProductLinkCategory.query.filter_by(name='Vitrex').first()
    no_link = False
    check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
    if check_link:
        if 'http' not in check_link.link:
            db.session.delete(check_link)
            no_link = True
    else:
        no_link = True
    if no_link:
        try:
            driver.get("https://www.vitrex-shop.de/de/erweiterte-suche__13/?itid=13&send_form=1&vtx_search=1&quicksearch=" + product.hsp_id + "&search_button=1")
            element = driver.find_element_by_xpath('/html/body/div[3]/div/div[3]/div[2]/div[2]/div[4]/div/div/div[3]/a')
            driver.execute_script("arguments[0].click();", element)
            time.sleep(2)
            db.session.add(ProductLink(driver.current_url, plc.id, product.id))
            db.session.commit()
        except:
            pass


def proc_product(product_id: int):
    proc_count = 0
    product = Product.query.filter_by(id=product_id).first()

    idealo_dict = get_ext_feature_dict(product_id, 'Idealo')
    ent_trading_dict = get_ext_feature_dict(product_id, 'Entertainment Trading')
    vitrex_dict = get_ext_feature_dict(product_id, 'Vitrex')
    ogdb_dict = get_ext_feature_dict(product_id, 'OGDB')
    vitrex_img_link = ''
    et_img_link = ''
    toy_cat = ProductCategory.query.filter_by(id=27).first()
    toy_cats = [toy_cat.id] + [cat.id for cat in toy_cat.get_successors()]
    if 'Region' in ent_trading_dict:
        if ent_trading_dict['Region'] in region_dict:
            product.spec_trait_3 = region_dict[ent_trading_dict['Region']]
        else:
            product.spec_trait_3 = ent_trading_dict['Region']
    if not product.spec_trait_3:
        if 'FSK' in vitrex_dict:
            if vitrex_dict['FSK'].strip() in ['o.A.', '6', '12', '16', '18']:
                product.spec_trait_3 = 'USK'
    if not product.spec_trait_3:
        for version in ['AT', 'UK', 'USK', 'Nordic', 'PEGI']:
            if version in product.name:
                product.spec_trait_3 = version
    if idealo_dict:
        if 'Plattform' in idealo_dict:
            if idealo_dict['Plattform'] in platform_dict:
                product.spec_trait_2 = platform_dict[idealo_dict['Plattform']]
            else:
                product.spec_trait_2 = ''
        if 'Hersteller/Publisher' in idealo_dict:
            if idealo_dict['Hersteller/Publisher']:
                product.brand = idealo_dict['Hersteller/Publisher']
                proc_count += 1
        elif 'Entwickler' in idealo_dict:
            if idealo_dict['Entwickler']:
                product.brand = idealo_dict['Entwickler']
                proc_count += 1
        elif product.brand not in ['', None]:
            proc_count += 1
        if 'category_path' in idealo_dict:
            if 'Konsolenspiele' in idealo_dict['category_path'] or 'PC-Spiele' in idealo_dict['category_path']:
                product.category_id = 1
                proc_count += 1
            elif 'Gamepads' in idealo_dict['category_path']:
                product.category_id = 5
                proc_count += 1
            elif product.category_id != None:
                proc_count += 1
        if 'title' in idealo_dict:
            split_name = idealo_dict['title'].split(' - ')
            product.spec_trait_0 = split_name[0]
            product.spec_trait_1 = split_name[1] if len(split_name) > 2 else ''
            if len(split_name) > 1:
                st2 = split_name[2] if len(split_name) > 2 else split_name[1]
            else:
                st2 = ''
            if product.category_id in [1, 5]:
                product.spec_trait_2 = platform_dict[st2] if st2 in platform_dict else ''
            else:
                product.spec_trait_2 = st2
    elif ent_trading_dict:
        product.spec_trait_0 = ent_trading_dict['title']
        product.spec_trait_1 = ent_trading_dict['Edition'] if ent_trading_dict['Edition'] != 'Standard' else ''
        if ent_trading_dict['platform']:
            product.spec_trait_2 = platform_dict[ent_trading_dict['platform']] if ent_trading_dict['platform'] in platform_dict else ''
        else:
            product.spec_trait_2 = ''
        if ent_trading_dict['brand']:
            product.brand = ent_trading_dict['brand']
            proc_count += 1
        else:
            product.brand = ent_trading_dict['manufacturer']
            proc_count += 1
        if ent_trading_dict['category'].split(' - ')[-1] == 'Games':
            product.category_id = 1
            proc_count += 1
        et_img_link = ent_trading_dict['image']
    elif vitrex_dict:
        product.spec_trait_2 = platform_dict[vitrex_dict['System']] if vitrex_dict['System'] else ''
        product.name = vitrex_dict['Titel']
        product.brand = vitrex_dict['Label']
        if 'Software' in vitrex_dict['Warengruppe']:
            product.category_id = 1
            proc_count += 1
        if 'Bild' in vitrex_dict:
            vitrex_img_link = vitrex_dict['Bild'] if vitrex_dict['Bild'] else ''
        elif 'Jpg-Pfad' in vitrex_dict:
            vitrex_img_link = vitrex_dict['Jpg-Pfad'] if vitrex_dict['Jpg-Pfad'] else ''
    if product.spec_trait_0 == None or product.spec_trait_1 == None or product.spec_trait_2 == None:
        if ent_trading_dict:
            product.spec_trait_0 = ent_trading_dict['title']
            product.spec_trait_1 = ent_trading_dict['Edition'] if ent_trading_dict['Edition'] != 'Standard' else ''
            if ent_trading_dict['platform']:
                product.spec_trait_2 = platform_dict[ent_trading_dict['platform']] if ent_trading_dict['platform'] in platform_dict else ''
            else:
                product.spec_trait_2 = ''
            if ent_trading_dict['brand']:
                product.brand = ent_trading_dict['brand']
                proc_count += 1
            else:
                product.brand = ent_trading_dict['manufacturer']
                proc_count += 1
            if ent_trading_dict['category'].split(' - ')[-1] == 'Games':
                product.category_id = 1
                proc_count += 1
            et_img_link = ent_trading_dict['image']
        elif vitrex_dict:
            product.spec_trait_2 = platform_dict[vitrex_dict['System']] if vitrex_dict['System'] else ''
            product.name = vitrex_dict['Titel']
            product.brand = vitrex_dict['Label']
            if 'Software' in vitrex_dict['Warengruppe']:
                product.category_id = 1
                proc_count += 1
            if 'Bild' in vitrex_dict:
                vitrex_img_link = vitrex_dict['Bild'] if vitrex_dict['Bild'] else ''
            elif 'Jpg-Pfad' in vitrex_dict:
                vitrex_img_link = vitrex_dict['Jpg-Pfad'] if vitrex_dict['Jpg-Pfad'] else ''
    db.session.commit()
    if not product.release_date:
        if ent_trading_dict:
            product.release_date = datetime.strptime(ent_trading_dict['release_date'], '%Y-%m-%d') if ent_trading_dict['release_date'] else None
        elif vitrex_dict:
            product.release_date = datetime.strptime(vitrex_dict['VÖ-Datum'], '%d.%m.%Y') if vitrex_dict['VÖ-Datum'] else None
    if product.spec_trait_0:
        product.name = product.spec_trait_0
        product.name += f' - {product.spec_trait_1}' if product.spec_trait_1 else ''
        product.name += f' - {product.spec_trait_2}' if product.spec_trait_2 else ''
        product.name += f' - {product.spec_trait_3}' if product.spec_trait_3 else ''
        proc_count += 4
        for mpa in product.marketplace_attributes:
            mpa.name = product.spec_trait_0 if product.spec_trait_0 else product.name
            mpa.name += f' - {product.spec_trait_1}' if product.spec_trait_1 else ''
            mpa.name += f' - {product.spec_trait_2}' if product.spec_trait_2 else ''
            mpa.name += ' - Neu & OVP'
            mpa.name += f' - {version_normalizer_dict[product.spec_trait_3]}' if product.spec_trait_3 in version_normalizer_dict else ''
            if mpa.marketplace.id == 1:
                if product.spec_trait_3 in ['AT', 'EU', 'UK', 'Nordic', 'PEGI', 'AUS'] and product.category_id == 1:
                    if product.spec_trait_3 in ['UK', 'AUS', 'Nordic']:
                        mpa.name += f' - Englisches Cover'
                    elif product.spec_trait_3 not in ['EU', 'PEGI']:
                        mpa.name += f' - {product.spec_trait_3} Cover'
                if product.release_date:
                    if product.release_date > datetime.now():
                        mpa.name += ' - Release: ' + datetime.strftime(product.release_date, '%d.%m.%Y')
                if 'category_path' in idealo_dict:
                    mpa.category_path = idealo_dict['category_path']
    db.session.commit()
    if not product.brand:
        if ogdb_dict:
            if 'Entwickler' in ogdb_dict:
                product.brand = ogdb_dict['Entwickler'] if ogdb_dict['Entwickler'] else ''
            if not product.brand:
                if 'Publisher' in ogdb_dict:
                    product.brand = ogdb_dict['Publisher'] if ogdb_dict['Publisher'] else ''
    db.session.commit()

    # FEATURES
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
        connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=key).first()
        if not connection:
            db.session.add(Product_ProductFeatureValue(product.id, key))
            db.session.commit()

    if product.spec_trait_0:
        feature = ProductFeature.query.filter_by(source='lotus', name='Spielname').first()
        if feature.active:
            featurevalue = product.spec_trait_0
            featurevalue += f' - {product.spec_trait_1}' if product.spec_trait_1 else ''
            checkvalues = feature.get_value_product(product.id)
            if checkvalues:
                for checkvalue in checkvalues:
                    connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=checkvalue.id).first()
                    if connection:
                        db.session.delete(connection)
                        db.session.commit()
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

    if product.spec_trait_1:
        feature = ProductFeature.query.filter_by(source='lotus', name='Besonderheiten').first()
        if feature.active:
            featurevalue = product.spec_trait_1
            checkvalues = feature.get_value_product(product.id)
            if checkvalues:
                for checkvalue in checkvalues:
                    connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=checkvalue.id).first()
                    if connection:
                        db.session.delete(connection)
                        db.session.commit()
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

    # DESCRIPTIONS
    ebay = Marketplace.query.filter_by(name='Ebay').first()
    ebay_mpa = Marketplace_Product_Attributes.query.filter_by(product_id=product.id, marketplace_id=ebay.id).first()

    description = Marketplace_Product_Attributes_Description.query.filter(
        Marketplace_Product_Attributes_Description.position == 2
    ).filter(
        Marketplace_Product_Attributes_Description.marketplace_product_attributes_id == ebay_mpa.id
    ).first()
    if description:
        description = description.text
        proc_count += 1
    if not description:
        if vitrex_dict:
            if 'Beschreibung' in vitrex_dict:
                description = h.handle(vitrex_dict['Beschreibung'].replace(' <BR> ', ' ').replace('<BR><BR>', '\n').replace(' <BR>', ' ').replace('<BR> ', ' '))
                proc_count += 1
            else:
                description = ''
        elif ent_trading_dict:
            description = h.handle(ent_trading_dict['description'])
            proc_count += 1
        else:
            description = ''
    routines.ebay_description_generator(product, description, usk, usk_val)

    # IMAGES
    ftp_session = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')
    pictures = ProductPicture.query.filter_by(product_id=product.id).all()
    update_pictures = False
    if pictures:
        for pic in pictures:
            if pic.link == 'generic_pic.jpg' and product.category_id not in toy_cats:
                update_pictures = True
                break
    if update_pictures:
        for picture in pictures:
            db.session.delete(picture)
            db.session.commit()
    else:
        proc_count += 1
    if vitrex_img_link and update_pictures:
        j = 0
        try:
            product_id = vitrex_img_link.split('/')[-1].split('.')[0]
            url = vitrex_img_link
            for j in range(10):
                file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(product.name)) + str(j+1) + '.jpg'
                res = routines.store_image(ftp_session, product, url, file_name)
                if res == 400:
                    break
                url = 'https://bilderserver.vitrex.de/' + product_id + '_' + str(j) + '.jpg'
        except Exception:
            pass
        if j == 1:
            proc_count += 1
            while j <= 1:
                file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(product.name)) + str(j + 1) + '.jpg'
                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                j += 1
        else:
            while j <= 1:
                file_name = 'generic_pic.jpg'
                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                j += 1
        db.session.commit()
        update_pictures = False
    if et_img_link and update_pictures:
        j = 0
        try:
            file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(product.name)) + str(j + 1) + '.jpg'
            res = routines.store_image(ftp_session, product, et_img_link, file_name)
            if res == 200:
                j+=1
        except Exception:
            pass
        if j == 1:
            proc_count += 1
            while j <= 1:
                file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(product.name)) + str(j + 1) + '.jpg'
                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                j += 1
        else:
            while j <= 1:
                file_name = 'generic_pic.jpg'
                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                j += 1
        db.session.commit()
    ftp_session.quit()
    print(proc_count)
    routines.r_ify_product(product)
    if proc_count > 6:
        product.state = 1
        db.session.commit()
    return 200
