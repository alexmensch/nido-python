# from contextlib import contextmanager
#
# @contextmanager
# def session_scope():
#     """Provide a transactional scope around a series of operations."""
#     session = Session()
#     try:
#         yield session
#         session.commit()
#     except:
#         session.rollback()
#         raise
#     finally:
#         session.close()
#
#
# def run_my_program():
#     with session_scope() as session:
#         ThingOne().go(session)
#         ThingTwo().go(session)

from sqlalchemy import create_engine, Column, Integer, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from nidod.config import DaemonConfig, Mode

engine = create_engine('sqlite:///{}'.format(DaemonConfig.DB_PATH))
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    set_temp = Column(Float)
    set_mode = Column(Integer)
    celsius = Column(Boolean)

    def __repr__(self):
        return (
            '<Settings(set_temp={}, set_mode={}, celsius={})>'
            .format(self.set_temp, Mode(self.set_mode).name, self.celsius)
        )


def init_db(base, engine):
    base.metadata.create_all(engine)
    default_settings = Settings(set_temp=21.0,
                                set_mode=Mode.Off.value,
                                celsius=False)
    print('Initializing default settings: {}'.format(default_settings))
    session = Session()
    session.add(default_settings)
    session.commit()


if __name__ == '__main__':
    init_db(Base, engine)

# query = session.query(db.Settings)
# query.one()  # Returns MultipleResultsFound and NoResultFound exceptions
