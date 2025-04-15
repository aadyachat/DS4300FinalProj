import streamlit as st
import pandas as pd
import time
import boto3
from botocore.exceptions import NoCredentialsError
import io


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


   df = None  # Placeholder for the data


   if uploaded_file or use_sample:
       if uploaded_file:
           st.success("File successfully uploaded!")


           # Read content once into memory
           file_bytes = uploaded_file.read()
           file_buffer = io.BytesIO(file_bytes)


           # Upload to S3
           st.info("Uploading file to secure cloud storage (S3)...")
           success = upload_to_s3(
               file_buffer=file_buffer,
               filename=uploaded_file.name,
               bucket=st.secrets["S3_BUCKET"],
               aws_access_key=st.secrets["AWS_ACCESS_KEY"],
               aws_secret_key=st.secrets["AWS_SECRET_KEY"],
               region=st.secrets.get("AWS_REGION", "us-east-1")
           )


           if success:
               st.success("File successfully uploaded to S3.")


           # Load into DataFrame
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
               'Test': ['Hemoglobin', 'White Blood Cells', 'Platelets', 'Glucose', 'Cholesterol', 'HDL', 'LDL', 'Triglycerides'],
               'Result': [14.2, 6.8, 250, 92, 185, 55, 110, 120],
               'Lower Limit': [13.0, 4.5, 150, 70, None, 40, None, None],
               'Upper Limit': [17.0, 11.0, 450, 99, 200, 60, 130, 150],
               'Units': ['g/dL', 'k/μL', 'k/μL', 'mg/dL', 'mg/dL', 'mg/dL', 'mg/dL', 'mg/dL'],
               'Date': ['2023-05-15'] * 8
           })


           # Upload sample data to S3
           sample_buffer = io.BytesIO(df.to_csv(index=False).encode('utf-8'))
           upload_to_s3(
               sample_buffer,
               filename="sample_data.csv",
               bucket=st.secrets["S3_BUCKET"],
               aws_access_key=st.secrets["AWS_ACCESS_KEY"],
               aws_secret_key=st.secrets["AWS_SECRET_KEY"]
           )
           st.success("Sample data uploaded to S3.")


       # Show preview and next steps
       st.markdown("### Data Preview")
       st.dataframe(df)


       if st.button("Generate Visualizations"):
           st.markdown("### Future Visualization Placeholders")
           col1, col2 = st.columns(2)


           with col1:
               st.markdown("#### Results vs. Reference Ranges")
               st.image("https://via.placeholder.com/400x300.png?text=Results+Chart")


           with col2:
               st.markdown("#### Historical Trends")
               st.image("https://via.placeholder.com/400x300.png?text=Trends+Chart")


           st.markdown("#### Biomarker Correlations")
           st.image("https://via.placeholder.com/800x400.png?text=Correlation+Chart")


   else:
       st.info("Please upload a CSV file or select the sample data option to continue.")


   # Disclaimer
   st.markdown("---")
   st.markdown("**Disclaimer:** This tool is for educational and informational purposes only. It is not intended to provide medical advice.")


if __name__ == "__main__":
   main()