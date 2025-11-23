import base64
import json
import pycurl
from io import BytesIO
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
      protocolo = empresa.get('protocoloRelatorio')

      dadospedidoEmitir = {
          
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
              "idServico": "RELATORIOSITFIS92",
              "versaoSistema": "2.0",
              "dados": "{ \"protocoloRelatorio\":"+'"'+protocolo+'"'+ "}"
            }  
          }
      post_data_Emitir=json.dumps(dadospedidoEmitir)
      # definição do cabeçalho header
      headers=['jwt_token:'+jwt_token,'Authorization: Bearer '+token,'Content-Type: application/json','accept: text/pain']
      buffer = BytesIO()
      c = pycurl.Curl()
      c.setopt(c.URL,'https://gateway.apiserpro.serpro.gov.br/integra-contador/v1/Emitir')
      c.setopt(c.POSTFIELDS,post_data_Emitir)
      c.setopt(c.HTTPHEADER,headers)
      c.setopt(c.WRITEDATA,buffer)
      c.perform() # executa a requisicao
      c.close()

      responseEmitir = buffer.getvalue()

      resultadoEmitir=json.loads(responseEmitir.decode("utf-8"))
      dadosEmitir=json.loads(resultadoEmitir['dados'])
      pdfbase64= dadosEmitir['pdf']
      with open('c:\\temp\\relatoriofiscal'+cnpj+'.pdf',"wb") as f:
          f.write(base64.b64decode(pdfbase64))
          print('Arquivo salvo na pasta')
        
          # Limpa o protocolo no JSON após gerar o PDF
          empresa['protocoloRelatorio'] = ''
          salvar_empresas(empresas)

















                    


    
