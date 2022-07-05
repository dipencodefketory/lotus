# -*- coding: utf-8 -*-


from lotus import db
from basismodels import Sale, ShippingEvent
from ext.shipping import dhl_dp_api

from sqlalchemy import func, case, and_, or_
import re
import xml.etree.ElementTree as ETree
from datetime import datetime
import time as t


# GET RAW-EVENTS

sales = Sale.query.filter(
    Sale.received_by == None
).filter(
    Sale.tracking_number.like('00%')
).filter(
    Sale.timestamp >= datetime.strptime('2022-01-01', '%Y-%m-%d')
).order_by(
    Sale.timestamp
).limit(500).all()
print(len(sales))
for sale in sales:
    trs = [sale.tracking_number]
    print(trs)
    try:
        r = dhl_dp_api.get_shipment_tracking(trs)
        print(r.text)
        print('------------------------------------')
        tree = ETree.fromstring(r.text)
        data = tree.findall('.//data')
        sale = None
        sh_events = []
        i = 0
        success = False
        for el in data:
            if el.attrib['name'] == 'piece-shipment':
                if el.attrib['error-status'] == "0":
                    success = True
                else:
                    success = False
            if success is True:
                if el.attrib['name'] == 'piece-shipment':
                    sale = Sale.query.filter(Sale.tracking_number == el.attrib['piece-code']).first()
                    if not sale:
                        sale = None
                        sh_events = []
                        continue
                    else:
                        sh_events = ShippingEvent.query.filter_by(sale_id=sale.id).order_by(ShippingEvent.timestamp).all()
                        i = 0
                        if el.attrib['short-status'] == 'Zustellung erfolgreich':
                            sale.received_by = datetime.strptime(el.attrib['status-timestamp'], '%d.%m.%Y %H:%M')
                elif sale != None and el.attrib['name'] == 'piece-event':
                    if i < len(sh_events):
                        i+=1
                        continue
                    else:
                        db.session.add(ShippingEvent(datetime.strptime(el.attrib['event-timestamp'], '%d.%m.%Y %H:%M'), el.attrib['event-status'], el.attrib['event-text'], el.attrib['event-short-status'], el.attrib['ice'], el.attrib['ric'],
                                                     el.attrib['event-location'], el.attrib['event-country'], el.attrib['ruecksendung'] == 'true', sale.id))
                        db.session.commit()
            else:
                continue
        t.sleep(5)
    except Exception as e:
        print(e)


# TRANSFORM RAW-EVENTS

prb_query = db.session.query(
    ShippingEvent.sale_id.label('sale_id'), func.min(ShippingEvent.timestamp).label('pickup_ready_dt')
).filter(
    ShippingEvent.ice == 'HLDCC'
).filter(
    ShippingEvent.timestamp >= datetime.strptime('01.01.2022', '%d.%m.%Y')
).group_by(
    ShippingEvent.sale_id
).subquery()

rcb_query = db.session.query(
    ShippingEvent.sale_id.label('sale_id'), func.min(ShippingEvent.timestamp).label('receive_dt')
).filter(
    ShippingEvent.ice == 'DLVRD'
).filter(
    ShippingEvent.timestamp >= datetime.strptime('01.01.2022', '%d.%m.%Y')
).group_by(
    ShippingEvent.sale_id
).subquery()

rfb_query = db.session.query(
    ShippingEvent.sale_id.label('sale_id'), func.min(ShippingEvent.timestamp).label('refuse_dt')
).filter(
    ShippingEvent.ice == 'DLVRF'
).filter(
    ShippingEvent.timestamp >= datetime.strptime('01.01.2022', '%d.%m.%Y')
).group_by(
    ShippingEvent.sale_id
).subquery()

ta_query = db.session.query(
    ShippingEvent.sale_id.label('sale_id'), func.min(ShippingEvent.timestamp).label('ta_dt')
).filter(
    ShippingEvent.ice == 'NTDEL'
).filter(
    ShippingEvent._return == False
).filter(
    ShippingEvent.timestamp >= datetime.strptime('01.01.2022', '%d.%m.%Y')
).group_by(
    ShippingEvent.sale_id
).subquery()

fail_query = db.session.query(
    ShippingEvent.sale_id.label('sale_id'), func.min(ShippingEvent.timestamp).label('fail_dt')
).filter(
    ShippingEvent.ice == 'NTDEL'
).filter(
    ShippingEvent._return == True
).filter(
    ShippingEvent.timestamp >= datetime.strptime('01.01.2022', '%d.%m.%Y')
).group_by(
    ShippingEvent.sale_id
).subquery()

des_date_query = db.session.query(
    ShippingEvent.sale_id.label('sale_id'), func.min(ShippingEvent.text).label('des_date_text')
).filter(
    ShippingEvent.ice == 'ADVIS'
).filter(
    ShippingEvent.text.like('%Wunschtag%')
).filter(
    ShippingEvent.timestamp >= datetime.strptime('01.01.2022', '%d.%m.%Y')
).group_by(
    ShippingEvent.sale_id
).subquery()

