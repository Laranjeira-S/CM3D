import importlib.resources
import json
import os
import sys
from pathlib import Path

import click
import pandas as pd
from flask_httpauth import HTTPDigestAuth
from rotate_backups import RotateBackups
from waitress import serve

from cm3d import (BACKUPS_DIRNAME, DATABASE_FILENAME, DOWNLOADS_DIRNAME,
                   FILTERS_FILENAME, INPUT_TEMPLATE_FILENAME, UPLOADS_DIRNAME,
                   USERS_FILENAME)
from cm3d.connection import ROSession, RWSession
from cm3d.database import get_denormalised, get_filtered
from cm3d.ingest import read_file
from cm3d.model import Base, Study
from cm3d.utils import get_timestamp, mock_study_worksheets


class NaturalOrderGroup(click.Group):
    """Will display command help in the order commands are defined in this file"""
    def list_commands(self, ctx):
        return self.commands.keys()


@click.group(cls=NaturalOrderGroup)
def cli():
    pass


@cli.command()
def init():
    """Sets up a new working directory to run the database application"""
    working_directory = Path(os.getcwd())
    click.echo(f'You are setting up CM3D in {working_directory}')
    click.echo('Continue (y/n)? ', nl=False)
    choice = input().lower()
    if choice != 'y':
        click.echo('Aborting.')
        sys.exit(0)
    if len(os.listdir(working_directory)) != 0:
        click.echo('FAILED: Directory is not empty. Aborting.')
        sys.exit(0)
    for directory in [BACKUPS_DIRNAME, DOWNLOADS_DIRNAME, UPLOADS_DIRNAME]:
        os.mkdir(working_directory / directory)
        click.echo(f'Created ./{directory}')
    with RWSession() as session:
        Base.metadata.create_all(session.get_bind())
    click.echo('Created database.')
    from . import resources
    with open(working_directory / INPUT_TEMPLATE_FILENAME, 'wb') as excel_file:
        excel_file.write(importlib.resources.read_binary(resources, INPUT_TEMPLATE_FILENAME))
    click.echo('Copied template.')
    with open(working_directory / USERS_FILENAME, 'w') as user_file:
        user_file.write(importlib.resources.read_text(resources, USERS_FILENAME))
    click.echo('Created user file.')
    with open(working_directory / FILTERS_FILENAME, 'w') as filters_file:
        filters_file.write(importlib.resources.read_text(resources, FILTERS_FILENAME))
    click.echo('Created filters file.')
    click.echo('Success!')


@cli.command()
@click.argument('username')
@click.argument('password')
def add_user(username, password):
    """Adds credentials for user to access the website."""
    users = json.load(open(USERS_FILENAME, 'r'))
    if username in users:
        click.echo(f"ERROR: User {username} already exists.")
        sys.exit(1)
    auth = HTTPDigestAuth(use_ha1_pw=True)
    encrypted_password = auth.generate_ha1(username, password)
    users[username] = encrypted_password
    json.dump(users, open(USERS_FILENAME, 'w'))
    click.echo(f"User {username} added to {USERS_FILENAME}")


@cli.command()
@click.option('--debug', is_flag=True)
def web(debug):
    """Start the web application."""
    from .web import app
    app.debug = debug
    if debug:
        app.run(debug=debug)
    else:
        import logging
        logger = logging.getLogger('waitress')
        logger.setLevel(logging.INFO)
        serve(app, host='0.0.0.0', port=8080)


@cli.command()
@click.option('--drop', is_flag=True)
def create_db(drop):
    """Create the database schema."""
    with RWSession() as session:
        if drop:
            Base.metadata.drop_all(session.get_bind())
        Base.metadata.create_all(session.get_bind())


@cli.command()
def export_db():
    """Exports the entire database in CSV format. The database tables are denormalised and flattened."""
    with ROSession() as session:
        records = get_denormalised(session)
        csv_records = records.to_csv(None, index=False)
        print(csv_records)


@cli.command()
@click.argument('sql_filter')
def query_db(sql_filter):
    """Query the database."""
    with ROSession() as session:
        records = get_filtered(session, sql_filter)
        csv_records = records.to_csv(None, index_label='number')
        print(csv_records)


@cli.command()
def backup_db():
    """Makes a timestamped copy of the database & rotates the backups.
    This command can be setup as a cron job (for example) to schedule backups."""
    working_directory = Path(os.getcwd())
    db_filename = Path(DATABASE_FILENAME)
    new_db_filename = f'{db_filename.stem}_{get_timestamp()}.db'

    def progress(status, remaining, total):
        click.echo(f'Copied {total - remaining} of {total} pages [status {status}].')

    import sqlite3
    con = sqlite3.connect(working_directory / DATABASE_FILENAME)
    bck = sqlite3.connect(working_directory / BACKUPS_DIRNAME / new_db_filename)
    with bck:
        con.backup(bck, pages=-1, progress=progress)
    bck.close()
    con.close()

    click.echo(f'Saved {new_db_filename}')

    # rotate backups
    rotation_scheme = {
        'hourly': 24, 'daily': 7, 'weekly': 4, 'monthly': 12, 'yearly': 1
    }
    rotate_program = RotateBackups(rotation_scheme=rotation_scheme, dry_run=False)
    rotate_program.rotate_backups(str(working_directory / BACKUPS_DIRNAME))


@cli.command()
@click.argument('filename')
@click.option('--username', hidden=True)
def add_study(filename, username):
    """Load a new study spreadsheet into the database. The spreadsheet must be an Excel file based on the NGC
    template. Example: cm3d-cli my_latest_study.xlsx
    """
    click.echo('You are loading %s' % filename)
    new_study = read_file(filename)
    if username is None:
        username = 'anonymous-cli'
    new_study.added_by = username

    # add the study and get the study id
    with RWSession() as session:
        session.add(new_study)
        session.commit()
        study_id = new_study.id

    # retrieve the same study and check parts were saved
    with ROSession() as session:
        result = session.query(Study).where(Study.id == study_id).one()
        measurements = biological_replicas = groups = 0
        for group in result.groups:
            groups += 1
            for biological_replica in group.biological_replicas:
                biological_replicas += 1
                measurements += len(biological_replica.measurements)

    click.echo(f'Successfully added study (id={study_id}) with {groups} groups, {biological_replicas} biological_replicas, {measurements} measurements.')


@cli.command()
def mock_study():
    """Create a mock experimental study Excel file in the required format."""
    workbook = mock_study_worksheets()
    filename = f"fake_{get_timestamp()}.xlsx"
    with pd.ExcelWriter(filename) as writer:
        for k, v in workbook.items():
            v.to_excel(writer, sheet_name=k, index=False)
    click.echo(filename)


if __name__ == '__main__':
    cli()
