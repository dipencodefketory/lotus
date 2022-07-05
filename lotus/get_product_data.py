# -*- coding: utf-8 -*-

from lotus import *
import ftplib


def remove_multiples(string, substring):
    while string.count(substring)>1:
        string = string.replace(substring, "", 1)
    return string


def replacer(string):
    string = remove_multiples(string, 'Nintendo Switch')
    string = remove_multiples(string, 'Switch')
    string = remove_multiples(string, 'Nintendo 3DS')
    string = remove_multiples(string, 'PS4')
    string = remove_multiples(string, 'PlayStation 4')
    string = remove_multiples(string, 'Playstation 4')
    string = remove_multiples(string, 'PlayStation 5')
    string = remove_multiples(string, 'Playstation 5')
    string = remove_multiples(string, 'Switch')
    string = string.replace('Switch', 'Nintendo Switch')
    string = remove_multiples(string, 'Nintendo ')
    string = string.replace('3DS', 'Nintendo 3DS')
    string = string.replace('PC/Mac', 'PC')
    string = string.replace('(Nintendo 3DS)', '- Nintendo 3DS')
    string = string.replace('(Nintendo Switch)', '- Nintendo Switch')
    string = string.replace('(DS)', '- Nintendo DS')
    string = string.replace('(Xbox One)', '- Xbox ONE')
    string = string.replace('Xbox One', 'Xbox ONE')
    string = string.replace('(Xbox Series X)', '- Xbox Series X')
    string = string.replace('xbox series x', 'Xbox Series X')
    string = string.replace('(Wii)', '- Wii')
    string = string.replace('(PC)', '- PC')
    string = string.replace('(PS4)', '- PS4')
    string = string.replace('(PS5)', '- PS5')
    string = string.replace('(Steelbook)', '- Steelbook Edition')
    string = string.replace('[Blu-ray]', '- Blu-ray')
    string = string.replace('[DVD]', '- DVD')
    string = string.replace('(Xbox 360)', '- Xbox 360')
    string = string.replace('(PlayStation 4)', '- PS4')
    string = string.replace('PlayStation 4 - PS4', '- PS4')
    string = string.replace('PlayStation 4', 'PS4 / PlayStation 4')
    string = string.replace('PlayStation 5 - PS5', '- PS5')
    string = string.replace('PlayStation 5', 'PS5 / PlayStation 5')
    string = string.replace('PS4', 'PS4 / PlayStation 4')
    string = string.replace('PlayStation 4  PlayStation 4', 'PlayStation 4')
    string = string.replace('PS5', 'PS5 / PlayStation 5')
    string = string.replace('PlayStation 5  PlayStation 5', 'PlayStation 5')
    string = string.replace('Game of the Year Edition', 'GOTY')
    return string


ps = Product.query.filter_by(state=0).all()

cat = ProductLinkCategory.query.filter_by(name='Idealo').first()

own_features = ProductFeature.query.order_by(ProductFeature.name).filter_by(active=True, source='lotus').all()
own_feature_ids = [feature.id for feature in own_features]

session = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')

options = webdriver.FirefoxOptions()
options.add_argument('--headless')

driver = webdriver.Firefox(options=options)