query = db.session.query(
    Sale
).outerjoin(
    prb_query, prb_query.c.sale_id == Sale.id
).outerjoin(
    rcb_query, rcb_query.c.sale_id == Sale.id
).outerjoin(
    rfb_query, rfb_query.c.sale_id == Sale.id
).outerjoin(
    ta_query, ta_query.c.sale_id == Sale.id
).outerjoin(
    fail_query, fail_query.c.sale_id == Sale.id
).outerjoin(
    des_date_query, des_date_query.c.sale_id == Sale.id
).add_column(
    func.coalesce(prb_query.c.pickup_ready_dt, None)
).add_column(
    func.coalesce(rcb_query.c.receive_dt, None)
).add_column(
    func.coalesce(rfb_query.c.refuse_dt, None)
).add_column(
    func.coalesce(ta_query.c.ta_dt, None)
).add_column(
    func.coalesce(fail_query.c.fail_dt, None)
).add_column(
    func.coalesce(des_date_query.c.des_date_text, None)
).filter(
    Sale.timestamp >= datetime.strptime('01.01.2022', '%d.%m.%Y')
).filter(
    or_(
        func.coalesce(prb_query.c.pickup_ready_dt, None) != None,
        func.coalesce(rcb_query.c.receive_dt, None) != None,
        func.coalesce(rfb_query.c.refuse_dt, None) != None,
        func.coalesce(ta_query.c.ta_dt, None) != None,
        func.coalesce(fail_query.c.fail_dt, None) != None,
        func.coalesce(des_date_query.c.des_date_text, None) != None
    )
).filter(
    or_(
        Sale.received_by == None,
        Sale.returned_by == None
    )
).all()

for sale, pickup_ready_dt, receive_dt, refuse_dt, ta_dt, fail_dt, des_date_text in query:
    sale.pickup_ready_by = None
    sale.refused_by = None
    sale.failed_by = None
    sale.received_by = None
    sale.return_by = None
    sale.returned_by = None
    if des_date_text:
        try:
            d_candidates = re.findall(r"[\d]{1,2}.[\d]{1,2}.[\d]{4}", des_date_text)
            for d_candidate in d_candidates:
                sale.deliver_by = datetime.strptime(d_candidate + ' 20:00:00', '%d.%m.%Y %H:%M:%S')
        except ValueError:
            pass
    sale.pickup_ready_by = pickup_ready_dt
    sale.refused_by = refuse_dt
    sale.failed_by = fail_dt
    sale.received_by = receive_dt if not (refuse_dt or fail_dt) else None
    sale.return_by = refuse_dt if refuse_dt else fail_dt
    sale.returned_by = receive_dt if refuse_dt or fail_dt else None
    db.session.commit()


# CALC_PUNCTUALITY

query = db.session.query(
    Sale
).add_column(
    (case([
        (and_(Sale.shipping_method.in_(['DE_DHLAlterssichtprüfung18', 'DE_DeutschePostWarensendung', 'DE_DHLPaket']), Sale.pickup_ready_by > Sale.deliver_by), False),
        (and_(Sale.shipping_method.in_(['DE_DHLAlterssichtprüfung18', 'DE_DeutschePostWarensendung', 'DE_DHLPaket']), Sale.pickup_ready_by == None, Sale.received_by > Sale.deliver_by), False),
        (and_(Sale.shipping_method.in_(['DE_DHLAlterssichtprüfung18', 'DE_DeutschePostWarensendung', 'DE_DHLPaket']), Sale.pickup_ready_by == None, Sale.received_by == None, datetime.now() > Sale.deliver_by), False),
        (and_(Sale.shipping_method.in_(['DE_DHLAlterssichtprüfung18', 'DE_DeutschePostWarensendung', 'DE_DHLPaket']), or_(Sale.pickup_ready_by <= Sale.deliver_by, Sale.received_by <= Sale.deliver_by)), True),
        (and_(Sale.shipping_method.notin_(['DE_DHLAlterssichtprüfung18', 'DE_DeutschePostWarensendung', 'DE_DHLPaket']), Sale.sent_by > Sale.send_by), False),
        (and_(Sale.shipping_method.notin_(['DE_DHLAlterssichtprüfung18', 'DE_DeutschePostWarensendung', 'DE_DHLPaket']), Sale.sent_by == None, datetime.now() > Sale.send_by), False),
        (and_(Sale.shipping_method.notin_(['DE_DHLAlterssichtprüfung18', 'DE_DeutschePostWarensendung', 'DE_DHLPaket']), Sale.sent_by <= Sale.send_by), True)
    ], else_=None)).label('calc_punctual')
).filter(
    and_(
        Sale.cancelled == False,
        Sale.quantity > 0,
        Sale.timestamp >= datetime.strptime('2022-01-01', '%Y-%m-%d')
    )
).filter(
    Sale.send_by >= datetime.strptime('2022-01-03', '%Y-%m-%d')
).order_by(
    Sale.send_by
).all()

for sale, calc_punctual in query:
    sale.punctual = calc_punctual
    db.session.commit()
