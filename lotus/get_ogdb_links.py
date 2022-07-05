from lotus import *
import time as t

products = Product.query.order_by(Product.id).all()

options = webdriver.FirefoxOptions()
options.add_argument('--headless')

driver = webdriver.Firefox(options=options)
for product in products:
    print(product.id)
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

            t.sleep(1)
            driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[3]/table[2]/tbody/tr[2]/td/span/a').click()

            db.session.add(ProductLink(driver.current_url, plc.id, product.id))
            db.session.commit()
            t.sleep(2)

        except:

            pass

driver.quit()
