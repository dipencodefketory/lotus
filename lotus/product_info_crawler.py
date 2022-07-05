# -*- coding: utf-8 -*-

from lotus import *
import time
from selenium import webdriver

options = webdriver.FirefoxOptions()
options.add_argument('--headless')

driver = webdriver.Firefox(options=options)

product_ids = [126, 190, 679]

products = Product.query.filter(Product.id.in_(product_ids)).all()

for product in products:
    ####################### EBAY #######################

    ebay_link = 'https://www.ebay.de/sch/i.html?_nkw=' + product.hsp_id + '&LH_ItemCondition=3&rt=nc&LH_BIN=1'

    plc = ProductLinkCategory.query.filter_by(name='Ebay').first()
    check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
    if check_link:
        db.session.delete(check_link)
    db.session.add(ProductLink(ebay_link, plc.id, product.id))
    db.session.commit()

    ####################### GROSS #######################

    try:

        driver.get("https://www.gross-electronic.de/")
        driver.find_element_by_id('search').send_keys(product.hsp_id)
        driver.find_element_by_id("btnSearch").click()

        a = driver.find_element_by_class_name("BGArtikelBoxListing_Bezeichnung")
        a.click()

        plc = ProductLinkCategory.query.filter_by(name='Groß Electronic').first()
        check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if check_link:
            db.session.delete(check_link)
        db.session.add(ProductLink(driver.current_url, plc.id, product.id))
        db.session.commit()

    except:

        k = 5

    ####################### MERCATEO #######################

    try:

        driver.get("http://www.mercateo.com/")
        driver.find_element_by_id('query').send_keys(product.hsp_id)
        driver.find_element_by_id("searchbutton").click()

        plc = ProductLinkCategory.query.filter_by(name='Mercateo').first()
        check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if check_link:
            db.session.delete(check_link)
        db.session.add(ProductLink(driver.current_url, plc.id, product.id))
        db.session.commit()

    except:

        k = 5

    ####################### OGDB #######################

    try:

        driver.get("https://ogdb.eu/")
        driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[1]/table/tbody/tr/td/div/form/div/input[1]').send_keys(product.hsp_id)
        driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[1]/table/tbody/tr/td/div/form/div/input[2]').click()

        driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[3]/table[2]/tbody/tr[2]/td/span/a').click()

        plc = ProductLinkCategory.query.filter_by(name='OGDB').first()
        check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if check_link:
            db.session.delete(check_link)
        db.session.add(ProductLink(driver.current_url, plc.id, product.id))
        db.session.commit()

    except:

        k = 5


    ####################### VITREX #######################

    try:

        driver.get("https://www.vitrex-shop.de/de/erweiterte-suche__13/?itid=13&send_form=1&vtx_search=1&quicksearch=" + product.hsp_id + "&search_button=1")

        driver.find_element_by_xpath('/html/body/div[3]/div/div[3]/div[2]/div[2]/div[4]/div/div/div[3]/a').click()

        plc = ProductLinkCategory.query.filter_by(name='Vitrex').first()
        check_link = ProductLink.query.filter_by(product_id=product.id, category_id=plc.id).first()
        if check_link:
            db.session.delete(check_link)
        db.session.add(ProductLink(driver.current_url, plc.id, product.id))
        db.session.commit()

    except:

        k = 5

driver.set_window_size(1120, 550)
driver.quit()
