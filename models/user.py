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

# --- MODELOS CORRIGIDOS E ADICIONADOS ABAIXO ---

# CLASSE RENOMEADA DE NFe PARA NotaFiscal
class NotaFiscal(db.Model):
    __tablename__ = 'nota_fiscal' # Trocado para nome mais padrão
    id = db.Column(db.Integer, primary_key=True)
    chave_acesso = db.Column(db.String(44), unique=True, nullable=False)
    numero = db.Column(db.String(9), nullable=False)
    data_emissao = db.Column(DateTime, nullable=False)
    
    # Relação com os itens
    itens = db.relationship('ItemNotaFiscal', backref='nota_fiscal', lazy=True)

# NOVA CLASSE ADICIONADA
class ItemNotaFiscal(db.Model):
    __tablename__ = 'item_nota_fiscal'
    id = db.Column(db.Integer, primary_key=True)
    codigo_produto = db.Column(db.String, nullable=False)
    descricao_produto = db.Column(db.String, nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    
    # Chave estrangeira para ligar o item à sua nota fiscal
    nota_fiscal_id = db.Column(db.Integer, db.ForeignKey('nota_fiscal.id'), nullable=False)

class Produto(db.Model):
    __tablename__ = 'produto'
    id = db.Column(db.Integer, primary_key=True)
    cProd = db.Column(db.String, unique=True, nullable=False)
    xProd = db.Column(db.String, nullable=False)

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    cnpj_dest = db.Column(db.String, unique=True, nullable=False)
    xNome_dest = db.Column(db.String, nullable=False)

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
