# -*- coding: utf-8 -*-

from lotus import db
from flask import Blueprint, render_template
from decorators import is_logged_in, new_pageload, roles_required
from basismodels import Marketplace, ShippingService, ShippingProvider, SSCAttr, SSRAttr, Country, Region, MPShippingService, ShippingServiceSD, ShippingProfile, ShippingProfilePrice

from flask import request, flash, redirect, url_for
from datetime import datetime

shipping = Blueprint('shipping', __name__, static_folder='static', template_folder='templates')


@shipping.route('/', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def index():
    shipping_services = ShippingService.query.order_by(ShippingService.international, ShippingService.name).all()
    shipping_providers = ShippingProvider.query.all()
    if request.method == 'POST':
        provider = request.form['provider'].strip()
        shipping_type = request.form['shipping_type'].strip()
        check = request.form.getlist('check')
        signature = True if 'signature' in check else False
        tracking = True if 'tracking' in check else False
        min_days = int(request.form['min_days'])
        max_days = int(request.form['max_days'])
        internal_id = request.form['internal_id']
        weight_kg = int(request.form['weight_kg'])
        length_mm = int(request.form['length_mm'])
        width_mm = int(request.form['width_mm'])
        height_mm = int(request.form['height_mm'])
        name = request.form['name'].strip()
        price = request.form['price']
        try:
            db.session.add(ShippingService(shipping_type, signature, tracking, min_days, max_days, name, price, provider, internal_id, weight_kg, length_mm, width_mm, height_mm))
        except Exception as e:
            flash(str(e), 'danger')
        db.session.commit()
        flash('Änderungen gespeichert.', 'success')
        return redirect(url_for('settings.shipping.shipping'))
    return render_template('shipping/shipping.html', shipping_services=shipping_services, shipping_providers=shipping_providers)


@shipping.route('/shipping_service/<service_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def shipping_service(service_id):
    sh_service = ShippingService.query.filter_by(id=service_id).first()
    shipping_providers = ShippingProvider.query.all()
    ssc_s = db.session.query(SSCAttr.country_id).filter_by(shipping_service_id=service_id, not_=False).all()
    ssc_s = [ssc for ssc, in ssc_s]
    ssc_nots = db.session.query(SSCAttr.country_id).filter_by(shipping_service_id=service_id, not_=True).all()
    ssc_nots = [ssc for ssc, in ssc_nots]
    ssr_s = db.session.query(SSRAttr.region_id).filter_by(shipping_service_id=service_id, not_=False).all()
    ssr_s = [ssr for ssr, in ssr_s]
    ssr_nots = db.session.query(SSRAttr.region_id).filter_by(shipping_service_id=service_id, not_=True).all()
    ssr_nots = [ssr for ssr, in ssr_nots]
    countries = Country.query.order_by(Country.name).all()
    regions = Region.query.order_by(Region.name).all()
    marketplaces = Marketplace.query.all()
    mp_shipping_services = MPShippingService.query.filter_by(shipping_service_id=sh_service.id).all()
    labels = dict((mps.marketplace_id, mps.code) for mps in mp_shipping_services)
    if request.method == 'POST':
        try:
            if request.form['btn'] == 'basic':
                price = float(request.form['price'])
                if price != sh_service.price:
                    rep_datetime = datetime.now()
                    sh_service.serial_data.sort(key=lambda x: x.init_datetime, reverse=True)
                    sh_service.serial_data[-1].rep_datetime = rep_datetime
                    db.session.add(ShippingServiceSD(price, service_id=sh_service.id))
                    sh_service.price = price
                    db.session.commit()
                for marketplace in marketplaces:
                    code = request.form[f'code_{ marketplace.id }'].strip()
                    if not code:
                        flash('Bitte gib für jeden Marketplace einen Code an.', 'danger')
                    else:
                        mps = MPShippingService.query.filter_by(shipping_service_id=sh_service.id, marketplace_id=marketplace.id).first()
                        if mps:
                            mps.code = code
                        else:
                            db.session.add(MPShippingService(code, marketplace.id, sh_service.id))
                sh_service.international = request.form['shipping_type'].strip()=='international'
                provider = request.form['provider'].strip()
                if provider != sh_service.provider.name:
                    check_provider = ShippingProvider.query.filter_by(name=provider).first()
                    if not check_provider:
                        check_provider = ShippingProvider(provider)
                        db.session.add(check_provider)
                        db.session.commit()
                    sh_service.provider_id = check_provider.id
                min_days = int(request.form['min_days']) if request.form['min_days'] else None
                max_days = int(request.form['max_days']) if request.form['max_days'] else None
                weight_kg = int(request.form['weight_kg']) if request.form['weight_kg'] else None
                length_mm = int(request.form['length_mm']) if request.form['length_mm'] else None
                width_mm = int(request.form['width_mm']) if request.form['width_mm'] else None
                height_mm = int(request.form['height_mm']) if request.form['height_mm'] else None
                sh_service.internal_id = request.form['internal_id']
                check = request.form.getlist('check')
                sh_service.signature = True if 'signature' in check else False
                sh_service.tracking = True if 'tracking' in check else False
                sh_service.name = request.form['name'] if request.form['name'] else sh_service.name
                sh_service.min_days = min_days if min_days is not None else sh_service.min_days
                sh_service.max_days = max_days if max_days is not None else sh_service.max_days
                sh_service.weight_kg = weight_kg if weight_kg is not None else sh_service.weight_kg
                sh_service.length_mm = length_mm if length_mm is not None else sh_service.length_mm
                sh_service.width_mm = width_mm if width_mm is not None else sh_service.width_mm
                sh_service.height_mm = height_mm if height_mm is not None else sh_service.height_mm
                db.session.commit()
                flash('Änderungen gespeichert.', 'success')
            elif request.form['btn'] == 'area':
                form_regions = request.form.getlist('region')
                form_not_regions = request.form.getlist('not_region')
                form_countries = request.form.getlist('country')
                form_not_countries = request.form.getlist('not_country')
                SSRAttr.query.filter_by(shipping_service_id=service_id).delete()
                SSCAttr.query.filter_by(shipping_service_id=service_id).delete()
                for region in form_regions:
                    db.session.add(SSRAttr(0, .0, False, int(region), int(service_id)))
                for region in form_not_regions:
                    db.session.add(SSRAttr(0, .0, True, int(region), int(service_id)))
                for country in form_countries:
                    db.session.add(SSCAttr(0, .0, False, int(country), int(service_id)))
                for country in form_not_countries:
                    db.session.add(SSCAttr(0, .0, True, int(country), int(service_id)))
                db.session.commit()
        except Exception as e:
            print(e)
            flash(str(e), 'danger')
        return redirect(url_for('settings.shipping.shipping_service', service_id=service_id))
    return render_template('shipping/shipping_service.html', shipping_service=sh_service, marketplaces=marketplaces, labels=labels, shipping_providers=shipping_providers, ssc_s=ssc_s, ssc_nots=ssc_nots,
                           ssr_s=ssr_s, ssr_nots=ssr_nots, countries=countries, regions=regions)


@shipping.route('/shipping_profiles', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def shipping_profiles():
    sh_profiles = ShippingProfile.query.all()
    sh_services = ShippingService.query.all()
    marketplaces = Marketplace.query.all()
    mp_shipping_services = MPShippingService.query.all()
    mps_list = [f'{mps.marketplace_id}_{mps.shipping_service_id}' for mps in mp_shipping_services]
    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            service_dict = {}
            for mps in mp_shipping_services:
                price = request.form[f'price_{ mps.marketplace_id }_{ mps.shipping_service_id }']
                if not price:
                    flash('Bitte fülle alle möglichen Felder aus.', 'danger')
                    return redirect(url_for('center_settings_shipping_profiles'))
                service_dict[mps.id] = request.form[f'price_{ mps.marketplace_id }_{ mps.shipping_service_id }']
            db.session.add(ShippingProfile(name, service_dict))
            db.session.commit()
        except Exception as e:
            print(e)
            flash(str(e), 'danger')
        flash('Profil hinzugefügt.', 'success')
        return redirect(url_for('settings.shipping.shipping_profiles'))
    return render_template('shipping/shipping_profiles.html', shipping_profiles=sh_profiles, shipping_services=sh_services, marketplaces=marketplaces, mps_list=mps_list)


@shipping.route('/shipping_profile/<shipping_profile_id>', methods=['GET', 'POST'])
@is_logged_in
@new_pageload
@roles_required('Admin')
def shipping_profile(shipping_profile_id):
    sh_profile = ShippingProfile.query.filter_by(id=shipping_profile_id).first()
    sh_services = ShippingService.query.all()
    marketplaces = Marketplace.query.all()
    mp_shipping_services = MPShippingService.query.all()
    mps_list = [f'{mps.marketplace_id}_{mps.shipping_service_id}' for mps in mp_shipping_services]
    price_dict = dict((f'{price.mp_service.marketplace_id}_{price.mp_service.shipping_service_id}', price.price) for price in sh_profile.mp_services)
    if request.method == 'POST':
        sh_profile.name = request.form['name'].strip()
        for mps in mp_shipping_services:
            price = request.form[f'price_{ mps.marketplace_id }_{ mps.shipping_service_id }']
            if not price:
                flash('Bitte fülle alle möglichen Felder aus.', 'danger')
                return redirect(url_for('center_settings_shipping_profile', shipping_profile_id=shipping_profile_id))
            spp = ShippingProfilePrice.query.filter_by(mp_service_id=mps.id, profile_id=sh_profile.id).first()
            if not spp:
                db.session.add(ShippingProfilePrice(price, mps.id, sh_profile.id))
            else:
                spp.update_price(price)
        db.session.commit()
        flash('Änderungen gespeichert.', 'success')
        return redirect(url_for('settings.shipping.shipping_profile', shipping_profile_id=shipping_profile_id))
    return render_template('shipping/shipping_profile.html', shipping_profile=sh_profile, shipping_services=sh_services, marketplaces=marketplaces, mps_list=mps_list,
                           price_dict=price_dict)
