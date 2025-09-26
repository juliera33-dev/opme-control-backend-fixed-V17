import os
from flask import Flask
from models.user import db

# Criar uma instância mínima do Flask para o contexto da aplicação
app = Flask(__name__)

# Configurar o URI do banco de dados a partir da variável de ambiente
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar o SQLAlchemy com o aplicativo Flask
db.init_app(app)

# Criar todas as tabelas dentro do contexto da aplicação
with app.app_context():
    db.create_all()
    print("Tabelas do banco de dados PostgreSQL criadas ou já existentes.")


