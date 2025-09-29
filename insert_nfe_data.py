import xml.etree.ElementTree as ET
from models.user import NotaFiscal, ItemNotaFiscal, db 
from flask import current_app
from datetime import datetime

def insert_nfe_data(xml_data, is_content=False):
    """
    Insere dados de um XML de NF-e no banco de dados.
    Pode receber um caminho de arquivo ou o conteúdo do XML diretamente.
    """
    try:
        app = current_app._get_current_object()
        with app.app_context():
            # Parse do XML
            if is_content:
                # Se for conteúdo, decodifica se for bytes e faz o parse da string
                if isinstance(xml_data, bytes):
                    xml_data = xml_data.decode('utf-8')
                root = ET.fromstring(xml_data)
            else:
                # Se for um caminho de arquivo, faz o parse do arquivo
                tree = ET.parse(xml_data)
                root = tree.getroot()

            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            inf_nfe_element = root.find('.//nfe:infNFe', ns)
            if inf_nfe_element is None:
                raise ValueError("XML inválido: tag infNFe não encontrada.")

            chave_acesso = inf_nfe_element.attrib.get('Id', '').replace('NFe', '')
            if not chave_acesso:
                 raise ValueError("Chave de acesso não encontrada no XML.")

            # Verificação de duplicidade
            existing_nfe = NotaFiscal.query.filter_by(chave_acesso=chave_acesso).first()
            if existing_nfe:
                return {'success': False, 'message': f'Nota fiscal com chave {chave_acesso} já existe.'}

            # Extrair dados da NF-e
            ide = inf_nfe_element.find('nfe:ide', ns)
            dest = inf_nfe_element.find('nfe:dest', ns)
            
            nova_nfe = NotaFiscal(
                chave_acesso=chave_acesso,
                numero=ide.find('nfe:nNF', ns).text,
                serie=ide.find('nfe:serie', ns).text,
                data_emissao=datetime.fromisoformat(ide.find('nfe:dhEmi', ns).text),
                destinatario_nome=dest.find('nfe:xNome', ns).text,
                destinatario_cnpj=dest.find('nfe:CNPJ', ns).text,
                # Adicione outras colunas conforme necessário
            )
            db.session.add(nova_nfe)
            
            # Extrair dados dos itens
            for det in root.findall('.//nfe:det', ns):
                prod = det.find('nfe:prod', ns)
                novo_item = ItemNotaFiscal(
                    codigo_produto=prod.find('nfe:cProd', ns).text,
                    descricao_produto=prod.find('nfe:xProd', ns).text,
                    quantidade=float(prod.find('nfe:qCom', ns).text),
                    valor_total=float(prod.find('nfe:vProd', ns).text),
                    nota_fiscal=nova_nfe
                )
                db.session.add(novo_item)

            db.session.commit()
            return {'success': True, 'message': f'Nota fiscal {nova_nfe.numero} inserida com sucesso!'}

    except Exception as e:
        db.session.rollback()
        # Logar o erro pode ser útil em produção
        print(f"ERRO em insert_nfe_data: {str(e)}")
        raise e
