import boto3
import csv
import json
import os
import io

# Standardize test names and units
test_name_mapping = {
   'WHITE BLOOD CELL COUNT': 'WBC',
   'WHITE BLOOD CELL COUNT (WBC)': 'WBC',
   'WBC COUNT': 'WBC',
   'RED BLOOD CELL COUNT': 'RBC',
   'RED BLOOD CELL COUNT (RBC)': 'RBC',
   'RBC COUNT': 'RBC',
   'HEMOGLOBIN': 'Hemoglobin',
   'HEMOGLOBIN (HGB)': 'Hemoglobin',
   'HGB': 'Hemoglobin',
   'GLUCOSE': 'Glucose',
   'CALCIUM': 'Calcium',
   'SODIUM': 'Sodium',
   'POTASSIUM': 'Potassium',
   'TOTAL CHOLESTEROL': 'Total Cholesterol',
   'CHOLESTEROL': 'Total Cholesterol',
   'LDL CHOLESTEROL': 'LDL Cholesterol',
   'LDL-C': 'LDL Cholesterol',
   'LDL': 'LDL Cholesterol',
   'HDL CHOLESTEROL': 'HDL Cholesterol',
   'HDL-C': 'HDL Cholesterol',
   'HDL': 'HDL Cholesterol',
   'TSH (THYROID STIMULATING HORMONE)': 'TSH',
   'THYROID STIMULATING HORMONE': 'TSH',
   'TSH': 'TSH',
   'FREE T4': 'Free T4',
   'T4, FREE': 'Free T4',
   'FT4': 'Free T4'
}

target_units = {
   'WBC': '10^3/uL',
   'RBC': '10^6/uL',
   'Hemoglobin': 'g/dL',
   'Glucose': 'mg/dL',
   'Calcium': 'mg/dL',
   'Sodium': 'mmol/L',
   'Total Cholesterol': 'mg/dL',
   'LDL Cholesterol': 'mg/dL',
   'HDL Cholesterol': 'mg/dL',
   'TSH': 'mIU/L',
   'Free T4': 'ng/dL'
}

def convert_value(value, from_unit, to_unit, test):
   value = float(value)
   
   # Convert WBC count
   if test == 'WBC':
       if 'x10^9/L' in from_unit or '10^9/L' in from_unit:
           return value  # Equivalent to 10^3/uL
   
   # Convert RBC count
   if test == 'RBC':
       if 'x10^12/L' in from_unit or '10^12/L' in from_unit:
           return value  # Equivalent to 10^6/uL
   
   # Convert Glucose
   if test == 'Glucose' and 'mmol/L' in from_unit and 'mg/dL' in to_unit:
       return value * 18.0
   
   # Convert Calcium
   if test == 'Calcium' and 'mmol/L' in from_unit and 'mg/dL' in to_unit:
       return value * 4.0
   
   # Convert Free T4
   if test == 'Free T4' and 'pmol/L' in from_unit and 'ng/dL' in to_unit:
       return value / 12.87
   
   # If no specific conversion needed, return original
   return value

def preprocess_bloodwork_data(file_obj):
   """
   Processes the uploaded bloodwork data, standardizes test names and units
   without using pandas.
   """
   # Read CSV file using csv module
   csv_data = file_obj.read().decode('utf-8')
   csv_reader = csv.DictReader(io.StringIO(csv_data))
   
   # Convert to list of dictionaries
   rows = list(csv_reader)
   
   # Standardize test names and units
   for row in rows:
       test = row['test_name'].strip().upper()
       if test in test_name_mapping:
           row['test_name'] = test_name_mapping[test]
   
   # Standardize units and convert values if needed
   for row in rows:
       test = row['test_name']
       if test in target_units:
           current_unit = row['unit'].strip()
           target_unit = target_units[test]
           
           if current_unit != target_unit:
               row['value'] = convert_value(row['value'], current_unit, target_unit, test)
               row['unit'] = target_unit
   
   # Ensure values are numeric and properly rounded
   for row in rows:
       try:
           row['value'] = round(float(row['value']), 2)
       except (ValueError, TypeError):
           row['value'] = None
   
   return rows

def lambda_handler(event, context):
   """
   Lambda function handler that is triggered when a file is uploaded to S3.
   Processes the uploaded file and stores the cleaned data in another S3 bucket.
   """
   # Initialize S3 client
   s3 = boto3.client('s3')
   
   # Get the uploaded file's details from the event
   bucket_name = event['Records'][0]['s3']['bucket']['name']
   file_key = event['Records'][0]['s3']['object']['key']
   
   # Get the file object from S3
   response = s3.get_object(Bucket=bucket_name, Key=file_key)
   file_obj = response['Body']
   
   # Process the file
   processed_rows = preprocess_bloodwork_data(file_obj)
   
   # Save the cleaned file to a new bucket
   output_bucket = 'processed-bloodtest-data'  # Your destination bucket
   output_key = f"processed/{os.path.basename(file_key)}"  # New file name
   
   # Convert the data back to CSV
   output = io.StringIO()
   if processed_rows:
       writer = csv.DictWriter(output, fieldnames=processed_rows[0].keys())
       writer.writeheader()
       writer.writerows(processed_rows)
   
   # Upload to S3
   s3.put_object(Bucket=output_bucket, Key=output_key, Body=output.getvalue())
   
   return {
       'statusCode': 200,
       'body': f"File processed and saved to {output_bucket}/{output_key}"
   }