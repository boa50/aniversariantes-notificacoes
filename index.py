from flask import Flask
import requests
import json
import io
import os
from datetime import date, datetime
import pytz
import configparser
import time

# Dev ou Prd também?
from dotenv import load_dotenv
load_dotenv()

def get_local_filename(filename):
    try:
        return os.path.join(os.path.dirname(__file__), filename)
    except:
        return filename

    
PROJECT = os.environ.get('PROJECT')
DB_API_KEY = os.environ.get('DB_API_KEY')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
EMAIL = os.environ.get('EMAIL')
SERVER_KEY = os.environ.get('SERVER_KEY')
NOTIFICATION_ICON = os.environ.get('NOTIFICATION_ICON')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL')


def get_dados(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(response.text)
        raise BaseException('GET /tasks/ {}'.format(response.status_code))
        
    try:
        return response.json()['documents']
    except:
        return {}
    
def get_id(document):
    return document['name'].split('/')[-1]

def get_ids(documents):
    ids = []
    
    for document in documents:
        identifier = get_id(document)
        ids.append(identifier)
        
    return ids

def envia_notificacao(texto, familia_nome, usuario_token):
    url = 'https://fcm.googleapis.com/fcm/send'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'key={SERVER_KEY}'
    }
    payload = {
          'to': usuario_token,
          'notification': {
                'title': f'Hoje tem aniversário na família {familia_nome} :)',
                'body': texto,
                'icon': NOTIFICATION_ICON,
                'click_action': NOTIFICATION_URL
          }
    }
    
    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    if resp.status_code != 200:
        raise BaseException('GET /tasks/ {}'.format(resp.status_code))
        
    return resp

def get_usuario_token(notificado):
    return notificado['fields']['tokenDestino']['stringValue']

def get_aniversariantes_dia(url, familia_id, headers):
    aniversariantes_url = url.split('?')[0]
    aniversariantes_url += f'/{familia_id}/aniversariantes?pageSize=2000'

    aniversariantes = get_dados(aniversariantes_url, headers)
   
    data_atual = date.today().strftime("%m-%d")

    aniversariantes_dia = []
    for aniversariante in aniversariantes:
        nome = aniversariante['fields']['pessoa']['stringValue']
        mes_dia = aniversariante['fields']['nascimento']['timestampValue'][5:10]

        if mes_dia == data_atual:
            aniversariantes_dia.append(nome)

    return aniversariantes_dia

def get_texto_aniversariantes(aniversariantes_dia):
    texto = 'Hoje a festa é para'

    for nome in aniversariantes_dia:
        texto += f' {nome},'

    if len(aniversariantes_dia) > 1:
        last_virgula = texto[:-1].rindex(',')
        return texto[:last_virgula] + ' e' + texto[last_virgula + 1:-1]
    else:
        return texto[:-1]
    
def escreve_log(usuario_token, response):
    log_texto = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    
    sucesso = json.loads(response.text)['success']
    resultado =  json.loads(response.text)['results']

    if sucesso == 1:
        log_texto += '\tSUCESSO\t\t'
    else:
        log_texto += '\tERRO\t\t'

    log_texto += f'Usuário: {usuario_token}\t\t'
    
    log_texto += f'Resultado: {resultado}'
    
    log_texto += '\n'
    
    print(log_texto)
        
def process_notifications():
    authUrl = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={DB_API_KEY}'

    authData = {
        'email': EMAIL,
        'password': DB_PASSWORD,
        'returnSecureToken': True,
    };

    resp = requests.post(authUrl, data=json.dumps(authData))
    if resp.status_code != 200:
        raise BaseException('GET /tasks/ {}'.format(resp.status_code))

    id_token = resp.json()['idToken']
    
    headers = {'Authorization': f'Bearer {id_token}'}
    
    url = f'https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents/familias?pageSize=2000'

    familias = get_dados(url, headers)

    familias_dict = {get_id(familia): familia['fields']['nome']['stringValue'] for familia in familias}
    
    for familia_id, familia_nome in familias_dict.items():
        familia_url = url.split('?')[0]
        familia_url += f'/{familia_id}/notificados?pageSize=2000'

        aniversariantes_dia = get_aniversariantes_dia(url, familia_id, headers)

        if len(aniversariantes_dia) > 0:

            notificados = get_dados(familia_url, headers)

            for notificado in notificados:
                identificador = get_id(notificado)
                usuario_token = get_usuario_token(notificado)
                texto = get_texto_aniversariantes(aniversariantes_dia)

                response = envia_notificacao(texto, familia_nome, usuario_token)

                escreve_log(usuario_token, response)

                time.sleep(5)

    return 'Notificações enviadas com sucesso'

app = Flask(__name__)

@app.route('/')
def home():
    return process_notifications()