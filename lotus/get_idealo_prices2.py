# -*- coding: utf-8 -*-

from lotus import *
import time as t
import os
import zipfile
import re
from io import TextIOWrapper
from selenium.common.exceptions import TimeoutException
'''
options = webdriver.FirefoxOptions()
options.add_argument('--headless')
options.set_preference("browser.download.folderList",2)
options.set_preference("browser.download.manager.showWhenStarting", False)
options.set_preference("browser.download.dir", "/home/lotus/")
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream,application/vnd.ms-excel")

driver = webdriver.Firefox(options=options)
driver.get("https://business.idealo.com/de/login")
iframe = driver.find_elements_by_xpath("//*[contains(@id, 'sp_message_iframe')]")[0]
driver.switch_to.frame(iframe)
driver.find_element_by_xpath('/html/body/div/div[3]/div[4]/div[2]/button').click()
driver.switch_to.default_content()
driver.find_element_by_xpath('//*[@id="mat-input-0"]').send_keys('farukoenal@lotusicafe.de')
driver.find_element_by_xpath('//*[@id="mat-input-1"]').send_keys('Ideal21Lot06!')
driver.find_element_by_xpath('/html/body/app-root/div/app-login/div/div/app-prime-content-box/div/div[2]/form/div[2]/button[2]').click()
t.sleep(10)
driver.get("https://business.idealo.com/de/shops/318578/1/checkout/statistics")
t.sleep(10)
driver.find_element_by_xpath('/html/body/app-root/div/app-navigation-frame-page/app-checkout-statistics-page/div[1]/app-permission-alert-wrapper/div/app-price-report-widget/app-data-card/div/div[2]/app-status-wrapper/div/div/a').click()
t.sleep(120)
driver.find_element_by_xpath('/html/body/app-root/div/app-navigation-frame-page/app-checkout-statistics-page/div[1]/app-permission-alert-wrapper/div/app-price-report-widget/app-data-card/div/div[2]/app-status-wrapper/table/tbody/tr[1]/td[3]/div/div/a[2]').click()
t.sleep(120)
try:
    driver.get("https://businessapi.idealo.com/businessbackend/api/v1/shops/318578/offers/report/download?site=IDEALO_DE")
except TimeoutException:
    pass

driver.quit()
'''
update = datetime.now().replace(microsecond=0, second=0, minute=0)
marketplace = Marketplace.query.filter_by(name='Idealo').first()

licSeller = ExtSeller.query.filter_by(name='lotusicafe').first()
licPlatform = ExtPlatform.query.filter_by(name='lotusicafe').first()
extSeller = ExtSeller.query.filter_by(name='Unbekannt').first()
extPlatform = ExtPlatform.query.filter_by(name='Unbekannt').first()

offerDict = {}
# offerDict = {idealoID: {SKUs: [SKU1, SKU2, ...}, offers: [[SellerID, PlatformID, sellingPrice, shippingPrice, delivery_time], [SellerID, PlatformID, sellingPrice, shippingPrice, delivery_time], ...]}
for file in os.listdir("/home/lotus"):
    if file.endswith(".zip"):
        if 'price' in file:
            with zipfile.ZipFile("/home/lotus/" + file) as z:
                for filename in z.namelist():
                    with z.open(filename, 'r') as csv_file:
                        csv_reader = csv.reader(TextIOWrapper(csv_file, 'utf-8'), delimiter=',')
                        i = 0
                        for row in csv_reader:
                            print(i)
                            if i <= 1:
                                i += 1
                                continue
                            idealoID = row[1].split('/')[-1]
                            if idealoID in offerDict:
                                offerDict[idealoID]['offers'][int(re.sub('[^0-9]', '', row[5]))-1][0] = licSeller.id
                                offerDict[idealoID]['offers'][int(re.sub('[^0-9]', '', row[5]))-1][1] = licPlatform.id
                                offerDict[idealoID]['SKUs'].append(row[3])
                                continue
                            else:
                                for k in range(10):
                                    if k == int(re.sub('[^0-9]', '', row[5])) - 1:
                                        seller_id = licSeller.id
                                        platform_id = licPlatform.id
                                    else:
                                        seller_id = extSeller.id
                                        platform_id = extPlatform.id
                                    price_w_sh = str_to_float(money_to_float(row[12+k*4]))
                                    if price_w_sh==None:
                                        continue
                                    selling_price = str_to_float(money_to_float(row[10+k*4]))
                                    shipping_price = str_to_float(money_to_float(row[11+k*4]))
                                    delivery_time = row[13+k*4]
                                    if k == 0:
                                        offerDict[idealoID] = {'SKUs': [row[3]], 'offers': [[seller_id, platform_id, selling_price, shipping_price, delivery_time]]}
                                    else:
                                        offerDict[idealoID]['offers'].append([seller_id, platform_id, selling_price, shipping_price, delivery_time])

                            i += 1
                        print(offerDict)
                        '''
                        i = 0
                        for key in offerDict:
                            skus = offerDict[key]['SKUs']
                            print('------------------')
                            print(i)
                            print(skus)
                            products = Product.query.filter(Product.internal_id.in_(skus)).all()
                            for offer in offerDict[key]['offers']:
                                seller_id = offer[0]
                                platform_id = offer[1]
                                selling_price = offer[2]
                                shipping_price = offer[3]
                                delivery_time = offer[4]
                                for product in products:
                                    offer = ExtOffer.query.order_by(ExtOffer.init_date.desc()).filter_by(seller_id=offer[0], platform_id=offer[1], product_id=product.id, marketplace_id=marketplace.id,
                                                                                                         selling_price=offer[2], shipping_price=offer[3]).first()
                                    if offer is None:
                                        offer = ExtOffer(offer[2], offer[3], None, k+1, offer[4], None, None, None, marketplace.id, offer[1], product.id, offer[0])
                                        db.session.add(offer)
                                    else:
                                        if (offer[2] != offer.selling_price
                                                or offer[3] != offer.shipping_price
                                                or offer[4] != offer.delivery_time):
                                            offer = ExtOffer(offer[2], offer[3], None, k+1, offer[4], None, None, None, marketplace.id, offer[1], product.id, offer[0])
                                            db.session.add(offer)
                                        else:
                                            offer.last_seen = update
                                    db.session.commit()
                            i+=1
                        '''
        #os.remove("/home/lotus/" + file)
