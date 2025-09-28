import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Imports dos módulos da aplicação
from models.user import db
from routes.user import user_bp
from routes.opme import opme_bp
from routes.maino import maino_bp

app = Flask(__name__, static_folder='static')

# Configuração do CORS
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "https://opme-control-frontend-production.up.railway.app", "https://opme-control-backend-fixed-v17-production.up.railway.app"]}})

# Configuração da chave secreta
app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"

# Registro dos blueprints (onde as rotas da API são adicionadas ao app)
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(opme_bp, url_prefix='/api')
app.register_blueprint(maino_bp, url_prefix='/api')

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Rota "pega-tudo" para servir o frontend React
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        return send_from_directory(static_folder_path, 'index.html')

# Bloco de execução principal
if __name__ == '__main__':
    # Cria as tabelas do banco de dados ANTES de iniciar o servidor
    with app.app_context():
        db.create_all()
    
    # ---- INÍCIO DO BLOCO DE DEBUGGING DE ROTAS ----
    # Este código vai imprimir no terminal todas as rotas que o Flask conhece
    print("\n--- ROTAS REGISTRADAS NA APLICAÇÃO ---")
    for rule in app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint}, Rota: {rule.rule}")
    print("--- FIM DAS ROTAS ---\n")
    # ---- FIM DO BLOCO DE DEBUGGING ----

    # Define a porta e inicia o servidor
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)