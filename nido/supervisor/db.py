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
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from nido.supervisor.config import DaemonConfig
from nido.lib import Mode
from nido.lib.exceptions import DBError

engine = create_engine("sqlite:///{}".format(DaemonConfig.DB_PATH))
Base = declarative_base()
Session = sessionmaker(bind=engine)


class _Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    set_temp = Column(Float, nullable=False)
    set_mode = Column(Integer, nullable=False)
    celsius = Column(Boolean, nullable=False)

    def __repr__(self):
        return "<Settings(set_temp={}, set_mode={}, celsius={})>".format(
            self.set_temp, Mode(self.set_mode).name, self.celsius
        )

    def to_dict(self):
        return {
            "set_temp": self.set_temp,
            "set_mode": Mode(self.set_mode).name,
            "celsius": self.celsius,
        }


@contextmanager
def _db_session():
    session = Session()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise DBError(e)
    finally:
        session.close()


def _get_settings(session):
    return session.query(_Settings).one()


def get_settings():
    with _db_session() as session:
        settings = _get_settings(session)
        return settings.to_dict()


def set_settings(set_temp=None, set_mode=None, celsius=None):
    with _db_session() as session:
        settings = _get_settings(session)
        if set_temp is not None:
            settings.set_temp = set_temp
        if set_mode is not None:
            settings.set_mode = set_mode
        if celsius is not None:
            settings.celsius = celsius
        session.add(settings)
    return None


def _init_db(base=Base, engine=engine):
    session = Session()
    query = session.query(_Settings)
    settings = None
    try:
        settings = query.one()
    except OperationalError:
        base.metadata.create_all(engine)
    except NoResultFound:
        pass
    except MultipleResultsFound:
        rows = query.all()
        for r in rows:
            session.delete(r)
        session.commit()
    else:
        settings.set_temp = 21.0
        settings.set_mode = Mode.Off.value
        settings.celsius = False
    finally:
        if not isinstance(settings, _Settings):
            settings = _Settings(set_temp=21.0, set_mode=Mode.Off.value, celsius=False)
        print("Initializing database with default settings: {}".format(settings))
        session.add(settings)
        session.commit()
    return None
