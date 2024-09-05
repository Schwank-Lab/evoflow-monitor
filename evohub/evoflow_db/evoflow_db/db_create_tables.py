from evoflow_db.base import Base
from evoflow_db import idec_engine 
from evoflow_db.idec import *

def create_all_tables():
    print('Creating all tables...')
    print(Base.metadata.tables.keys())
    Base.metadata.create_all(idec_engine())

if __name__ == '__main__':
    create_all_tables()
