import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Imports dos módulos da aplicação
from models.user import db
from routes.user import user_bp
from routes.opme import opme_bp
from routes.maino import maino_bp

app = Flask(__name__, static_folder='static')

# 1. Configurações Básicas
app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"

# 2. Configuração do CORS: Usando o curinga "*"
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 3. Configuração e Inicialização do Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 4. Registro dos Blueprints (As rotas da API TÊM PRIORIDADE)
# Colocar o registro dos blueprints aqui garante que o Flask os reconheça antes da rota catch-all
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(opme_bp, url_prefix='/api')
app.register_blueprint(maino_bp, url_prefix='/api')


# 5. Rota "pega-tudo" para servir o frontend React (ÚLTIMA PRIORIDADE)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        # Se o static folder não estiver configurado (não deve acontecer no Railway)
        return "Static folder not configured", 404

    # Primeiro, verifica se o caminho corresponde a um arquivo estático (CSS, JS, imagem)
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    
    # Se não for um arquivo estático E não for uma rota de API (o Flask verifica isso primeiro),
    # retorna o index.html para o roteador do frontend
    else:
        return send_from_directory(static_folder_path, 'index.html')

# Bloco de execução principal
if __name__ == '__main__':
    # Cria as tabelas do banco de dados ANTES de iniciar o servidor
    with app.app_context():
        db.create_all()
    
    # Define a porta e inicia o servidor
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
