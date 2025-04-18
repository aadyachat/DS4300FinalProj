import streamlit as st
import pandas as pd
import time
import boto3
from botocore.exceptions import NoCredentialsError
import io
import matplotlib.pyplot as plt
import psycopg2
from psycopg2 import sql

# Upload helper function
def upload_to_s3(file_buffer, filename, bucket, aws_access_key, aws_secret_key, region="us-east-1"):
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        s3.upload_fileobj(file_buffer, bucket, filename)
        return True
    except NoCredentialsError:
        return False
    except Exception as e:
        st.error(f"Failed to upload to S3: {e}")
        return False

# Generate bar plot and return image buffer
def generate_result_plot(df):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df['test_name'], df['value'], color='skyblue')
    ax.set_ylabel('Result')
    ax.set_title('Blood Test Results')
    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

# LLM processing moved to EC2

def save_to_rds(summary_text, plot_bytes, filename):
    db_config = {
        'dbname': st.secrets["RDS_CONFIG"]["dbname"],
        'user': st.secrets["RDS_CONFIG"]["user"],
        'password': st.secrets["RDS_CONFIG"]["password"],
        'host': st.secrets["RDS_CONFIG"]["host"],
        'port': st.secrets["RDS_CONFIG"]["port"],
    }

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO blood_analysis (filename, summary, plot_image)
            VALUES (%s, %s, %s)
        """)
        cursor.execute(insert_query, (filename, summary_text, psycopg2.Binary(plot_bytes)))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Failed to save to RDS: {e}")


# Function to display custom loading animation
def display_loading_animation(text="Processing..."):
    # Custom CSS for animated loading indicator
    st.markdown("""
    <style>
    .loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    .loader {
        border: 8px solid #f3f3f3;
        border-radius: 50%;
        border-top: 8px solid #3498db;
        width: 60px;
        height: 60px;
        animation: spin 1.5s linear infinite;
        margin-bottom: 15px;
    }
    .dna-loader {
        width: 80px;
        height: 80px;
        background: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgdmlld0JveD0iMCAwIDEwMCAxMDAiIHByZXNlcnZlQXNwZWN0UmF0aW89InhNaWRZTWlkIiBjbGFzcz0ibGRzLWRuYSI+PGNpcmNsZSBjeD0iNiIgY3k9IjUwIiByPSI2IiBmaWxsPSIjZTc0YzNjIj48YW5pbWF0ZSBhdHRyaWJ1dGVOYW1lPSJjeCIgdmFsdWVzPSI2OzY7MzE7OTQ7OTQ7OTQ7Njk7MzE7NiIgdGltZXM9IjA7MC4xMjU7MC4xNzU7MC4zMjU7MC41OzAuNjI1OzAuNjc1OzAuODI1OzEiIGR1cj0iMXMiIHJlcGVhdENvdW50PSJpbmRlZmluaXRlIj48L2FuaW1hdGU+PGFuaW1hdGUgYXR0cmlidXRlTmFtZT0iY3kiIHZhbHVlcz0iNTA7NTA7NzU7NzU7NTA7MjU7MjU7NTA7NTAiIHRpbWVzPSIwOzAuMTI1OzAuMTc1OzAuMzI1OzAuNTswLjYyNTswLjY3NTswLjgyNTsxIiBkdXI9IjFzIiByZXBlYXRDb3VudD0iaW5kZWZpbml0ZSI+PC9hbmltYXRlPjwvY2lyY2xlPjxjaXJjbGUgY3g9IjMxIiBjeT0iNzUiIHI9IjYiIGZpbGw9IiM1ZGFkZWMiPjxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9ImN4IiB2YWx1ZXM9IjMxOzMxOzU2Ozk0Ozk0Ozk0Ozk0OzU2OzMxIiB0aW1lcz0iMDswLjEyNTswLjE3NTswLjMyNTswLjQ3NTswLjYyNTswLjY3NTswLjgyNTsxIiBkdXI9IjFzIiByZXBlYXRDb3VudD0iaW5kZWZpbml0ZSI+PC9hbmltYXRlPjxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9ImN5IiB2YWx1ZXM9Ijc1Ozc1Ozc1OzM3OzMwOzc1Ozc1Ozc1Ozc1IiB0aW1lcz0iMDswLjEyNTswLjE3NTswLjMyNTswLjQ3NTswLjYyNTswLjY3NTswLjgyNTsxIiBkdXI9IjFzIiByZXBlYXRDb3VudD0iaW5kZWZpbml0ZSI+PC9hbmltYXRlPjwvY2lyY2xlPjxjaXJjbGUgY3g9IjU2IiBjeT0iNzUiIHI9IjYiIGZpbGw9IiMyYWJhOTUiPjxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9ImN4IiB2YWx1ZXM9IjU2OzU2Ozk0Ozk0Ozk0Ozk0OzMxOzU2OzU2IiB0aW1lcz0iMDswLjEyNTswLjE3NTswLjMyNTswLjQ3NTswLjYyNTswLjc1OzAuODI1OzEiIGR1cj0iMXMiIHJlcGVhdENvdW50PSJpbmRlZmluaXRlIj48L2FuaW1hdGU+PGFuaW1hdGUgYXR0cmlidXRlTmFtZT0iY3kiIHZhbHVlcz0iNzU7NzU7MTg7MTU7NzU7NzU7NzU7NzU7NzUiIHRpbWVzPSIwOzAuMTI1OzAuMTc1OzAuMzI1OzAuNDc1OzAuNjI1OzAuNzU7MC44MjU7MSIgZHVyPSIxcyIgcmVwZWF0Q291bnQ9ImluZGVmaW5pdGUiPjwvYW5pbWF0ZT48L2NpcmNsZT48Y2lyY2xlIGN4PSI5NCIgY3k9IjUwIiByPSI2IiBmaWxsPSIjNDk4NmU3Ij48YW5pbWF0ZSBhdHRyaWJ1dGVOYW1lPSJjeCIgdmFsdWVzPSI5NDs5NDs5NDs5NDs5NDs5NDs5NDs5NDs5NCIgdGltZXM9IjA7MC4xMjU7MC4xNzU7MC4zMjU7MC40NzU7MC42MjU7MC43NTswLjg3NTsxIiBkdXI9IjFzIiByZXBlYXRDb3VudD0iaW5kZWZpbml0ZSI+PC9hbmltYXRlPjxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9ImN5IiB2YWx1ZXM9IjUwOzUwOzUwOzUwOzUwOzUwOzUwOzUwOzUwIiB0aW1lcz0iMDswLjEyNTswLjE3NTswLjMyNTswLjQ3NTswLjYyNTswLjc1OzAuODc1OzEiIGR1cj0iMXMiIHJlcGVhdENvdW50PSJpbmRlZmluaXRlIj48L2FuaW1hdGU+PC9jaXJjbGU+PC9zdmc+');
        background-size: contain;
        margin-bottom: 15px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .loading-text {
        color: #3498db;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display the animated loader with message
    st.markdown(f"""
    <div class="loader-container">
        <div class="dna-loader"></div>
        <div class="loading-text">{text}</div>
    </div>
    """, unsafe_allow_html=True)

# Streamlit UI

def load_summary_from_s3(filename):
    s3 = boto3.client(
        's3',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
        aws_secret_access_key=st.secrets["AWS_SECRET_KEY"],
        region_name=st.secrets.get("AWS_REGION", "us-east-1")
    )
    key = f"summaries/{filename}-summary.txt"
    st.write("📂 Looking for summary at:", key)
    try:
        obj = s3.get_object(Bucket=st.secrets["S3_BUCKET_PROC"], Key=key)
        return obj["Body"].read().decode("utf-8")
    except Exception as e:
        return f"⏳ Summary not available yet. (EC2 may still be processing)\n\nError: {e}"
    
def notify_ec2_to_process(filename):         
    s3 = boto3.client(
        's3',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
        aws_secret_access_key=st.secrets["AWS_SECRET_KEY"],
        region_name=st.secrets.get("AWS_REGION", "us-east-1")
    )
    s3.put_object(
        Bucket=st.secrets["S3_BUCKET_PROC"],
        Key=f"to-process/{filename}.txt",
        Body=filename.encode('utf-8')
    )

def main():
    st.set_page_config(
        page_title="HealthInsight - Bloodwork Analyzer",
        page_icon="🩸",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""<style> .main {background-color: #f8f9fa;} .stApp {max-width: 1200px; margin: 0 auto;} </style>""", unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=HealthInsight", width=150)
        st.title("HealthInsight")
        st.markdown("## Bloodwork Analyzer")
        st.markdown("Understand your lab results without the extra copay.")
        st.markdown("---")
        st.markdown("### How it works")
        st.markdown("""
        1. Upload your bloodwork CSV file 
        2. Our system analyzes your results 
        3. View visualizations and explanations 
        4. Track changes over time 
        """)
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        HealthInsight helps you understand your blood test results through
        data visualization and plain-language explanations.

        This tool is for educational purposes only and does not provide medical advice.
        """)

    # Main UI
    st.title("Bloodwork Analysis Dashboard")
    st.markdown("Upload your blood test results to visualize and better understand your health data")

    st.markdown("### Upload Your Blood Test Results")
    st.markdown("Upload a CSV with test names, results, and reference ranges.")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    use_sample = st.checkbox("Use sample data instead")

    df = None

    if uploaded_file or use_sample:
        if uploaded_file:
            notify_ec2_to_process(uploaded_file.name)

            st.success("File successfully uploaded!")
            file_bytes = uploaded_file.read()
            file_buffer = io.BytesIO(file_bytes)

            # Upload to S3
            st.info("Uploading file to secure cloud storage (S3)...")
            success = upload_to_s3(
                file_buffer=file_buffer,
                filename=uploaded_file.name,
                bucket=st.secrets["S3_BUCKET_RAW"],
                aws_access_key=st.secrets["AWS_ACCESS_KEY"],
                aws_secret_key=st.secrets["AWS_SECRET_KEY"],
                region=st.secrets.get("AWS_REGION", "us-east-1")
            )

            if success:
                st.success("File successfully uploaded to S3.")

            # Read CSV
            with st.spinner("Processing your bloodwork data..."):
                time.sleep(2)
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes))
                    st.success(f"Successfully read {len(df)} test results.")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
                    st.stop()

        elif use_sample:
            st.info("Using sample bloodwork data...")
            time.sleep(1)
            df = pd.DataFrame({
                'panel_category': [
                    'CBC', 'CBC', 'CBC',
                    'CMP', 'Lipid Panel', 'Lipid Panel', 'Lipid Panel', 'Lipid Panel'
                ],
                'test_name': [
                    'Hemoglobin', 'White Blood Cells', 'Platelets',
                    'Glucose', 'Total Cholesterol', 'HDL Cholesterol', 'LDL Cholesterol', 'Triglycerides'
                ],
                'date': ['2023-05-15'] * 8,
                'value': [14.2, 6.8, 250.0, 92.0, 185.0, 55.0, 110.0, 120.0],
                'unit': ['g/dL', 'k/μL', 'k/μL', 'mg/dL', 'mg/dL', 'mg/dL', 'mg/dL', 'mg/dL'],
                'reference_range': [
                    '13.0-17.0', '4.5-11.0', '150.0-450.0',
                    '70.0-99.0', '< 200.0', '> 40.0', '< 130.0', '< 150.0'
                ]
            })

            sample_buffer = io.BytesIO(df.to_csv(index=False).encode('utf-8'))
            upload_to_s3(
                sample_buffer,
                filename="sample_data.csv",
                bucket=st.secrets["S3_BUCKET_PROC"],
                aws_access_key=st.secrets["AWS_ACCESS_KEY"],
                aws_secret_key=st.secrets["AWS_SECRET_KEY"]
            )
            st.success("Sample data uploaded to S3.")

        # Data Preview
        st.markdown("### Data Preview")
        st.dataframe(df)

        if st.button("Generate Visualizations and Summary"):
            st.markdown("### Summary and Insights")

            summary = ""
            if uploaded_file:
                summary = load_summary_from_s3(uploaded_file.name)
                st.subheader("💬 LLM Summary")
                st.write("🔎 Looking for summary key:", f"summaries/{uploaded_file.name}-summary.txt")
                st.text_area("Explanation", summary, height=300)


            plot_buf = generate_result_plot(df)
            st.image(plot_buf)

            save_to_rds(summary, plot_buf.getvalue(), uploaded_file.name if uploaded_file else "sample_data.csv")

            st.success("Summary and plot saved to database.")

    else:
        st.info("Please upload a CSV file or select the sample data option to continue.")

    # Disclaimer
    st.markdown("---")
    st.markdown("**Disclaimer:** This tool is for educational and informational purposes only. It is not intended to provide medical advice.")

if __name__ == "__main__":
    main()
