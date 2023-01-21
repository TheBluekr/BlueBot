import logging
import sys

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.core.database"
logger = logging.getLogger(__cogname__)

class Database:
    def __init__(self, *args, **kwargs):
        self.logger = logger

        try:
            self.engine = create_engine("postgresql+psycopg2://bluebot@localhost:5432/bluebot", echo=True)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            self.logger.info(f"Opened database session")

        except exc.SQLAlchemyError as e:
            self.logger.fatal(
                f"sqlalchemy-error={e}"
            )
            sys.exit(1)
        except Exception as e:
            self.logger.fatal(e)
            sys.exit(1)