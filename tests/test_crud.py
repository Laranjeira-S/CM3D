from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

from cm3d.model import Sample, Base, Group, Measurement, Study

# use an in-memory database for testing
engine = create_engine('sqlite://', future=True, echo=False)
Session = sessionmaker(bind=engine)


def test_create_and_read():
    with Session() as session:
        Base.metadata.create_all(session.get_bind())

    # make a Study instance
    study9999 = Study(title="Test study for checking database operation", authors="S Laranjeira")

    # make experiments associated with this study
    study9999_group1 = Group(study=study9999, model="Singel cell",)
    study9999_group2 = Group(study=study9999, model="Compartmental model",)

    study99_g1_a1 = Sample(group=study9999_group1, cell_name="MDDA/MB/231", cell_origin='Human Caucasian breast adenocarcinoma')
    Sample(group=study9999_group2, cell_name="HT-29", cell_origin='Human Caucasian breast adenocarcinoma')

    # make tests associated with experiment
    Measurement(sample=study99_g1_a1, method='Metabiolic assay', measurement='Cell number', value=5183, unit='dimensionless')

    # Add new data
    with Session.begin() as session:
        session.add(study9999)
        # if no errors, change committed and sesion closed
        # if errors raised, issues a rollback to cancel all changes

        query_select = select(Study).where(Study.title == "Test study for checking database operation")

        # Check study is in database
        result = session.execute(query_select).scalars().all()

        # CHECK only one study with this name
        assert(len(result) == 1)

        # CHECK study name is correct
        assert(result[0].title == study9999.title)

        # CHECK groups associated with study
        assert len(result[0].groups) == 2

        # CHECK animals associated with groups
        assert len(result[0].groups[0].samples) == 1
        assert len(result[0].groups[1].samples) == 1


def test_update():
    # update authors of study
    with Session.begin() as session:
        query_select = select(Study).where(Study.title == "Test study for checking database operation")

        # Get study
        result = session.execute(query_select).scalars().all()

        # CHECK only one study with this name
        assert(len(result) == 1)

        # CHECK original author
        assert(result[0].authors == "S Laranjeira")

        # Update author
        session.execute(update(Study).
                        values(authors="Laranjeira, S").
                        where(Study.title == "Test study for checking database operation")
                        )

        # Get updated Study
        result = session.execute(query_select).scalars().all()

        # CHECK author updated
        assert(result[0].authors == "Laranjeira, S")


def test_delete():
    # delete study and check cascades work
    with Session.begin() as session:
        # Get study
        query_select = select(Study).where(Study.title == "Test study for checking database operation")
        result = session.execute(query_select).scalars().all()

        test_study_id = result[0].id

        # CHECK only one study with this name
        assert(len(result) == 1)

        session.delete(result[0])

        # Get study
        result = session.execute(query_select).scalars().all()

        # CHECK no study with this name
        assert(len(result) == 0)

        # query groups
        query_select = select(Group).where(Group.study_id == test_study_id)
        result = session.execute(query_select).scalars().all()

        # CHECK no groups with this study
        assert(len(result) == 0)
