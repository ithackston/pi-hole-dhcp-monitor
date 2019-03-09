from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db
import re

bp = Blueprint('admin', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()
    allowed = db.execute(
        'SELECT id, mac_address, created, memo'
        ' FROM allowed'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('admin/index.html', allowed=allowed)


class ValidationException(Exception, object):
    pass


class Entry(dict):
    fields = ('id', 'mac_address', 'created', 'memo')

    def __str__(self):
        return self['mac_address']

    def validate(self):
        if not self['mac_address']:
            raise ValidationException('MAC address is required.')

        if not re.match('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', self['mac_address']):
            raise ValidationException('Not a valid MAC address format.')

        row = get_db().execute(
            'SELECT id'
            ' FROM allowed'
            ' WHERE mac_address = ?',
            (self['mac_address'],)
        ).fetchone()

        if not row is None:
            raise ValidationException('MAC address is already whitelisted.')

    def db_create(self):
        db = get_db()
        db.execute(
            'INSERT INTO allowed (mac_address, memo)'
            ' VALUES (?, ?)',
            (self['mac_address'], self['memo'])
        )
        db.commit()

    def db_update(self):
        if self['id'] is None:
            raise ValidationException('Cannot update entry. Does not exist.')

        db = get_db()
        db.execute(
            'UPDATE allowed SET title = ?, body = ?'
            ' WHERE id = ?',
            (self['mac_address'], self['memo'], self['id'])
        )
        db.commit()

    def db_delete(self):
        db = get_db()
        db.execute('DELETE FROM allowed WHERE id = ?', (self['id'],))
        db.commit()

    @staticmethod
    def from_dict(d):
        return Entry({k:d[k] for k in set(Entry.fields) & set(d.keys())})

    @staticmethod
    def get_entry(id):
        row = get_db().execute(
            'SELECT id, mac_address, created, memo'
            ' FROM allowed'
            ' WHERE id = ?',
            (id,)
        ).fetchone()

        if not row is None:
            return Entry.from_dict(row)


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    if request.method == 'POST':
        entry = Entry.from_dict(request.form)

        try:
            entry.validate()
            entry.db_create()

            return redirect(url_for('admin.index'))
        except ValidationException as e:
            flash(e)

    return render_template('admin/add.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    entry = Entry.get_entry(id)

    if entry is None:
        abort(404, "Entry id {0} doesn't exist.".format(id))

    if request.method == 'POST':
        try:
            entry.validate()
            entry.db_update()

            return redirect(url_for('admin.index'))
        except ValidationException as e:
            flash(e)

    return render_template('admin/edit.html', entry=entry)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    entry = Entry.get_entry(id)

    if entry is None:
        abort(404, "Entry id {0} doesn't exist.".format(id))

    entry.db_delete()

    return redirect(url_for('admin.index'))
