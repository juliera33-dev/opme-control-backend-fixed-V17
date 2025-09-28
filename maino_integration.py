import requests
import json
from datetime import datetime
import tempfile
import zipfile
import os
import logging
from models.opme import NotaFiscal, ItemNotaFiscal, db
from insert_nfe_data import insert_nfe_data 

# Configuração de logging para diagnóstico no backend
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MainoAPI:
    _access_token = None 

    def __init__(self, api_key=None, email=None, password=None):
        self.base_url = "https://api.maino.com.br"
        self.api_key = api_key
        self.email = email
        self.password = password
        
    def _authenticate(self):
        """Faz a requisição para obter o access_token."""
        endpoint = f"{self.base_url}/api/v2/authentication"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "application_uid": self.api_key,
            "email": self.email,
            "password": self.password
        }
        
        logger.info("Tentando autenticar na API do Maino...")
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=10, verify=False)
            response.raise_for_status()
            
            result = response.json()
            token = result.get('access_token')
            
            if token:
                MainoAPI._access_token = token
                logger.info("Autenticação bem-sucedida! Token obtido.")
                return True
            else:
                logger.error("Autenticação falhou: Token não encontrado na resposta.")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede ou HTTP durante a autenticação: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado durante a autenticação: {e}")
            return False

    def _get_headers(self):
        """Retorna os headers para requisições autenticadas."""
        headers = {"Content-Type": "application/json"}
        
        if not MainoAPI._access_token:
            if not self._authenticate():
                raise Exception("Falha na autenticação. Verifique application_uid, email e password.")

        headers["Authorization"] = f"Bearer {MainoAPI._access_token}"
        
        return headers
    
    def test_connection(self):
        """
        Teste a conexão e autenticação com a API do Mainô fazendo uma requisição simples.
        """
        try:
            self._get_headers() 
            return {"status": "ok", "code": 200, "message": "Conexão e autenticação bem-sucedidas!"}
        except Exception as e:
            logger.error(f"Erro no teste de conexão: {e}")
            return {"status": "error", "message": str(e), "code": 401}
            
    def listar_notas_fiscais_emitidas(self, data_inicio, data_fim, numero_nfe=None, cnpj_destinatario=None, exibir_xmls=False):
        """Lista notas fiscais emitidas"""
        endpoint = f"{self.base_url}/api/v2/notas_fiscais_emitidas"
        
        params = {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "exibir_xmls": str(exibir_xmls).lower()
        }
        
        if numero_nfe:
            params["numero_nfe"] = numero_nfe
        if cnpj_destinatario:
            params["cnpj_destinatario"] = cnpj_destinatario
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), params=params, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP ao listar notas fiscais: {e}")
            return {"error": f"Erro na API do Mainô: {response.status_code}. {e}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede/conexão: {e}")
            return {"error": f"Erro de rede ao conectar à API do Mainô: {e}"}
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return {"error": f"Erro inesperado: {e}"}

    def exportar_xmls_nfes_emitidas(self, data_inicio, data_fim):
        """Exporta XMLs das NF-es emitidas em um período"""
        endpoint = f"{self.base_url}/api/v2/nfes_emitidas"
        
        params = {
            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), params=params, verify=False)
            response.raise_for_status()
            result = response.json()
            return result.get("zip_url")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao exportar XMLs: {e}")
            return None
    
    def baixar_e_processar_xmls(self, data_inicio, data_fim, db_path="database/app.db"):
        """
        Baixa XMLs do Mainô e processa automaticamente
        
        Args:
            data_inicio (str): Data de início no formato DD/MM/AAAA
            data_fim (str): Data de fim no formato DD/MM/AAAA
            db_path (str): Caminho para o banco de dados
        
        Returns:
            dict: Resultado do processamento
        """
        zip_url = self.exportar_xmls_nfes_emitidas(data_inicio, data_fim)
        
        if not zip_url:
            return {"success": False, "message": "Erro ao obter URL do ZIP"}
        
        try:
            zip_response = requests.get(zip_url, verify=False)
            zip_response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                temp_zip.write(zip_response.content)
                temp_zip_path = temp_zip.name
            
            processed_count = 0
            errors = []
            
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    for filename in os.listdir(temp_dir):
                        if filename.lower().endswith('.xml'):
                            xml_path = os.path.join(temp_dir, filename)
                            try:
                                insert_nfe_data(xml_path)
                                processed_count += 1
                            except Exception as e:
                                errors.append(f"Erro ao processar {filename}: {str(e)}")
            
            os.unlink(temp_zip_path)
            
            return {
                "success": True,
                "processed_count": processed_count,
                "errors": errors,
                "message": f"Processados {processed_count} XMLs com sucesso"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Erro ao processar XMLs: {str(e)}"}
