import os
import random
import sys
from datetime import datetime as dt
from pathlib import Path

import pandas as pd
from faker import Faker

from cm3d import (BACKUPS_DIRNAME, DATABASE_FILENAME, DOWNLOADS_DIRNAME,
                   INPUT_TEMPLATE_FILENAME, UPLOADS_DIRNAME)


def check_cm3d_setup(working_directory: Path, echo=False):
    """Checks whether the working directory has been set up correctly for the app to work"""
    if echo:
        print(f'Checking working directory {working_directory}')
    setup_correct = True
    required_files_and_dirs = [DATABASE_FILENAME, INPUT_TEMPLATE_FILENAME, DOWNLOADS_DIRNAME, UPLOADS_DIRNAME,
                               BACKUPS_DIRNAME]
    for required in required_files_and_dirs:
        if not os.path.exists(working_directory / required):
            setup_correct = False
            print(f'{required} not found in working directory.')
    if setup_correct:
        if echo:
            print('CM3D setup okay!')
    else:
        print('CM3D not setup correctly.')
        sys.exit(1)


def get_timestamp():
    date_format = "%Y%m%d-%H%M%S"
    return dt.strftime(dt.now(), format=date_format)


def mock_study_worksheets():
    fake = Faker()

    number_of_authors = random.randint(1, 3)
    authors = '; '.join([fake.name() for _ in range(0, number_of_authors)])

    study = {'Study title': fake.sentence(nb_words=9), 'Author': authors}
    study = pd.DataFrame.from_records(study, index=[0])

    groups = list()
    number_of_groups = random.randint(5, 15)
    for g in range(1, number_of_groups):
        groups.append(
            {'Group': g,
             'Model': fake.sentence(nb_words=3).replace('.', '').lower(),
             'Study duration': str(random.choice([2, 4, 8, 12, 24])) + ' weeks',
             'Protein treatment': fake.sentence(nb_words=3).replace('.', '').lower(),
             'Additional suplementation': random.choice(['abc', 'def', 'ghi', 'jkl'])
             }
        )
    groups = pd.DataFrame.from_records(groups)

    biological_replicas = list()
    number_of_biological_replicas = random.randint(5, 15)
    for a in range(1, number_of_biological_replicas):
        biological_replicas.append({'Biological replica': a,
                        'Cell name': random.choice(['MDDA/MB/231']),
                        'Cell line origin': random.choice(['abc', 'def', 'ghi', 'jkl']),
                        'Receptor expression': random.choice(['abc', 'def', 'ghi', 'jkl']),
			'Media composition': random.choice(['abc', 'def', 'ghi', 'jkl']),
		        'Passage number': random.randint(1, 10),
                        'Morphology': random.choice(['abc', 'def', 'ghi', 'jkl']),
			'Patient characteristics': random.choice(['abc', 'def', 'ghi', 'jkl']),
                        'Group': random.randint(1, number_of_groups-1)})
    biological_replicas = pd.DataFrame.from_records(biological_replicas)

    collected_sheets = {'Study': study, 'Groups': groups, 'Biological replicas': biological_replicas}

    for sheet in random.biological_replica(['Proliferation assay', 'Imono flurecence', 'Protein essay'], random.randint(1, 3)):
        measurements = list()
        for m in range(1, random.randint(1, 10)):
            measurement = {
                           'Biological replica': random.randint(1, number_of_biological_replicas-1),
                           'Timepoint': random.randint(1, 48),
                           'Method': fake.sentence(nb_words=3).replace('.', '').lower(),
                           'Measurement': random.choice(['abc', 'def', 'ghi', 'jkl', 'xyz', 'ghi', 'qwe', 'hjk']),
                           'Value': random.random() * 10000,
                           'Units': random.choice(['unit', 'g', 'mm', 'cm', 'nm'])
                       }
            number_of_extras = random.randint(0, 2)
            for extra in random.biological_replica(['xyz', 'ghi', 'qwe', 'jhk'], k=number_of_extras):
                measurement[extra] = random.choice(list(range(1, 10)) + [None])
            measurements.append(measurement)
        measurements = pd.DataFrame.from_records(measurements)
        collected_sheets[f'Test-{sheet}'] = measurements

    return collected_sheets