for product in ps:

    try:
        link = ProductLink.query.filter_by(category_id=cat.id, product_id=product.id).first()
        if link:
            if 'OffersOfProduct' in link.link:
                link = link.link
            else:
                continue
        else:
            continue

        print('---------------------')
        print(product.id)

        # GENERATE LINKS

        ###################### EBAY #######################

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

        ####################### MERCATEO #######################

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

        ####################### OGDB #######################

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

        ####################### VITREX #######################

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

        def remove_multiples(string, substring):
            while string.count(substring) > 1:
                string = string.replace(substring, "", 1)
            return string

        def replacer(string):
            string = remove_multiples(string, 'Nintendo Switch')
            string = remove_multiples(string, 'Switch')
            string = remove_multiples(string, 'Nintendo 3DS')
            string = remove_multiples(string, 'PS4')
            string = remove_multiples(string, 'PlayStation 4')
            string = remove_multiples(string, 'Playstation 4')
            string = remove_multiples(string, 'PlayStation 5')
            string = remove_multiples(string, 'Playstation 5')
            string = remove_multiples(string, 'Switch')
            string = string.replace('Switch', 'Nintendo Switch')
            string = remove_multiples(string, 'Nintendo ')
            string = string.replace('3DS', 'Nintendo 3DS')
            string = string.replace('PC/Mac', 'PC')
            string = string.replace('(Nintendo 3DS)', '- Nintendo 3DS')
            string = string.replace('(Nintendo Switch)', '- Nintendo Switch')
            string = string.replace('(DS)', '- Nintendo DS')
            string = string.replace('(Xbox One)', '- Xbox ONE')
            string = string.replace('Xbox One', 'Xbox ONE')
            string = string.replace('(Xbox Series X)', '- Xbox Series X')
            string = string.replace('xbox series x', 'Xbox Series X')
            string = string.replace('(Wii)', '- Wii')
            string = string.replace('(PC)', '- PC')
            string = string.replace('(PS4)', '- PS4')
            string = string.replace('(PS5)', '- PS5')
            string = string.replace('(Steelbook)', '- Steelbook Edition')
            string = string.replace('[Blu-ray]', '- Blu-ray')
            string = string.replace('[DVD]', '- DVD')
            string = string.replace('(Xbox 360)', '- Xbox 360')
            string = string.replace('(PlayStation 4)', '- PS4')
            string = string.replace('PlayStation 4 - PS4', '- PS4')
            string = string.replace('PlayStation 4', 'PS4 / PlayStation 4')
            string = string.replace('PlayStation 5 - PS5', '- PS5')
            string = string.replace('PlayStation 5', 'PS5 / PlayStation 5')
            string = string.replace('PS4', 'PS4 / PlayStation 4')
            string = string.replace('PlayStation 4  PlayStation 4', 'PlayStation 4')
            string = string.replace('PS5', 'PS5 / PlayStation 5')
            string = string.replace('PlayStation 5  PlayStation 5', 'PlayStation 5')
            string = string.replace('Game of the Year Edition', 'GOTY')
            return string

        mpa_name = product.name + ' - Neu & OVP'

        if product.release_date:
            rel_year_feature = ProductFeature.query.filter_by(id=5).first()
            rel_year = product.release_date.year
            featurevalue = ProductFeatureValue.query.filter_by(value=str(rel_year), productfeature_id=rel_year_feature.id).first()
            connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=featurevalue.id).first()
            if not connection:
                db.session.add(Product_ProductFeatureValue(product.id, featurevalue.id))
                db.session.commit()
            if product.release_date > datetime.now():
                mpa_name += ' - Release: ' + datetime.strftime(product.release_date, '%d.%m.%Y')
        for mpa in product.marketplace_attributes:
            mpa.name = mpa_name

        db.session.commit()

        # OGDB
        plc = ProductLinkCategory.query.filter_by(name='OGDB').first()
        link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if link:
            if link.link:
                if 'http' in link.link:
                    shop_request = requests.get(link.link)
                    shop_soup = BS(shop_request.text.replace("\xa0", " "), 'html.parser')
                    rows = shop_soup.findAll(['tr'])
                    for row in rows:
                        data_left = row.find("td", ["tboldc"])
                        data_right = row.find("td", ["tnormg", "tnorm"])
                        if data_left and data_right:
                            feature_name = data_left.text.replace("\xa0", " ").replace(':', '').replace("\n", "").strip()
                            while feature_name[0] == ' ':
                                feature_name = feature_name[1:]
                            if feature_name == 'Allgemeine Informationen':
                                continue
                            if feature_name != 'Unverb. Preisempf.':
                                values = data_right.text[1:].replace("\r", "").replace("\n", "").replace("\xa0", "").strip()
                                if not values:
                                    continue
                                while values[0] == ' ':
                                    values = values[1:]
                                while values[-1] == ' ':
                                    values = values[:-1]
                                values = values.split(', ')
                            else:
                                values = [data_right.text[1:]]
                            feature = ProductFeature.query.filter_by(name=feature_name, source='OGDB').first()
                            if feature is None:
                                feature = ProductFeature(None, feature_name, False)
                                feature.source = 'OGDB'
                                db.session.add(feature)
                                db.session.commit()
                            for value in values:
                                if len(value) > 200:
                                    continue
                                feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                                if feature_value is None:
                                    feature_value = ProductFeatureValue(value, feature.id)
                                    db.session.add(feature_value)
                                    db.session.commit()

                                if product not in feature_value.get_products():
                                    db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                                    db.session.commit()

        # VITREX
        plc = ProductLinkCategory.query.filter_by(name='Vitrex').first()
        link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if link:
            if link.link:
                if 'http' in link.link:
                    shop_request = requests.get(link.link)
                    shop_soup = BS(shop_request.text, 'html.parser')
                    img = shop_soup.find("img", ['img-responsive center-block'])
                    pictures = ProductPicture.query.filter_by(product_id=product.id).all()
                    update_pictures = False
                    if pictures:
                        for pic in pictures:
                            if pic.link == 'generic_pic.jpg':
                                update_pictures = True
                                break
                    if update_pictures:
                        for picture in pictures:
                            db.session.delete(picture)
                            db.session.commit()
                    if img and update_pictures:
                        j = 0
                        try:
                            pic_link = [img['src']][0]
                            product_id = pic_link.split('/')[-1].split('.')[0]

                            page = requests.get(pic_link)

                            while page.status_code == 200:
                                file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(product.name)) + str(j + 1) + '.jpg'
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

                        if j == 1:
                            while j <= 1:
                                file_name = re.sub("[^a-zA-Z0-9]+", "", deumlaut(product.name)) + str(j + 1) + '.jpg'
                                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                                j += 1

                        else:
                            while j <= 1:
                                file_name = 'generic_pic.jpg'
                                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                                j += 1
                    rows = shop_soup.findAll("div", ['row vtx_facts_list'])
                    for row in rows:
                        product_feature_name = row.findAll("div")[0].text[:-1]
                        values = [row.findAll("div")[1].text]
                        feature = ProductFeature.query.filter_by(name=product_feature_name, source='Vitrex').first()
                        if feature is None:
                            feature = ProductFeature(None, product_feature_name, False)
                            feature.source = 'Vitrex'
                            db.session.add(feature)
                            db.session.commit()
                        for value in values:
                            if len(value) > 200:
                                continue
                            feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                            if feature_value is None:
                                feature_value = ProductFeatureValue(value, feature.id)
                                db.session.add(feature_value)
                                db.session.commit()

                            if product not in feature_value.get_products():
                                db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                                db.session.commit()

        usk = False
        usk_val = ''

        insert_list = []
        for value in product.get_ext_featurevalues():
            if value.int_value_id:
                insert_list.append(value.int_value_id)
        for key in insert_list:
            featurevalue = ProductFeatureValue.query.filter_by(id=key).first()
            feature = featurevalue.productfeature
            if product.brand == None or product.brand == '':
                if feature.source == 'Idealo' and feature.name == 'Hersteller/Publisher':
                    product.brand = featurevalue.value
                    db.session.commit()
                elif feature.source == 'Idealo' and feature.name == 'Entwickler':
                    product.brand = featurevalue.value
                    db.session.commit()
            if feature.name == 'USK-Einstufung':
                usk = True
                usk_val = featurevalue.value.split(' ')[-1]
                for mpa in product.marketplace_attributes:
                    if 'Deutsche Version' not in mpa.name and 'EU Version' not in mpa.name:
                        mpa.name += ' - Deutsche Version'
                        db.session.commit()
            connection = Product_ProductFeatureValue.query.filter_by(product_id=product.id, productfeaturevalue_id=key).first()
            if not connection:
                db.session.add(Product_ProductFeatureValue(product.id, key))
                db.session.commit()

        dscrpt_generated = False
        # VITREX DESCRIPTION
        plc = ProductLinkCategory.query.filter_by(name='Vitrex').first()
        link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if link:
            if link.link:
                if 'http' in link.link:
                    shop_request = requests.get(link.link)
                    shop_soup = BS(shop_request.text, 'html.parser')
                    ebay = Marketplace.query.filter_by(name='Ebay').first()
                    dscrpt = Marketplace_Product_Attributes_Description.query.filter_by(
                        marketplace_product_attributes_id=product.get_marketplace_attributes(ebay.id).id,
                        text=''
                    ).first()
                    if dscrpt:
                        description_2 = ''
                        description_wrapper = shop_soup.find("div", ['vtx_desc'])
                        if description_wrapper:
                            description_2 = description_wrapper.p.renderContents().decode().replace("\r", "").replace("\n", "").replace("\xa0", "").replace("<br/>", "\n")
                            while description_2[0] == " ":
                                description_2 = description_2[1:]
                        dscrpt.text = description_2
                        dscrpt_generated = True
                        db.session.commit()
                    else:
                        dscrpts = Marketplace_Product_Attributes_Description.query.filter_by(
                            marketplace_product_attributes_id=product.get_marketplace_attributes(ebay.id).id
                        ).all()
                        if len(dscrpts) < 3:
                            for d in dscrpts:
                                db.session.delete(d)
                            version_ext = 'Deutsche Version mit USK ' + usk_val + ' Kennzeichnung\nEuropäische Verkaufsversion\nDeutsche Spielsprache und Texte verfügbar'

                            if 'PS4 / PlayStation 4' in product.name or 'PlayStation 4' in product.name:
                                console = 'PS4 / PlayStation 4'
                            elif 'PS5 / PlayStation 5' in product.name or 'PlayStation 5' in product.name:
                                console = 'PS5 / PlayStation 5'
                            elif 'Xbox ONE' in product.name:
                                console = 'Xbox ONE'
                            elif 'Xbox Series X' in product.name:
                                console = 'Xbox Series X'
                            elif 'PC' in product.name:
                                console = 'PC'
                            elif 'Nintendo 3DS' in product.name:
                                console = 'Nintendo 3DS'
                            elif 'Nintendo Switch' in product.name:
                                console = 'Nintendo Switch'
                            else:
                                console = 'PS4 / PlayStation 4 PS5 / PlayStation 5 Xbox ONE Xbox Series X PC'

                            description_1 = product.name + '\n' + console + '\nNeu & OVP'
                            description_2 = ''
                            description_wrapper = shop_soup.find("div", ['vtx_desc'])
                            if description_wrapper:
                                description_2 = description_wrapper.p.renderContents().decode().replace("\r", "").replace("\n", "").replace("\xa0", "")
                                while '<br>' in description_2:
                                    index = description_2.index('<br>')
                                    if description_2[index-1] in ['.', '?', '!']:
                                        description_2 = description_2[:index]+'\n'+description_2[index+4:]
                                    else:
                                        description_2 = description_2[:index]+' '+description_2[index+4:]
                                while '<br/>' in description_2:
                                    index = description_2.index('<br/>')
                                    if description_2[index-1] in ['.', '?', '!']:
                                        description_2 = description_2[:index]+'\n'+description_2[index+5:]
                                    else:
                                        description_2 = description_2[:index]+' '+description_2[index+5:]
                                while description_2[0] == " ":
                                    description_2 = description_2[1:]
                            description_3 = 'FEATURES\n\nWAS BEINHALTET DIESE EDITION?'
                            description_4 = '''WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN\nNeu und originalverpackt\nEuropäische Verkaufsversion\nDeutsche Verkaufsversion mit USK Kennzeichnung\nDie Spielehülle beinhaltet nur einen Download-Code, Speicherkarte nicht vorhanden\nSpielsprache: xy | Texte: xy'''
                            if product.release_date:
                                if product.release_date > datetime.now():
                                    description_4 += '\nRelease-Datum: ' + datetime.strftime(product.release_date, '%d.%m.%Y') + ' / Voraussichtlicher Versand am ' + datetime.strftime(
                                        product.release_date - timedelta(days=1), '%d.%m.%Y')
                            db.session.add(Marketplace_Product_Attributes_Description(description_1, product.get_marketplace_attributes(ebay.id).id))
                            db.session.commit()
                            db.session.add(Marketplace_Product_Attributes_Description(description_2, product.get_marketplace_attributes(ebay.id).id))
                            db.session.commit()
                            dscrpt_generated = True
                            db.session.add(Marketplace_Product_Attributes_Description(description_3, product.get_marketplace_attributes(ebay.id).id))
                            db.session.commit()
                            db.session.add(Marketplace_Product_Attributes_Description(description_4, product.get_marketplace_attributes(ebay.id).id))
                            db.session.commit()
        if dscrpt_generated is False:
            ent_dscrpt = ProductFeature.query.filter_by(name='description', source='Entertainment Trading').first()
            dscrpt_ids = [dscrpt.id for dscrpt in ent_dscrpt.values]
            description = Product_ProductFeatureValue.query.filter(Product_ProductFeatureValue.productfeaturevalue_id.in_(dscrpt_ids)).filter_by(product_id=product.id).first()
            if description:
                description = description.productfeaturevalue.value
                ebay = Marketplace.query.filter_by(name='Ebay').first()
                dscrpt = Marketplace_Product_Attributes_Description.query.filter_by(
                    marketplace_product_attributes_id=product.get_marketplace_attributes(ebay.id).id,
                    text=''
                ).first()
                if dscrpt:
                    dscrpt.text = description
                    dscrpt_generated = True
                    db.session.commit()
                else:
                    dscrpts = Marketplace_Product_Attributes_Description.query.filter_by(
                        marketplace_product_attributes_id=product.get_marketplace_attributes(ebay.id).id
                    ).all()
                    if len(dscrpts) < 3:
                        for d in dscrpts:
                            db.session.delete(d)
                        version_ext = 'Deutsche Version mit USK ' + usk_val + ' Kennzeichnung\nEuropäische Verkaufsversion\nDeutsche Spielsprache und Texte verfügbar'

                        if 'PS4 / PlayStation 4' in product.name or 'PlayStation 4' in product.name:
                            console = 'PS4 / PlayStation 4'
                        elif 'PS5 / PlayStation 5' in product.name or 'PlayStation 5' in product.name:
                            console = 'PS5 / PlayStation 5'
                        elif 'Xbox ONE' in product.name:
                            console = 'Xbox ONE'
                        elif 'PC' in product.name:
                            console = 'PC'
                        elif 'Nintendo 3DS' in product.name:
                            console = 'Nintendo 3DS'
                        elif 'Nintendo Switch' in product.name:
                            console = 'Nintendo Switch'
                        else:
                            console = 'PS4 / PlayStation 4 Xbox ONE PC'

                        description_1 = product.name + '\n' + console + '\nNeu & OVP'
                        description_2 = description
                        description_3 = 'WAS SIE NOCH ÜBER DAS PRODUKT WISSEN SOLLTEN\nNeu und originalverpackt\n' + version_ext
                        if product.release_date:
                            if product.release_date > datetime.now():
                                description_3 += '\nRelease-Datum: ' + datetime.strftime(product.release_date, '%d.%m.%Y') + ' / Voraussichtlicher Versand am ' + datetime.strftime(
                                    product.release_date - timedelta(days=1), '%d.%m.%Y')
                        db.session.add(Marketplace_Product_Attributes_Description(description_1, product.get_marketplace_attributes(ebay.id).id))
                        db.session.commit()
                        db.session.add(Marketplace_Product_Attributes_Description(description_2, product.get_marketplace_attributes(ebay.id).id))
                        db.session.commit()
                        dscrpt_generated = True
                        db.session.add(Marketplace_Product_Attributes_Description(description_3, product.get_marketplace_attributes(ebay.id).id))
                        db.session.commit()

        product.state = 1
        db.session.commit()
    except:
        continue

driver.quit()
session = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')
