from lotus import *
import json
import time
from selenium import webdriver
import time

update = datetime.now().replace(microsecond=0,second=0,minute=0)

def match_class(target):
    def do_match(tag):
        classes = tag.get('class', [])
        return all(c in classes for c in target)

    return do_match

last_log = Ext_Idealo_Script_Log.query.order_by(Ext_Idealo_Script_Log.start.desc()).first()

if last_log.last_product_id != 0 and (datetime.now()-last_log.last_activity).seconds >= 60:

    products = Product.query.order_by(Product.id).filter(Product.id >= last_log.last_product_id).all()

    for product in products:
        last_log.last_product_id = product.id
        last_log.last_activity = datetime.now()
        db.session.commit()
        print(product.id)
        try:
            cat = ProductLinkCategory.query.filter_by(label='Idealo').first()
            link = ProductLink.query.filter_by(productlinkcategory_id=cat.id, product_id=product.id).first()
            if link!=None:
                if link.link!=None:
                    if 'OffersOfProduct' in link.link:
                        link=link.link
                    else:
                        continue
                else:
                    continue
            else:
                continue

            r = requests.get(url=link)

            if 'Spam' in r.text:
                print('Detected!')
                print('----------------------')
                print('RESTARTING ROUTER')
                print('')
                print('- Opening Chrome')
                driver = webdriver.Chrome('C:\\flask_projects\\chromedriver.exe')

                print('- Login')
                driver.get ('http://192.168.2.1')
                driver.find_element_by_id('router_password').send_keys('92601366')
                driver.find_element_by_id('loginbutton').click()

                print('- Waiting 30 Seconds')
                for i in range(6):
                    time.sleep(5)
                    print(5*(1+i))

                print('- Disconnect')
                a = driver.find_element_by_xpath('//*[@id="inetAlways"]/a')
                a.click()

                print('- Waiting 30 Seconds')
                for i in range(6):
                    time.sleep(5)
                    print(5*(1+i))

                print('- Connect')
                a = driver.find_element_by_xpath('//*[@id="inetDisabled"]/a')
                a.click()

                print('- Waiting 30 Seconds')
                for i in range(6):
                    time.sleep(5)
                    print(5*(1+i))

                driver.quit()
                print('- Done')
                print('- Exiting Chrome')
                print('----------------------')
                print('CHECKING REQUEST')
                print('')

                r = requests.get(url=link)
                if 'Spam' in r.text:
                    print('- Still detected')
                    send_email('IdealoWarning - Bot detected!', 'system@lotusicafe.de', ['farukoenal@lotusicafe.de'], str(product.id) + ' - ' + product.name, str(product.id) + ' - ' + product.name)
                    break
                else:
                    print('- Undetected')
                    print('----------------------')
                    print('BULLET DODGED')
                    print('----------------------')

            soup = BS(r.text, 'html.parser')

            items = soup.find_all(match_class(["productOffers-listItem"]))
            seen = []
            for item in items:
                dictionary = item.find(match_class(["productOffers-listItemTitle"]))
                data = json.loads(dictionary.get("data-gtm-payload", None))
                try:
                    price_w_sh = float(re.sub("[^,0-9]+", "", item.find(match_class(["productOffers-listItemOfferShippingDetailsLeft"])).text).replace(',','.'))
                except:
                    price_w_sh = None
                seller = Ext_Idealo_Seller.query.filter_by(name=data['shop_name']).first()
                if seller == None:
                    seller = Ext_Idealo_Seller(data['shop_name'])
                    db.session.add(seller)
                    db.session.commit()

                if seller.name not in seen:
                    platform = Ext_Idealo_Seller_Platform.query.filter_by(name=item.find(match_class(["productOffers-listItemOfferLogoLink"])).get("data-shop-name").split(' - ')[0]).first()
                    if platform == None:
                        platform = Ext_Idealo_Seller_Platform(item.find(match_class(["productOffers-listItemOfferLogoLink"])).get("data-shop-name").split(' - ')[0])
                        db.session.add(platform)
                        db.session.commit()

                    offer = Ext_Idealo_Offer.query.order_by(Ext_Idealo_Offer.entry_date.desc()).filter_by(seller_id=seller.id, product_id=product.id, platform_id=platform.id).first()
                    if price_w_sh:
                        shipping = round(price_w_sh-float(data['product_price']),2)
                    else:
                        shipping = 0
                    if data['product_price'] == 'button.checkout':
                        direct_checkout = True
                    else:
                        direct_checkout = False
                    if offer == None:
                        offer = Ext_Idealo_Offer(seller.id,
                                                 product.id,
                                                 platform.id,
                                                 float(data['product_price']),
                                                 shipping, direct_checkout,
                                                 int(data['position']),
                                                 data['delivery_time'],
                                                 int(data['free_return']),
                                                 int(data['shop_rating']),
                                                 data['approved_shipping']=='true',
                                                 data['voucher']=='true',
                                                 update)
                        db.session.add(offer)
                    else:
                        if (float(data['product_price']) != offer.price
                        or shipping != offer.shipping_price
                        or data['delivery_time'] != offer.delivery_time):
                            offer = Ext_Idealo_Offer(seller.id,
                                                     product.id,
                                                     platform.id,
                                                     float(data['product_price']),
                                                     shipping, direct_checkout,
                                                     int(data['position']),
                                                     data['delivery_time'],
                                                     int(data['free_return']),
                                                     int(data['shop_rating']),
                                                     data['approved_shipping']=='true',
                                                     data['voucher']=='true',
                                                     update)
                            db.session.add(offer)
                        else:
                            offer.last_seen = update
                    seen.append(seller.name)
                    db.session.commit()
            print('done')
        except:
            print('invalid string')
    last_log.last_product_id = 0
    last_log.last_activity = datetime.now()
    last_log.end = datetime.now()

