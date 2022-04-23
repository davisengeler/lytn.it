import json
import boto3
import datetime
import uuid

app_url = "https://app.lytn.it"

def track_event(event_type, event_data):
    s3_client = boto3.client('s3')
    dest_bucket = "vibehouse-data"
    dest_key = f"lytnit/{event_type}/{uuid.uuid4()}.json"
    print(f"TODO: add object to {dest_bucket}/{dest_key}: {event_data}")
    try:
        print(s3_client.put_object(Body=json.dumps(event_data), Bucket=dest_bucket, Key=dest_key))
    except Exception as e:
        print(e)

def get_dest(id):
  ddb = boto3.client('dynamodb')
  result = ddb.get_item(
    TableName = 'lytn.it_forwards',
    Key = { 'id': { 'S': id }}
  )
  if 'Item' in result:
    return result['Item']['destination']['S']
  else:
    return False


def lambda_handler(event, context):
  # Get the path
  try: 
    request_path = event['requestContext']['http']['path']
  except Exception as e:
    print(f"Error caught: {e}")
    request_path = None
  # Handle non-id requests (homepage/app)
  if not request_path or request_path == '/':
    response = {
        "statusCode": 302,
        "body": app_url
    }
  # Handle id requests (forwarding a link)
  else:
    requested_id = request_path[1:]
    dest = get_dest(requested_id)
    if dest:  # the id exists
      # Get the source ip
      try: 
        ip = event['requestContext']['http']['sourceIp']
      except Exception as e:
        print(f"Error caught: {e}")
        ip = ""
      try:
        referer = event['headers']['referer']
      except Exception as e:
        print(f"Error caught: {e}")
        referer = ""
      track_event("forward", {
        'id': requested_id, 
        'dest': dest,
        'ip': ip,
        'referer': referer,
        'event_time': datetime.datetime.now().isoformat()
      })
      response = {
        'statusCode': 302,
        'body': dest
      }
    else:  # the id doesn't exist
      response = {
        'statusCode': 404,
        'body': f"That ID wasn't found ({requested_id})"
      }
    
  return response
