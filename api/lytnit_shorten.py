from urllib.parse import urlparse
import boto3
import datetime
import uuid
import json

import vainID

seed = "lytnit"

def track_event(event_type, event_data):
    s3_client = boto3.client('s3')
    dest_bucket = "vibehouse-data"
    dest_key = f"lytnit/{event_type}/{uuid.uuid4()}.json"
    print(f"TODO: add object to {dest_bucket}/{dest_key}: {event_data}")
    try:
        print(s3_client.put_object(Body=json.dumps(event_data), Bucket=dest_bucket, Key=dest_key))
    except Exception as e:
        print(e)
    
def get_iteration():
    iterators = boto3.resource('dynamodb').Table('lytn.it_iterators')
    response = iterators.update_item(
        Key={ 'seed': seed },
        UpdateExpression="SET iteration = iteration + :incr",
        ExpressionAttributeValues={ ":incr": 1 },
        ReturnValues="UPDATED_NEW"
    )
    return response['Attributes']['iteration']

def has_conflict(id):
    forwards = boto3.resource('dynamodb').Table('lytn.it_forwards')
    response = forwards.get_item(
        Key={ 'id': id }
    )
    print(response)
    return 'Item' in response

def meets_url_requirements(x):
    try:
        result = urlparse(x)
        print([result.scheme, result.netloc])
        return all([result.scheme, '.' in result.netloc])
    except:
        return False

def add_item(new_item):
    forwards = boto3.resource('dynamodb').Table('lytn.it_forwards')
    response = forwards.put_item(Item=new_item)
    
def lambda_handler(event, context):
    track_event("test2", event)
    params = event['queryStringParameters']
    dest = params['dest']
    clean_dest = f"http://{dest}" if (not meets_url_requirements(dest)) else dest
    if meets_url_requirements(clean_dest):
        while True:
            id = vainID.generate_id(get_iteration(), seed)
            if not has_conflict(id):
                print(f"There was no conflict with {id}")
                break
            else:
                print(f"There was a conflict with {id}, generating a new one.")
        try: 
            ip = event['headers']['x-forwarded-for']
        except Exception as e:
            print(f"Error caught: {e}")
            ip = ""
        new_item = { 
            'id': id,
            'destination': clean_dest,
            'ip': ip,
            'event_time': datetime.datetime.now().isoformat()
        }
        add_item(new_item)
        track_event("shorten", new_item)
        return {
            "statusCode": 200,
            "body": "<a href='https://lytn.it/"+id+"'>lytn.it/"+id+"</a>",
            "headers": { "Access-Control-Allow-Origin": "*" }
         }
    else:
        return {
            "statusCode": 200,
            "body": "The link seems to be invalid...",
            "headers": { "Access-Control-Allow-Origin": "*" }
         }
