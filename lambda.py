import boto3
import pandas as pd
from io import StringIO

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    # Get the uploaded file details
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    destination_bucket = 'your-processed-bucket-name'

    # Read the file from S3
    response = s3.get_object(Bucket=source_bucket, Key=object_key)
    df = pd.read_csv(response['Body'])

    # Clean the data
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    df['date'] = pd.to_datetime(df['date'])
    df.fillna('N/A', inplace=True)

    # Save cleaned data to processed bucket
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Bucket=destination_bucket, Key=object_key, Body=csv_buffer.getvalue())

    return {
        'statusCode': 200,
        'body': f'File cleaned and saved to {destination_bucket}'
    }
