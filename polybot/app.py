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


def get_result(respond):
    if "labels" in respond:
        try:
            dict_objects = dict()
            total_count = 0
            for lab in respond['labels']:
                item_class = lab['class']
                if item_class in dict_objects:
                    dict_objects[item_class] += 1
                else:
                    dict_objects[item_class] = 1
                total_count += 1
            return total_count, dict_objects
        except Exception as e:
            return None, {}
def summary_msg(total_object_number, object_dictionary):
    msg = f'We detect {total_object_number} objects.\n'
    for key, val in object_dictionary.items:
        object_count = f'object {key} found {val} times.\n'
        msg += object_count
    return msg

@app.route(f'/results', methods=['POST'])
def results():
    prediction_id = request.args.get('predictionId')

    dynamodb = boto3.resource('dynamodb')
    dyanamo_db = dynamodb.Table("ameerbadir-aws")
    response = dyanamo_db.get_item(key={"prediction_id": prediction_id})
    try:
        chat_id = response['Item']['chatId']
        # text_results = response['Item']['results']
        all_labels = response['Item']['labels']
        all_items = [label['class'] for label in all_labels]
        ret_msg = f'we found {len(all_items)} objects:\n'
        ret_msg += "\n".join(all_items)
        bot.send_text(chat_id, ret_msg)

    except Exception as e:
        return f'item not found: {e}', 404
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
