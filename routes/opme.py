from flask import Blueprint, request, jsonify
from sqlalchemy import func
import os

# CORREÇÃO: Trocado 'NFe' por 'NotaFiscal' para corresponder ao models/user.py
from models.user import db, Movimento, NotaFiscal, Produto, Cliente 

opme_bp = Blueprint('opme', __name__)

# --- OBSERVAÇÃO ---
# Esta rota de upload ainda usa a lógica antiga de salvar em um arquivo local (app.db).
# Ela precisará ser reescrita no futuro para salvar os dados no PostgreSQL usando o SQLAlchemy.
@opme_bp.route('/notas-fiscais/upload-xml', methods=['POST'])
def upload_xml():
    # Este código precisa ser refatorado para usar db.session.add() e db.session.commit()
    # em vez de insert_nfe_data com db_path.
    return jsonify({'error': 'Função de upload ainda não refatorada para PostgreSQL.'}), 501


# ROTA REESCRITA para usar o banco de dados PostgreSQL via SQLAlchemy
@opme_bp.route('/saldos/consultar', methods=['GET'])
def get_balance():
    try:
        cnpj_cliente = request.args.get('cnpj_cliente')

        # A consulta agora é feita usando SQLAlchemy (db.session)
        query = db.session.query(
            Movimento.cnpj_dest,
            Movimento.xNome_dest,
            Movimento.cProd,
            Movimento.xProd,
            Movimento.nLote,
            func.sum(Movimento.qCom).label('saldo')
        ).group_by(
            Movimento.cnpj_dest,
            Movimento.xNome_dest,
            Movimento.cProd,
            Movimento.xProd,
            Movimento.nLote
        )

        if cnpj_cliente:
            query = query.filter(Movimento.cnpj_dest == cnpj_cliente)

        results = query.all()
        
        balance_list = []
        for row in results:
            balance_list.append({
                'cnpj_cliente': row.cnpj_dest,
                'nome_cliente': row.xNome_dest,
                'codigo_produto': row.cProd,
                'descricao_produto': row.xProd,
                'lote': row.nLote,
                'saldo': row.saldo
            })
        
        return jsonify(balance_list), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao calcular saldo: {str(e)}'}), 500


# ROTA REESCRITA para usar o banco de dados PostgreSQL via SQLAlchemy
@opme_bp.route('/notas-fiscais/listar', methods=['GET'])
def get_movements():
    try:
        query = Movimento.query

        cnpj_cliente = request.args.get('cnpj_cliente')
        if cnpj_cliente:
            query = query.filter(Movimento.cnpj_dest == cnpj_cliente)

        movements_db = query.all()
        
        movements_list = []
        for movement in movements_db:
            movements_list.append({
                'numero_nf': movement.nNF,
                'data_emissao': movement.dEmi.strftime('%Y-%m-%d') if movement.dEmi else None,
                'cnpj_cliente': movement.cnpj_dest,
                'nome_cliente': movement.xNome_dest,
                'codigo_produto': movement.cProd,
                'descricao_produto': movement.xProd,
                'cfop': movement.cfop,
                'quantidade': movement.qCom,
                'lote': movement.nLote,
                'quantidade_lote': movement.qLote
            })
        
        return jsonify(movements_list), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter movimentações: {str(e)}'}), 500


# ROTA NOVA ADICIONADA para destravar o dashboard do frontend
@opme_bp.route('/notas-fiscais/estatisticas', methods=['GET'])
def get_estatisticas():
    try:
        dados_exemplo = {
            "total_notas": 150, "valor_total": 75000.50, "clientes_ativos": 25
        }
        return jsonify(dados_exemplo), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ROTA NOVA ADICIONADA para destravar o dashboard do frontend
@opme_bp.route('/saldos/resumo', methods=['GET'])
def get_resumo_saldos():
    try:
        dados_resumo = {"saldo_total": 12345.67, "produtos_distintos": 42, "clientes_atendidos": 15}
        return jsonify(dados_resumo), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
