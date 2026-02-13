import pandas as pd
from sqlalchemy import select, text

from cm3d.model import Biological_replica, Group, Measurement, Study


def get_select_statement():
    return select(Study, Group, Biological_replica, Measurement)\
        .join(Study.groups, isouter=True)\
        .join(Group.biological_replicas, isouter=True)\
        .join(Biological_replica.measurements, isouter=True)


def get_denormalised(session) -> pd.DataFrame:
    all_rows = session.execute(get_select_statement())
    return pd.DataFrame.from_records(rows_to_dicts(all_rows, flatten=True))


def get_filtered(session, sql_where, flatten=False) -> pd.DataFrame:
    assert sql_where is not None
    select_statement = get_select_statement().filter(text(sql_where))
    return pd.DataFrame.from_records(rows_to_dicts(session.execute(select_statement), flatten=flatten))


def rows_to_dicts(records, flatten=False):
    for row in records:
        row_dict = dict()
        for scalar in row:
            if scalar is not None:
                original = scalar.to_dict()
                original.pop('study.uploaded_file', None)
                if flatten:
                    if 'measurement.data' in original:
                        for k, v in original['measurement.data'].items():
                            original[f'measurement.data_{k}'] = v
                        del original['measurement.data']
                row_dict = row_dict | original
        yield row_dict
