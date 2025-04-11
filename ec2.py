import boto3
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import openai

# S3 setup
s3 = boto3.client('s3')
raw_bucket_name = 'your-raw-bucket-name'
processed_bucket_name = 'your-processed-bucket-name'

raw_object_key = 'raw-lab-results.csv'
processed_object_key = 'processed-lab-results.csv'

raw_local_file = '/tmp/raw.csv'
processed_local_file = '/tmp/processed.csv'

# Step 1: Download raw data from raw S3 bucket
s3.download_file(raw_bucket_name, raw_object_key, raw_local_file)

# Step 2: Load and process data
df = pd.read_csv(raw_local_file)

def flag_value(row):
    try:
        low, high = map(float, row['reference_range'].replace('<', '0-').replace('>', '-10000').split('-'))
        if row['value'] < low:
            return 'Low'
        elif row['value'] > high:
            return 'High'
        else:
            return 'Normal'
    except:
        return 'Check'

df['status'] = df.apply(flag_value, axis=1)

# Save processed CSV locally
df.to_csv(processed_local_file, index=False)

# Step 3: Upload processed file to processed S3 bucket
s3.upload_file(processed_local_file, processed_bucket_name, processed_object_key)

# Step 4: Connect to RDS
conn = psycopg2.connect(
    host='your-rds-endpoint',
    database='your-db-name',
    user='your-username',
    password='your-password'
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS lab_results (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(255),
    test_date DATE,
    value FLOAT,
    unit VARCHAR(50),
    reference_range VARCHAR(50),
    status VARCHAR(50),
    explanation TEXT
)
""")

# Step 5: Generate LLM explanation
openai.api_key = 'your-openai-api-key'

test_summary = "\n".join([
    f"{row['test_name']}: {row['value']} {row['unit']} (Normal Range: {row['reference_range']})"
    for _, row in df.iterrows()
])

prompt = f"""Analyze the following blood test results and explain them in simple terms.
Highlight any abnormal values and what they might mean.

{test_summary}

Provide recommendations if necessary."""

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)

explanation_text = response.choices[0].message['content'].strip()

# Step 6: Insert processed data into RDS
for _, row in df.iterrows():
    cur.execute(
        """
        INSERT INTO lab_results (test_name, test_date, value, unit, reference_range, status, explanation)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            row['test_name'],
            row['date'],
            row['value'],
            row['unit'],
            row['reference_range'],
            row['status'],
            explanation_text
        )
    )

conn.commit()
cur.close()
conn.close()

print("Lab results processed, saved to RDS, and uploaded to processed bucket!")


# import boto3
# import pandas as pd
# import psycopg2
# import matplotlib.pyplot as plt
# import openai

# # AWS and local setup
# s3 = boto3.client('s3')
# bucket_name = 'your-processed-bucket-name'
# object_key = 'uploaded-lab-results.csv'
# local_file = '/tmp/processed.csv'

# # Download the file
# s3.download_file(bucket_name, object_key, local_file)

# # Load data
# df = pd.read_csv(local_file)

# # Flagging abnormal values
# def flag_value(row):
#     try:
#         low, high = map(float, row['reference_range'].replace('<', '0-').replace('>', '-10000').split('-'))
#         if row['value'] < low:
#             return 'Low'
#         elif row['value'] > high:
#             return 'High'
#         else:
#             return 'Normal'
#     except:
#         return 'Check'

# df['status'] = df.apply(flag_value, axis=1)

# # Connect to RDS
# conn = psycopg2.connect(
#     host='your-rds-endpoint',
#     database='your-db-name',
#     user='your-username',
#     password='your-password'
# )
# cur = conn.cursor()

# # Create table
# cur.execute("""
# CREATE TABLE IF NOT EXISTS lab_results (
#     id SERIAL PRIMARY KEY,
#     test_name VARCHAR(255),
#     test_date DATE,
#     value FLOAT,
#     unit VARCHAR(50),
#     reference_range VARCHAR(50),
#     status VARCHAR(50),
#     explanation TEXT
# )
# """)

# # Prepare for LLM
# test_summary = "\n".join([f"{row['test_name']}: {row['value']} {row['unit']} (Normal Range: {row['reference_range']})"
#                          for _, row in df.iterrows()])

# # Call OpenAI LLM
# openai.api_key = 'your-openai-api-key'

# prompt = f"""Analyze the following blood test results and explain them in simple terms.
# Highlight any abnormal values and what they might mean.

# {test_summary}

# Provide recommendations if necessary."""

# response = openai.ChatCompletion.create(
#     model="gpt-3.5-turbo",
#     messages=[{"role": "user", "content": prompt}]
# )

# explanation_text = response.choices[0].message['content'].strip()

# # Insert data into RDS
# for _, row in df.iterrows():
#     cur.execute(
#         """
#         INSERT INTO lab_results (test_name, test_date, value, unit, reference_range, status, explanation)
#         VALUES (%s, %s, %s, %s, %s, %s, %s)
#         """,
#         (
#             row['test_name'],
#             row['date'],
#             row['value'],
#             row['unit'],
#             row['reference_range'],
#             row['status'],
#             explanation_text  # Same explanation for all for simplicity
#         )
#     )

# conn.commit()
# cur.close()
# conn.close()

# print("Lab results processed and saved to RDS!")
