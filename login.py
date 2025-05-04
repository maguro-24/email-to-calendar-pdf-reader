from google_api import create_service

client = 'client_secret_new.json'
API_SERVICE_NAME ='gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']

service = create_service(client, API_SERVICE_NAME, API_VERSION, SCOPES)