from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }

# --- MODELOS FALTANTES ADICIONADOS ABAIXO ---

class NFe(db.Model):
    __tablename__ = 'nfe'
    id = db.Column(db.Integer, primary_key=True)
    nNF = db.Column(db.String, unique=True, nullable=False)
    dEmi = db.Column(DateTime, nullable=False)
    # Adicione outras colunas da NFe conforme necessário

class Produto(db.Model):
    __tablename__ = 'produto'
    id = db.Column(db.Integer, primary_key=True)
    cProd = db.Column(db.String, unique=True, nullable=False)
    xProd = db.Column(db.String, nullable=False)
    # Adicione outras colunas do Produto conforme necessário

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    cnpj_dest = db.Column(db.String, unique=True, nullable=False)
    xNome_dest = db.Column(db.String, nullable=False)
    # Adicione outras colunas do Cliente conforme necessário

class Movimento(db.Model):
    __tablename__ = 'movimento'
    id = db.Column(db.Integer, primary_key=True)
    nNF = db.Column(db.String, nullable=False)
    dEmi = db.Column(DateTime)
    cnpj_dest = db.Column(db.String, nullable=False)
    xNome_dest = db.Column(db.String)
    cProd = db.Column(db.String, nullable=False)
    xProd = db.Column(db.String)
    cfop = db.Column(db.String)
    qCom = db.Column(db.Float, nullable=False)
    nLote = db.Column(db.String)
    qLote = db.Column(db.Float)