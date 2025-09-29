from flask import Blueprint, request, jsonify
from sqlalchemy import func
from datetime import datetime
import xml.etree.ElementTree as ET
import os

# Importação padronizada e completa
from models.user import db, Movimento, NotaFiscal, ItemNotaFiscal, Produto, Cliente 
from insert_nfe_data import insert_nfe_data

opme_bp = Blueprint('opme', __name__)

@opme_bp.route('/notas-fiscais/upload-xml', methods=['POST'])
def upload_xml():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if file and file.filename.lower().endswith('.xml'):
            xml_content = file.read() # Lê o conteúdo do arquivo
            
            # Chama a função de inserção passando o conteúdo do XML
            resultado = insert_nfe_data(xml_content, is_content=True)

            if resultado['success']:
                return jsonify({'message': resultado['message']}), 201
            else:
                # 409 é o código para 'Conflito', usado quando o recurso já existe
                return jsonify({'error': resultado['message']}), 409
        else:
            return jsonify({'error': 'Apenas arquivos XML são aceitos'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao processar XML: {str(e)}'}), 500


@opme_bp.route('/saldos/consultar', methods=['GET'])
def get_balance():
    try:
        query = db.session.query(
            Movimento.cnpj_dest, Movimento.xNome_dest,
            Movimento.cProd, Movimento.xProd,
            Movimento.nLote, func.sum(Movimento.qCom).label('saldo')
        ).group_by(
            Movimento.cnpj_dest, Movimento.xNome_dest,
            Movimento.cProd, Movimento.xProd, Movimento.nLote
        )

        cnpj_cliente = request.args.get('cnpj_cliente')
        if cnpj_cliente:
            query = query.filter(Movimento.cnpj_dest == cnpj_cliente)

        results = query.all()
        balance_list = [{'cnpj_cliente': r.cnpj_dest, 'nome_cliente': r.xNome_dest,
                         'codigo_produto': r.cProd, 'descricao_produto': r.xProd,
                         'lote': r.nLote, 'saldo': r.saldo} for r in results]
        
        return jsonify(balance_list), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao calcular saldo: {str(e)}'}), 500


@opme_bp.route('/notas-fiscais/listar', methods=['GET'])
def get_movements():
    try:
        query = Movimento.query
        movements_db = query.all()
        
        movements_list = [{
            'numero_nf': m.nNF, 'data_emissao': m.dEmi.strftime('%Y-%m-%d') if m.dEmi else None,
            'cnpj_cliente': m.cnpj_dest, 'nome_cliente': m.xNome_dest,
            'codigo_produto': m.cProd, 'descricao_produto': m.xProd,
            'cfop': m.cfop, 'quantidade': m.qCom, 'lote': m.nLote, 'quantidade_lote': m.qLote
        } for m in movements_db]
        
        return jsonify(movements_list), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao obter movimentações: {str(e)}'}), 500


@opme_bp.route('/notas-fiscais/estatisticas', methods=['GET'])
def get_estatisticas():
    try:
        dados_exemplo = {"total_notas": NotaFiscal.query.count(), "valor_total": 75000.50, "clientes_ativos": Cliente.query.count()}
        return jsonify(dados_exemplo), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@opme_bp.route('/saldos/resumo', methods=['GET'])
def get_resumo_saldos():
    try:
        dados_resumo = {"saldo_total": db.session.query(func.sum(Movimento.qCom)).scalar() or 0, "produtos_distintos": 42, "clientes_atendidos": 15}
        return jsonify(dados_resumo), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
