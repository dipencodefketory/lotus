from datetime import datetime

from lotus import db
from basismodels import Supplier, WSInvoice, WSIProduct, Product_Stock_Attributes, Stock,Product
import entertainment_trading as et


et_stock = Stock.query.filter_by(id=6).first()
supplier = Supplier.query.filter_by(firmname='Entertainment-Trading').first()
r = et.get_invoices(updated_since='2022-01-01T00:00:00')
page = 1
while r.ok:
    data = r.json()
    results = data['results']
    for result in results:
        wsi = WSInvoice.query.filter_by(invoice_number=str(result['doc_num'])).first()
        if wsi:
            print(result['doc_num'])
            print(wsi)
            if len(wsi.products) == 0:
                for el in result['lines']:
                    psa = Product_Stock_Attributes.query.filter_by(sku=el['sku'], stock_id=et_stock.id).first()
                    if not psa:
                        print('PROBLEM')
                        print(el['sku'])
                    else:
                        if str(el['sku']) == '9999':
                            p = Product.query.filter_by(name='Porto / Shipping costs Vitrex').first()
                            db.session.add(WSIProduct(el['qty'], el['unit_amount_ex_vat'], el['unit_vat_amount'], wsi.id, p.id))
                            db.session.commit()
                        else:
                            db.session.add(WSIProduct(el['qty'], el['unit_amount_ex_vat'], el['unit_vat_amount'], wsi.id, psa.product_id))
                            db.session.commit()
                wsi.gross_price = wsi.calc_gross_price()
                wsi.net_price = wsi.calc_net_price()
                wsi.positions = wsi.get_product_positions()
                wsi.num_products = wsi.get_product_quantity()
                db.session.commit()
        else:
            print('NEW_INVOICE')
            print(result)
            wsi = WSInvoice(name='Entertainment-Trading', invoice_number=result['doc_num'], invoice_dt=datetime.strptime(result['created_at'], '%Y-%m-%dT%H:%M:%SZ'), paid=False, net_price=result['total_amount_ex_vat'],
                 gross_price=result['total_amount_incl_vat'], positions=len(result['lines']), comment=f'AUTO-GENERATED AT {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', supplier_id=supplier.id)
            db.session.add(wsi)
            db.session.commit()
            for el in result['lines']:
                psa = Product_Stock_Attributes.query.filter_by(sku=el['sku'], stock_id=et_stock.id).first()
                if not psa:
                    if str(el['sku']) == '9999':
                        p = Product.query.filter_by(name='DPD shipping costs ET').first()
                        db.session.add(WSIProduct(el['qty'], el['unit_amount_ex_vat'], el['unit_vat_amount'], wsi.id, p.id))
                        db.session.commit()
                    else:
                        print('PROBLEM')
                        print(el['sku'])
                else:
                    db.session.add(WSIProduct(el['qty'], el['unit_amount_ex_vat'], el['unit_vat_amount'], wsi.id, psa.product_id))
                    db.session.commit()
            wsi.gross_price = wsi.calc_gross_price()
            wsi.net_price = wsi.calc_net_price()
            wsi.positions = wsi.get_product_positions()
            wsi.num_products = wsi.get_product_quantity()
            db.session.commit()
            print('DONE')
            print('--------------------------------')
    page += 1
    r = et.get_invoices(updated_since='2021-12-01T00:00:00', page=page)
