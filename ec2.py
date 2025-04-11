import boto3
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import openai

# AWS and local setup
s3 = boto3.client('s3')
bucket_name = 'your-processed-bucket-name'
object_key = 'uploaded-lab-results.csv'
local_file = '/tmp/processed.csv'

# Download the file
s3.download_file(bucket_name, object_key, local_file)

# Load data
df = pd.read_csv(local_file)

# Flagging abnormal values
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

# Connect to RDS
conn = psycopg2.connect(
    host='your-rds-endpoint',
    database='your-db-name',
    user='your-username',
    password='your-password'
)
cur = conn.cursor()

# Create table
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

# Prepare for LLM
test_summary = "\n".join([f"{row['test_name']}: {row['value']} {row['unit']} (Normal Range: {row['reference_range']})"
                         for _, row in df.iterrows()])

# Call OpenAI LLM
openai.api_key = 'your-openai-api-key'

prompt = f"""Analyze the following blood test results and explain them in simple terms.
Highlight any abnormal values and what they might mean.

{test_summary}

Provide recommendations if necessary."""

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)

explanation_text = response.choices[0].message['content'].strip()

# Insert data into RDS
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
            explanation_text  # Same explanation for all for simplicity
        )
    )

conn.commit()
cur.close()
conn.close()

print("Lab results processed and saved to RDS!")
