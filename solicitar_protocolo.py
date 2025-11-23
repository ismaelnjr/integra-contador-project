import base64
import json
from requests_pkcs12 import post
import pycurl
from io import BytesIO
import time
import re
import os
from autenticacao import serpro_componentes_autenticacaoLoja
from utils import carregar_empresas, salvar_empresas


if __name__ == "__main__":
  response = serpro_componentes_autenticacaoLoja() # FUNÇAO DE LOGIN NA API 

  print(response.status_code) # RETORNA O CODIGO DA RESPOSTA
  # RETORNA O CORPO DA RESPOSTA 
  #print(json.dumps(json.loads(response.content.decode("utf-8")), indent=4, separators=(',', ': '), sort_keys=True))
  resposta=json.loads(response.content.decode("utf-8")) # leia o json e decodifique para utf8
  token=resposta['access_token']
  jwt_token=resposta['jwt_token']
  print("token: ",token)
  print("jwt_token: ",jwt_token)

  print("--------------------------------")


  # Carrega empresas do arquivo JSON
  empresas = carregar_empresas()

  for empresa in empresas:
      idempresas = empresa.get('idempresas')
      cnpj = empresa.get('cnpj')
      razao = empresa.get('razao')
      protocolo_banco = empresa.get('protocoloRelatorio')

      if not protocolo_banco:
          
          dadospedido = {
              
                "contratante": {
                  "numero": "11497110000127",
                  "tipo": 2
                },
                "autorPedidoDados": {
                  "numero": "11497110000127",
                  "tipo": 2
                },
                "contribuinte": {
                  "numero": cnpj,
                  "tipo": 2
                },  
                "pedidoDados": {
                  "idSistema": "SITFIS",
                  "idServico": "SOLICITARPROTOCOLO91",
                  "versaoSistema": "2.0",
                  "dados": ""
                }  
              }
              
          post_data=json.dumps(dadospedido)    
          # definição do cabeçalho header
          headers=['jwt_token:'+jwt_token,'Authorization: Bearer '+token,'Content-Type: application/json','accept: text/pain']
          
          buffer = BytesIO()
          header_buffer = BytesIO() # essa linha nova foi alterada devido a versoes novas do python
          c = pycurl.Curl()
          c.setopt(c.URL,'https://gateway.apiserpro.serpro.gov.br/integra-contador/v1/Apoiar')
          c.setopt(c.POSTFIELDS,post_data)
          c.setopt(c.HTTPHEADER,headers)
          c.setopt(c.HEADERFUNCTION, header_buffer.write) # essa linha é nova , foi alterada, devido versoes novas do python
          c.setopt(c.WRITEDATA,buffer)
          c.perform() # executa a requisicao
          status_code = c.getinfo(c.RESPONSE_CODE)
          c.close()

          response = buffer.getvalue()
          print(response)
          headers_out = header_buffer.getvalue().decode('utf-8')# linha nova devido versoes novas do python
          # Verifica se o status e 304 not modified - nao modificado
          if status_code == 304:
              # se for 304 pega o cabeçalho
              #headers_out = c.getinfo(c.HEADER_OUT)
              match = re.search(r'etag:\s*"protocoloRelatorio:([^\s"]+)', headers_out) # versao alterada devido veroes novas do python, palavra etag precisa estar em minusculo 
              if match:
                  protocolo=match.group(1)
                  print("protocolo :",protocolo)
                  # Atualiza o protocolo no JSON
                  empresa['protocoloRelatorio'] = protocolo
                  salvar_empresas(empresas)
                  
                  
              else:
                  print("não encontramos o protocolo")

      
          elif status_code==200:
              
              print(response)

              resultado=json.loads(response.decode("utf-8"))
              print(resultado)
              dados=json.loads(resultado['dados'])
              protocolo=dados['protocoloRelatorio']
              # Atualiza o protocolo no JSON
              empresa['protocoloRelatorio'] = protocolo
              salvar_empresas(empresas)
                  
              
              print(protocolo)
              espera=dados['tempoEspera']
              print(f"tempo de espera : {espera}")
              time.sleep(espera/1000)








                    


    
