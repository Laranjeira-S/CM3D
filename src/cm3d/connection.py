from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cm3d import DATABASE_FILENAME

# NOTE: we expect the sqlite database to be in the working directory (where cm3d-cli are run)
_db_uri = f'sqlite:///file:{DATABASE_FILENAME}?uri=true'
_db_ro_uri = f'{_db_uri}&mode=ro'


RWSession = sessionmaker(
    bind=create_engine(_db_uri, future=True, echo=False, connect_args={"check_same_thread": False}),
    autocommit=False,
    autoflush=False
)

ROSession = sessionmaker(
    bind=create_engine(_db_ro_uri, future=True, echo=False, connect_args={"check_same_thread": False}),
    autocommit=False,
    autoflush=False
)
