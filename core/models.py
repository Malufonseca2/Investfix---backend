from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_PATH = os.path.join(ROOT_DIR, "API", "instance", "banco.db")

db = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=db)
session = Session()

Base = declarative_base()      

class Investimentos(Base):
    __tablename__ = 'investimentos'
    id = Column('Id', Integer, primary_key=True, autoincrement = True)
    titulo = Column('Título', String)
    valor_minimo = Column('Valo mínimo', String)
    vencimento = Column('Vencimento', String)
    taxa = Column('Taxa', String)
    liquidez = Column('Liquidez', String)
    tipo = Column('Tipo', String)

    def __init__(self, titulo, valor_minimo, vencimento, taxa, liquidez, tipo):
        self.titulo = titulo
        self.valor_minimo = valor_minimo
        self.vencimento = vencimento
        self.taxa = taxa
        self.liquidez = liquidez
        self.tipo = tipo

Base.metadata.create_all(bind=db)

