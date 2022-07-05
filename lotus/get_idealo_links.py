# -*- coding: utf-8 -*-

from lotus import *
import time as t
import os
import zipfile
from io import TextIOWrapper
from selenium.common.exceptions import TimeoutException

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
driver.get("https://business.idealo.com/de/shops/318578/1/offers/statistics")
t.sleep(10)
driver.find_element_by_xpath('/html/body/app-root/div/app-navigation-frame-page/app-offers-statistics-page/div[1]/app-permission-alert-wrapper/div/app-offers-list-widget/app-report-download-box/div/div[2]/div[2]/button').click()
t.sleep(20)
try:
    driver.get("https://businessapi.idealo.com/businessbackend/api/v1/shops/318578/offers/report/download?site=IDEALO_DE")
except TimeoutException:
    pass

driver.quit()

for file in os.listdir("/home/lotus"):
    if file.endswith(".zip"):
        with zipfile.ZipFile("/home/lotus/" + file) as z:
            for filename in z.namelist():
                with z.open(filename, 'r') as csv_file:
                    csv_reader = csv.reader(TextIOWrapper(csv_file, 'utf-8'), delimiter=',')
                    i = 0
                    for row in csv_reader:
                        if i == 0:
                            i += 1
                            continue
                        internal_id = row[10]
                        link = row[9]
                        if link:
                            plc = ProductLinkCategory.query.filter_by(name='Idealo').first()
                            product = Product.query.filter_by(internal_id=internal_id).first()
                            if product:
                                product_link = ProductLink.query.filter_by(category_id=plc.id, product_id=product.id).first()
                                if product_link:
                                    if 'OffersOfProduct' not in product_link.link:
                                        print('----------------')
                                        print(product.id)
                                        print('----------------')
                                        db.session.delete(product_link)
                                        new_link = ProductLink(link, plc.id, product.id)
                                        new_link.ext_idealo_watch_active = True
                                        db.session.add(new_link)
                                else:
                                    print('----------------')
                                    print(product.id)
                                    print('----------------')
                                    new_link = ProductLink(link, plc.id, product.id)
                                    new_link.ext_idealo_watch_active = True
                                    db.session.add(new_link)
                                db.session.commit()
        os.remove("/home/lotus/" + file)
