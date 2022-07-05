from lotus import *

get_et_product=Product_Stock_Attributes.query.filter_by(stock_id=6).filter(
            Product_Stock_Attributes.avail_date <= datetime.now()
        ).filter(
            Product_Stock_Attributes.termination_date >= datetime.now()
        ).all()
if len(get_et_product)<14000:
    send_email('Warning !! Entertainment trading stock', 'system@lotusicafe.de', ['developer@lotusicafe.de', 'farukoenal@lotusicafe.de'], 'ET stock is less than 14000', '')

