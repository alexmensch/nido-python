#!/usr/bin/python

#   Nido, a Raspberry Pi-based home thermostat.
#
#   Copyright (C) 2016 Alex Marshall
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.
#   If not, see <http://www.gnu.org/licenses/>.

from contextlib import contextmanager

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


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(base, engine):
    session = Session()
    # Need to check if table exists with a query
    # If it does, overwrite what's there, otherwise create it
    #     with session_scope() as session:
    #         ThingOne().go(session)
    #         ThingTwo().go(session)
    base.metadata.create_all(engine)
    default_settings = Settings(set_temp=21.0,
                                set_mode=Mode.Off.value,
                                celsius=False)
    print('Initializing default settings: {}'.format(default_settings))
    session.add(default_settings)
    session.commit()


if __name__ == '__main__':
    init_db(Base, engine)

# query = session.query(db.Settings)
# query.one()  # Returns MultipleResultsFound and NoResultFound exceptions
