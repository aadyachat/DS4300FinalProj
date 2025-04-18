
import boto3
import pandas as pd
import ollama
import os

# AWS setup
s3 = boto3.client('s3')
bucket_raw = 'raw-bloodtest-upload-sk'
bucket_proc = 'processed-bloodtest-upload-sk'

# List trigger files
trigger_prefix = 'to-process/'
trigger_objects = s3.list_objects_v2(Bucket=bucket_proc, Prefix=trigger_prefix)

if 'Contents' not in trigger_objects:
    print("No trigger files found.")
    exit()

for trigger in trigger_objects['Contents']:
    trigger_key = trigger['Key']
    if not trigger_key.endswith('.txt'):
        continue

    # Extract filename from trigger
    original_filename = trigger_key.replace(trigger_prefix, '').replace('.txt', '')
    local_file = f'/tmp/{original_filename}'
    print(f"🟡 Processing trigger for: {original_filename}")

    try:
        # Download original file from RAW bucket
        s3.download_file(bucket_raw, original_filename, local_file)
        df = pd.read_csv(local_file)

        # Create prompt
        test_summary = "\n".join([
            f"{row['test_name']}: {row['value']} {row['unit']} (Reference Range: {row['reference_range']})"
            for _, row in df.iterrows()
        ])

        prompt = f"""You are a health assistant. Given this blood test data, do the following:

        1. Summarize the test panel
        2. Identify any abnormal values. For each test:
        - Use the `reference_range` column for comparison
        - If the reference range is a range (e.g., 13.0 - 17.0), check if the value is inside it.
        - If the reference range is a bound (e.g., < 200 or > 40), compare accordingly.
        3. For each abnormal value, suggest one evidence-based dietary change.
        4. Clearly separate "Abnormal Results" and "Normal Results" in your response.

        Here is the data:

        {test_summary}
"""  # triple quotes preserved

        response = ollama.chat(
            model='llama3',
            messages=[{"role": "user", "content": prompt}]
        )

        summary = response['message']['content']

        # Upload summary
        output_key = f'summaries/{original_filename}-summary.txt'
        s3.put_object(Body=summary.encode('utf-8'), Bucket=bucket_proc, Key=output_key)

        print(f"✅ Summary uploaded: {output_key}")

        # Clean up trigger file
        s3.delete_object(Bucket=bucket_proc, Key=trigger_key)
        print(f"🧹 Trigger removed: {trigger_key}\n")

    except Exception as e:
        print(f"❌ Failed to process {original_filename}: {e}\n")
