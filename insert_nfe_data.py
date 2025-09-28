import xml.etree.ElementTree as ET
from models.opme import NotaFiscal, ItemNotaFiscal, db
from flask import current_app

def insert_nfe_data(xml_file_path):
    """
    Insere dados de um arquivo XML de NF-e no banco de dados.
    """
    try:
        # Pega a referência para o app Flask
        app = current_app._get_current_object()

        with app.app_context():
            # Parse do arquivo XML
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Namespaces para buscar os elementos
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Extrair dados da NF-e
            inf_nfe_element = root.find('.//nfe:infNFe', ns)
            identificacao_element = root.find('.//nfe:ide', ns)

            chave_acesso = inf_nfe_element.attrib['Id'].replace('NFe', '')
            numero_nfe = identificacao_element.find('nfe:nNF', ns).text
            data_emissao = identificacao_element.find('nfe:dhEmi', ns).text
            
            # Verificação de duplicidade da nota fiscal
            existing_nfe = NotaFiscal.query.filter_by(chave_acesso=chave_acesso).first()
            if existing_nfe:
                return {'success': False, 'message': f'Nota fiscal {numero_nfe} (Chave {chave_acesso}) já existe no banco de dados.'}

            # Criar novo objeto NotaFiscal
            nova_nfe = NotaFiscal(
                chave_acesso=chave_acesso,
                numero=numero_nfe,
                data_emissao=datetime.fromisoformat(data_emissao).replace(tzinfo=None)
            )
            
            db.session.add(nova_nfe)
            
            # Extrair dados dos itens
            det_elements = root.findall('.//nfe:det', ns)
            for det_element in det_elements:
                prod_element = det_element.find('nfe:prod', ns)
                codigo_produto = prod_element.find('nfe:cProd', ns).text
                descricao_produto = prod_element.find('nfe:xProd', ns).text
                quantidade = float(prod_element.find('nfe:qCom', ns).text)
                valor_total_item = float(prod_element.find('nfe:vProd', ns).text)

                novo_item = ItemNotaFiscal(
                    codigo_produto=codigo_produto,
                    descricao_produto=descricao_produto,
                    quantidade=quantidade,
                    valor_total=valor_total_item,
                    nota_fiscal=nova_nfe
                )
                db.session.add(novo_item)

            db.session.commit()
            return {'success': True, 'message': f'Nota fiscal {numero_nfe} e seus itens inseridos com sucesso!'}

    except Exception as e:
        db.session.rollback()
        raise Exception(f'Erro ao processar o arquivo XML: {str(e)}')
