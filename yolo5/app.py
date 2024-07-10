import json
import time
from pathlib import Path
from detect import run
import yaml
from loguru import logger
import os
import boto3
import requests

images_bucket = os.environ['BUCKET_NAME']
queue_name = os.environ['SQS_QUEUE_NAME']

region = os.environ['REGION']
db_table_name = os.environ['DB_TABLE_NAME']
sqs_client = boto3.client('sqs', region_name=region)

with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']
session = boto3.Session()
s3 = session.client('s3', region)
dynamo_db = boto3.client('dynamodb', region_name=region)

def download_img_s3(img_name):
    try:
        local_path = f'{img_name}'
        s3.download_file(images_bucket, img_name, local_path)
        return local_path
    except Exception as e:
        logger.error("Download image failed")
        return f'Download image failed: {e}', 404


def upload_img_to_s3(predicted_img_path, img_name, prediction_id):
    try:
        s3.upload_file(predicted_img_path, images_bucket,
                       f'{img_name.split(".")[0]}_predicted.'
                       f'{img_name.split(".")[1]}')
    except Exception as e:
        return f'failed to upload images to s3: {e}', 404


def consume():
    while True:
        response = sqs_client.receive_message(QueueUrl=queue_name, MaxNumberOfMessages=1, WaitTimeSeconds=5)

        if 'Messages' in response:
            message = response['Messages'][0]['Body']
            message = json.loads(message)
            receipt_handle = response['Messages'][0]['ReceiptHandle']

            # Use the ReceiptHandle as a prediction UUID
            prediction_id = response['Messages'][0]['MessageId']

            logger.info(f'prediction: {prediction_id}. start processing')

            # Receives a URL parameter representing the image to download from S3
            img_name = message["imgName"]
            chat_id = message["chat_id"]
            try:
                original_img_path = download_img_s3(img_name)
            except Exception as e:
                return f'Download image failed: {e}', 404

            logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')

            # Predicts the objects in the image
            run(
                weights='yolov5s.pt',
                data='data/coco128.yaml',
                source=original_img_path,
                project='static/data',
                name=prediction_id,
                save_txt=True
            )

            logger.info(f'prediction: {prediction_id}/{original_img_path}. done')

            # This is the path for the predicted image with labels
            # The predicted image typically includes bounding boxes drawn around the detected objects, along with class labels and possibly confidence scores.
            predicted_img_path = Path(f'static/data/{prediction_id}/{original_img_path}')

            # Uploads the predicted image (predicted_img_path) to S3 (be careful not to override the original image).
            try:
                upload_img_to_s3(predicted_img_path, img_name, prediction_id)
            except Exception as e:
                return f'failed to upload images to s3: {e}', 404

            # Parse prediction labels and create a summary
            pred_summary_path = Path(f'static/data/{prediction_id}/labels/{original_img_path.split(".")[0]}.txt')
            if pred_summary_path.exists():
                with open(pred_summary_path) as f:
                    labels = f.read().splitlines()
                    labels = [line.split(' ') for line in labels]
                    labels = [{
                        'class': names[int(l[0])],
                        'cx': float(l[1]),
                        'cy': float(l[2]),
                        'width': float(l[3]),
                        'height': float(l[4]),
                    } for l in labels]

                logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')

                prediction_summary = {
                    'prediction_id': {"S": prediction_id},
                    'original_img_path': {"S": original_img_path},
                    'predicted_img_path': {"S": str(predicted_img_path)},
                    'labels': {"SS": [str(label) for label in labels]},
                    'time': {"S": str(time.time())}
                }


                # store the prediction_summary in a DynamoDB table
                try:
                    db = db_table_name
                    response =dynamo_db.put_item(
                        TableName=db, Item=prediction_summary
                    )
                    logger.info(f'store the  prediction summary: {response}')
                except Exception as e:

                    logger.error(f' store prediction summary failed')
                    return f' store prediction summary failed: {e}', 404

                #  perform a GET request to Polybot to `/results` endpoint
                params = {
                    'predictionId': prediction_id,
                    'chatId': chat_id
                }
                requests.post('http://dev-tel.ameer-domain.click/results',
                              params=params)

            # Delete the message from the queue as the job is considered as DONE
            sqs_client.delete_message(QueueUrl=queue_name, ReceiptHandle=receipt_handle)


if __name__ == "__main__":
    consume()
