# -*- coding: utf-8 -*-

from lotus import db
from basismodels import User, Role, UserSession, UserPageload

from flask import session, redirect, url_for, flash, request
from functools import wraps
from datetime import datetime


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorisierter Zugriff.', 'danger')
            return redirect(url_for('center_login'))
    return wrap


def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            user = User.query.filter_by(id=session['user_id']).first()
            for role in roles:
                loop_role = Role.query.filter_by(name=role).first()
                if loop_role not in user.get_roles():
                    flash('Unauthorisierter Zugriff.', 'danger')
                    return redirect(url_for('center_dashboard'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def new_pageload(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        user = User.query.filter_by(id=session['user_id']).first()
        u_session = UserSession.query.filter_by(
            user_id=user.id
        ).filter(
            UserSession.check_in_dt <= datetime.now()
        ).filter(
            UserSession.check_out_dt == None
        ).first()
        ip = request.environ['HTTP_X_REAL_IP'] if 'HTTP_X_REAL_IP' in request.environ else request.environ['REMOTE_ADDR']
        if u_session is None:
            u_session = UserSession(datetime.now(), ip, user.id)
            db.session.add(u_session)
            db.session.commit()
        if (datetime.now() - user.lastpageload).seconds > 43200:
            u_session.check_out_dt = datetime.now()
            u_session.check_out_ip = ip
            db.session.commit()
            session.clear()
            flash('Automatisch ausgeloggt.', 'danger')
            return redirect(url_for('center_login'))
        else:
            db.session.add(UserPageload(request.url, ip, u_session.id))
            user.lastpageload = datetime.now()
            db.session.commit()
            return f(*args, **kwargs)
    return wrap
