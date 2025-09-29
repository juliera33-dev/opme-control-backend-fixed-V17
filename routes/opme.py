from flask import Blueprint, request, jsonify
from sqlalchemy import func
from datetime import datetime
import xml.etree.ElementTree as ET
import os

# Importação corrigida e completa
from models.user import db, Movimento, NotaFiscal, ItemNotaFiscal, Produto, Cliente 

opme_bp = Blueprint('opme', __name__)

# ROTA COMPLETAMENTE REFATORADA para extrair dados do XML e salvar no PostgreSQL
@opme_bp.route('/notas-fiscais/upload-xml', methods=['POST'])
def upload_xml():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if file and file.filename.lower().endswith('.xml'):
            xml_content = file.read()
            
            # Parse do XML a partir do conteúdo em memória
            root = ET.fromstring(xml_content)
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

            inf_nfe_element = root.find('.//nfe:infNFe', ns)
            if inf_nfe_element is None:
                return jsonify({'error': 'Estrutura de XML inválida: tag infNFe não encontrada.'}), 400
            
            chave_acesso = inf_nfe_element.attrib.get('Id', '').replace('NFe', '')
            if not chave_acesso:
                return jsonify({'error': 'Não foi possível encontrar a chave de acesso no XML.'}), 400

            # Verificação de duplicidade
            existing_nfe = NotaFiscal.query.filter_by(chave_acesso=chave_acesso).first()
            if existing_nfe:
                return jsonify({'message': f'Nota fiscal com chave {chave_acesso} já existe no banco de dados.'}), 409 # 409 Conflict

            # Extrair outros dados
            ide_element = inf_nfe_element.find('nfe:ide', ns)
            numero_nfe = ide_element.find('nfe:nNF', ns).text
            serie_nfe = ide_element.find('nfe:serie', ns).text
            data_emissao_str = ide_element.find('nfe:dhEmi', ns).text
            data_emissao = datetime.fromisoformat(data_emissao_str)

            dest_element = inf_nfe_element.find('nfe:dest', ns)
            dest_cnpj = dest_element.find('nfe:CNPJ', ns).text
            dest_nome = dest_element.find('nfe:xNome', ns).text

            # Criar novo objeto NotaFiscal
            nova_nfe = NotaFiscal(
                chave_acesso=chave_acesso,
                numero=numero_nfe,
                serie=serie_nfe,
                data_emissao=data_emissao,
                destinatario_nome=dest_nome,
                destinatario_cnpj=dest_cnpj
            )
            db.session.add(nova_nfe)

            # Extrair e adicionar itens
            for det_element in inf_nfe_element.findall('nfe:det', ns):
                prod_element = det_element.find('nfe:prod', ns)
                novo_item = ItemNotaFiscal(
                    codigo_produto=prod_element.find('nfe:cProd', ns).text,
                    descricao_produto=prod_element.find('nfe:xProd', ns).text,
                    quantidade=float(prod_element.find('nfe:qCom', ns).text),
                    valor_total=float(prod_element.find('nfe:vProd', ns).text),
                    nota_fiscal=nova_nfe # Associa o item à nota fiscal
                )
                db.session.add(novo_item)

            db.session.commit()
            return jsonify({'message': f'Nota fiscal {numero_nfe} processada com sucesso'}), 201

        else:
            return jsonify({'error': 'Apenas arquivos XML são aceitos'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao processar XML: {str(e)}'}), 500


# Rota para consultar saldos
@opme_bp.route('/saldos/consultar', methods=['GET'])
def get_balance():
    try:
        # Lógica para calcular o saldo a partir dos movimentos
        # Esta é uma consulta de exemplo e pode precisar de ajustes
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


# Rota para listar movimentos
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


# Rota de exemplo para estatísticas do dashboard
@opme_bp.route('/notas-fiscais/estatisticas', methods=['GET'])
def get_estatisticas():
    try:
        # Lógica para buscar estatísticas reais do banco
        dados_exemplo = {"total_notas": NotaFiscal.query.count(), "valor_total": 75000.50, "clientes_ativos": Cliente.query.count()}
        return jsonify(dados_exemplo), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Rota de exemplo para resumo de saldos do dashboard
@opme_bp.route('/saldos/resumo', methods=['GET'])
def get_resumo_saldos():
    try:
        # Lógica para buscar resumo de saldos real
        dados_resumo = {"saldo_total": db.session.query(func.sum(Movimento.qCom)).scalar() or 0, "produtos_distintos": 42, "clientes_atendidos": 15}
        return jsonify(dados_resumo), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
