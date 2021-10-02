from .config import Config
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

metadata = MetaData()

Base = declarative_base()


class FailedBuilds(Base):
    __tablename__ = "failed_builds"

    oid = Column(String(100), primary_key=True)
    datamodel_id = Column(String(100))
    datamodel_title = Column(String(100))
    instance_id = Column(String(100))

    def __init__(self, oid, datamodel_id, datamodel_title, instance_id):
        self.oid = oid
        self.datamodel_id = datamodel_id
        self.datamodel_title = datamodel_title
        self.instance_id = instance_id


metadata.create_all(engine)
