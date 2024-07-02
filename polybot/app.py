import json

import flask
from flask import request
import os
from bot import ObjectDetectionBot
import boto3
from botocore.exceptions import ClientError


def get_secret():
    secret_name = "ameer-tel-token"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = json.loads(get_secret_value_response['SecretString'])['TELEGRAM_TOKEN']
    return secret


app = flask.Flask(__name__)

# TODO load TELEGRAM_TOKEN value from Secret Manager
TELEGRAM_TOKEN = get_secret()

TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']


@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


@app.route(f'/results', methods=['POST'])
def results():
    prediction_id = request.args.get('predictionId')

    dynamodb = boto3.resource('dynamodb')
    # TODO use the prediction_id to retrieve results from DynamoDB and send to the end-user
    dyanamo_db = dynamodb.Table("ameerbadir-aws")
    response = dyanamo_db.get_item(key={"prediction_id": prediction_id})
    chat_id = response['Item']['chatId']
    text_results = response['Item']['results']
    bot.send_text(chat_id, text_results)
    return 'Ok'


@app.route(f'/loadTest/', methods=['POST'])
def load_test():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


if __name__ == "__main__":
    bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)
    ssl_context = ("YOURPUBLIC.pem", "YOURPRIVATE.key")
    app.run(host='0.0.0.0', port=8443, ssl_context=ssl_context)
