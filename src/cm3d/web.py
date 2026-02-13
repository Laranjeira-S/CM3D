import json
import os
import secrets
from pathlib import Path
from typing import List

import pandas as pd
from flask import (Flask, current_app, flash, redirect, render_template,
                   request, send_file)
from flask_httpauth import HTTPDigestAuth
from sqlalchemy.orm import scoped_session
from werkzeug.utils import secure_filename

from cm3d import (DOWNLOADS_DIRNAME, FILTERS_FILENAME,
                   INPUT_TEMPLATE_FILENAME, UPLOADS_DIRNAME, USERS_FILENAME)
from cm3d.connection import ROSession, RWSession
from cm3d.database import get_denormalised, get_filtered
from cm3d.ingest import read_file
from cm3d.model import Study
from cm3d.utils import check_cm3d_setup, get_timestamp

ALLOWED_EXTENSIONS = {'xlsx'}


def index():
    return render_template('index.html', username=auth.current_user())


def show_studies():
    studies: List[Study] = app.session.query(Study).all()
    return render_template('studies.html', studies=studies)


def show_study(study_id):
    study: Study = app.session.get(Study, study_id)
    return render_template('study.html', study=study)


def study_download(study_id):
    study: Study = app.session.get(Study, study_id)
    study_filename = current_app.config['DOWNLOAD_FOLDER'] / f'study_{study_id}_{get_timestamp()}.xlsx'
    with open(study_filename, 'wb') as download_excel_file:
        download_excel_file.write(study.uploaded_file)
    return send_file(
        study_filename,
        as_attachment=True
    )


def query():
    filters_filename = current_app.config['WORKING_DIRECTORY'] / FILTERS_FILENAME
    if filters_filename.is_file():
        filters = json.load(open(filters_filename))
    else:
        filters = {}

    sql = request.form.get('sql')
    action = request.form.get('action')

    # if we have sql statement
    if sql is not None:
        # get the records (flatten if it's for downloading)
        flatten = True if action == 'Download' else False
        records: pd.DataFrame = get_filtered(app.session, sql, flatten=flatten)

        # no matching records
        if not len(records):
            return render_template('query.html', records=None, sql=sql, show_extras='', filters=filters)

        if action == 'Download':
            # save the records & return file
            data_dump_filename = current_app.config['DOWNLOAD_FOLDER'] / f'query_{get_timestamp()}.csv'
            records.to_csv(data_dump_filename)
            return send_file(data_dump_filename, as_attachment=True)

        # otherwise, we're showing records on webpage
        records['study.id'] = records['study.id'].apply(lambda x: f'<a href="/study/{x}">{x}</a>')
        # remove extra measurement data if requested
        if not request.form.get('extras'):
            records.drop('measurement.data', axis=1, inplace=True)
            show_extras = ''
        else:
            show_extras = 'checked'

        return render_template('query.html', records=records, sql=sql, show_extras=show_extras, filters=filters)
    return render_template('query.html', records=None, sql='', show_extras='', filters=filters)


def upload():
    uploaded = None
    error = None
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            timestamp = get_timestamp()
            filename = f'{timestamp}_{secure_filename(file.filename)}'
            # upload
            file.save(app.config['UPLOAD_FOLDER'] / filename)
            # ingest
            study = read_file(app.config['UPLOAD_FOLDER'] / filename)
            study.added_by = auth.current_user()
            with RWSession() as session:
                session.add(study)
                session.commit()
                study_id = study.id
            uploaded = {
                "filename": filename,
                "study_id": study_id
            }
        else:
            error = f"The file {file.filename} is the wrong type of file, please use the Excel file NGC template (.xlsx)"
    return render_template('upload.html', uploaded=uploaded, error=error)


def download_template():
    return send_file(
        current_app.config['WORKING_DIRECTORY'] / INPUT_TEMPLATE_FILENAME,
        as_attachment=True
    )


def dump_database():
    data_dump_filename = current_app.config['DOWNLOAD_FOLDER'] / f'db_dump_{get_timestamp()}.csv'
    records = get_denormalised(app.session)
    records.to_csv(data_dump_filename)
    return send_file(data_dump_filename, as_attachment=True)


def allowed_file(filename):
    return filename.split('.')[-1] in ALLOWED_EXTENSIONS


def logout():
    if 'done' in request.args:
        return render_template('logout.html')
    # http auth doesn't have concept of logging out - we try to log back in using a random un/pw combination
    # to deliberately make the credentials wrong
    return redirect(f'http://{get_timestamp()}:{get_timestamp()}@{request.host}/logout?done=1')


app = Flask(__name__)

app.config['WORKING_DIRECTORY'] = Path(os.getcwd())
app.config['UPLOAD_FOLDER'] = app.config['WORKING_DIRECTORY'] / UPLOADS_DIRNAME
app.config['DOWNLOAD_FOLDER'] = app.config['WORKING_DIRECTORY'] / DOWNLOADS_DIRNAME
app.config['SECRET_KEY'] = secrets.token_urlsafe(25)

auth = HTTPDigestAuth(use_ha1_pw=True)
app.session = scoped_session(ROSession)  # default SQLAlchemy session is read-only

check_cm3d_setup(app.config['WORKING_DIRECTORY'])

app.add_url_rule("/", view_func=auth.login_required(index))
app.add_url_rule("/studies", view_func=auth.login_required(show_studies))
app.add_url_rule("/study/<int:study_id>", view_func=auth.login_required(show_study))
app.add_url_rule("/study/<int:study_id>/download", view_func=auth.login_required(study_download))
app.add_url_rule("/upload", view_func=auth.login_required(upload), methods=['POST', 'GET'])
app.add_url_rule("/download-template", view_func=auth.login_required(download_template))
app.add_url_rule("/download-db", view_func=auth.login_required(dump_database))
app.add_url_rule("/query", view_func=auth.login_required(query), methods=['GET', 'POST'])
app.add_url_rule("/logout", view_func=logout)


@auth.get_password
def get_pw(username):
    users = json.load(open(current_app.config['WORKING_DIRECTORY'] / USERS_FILENAME, 'r'))
    if username in users:
        return users.get(username)
    return None


@app.teardown_appcontext
def remove_session(*args, **kwargs):
    app.session.remove()
