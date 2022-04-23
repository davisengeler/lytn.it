from urllib.parse import urlparse
from math import gcd
import math
import hashlib
import boto3
import datetime
import uuid
import json

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

def to_base(n): 
    chars="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = len(chars)
    if not n: return "0"
    return to_base(n//base).lstrip("0") + chars[int(n%base)]

def create_generator(capacity, seed):
    hashed_seed = int(hashlib.sha256(seed.encode('utf-8')).hexdigest(), 16)
    generator = hashed_seed % math.floor(capacity*.8)  # Starting point
    while gcd(generator,capacity)!=1 and generator < capacity:  # We need a generator that's coprime to the capacity.
        generator += 1  # There may be a smarter way to find one, but I just increment by 1 each time until I find one.
    if gcd(generator,capacity)!=1:
        # Raise an error if one can't be found. 
        raise ValueError("Could not find a 'generator' that is relatively prime to the capacity ({capacity})")
    return generator
    
def get_iteration(seed):
    iterators = boto3.resource('dynamodb').Table('lytn.it_iterators')
    response = iterators.update_item(
        Key={ 'seed': seed },
        UpdateExpression="SET iteration = iteration + :incr",
        ExpressionAttributeValues={ ":incr": 1 },
        ReturnValues="UPDATED_NEW"
    )
    return response['Attributes']['iteration']

def generate_id(seed):
    # Determine required values
    iteration = get_iteration(seed)
    try: # Determine the number of digits required for this iteration value
        required_digits = math.ceil(math.log(iteration+1)/math.log(62))
    except:
        required_digits = 1
    try: # Determine the capacity of the previous number of digits (how many are 'unavailable')
        unavailable = math.ceil(math.pow(62, required_digits-1))
        if unavailable == 1:
            unavailable = 0
    except:
        unavailable = 0
    capacity = max(62, math.ceil(math.pow(62, required_digits)) - unavailable)
    generator = create_generator(capacity, seed)
    # Calcuate the next id to generate and convert it to a base 62 alphanumeric string
    calc = ((iteration-unavailable)*generator) % capacity + unavailable
    id = to_base(calc)
    return id

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
            id = generate_id(seed)
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
            'destination': dest,
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
