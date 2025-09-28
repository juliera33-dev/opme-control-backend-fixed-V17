import requests
import json
from datetime import datetime
import tempfile
import zipfile
import os
from insert_nfe_data import insert_nfe_data
import logging

# Configuração de logging para diagnóstico no backend
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MainoAPI:
    def __init__(self, api_key=None, bearer_token=None):
        # Corrigido para a URL base oficial da API
        self.base_url = "https://api.maino.com.br"
        self.api_key = api_key
        self.bearer_token = bearer_token
        
    def _get_headers(self):
        """Retorna os headers para autenticação"""
        headers = {"Content-Type": "application/json"}
        
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        elif self.api_key:
            # Maino usa X-Api-Key para a chave de webservices
            headers["X-Api-Key"] = self.api_key
        
        return headers
    
    def test_connection(self):
        """
        Teste a conexão e autenticação com a API do Mainô fazendo uma requisição simples.
        
        Retorna:
            dict: {status: 'ok'} ou um erro.
        """
        # Endpoint de teste completo (usando a rota fornecida pelo time de dev)
        endpoint = f"{self.base_url}/api/v2/notas_fiscais_emitidas"
        
        hoje = datetime.now().strftime("%d/%m/%Y")
        params = {
            "data_inicio": hoje,
            "data_fim": hoje,
            "numero_nfe": "999999999"
        }
        
        try:
            # Adicionado logging para mostrar a URL e os headers enviados no console do backend
            headers = self._get_headers()
            logger.info(f"Tentando conectar a: {endpoint}")
            logger.info(f"Headers (chave oculta): X-Api-Key={self.api_key[:4]}...{self.api_key[-4:]}")

            # Desabilitando a verificação de SSL (verify=False) e adicionando timeout
            response = requests.get(endpoint, headers=headers, params=params, timeout=10, verify=False) 
            
            logger.info(f"Status da resposta da Maino: {response.status_code}")
            
            # Se recebermos um HTML (que causa o SyntaxError no front), logamos o conteúdo no backend
            if '<!DOCTYPE' in response.text.upper():
                 logger.error(f"Erro: Maino retornou HTML de erro! Conteúdo parcial: {response.text[:200]}")
                 return {"status": "error", "message": "Erro no retorno da API (HTML em vez de JSON). Verifique a chave ou o acesso ao endpoint.", "code": 500}

            # 200 OK: Conexão bem-sucedida.
            if response.status_code == 200:
                return {"status": "ok", "code": 200}
            
            # 401 Unauthorized / 403 Forbidden: Falha na autenticação (Chave errada).
            elif response.status_code in [401, 403]:
                return {"status": "error", "message": "Credenciais inválidas.", "code": response.status_code}
            
            # Outros erros HTTP (400, 500, etc.)
            else:
                try:
                    error_json = response.json()
                    error_message = error_json.get("error", f"Erro desconhecido na API do Mainô: Status {response.status_code}")
                except json.JSONDecodeError:
                    error_message = f"Status {response.status_code}. Resposta não JSON (provavelmente HTML de erro)."
                
                return {"status": "error", "message": error_message, "code": response.status_code}

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede/conexão: {e}")
            return {"status": "error", "message": f"Erro de rede ao conectar ao Mainô: {e}", "code": 503}
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return {"status": "error", "message": f"Erro inesperado: {e}", "code": 500}
            
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
            print(f"Erro HTTP ao listar notas fiscais: {e}")
            return {"error": f"Erro na API do Mainô: {response.status_code}. {e}"}
        except requests.exceptions.RequestException as e:
            print(f"Erro de rede/conexão: {e}")
            return {"error": f"Erro de rede ao conectar à API do Mainô: {e}"}
        except Exception as e:
            print(f"Erro inesperado: {e}")
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
            print(f"Erro ao exportar XMLs: {e}")
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