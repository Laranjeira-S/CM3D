"""Functions related to reading the Excel file for an experimental study and creating a Study, and related, objects to
save to the database"""
import datetime

import pandas as pd

from cm3d.model import Biological_replica, Group, Measurement, Study


def load_all(workbook):
    """Given the experimental study Excel workbook, creates the Study, Groups, Biological replica and Measurement objects"""
    study = create_study(workbook['Study'])
    groups = create_groups(workbook['Groups'], study)
    biological_replicas = add_biological_replicas(workbook['Biological replicas'], groups)
    add_measurements(workbook, biological_replicas)
    return study


def create_study(sheet):
    """Reads single row in the Study worksheet and creates the Study object"""
    # only single row
    study = Study(title=sheet['Study title'][0],
                  authors=sheet['Author'][0])
    study.date_input = datetime.date.today()
    return study


def create_groups(sheet, study):
    """Iterates over rows in the Groups worksheet and creates Group objects"""
    groups = dict()
    for _, row in sheet.iterrows():
        # exit at first empty row
        if pd.isna(row['Group']):
            break

        sheet_group_id = int(row['Group'])
        groups[sheet_group_id] = Group(model=row['Model'],
                                       duration=row['Study duration'],
                                       protein_treatment=row['Protein treatment'],
                                       additional_suplementation=row['Additional suplementation'],
                                       study=study)
    return groups


def add_biological_replicas(sheet, group_lookup):
    """Iterates over all rows in the Biological replicas worksheet, creates Biological replica objects and associates them with Group"""
    biological_replicas_lookup = dict()
    for _, row in sheet.iterrows():
        # exit loop at the first empty row
        if pd.isna(row['Biological replica']):
            break
        # create an biological_replica object for this row
        new_biological_replica = Biological_replica(cell_name=row['Cell name'],
                            cell_origin=row['Cell line origin'],
                            receptor_expression=row['Receptor expression'],
			    media_composition=row['Media composition'],
			    passage_number = row['Passage number'],
                            morphology=row['Morphology'],
		            patient_characteristics=row['Patient characteristics'],
                            group=group_lookup[int(row['Group'])])
        # TODO: handle error if biological_replica is in unspecified/missing group
        biological_replicas_lookup[int(row['Biological replica'])] = new_biological_replica
    return biological_replicas_lookup


def add_measurements(all_sheets, biological_replicas_lookup):
    """Looks for all sheets beginning with 'Test-' and parses the Test worksheets, creating Measurement objects and
    associating them with specified Biological replica"""
    # loop over each dataframe in the dictionary
    for name, sheet in all_sheets.items():
        # if dataframe name starts with "Test-"
        if name.startswith('Test-'):
            # this contains measurements - create them and link with biological_replica
            for _, row in sheet.iterrows():
                # exit loop at the first empty row
                if pd.isna(row['Biological replica']):
                    break
                measurement = Measurement(
                    method=row['Method'],
                    time_point=row['Timepoint'],
                    value=row['Value'],
                    unit=row['Units'],
                    measurement=row['Measurement'],
                    test_type=name[5:],
                    biological_replica=biological_replicas_lookup[int(row['Biological replica'])])
                # add any other columns which are not core measurement attributes
                for column in sheet.columns:
                    if column not in {'Biological replica', 'Timepoint', 'Method', 'Measurement', 'Value', 'Units'}:
                        if row[column] is not None and not pd.isna(row[column]):
                            measurement[column] = row[column]


def read_file(filename: str) -> Study:
    """Reads the Excel file at location given by argument and creates a Study object from contents"""
    excel_sheet = pd.read_excel(filename, sheet_name=None, index_col=None)
    study = load_all(excel_sheet)
    with open(filename, 'rb') as excel_file:
        binary_data = excel_file.read()
    study.uploaded_file = binary_data
    return study
