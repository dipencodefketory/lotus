from lotus import *
from selenium import webdriver
from datetime import *
import time
import csv

filename = '/home/lotus/lager/Gross_' + datetime.now().strftime('%Y_%m_%d') + '.csv'

options = webdriver.FirefoxOptions()
options.add_argument('--headless')

profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.dir', '/home/lotus/lager')
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/csv')
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", 'text/csv')
profile.set_preference("browser.download.manager.showWhenStarting",False)
profile.set_preference("browser.helperApps.neverAsk.openFile", 'text/csv')
profile.set_preference("browser.helperApps.alwaysAsk.force", False)
profile.set_preference("browser.download.manager.useWindow", False)
profile.set_preference("browser.download.manager.focusWhenStarting", False)
profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
profile.set_preference("browser.download.manager.showAlertOnComplete", False)
profile.set_preference("browser.download.manager.closeWhenDone", True)
profile.set_preference("pdfjs.disabled", True)

driver = webdriver.Firefox(firefox_profile=profile, options=options)

driver.get('https://www.gross-electronic.de/')
driver.find_element_by_xpath('/html/body/div[3]/div/div[1]/div/div[5]/div[2]/table/tbody/tr[1]/td[2]/input').send_keys('66493')
driver.find_element_by_xpath('/html/body/div[3]/div/div[1]/div/div[5]/div[2]/table/tbody/tr[2]/td[2]/input').send_keys('w24934v')
driver.find_element_by_xpath('/html/body/div[3]/div/div[1]/div/div[5]/div[2]/table/tbody/tr[3]/td[2]/input').click()

time.sleep(2)

driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/div[1]/div[2]/div[2]/a').click()

time.sleep(2)

driver.get(driver.find_element_by_xpath('/html/body/div[3]/div/div[4]/div[3]/div/ul/li[1]/ul/li[1]/a').get_attribute('href'))

time.sleep(2)

driver.switch_to.frame('export')
url = driver.find_elements_by_class_name("linkBase")[1].get_attribute('href')

response = requests.get(url)
with open(filename, 'wb') as f:
    f.write(response.content)

req_response = ''
error_message = 'Beim Upload der folgenden Produkte sind Fehler entstanden:\n'
error = False

success_message = 'Die Produkte mit den IDs '

counter = 0
with open(filename, encoding='cp1252') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    i=0
    new_products = []
    for row in csv_reader:
        if i==0:
            i+=1
            continue
        if row[1]=='-':
            counter +=1
            print('continued')
            continue
        prod_hsp_id = row[1]
        prod_name = row[2]
        usk = row[8]
        if usk in ['0', '6', '12', '16']:
            lotus_shipping_dhl = 3.55
            shipping_dhl_cost = 2.99
        else:
            lotus_shipping_dhl = 4.54
            shipping_dhl_cost = 4.99

        if len(prod_name)>80:
            prod_name = prod_name[:80].rsplit(' ',1)[0]

        prod_quant = 1 if row[6] == 'lieferbar' else 0
        prod_tax = 19
        prod_price = float(row[3])
        prod_red_price = float(row[5])

        print('-------------------------')
        print(prod_hsp_id)
        print(prod_name)
        print(prod_quant)
        print(prod_price)
        if prod_price != prod_red_price:
            print(prod_red_price)

        while len(prod_hsp_id) < 13:
            prod_hsp_id = '0' + prod_hsp_id
        k=0
        while len(prod_hsp_id) > 13 and prod_hsp_id[0]=='0' and k<10:
            prod_hsp_id = prod_hsp_id[1:]
            k+=1

        product = Product.query.filter_by(hsp_id=prod_hsp_id).first()
        if not product:
            product = Product('EAN', prod_hsp_id, name=prod_name, mpn='nicht zutreffend')
            product.category_id = 1
            db.session.add(product)
            db.session.commit()

            supplier = Supplier.query.filter_by(firmname='Groß Electronic').first()
            gross = Stock.query.filter_by(supplier_id=supplier.id, name='Angebote').first()

            psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                           datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, gross.id)
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

            product.add_basic_product_data(own_stock.id, lotus_shipping_dhl=lotus_shipping_dhl, shipping_dhl_cost=shipping_dhl_cost)

            new_products.append(product)

            j = 0

            while j <= 1:
                file_name = 'generic_pic.jpg'
                db.session.add(ProductPicture(min(j, 2), file_name, product.id))
                j += 1
        else:

            supplier = Supplier.query.filter_by(firmname='Groß Electronic').first()
            gross = Stock.query.filter_by(supplier_id=supplier.id, name='Angebote').first()

            check_psa = Product_Stock_Attributes.query.filter_by(
                product_id=product.id, stock_id=gross.id, user_generated=True
            ).filter(
                Product_Stock_Attributes.avail_date < datetime.now()
            ).filter(
                Product_Stock_Attributes.termination_date > datetime.now()
            ).first()

            if check_psa:
                db.session.delete(check_psa)
                db.session.commit()

            psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                           datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, gross.id)
            psa.last_seen = datetime.now()
            db.session.add(psa)
            db.session.commit()