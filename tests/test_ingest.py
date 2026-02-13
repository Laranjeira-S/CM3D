from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cm3d.ingest import read_file
from cm3d.model import Base, Study

engine = create_engine('sqlite://', future=True, echo=False)
Session = sessionmaker(bind=engine)

test_input = Path(__file__).parent / 'resources/CM3D_input_template.xlsx'


def test_read_excel(filename=test_input):
    with Session() as session:
        Base.metadata.create_all(session.get_bind())

    s = read_file(str(filename))

    with Session.begin() as session:
        session.add(s)

        query_select = select(Study).where(Study.authors == "Author A Author")

        # Check study is in database
        result = session.execute(query_select).scalars().all()

        # CHECK only one study with this name
        assert(len(result) == 1)

        # Delete template data
        session.delete(result[0])

        # Get study
        result = session.execute(query_select).scalars().all()

        # CHECK no study with this name
        assert(len(result) == 0)
