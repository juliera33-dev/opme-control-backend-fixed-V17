import os
from flask import Flask, send_from_directory
from flask_cors import CORS

# Imports dos módulos da aplicação
from models.user import db
from routes.user import user_bp
from routes.opme import opme_bp
from routes.maino import maino_bp

app = Flask(__name__, static_folder='static')

# Configuração do CORS
# Correção da sintaxe da URL do frontend
CORS(app, resources={r"/api/*": {"origins": ["https://opme-control-frontend-production.up.railway.app", "https://opme-control-backend-fixed-v17-production.up.railway.app"]}})

# Configuração da chave secreta
app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"

# Registro dos blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(opme_bp, url_prefix='/api')
app.register_blueprint(maino_bp, url_prefix='/api')

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Servindo o frontend React corretamente
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


if __name__ == '__main__':
    # Usando a variável de ambiente PORT ou a porta 5000 como padrão
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


with app.app_context():
    db.create_all()
