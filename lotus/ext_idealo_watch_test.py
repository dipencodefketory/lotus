from lotus import *

marketplace = Marketplace.query.filter_by(name='Idealo').first()

products = Product.query.order_by(Product.id).all()
check_ids = []

for product in products:
    print(product.id)
    cat = ProductLinkCategory.query.filter_by(name='Idealo').first()
    link = ProductLink.query.filter_by(category_id=cat.id, product_id=product.id).first()
    if link:
        if link.link and link.ext_idealo_watch_active:
            if 'OffersOfProduct' in link.link:
                link = link.link
            else:
                continue
        else:
            continue
    else:
        continue
    now = datetime.now()
    supremum = now
    minimum = now - timedelta(hours=168)
    any_offers = marketplace.get_extoffers_by_product(product.id, datetime.strptime('21000101', '%Y%m%d'), datetime.strptime('20200101', '%Y%m%d'))
    offers = marketplace.get_extoffers_by_product(product.id, supremum, minimum)
    if offers==[] and any_offers!=[]:
        cat = ProductLinkCategory.query.filter_by(name='Idealo').first()
        link = ProductLink.query.filter_by(category_id=cat.id, product_id=product.id).first()
        link.ext_idealo_watch_active = False
        db.session.commit()
        check_ids.append(product.id)
if check_ids:
    msg = 'Zu folgenden Produkt-IDs sind keine Konkurrenz-Angebote gefunden worden:\r\n'
    for product_id in check_ids:
        msg += str(product_id) + '\r\n'
    send_email('Idealo Konkurrenz-Betrachtung', 'system@lotusicafe.de', ['bardiahahn@lotusicafe.de', 'farukoenal@lotusicafe.de'], msg, msg)