elif last_log.last_product_id == 0 and (datetime.now()-last_log.start).seconds >= 21600:
    newlog = Ext_Idealo_Script_Log(datetime.now().replace(microsecond=0,second=0,minute=0))
    products = Product.query.order_by(Product.id).all()

    for product in products:
        newlog.last_product_id = product.id
        newlog.last_activity = datetime.now()
        db.session.commit()
        print(product.id)
        try:
            cat = ProductLinkCategory.query.filter_by(label='Idealo').first()
            link = ProductLink.query.filter_by(productlinkcategory_id=cat.id, product_id=product.id).first()
            if link != None:
                if link.link != None:
                    if 'OffersOfProduct' in link.link:
                        link = link.link
                    else:
                        continue
                else:
                    continue
            else:
                continue

            r = requests.get(url=link)

            if 'Spam' in r.text:
                print('Detected!')
                print('----------------------')
                print('RESTARTING ROUTER')
                print('')
                print('- Opening Chrome')
                driver = webdriver.Chrome('C:\\flask_projects\\chromedriver.exe')

                print('- Login')
                driver.get('http://192.168.2.1')
                driver.find_element_by_id('router_password').send_keys('92601366')
                driver.find_element_by_id('loginbutton').click()

                print('- Waiting 30 Seconds')
                for i in range(6):
                    time.sleep(5)
                    print(5 * (1 + i))

                print('- Disconnect')
                a = driver.find_element_by_xpath('//*[@id="inetAlways"]/a')
                a.click()

                print('- Waiting 30 Seconds')
                for i in range(6):
                    time.sleep(5)
                    print(5 * (1 + i))

                print('- Connect')
                a = driver.find_element_by_xpath('//*[@id="inetDisabled"]/a')
                a.click()

                print('- Waiting 30 Seconds')
                for i in range(6):
                    time.sleep(5)
                    print(5 * (1 + i))

                driver.quit()
                print('- Done')
                print('- Exiting Chrome')
                print('----------------------')
                print('CHECKING REQUEST')
                print('')

                r = requests.get(url=link)
                if 'Spam' in r.text:
                    print('- Still detected')
                    send_email('IdealoWarning - Bot detected!', 'system@lotusicafe.de', ['farukoenal@lotusicafe.de'],
                               str(product.id) + ' - ' + product.name, str(product.id) + ' - ' + product.name)
                    break
                else:
                    print('- Undetected')
                    print('----------------------')
                    print('BULLET DODGED')
                    print('----------------------')

            soup = BS(r.text, 'html.parser')

            items = soup.find_all(match_class(["productOffers-listItem"]))
            seen = []
            for item in items:
                dictionary = item.find(match_class(["productOffers-listItemTitle"]))
                data = json.loads(dictionary.get("data-gtm-payload", None))
                try:
                    price_w_sh = float(re.sub("[^,0-9]+", "", item.find(
                        match_class(["productOffers-listItemOfferShippingDetailsLeft"])).text).replace(',', '.'))
                except:
                    price_w_sh = None
                seller = Ext_Idealo_Seller.query.filter_by(name=data['shop_name']).first()
                if seller == None:
                    seller = Ext_Idealo_Seller(data['shop_name'])
                    db.session.add(seller)
                    db.session.commit()

                if seller.name not in seen:
                    platform = Ext_Idealo_Seller_Platform.query.filter_by(name=item.find(
                        match_class(["productOffers-listItemOfferLogoLink"])).get("data-shop-name").split(' - ')[
                        0]).first()
                    if platform == None:
                        platform = Ext_Idealo_Seller_Platform(
                            item.find(match_class(["productOffers-listItemOfferLogoLink"])).get("data-shop-name").split(
                                ' - ')[0])
                        db.session.add(platform)
                        db.session.commit()

                    offer = Ext_Idealo_Offer.query.order_by(Ext_Idealo_Offer.entry_date.desc()).filter_by(
                        seller_id=seller.id, product_id=product.id, platform_id=platform.id).first()
                    if price_w_sh:
                        shipping = round(price_w_sh - float(data['product_price']), 2)
                    else:
                        shipping = 0
                    if data['product_price'] == 'button.checkout':
                        direct_checkout = True
                    else:
                        direct_checkout = False
                    if offer == None:
                        offer = Ext_Idealo_Offer(seller.id,
                                                 product.id,
                                                 platform.id,
                                                 float(data['product_price']),
                                                 shipping, direct_checkout,
                                                 int(data['position']),
                                                 data['delivery_time'],
                                                 int(data['free_return']),
                                                 int(data['shop_rating']),
                                                 data['approved_shipping'] == 'true',
                                                 data['voucher'] == 'true',
                                                 update)
                        db.session.add(offer)
                    else:
                        if (float(data['product_price']) != offer.price
                                or shipping != offer.shipping_price
                                or data['delivery_time'] != offer.delivery_time):
                            offer = Ext_Idealo_Offer(seller.id,
                                                     product.id,
                                                     platform.id,
                                                     float(data['product_price']),
                                                     shipping, direct_checkout,
                                                     int(data['position']),
                                                     data['delivery_time'],
                                                     int(data['free_return']),
                                                     int(data['shop_rating']),
                                                     data['approved_shipping'] == 'true',
                                                     data['voucher'] == 'true',
                                                     update)
                            db.session.add(offer)
                        else:
                            offer.last_seen = update
                    seen.append(seller.name)
                    db.session.commit()
            print('done')
        except:
            print('invalid string')
    newlog.last_product_id = 0
    newlog.last_activity = datetime.now()
    newlog.end = datetime.now()
