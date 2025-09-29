from flask import Blueprint, request, jsonify
import os
from maino_integration import MainoAPI
# CORREÇÃO: A importação agora aponta para 'models.user' e usa os nomes corretos
from models.user import NotaFiscal, ItemNotaFiscal, db 

maino_bp = Blueprint('maino', __name__)

@maino_bp.route('/test-maino', methods=['GET'])
def test_maino():
    """Teste a conexão com a API do Mainô."""
    try:
        api_key = os.getenv('MAINO_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'Variável de ambiente MAINO_API_KEY não configurada'}), 500

        maino_api = MainoAPI(api_key=api_key)
        response = maino_api.test_connection() 
        
        if response and response.get('status') == 'ok':
            return jsonify({'success': True, 'message': 'Conexão estabelecida com sucesso!'}), 200
        else:
            return jsonify({'success': False, 'error': 'Falha na conexão. Verifique as credenciais.'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro na conexão: {str(e)}'}), 500

@maino_bp.route('/sync_maino', methods=['POST'])
def sync_maino():
    """Sincronizar dados do Mainô"""
    try:
        data = request.get_json()
        
        if not data or 'data_inicio' not in data or 'data_fim' not in data:
            return jsonify({'error': 'data_inicio e data_fim são obrigatórios'}), 400
        
        api_key = os.getenv('MAINO_API_KEY')
        if not api_key:
            return jsonify({'error': 'Variável de ambiente MAINO_API_KEY não configurada'}), 500
        
        maino_api = MainoAPI(api_key=api_key)
        
        resultado = maino_api.baixar_e_processar_xmls(
            data['data_inicio'],
            data['data_fim']
        )
        
        if resultado['success']:
            return jsonify({
                'message': resultado['message'],
                'processed_count': resultado['processed_count'],
                'errors': resultado['errors']
            }), 200
        else:
            return jsonify({'error': resultado['message']}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro na sincronização: {str(e)}'}), 500

@maino_bp.route('/list_nfes_maino', methods=['POST'])
def list_nfes_maino():
    """Listar NF-es do Mainô sem processar"""
    try:
        data = request.get_json()
        
        if not data or 'data_inicio' not in data or 'data_fim' not in data:
            return jsonify({'error': 'data_inicio e data_fim são obrigatórios'}), 400
        
        api_key = os.getenv('MAINO_API_KEY')
        if not api_key:
            return jsonify({'error': 'Variável de ambiente MAINO_API_KEY não configurada'}), 500
        
        maino_api = MainoAPI(api_key=api_key)
        
        notas = maino_api.listar_notas_fiscais_emitidas(
            data['data_inicio'],
            data['data_fim'],
            numero_nfe=data.get('numero_nfe'),
            cnpj_destinatario=data.get('cnpj_destinatario'),
            exibir_xmls=data.get('exibir_xmls', False)
        )
        
        if notas:
            return jsonify(notas), 200
        else:
            return jsonify({'error': 'Erro ao listar notas fiscais do Mainô'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao listar NF-es: {str(e)}'}), 500
