import streamlit as st
import pandas as pd
import time
import boto3
from botocore.exceptions import NoCredentialsError
import io
import matplotlib.pyplot as plt
import psycopg2
from psycopg2 import sql
import plotly.express as px
import plotly.graph_objects as go


# helper function for upload
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


# Generate visualization of results
def generate_result_plot(df):
   # Keep original plot logic but enhance it
   fig, ax = plt.subplots(figsize=(10, 5))
   bars = ax.bar(df['test_name'], df['value'], color='skyblue')
   ax.set_ylabel('Result')
   ax.set_title('Blood Test Results')
   ax.set_xticklabels(df['test_name'], rotation=45, ha='right')
  
   # Add reference range lines if available
   if 'reference_range' in df.columns:
       for i, (_, row) in enumerate(df.iterrows()):
           try:
               range_str = row['reference_range']
               if '<' in range_str:
                   # Handle formats like "< 200.0"
                   threshold = float(range_str.replace('<', '').strip())
                   ax.axhline(y=threshold, color='r', linestyle='--', alpha=0.3)
               elif '>' in range_str:
                   # Handle formats like "> 40.0"
                   threshold = float(range_str.replace('>', '').strip())
                   ax.axhline(y=threshold, color='g', linestyle='--', alpha=0.3)
               elif '-' in range_str:
                   # Handle ranges like "13.0-17.0"
                   lower, upper = map(float, range_str.split('-'))
                   ax.plot([i-0.4, i+0.4], [lower, lower], 'g--', alpha=0.5)
                   ax.plot([i-0.4, i+0.4], [upper, upper], 'r--', alpha=0.5)
           except:
               pass
  
   # Color bars based on reference range
   for i, (_, row) in enumerate(df.iterrows()):
       try:
           range_str = row['reference_range']
           value = row['value']
           if '<' in range_str:
               threshold = float(range_str.replace('<', '').strip())
               if value > threshold:
                   bars[i].set_color('salmon')
               else:
                   bars[i].set_color('lightgreen')
           elif '>' in range_str:
               threshold = float(range_str.replace('>', '').strip())
               if value < threshold:
                   bars[i].set_color('salmon')
               else:
                   bars[i].set_color('lightgreen')
           elif '-' in range_str:
               lower, upper = map(float, range_str.split('-'))
               if lower <= value <= upper:
                   bars[i].set_color('lightgreen')
               else:
                   bars[i].set_color('salmon')
       except:
           pass
  
   fig.tight_layout()
   buf = io.BytesIO()
   plt.savefig(buf, format='png')
   buf.seek(0)
   return buf


# Create additional visualizations
def create_panel_distribution(df):
   """Create a pie chart of test distribution by panel category"""
   if 'panel_category' in df.columns:
       panel_counts = df['panel_category'].value_counts().reset_index()
       panel_counts.columns = ['Category', 'Count']
      
       fig = px.pie(panel_counts, values='Count', names='Category',
                    title='Distribution of Tests by Panel',
                    color_discrete_sequence=px.colors.qualitative.Pastel)
       fig.update_traces(textposition='inside', textinfo='percent+label')
       return fig
   return None


def create_range_status_visualization(df):
   """Create a visualization showing which values are in/out of range"""
   if 'reference_range' not in df.columns:
       return None
      
   # Create a new status column
   statuses = []
   for i, row in df.iterrows():
       try:
           range_str = row['reference_range']
           value = row['value']
          
           if '<' in range_str:
               threshold = float(range_str.replace('<', '').strip())
               if value > threshold:
                   statuses.append('Above Range')
               else:
                   statuses.append('Normal')
           elif '>' in range_str:
               threshold = float(range_str.replace('>', '').strip())
               if value < threshold:
                   statuses.append('Below Range')
               else:
                   statuses.append('Normal')
           elif '-' in range_str:
               lower, upper = map(float, range_str.split('-'))
               if value < lower:
                   statuses.append('Below Range')
               elif value > upper:
                   statuses.append('Above Range')
               else:
                   statuses.append('Normal')
           else:
               statuses.append('Unknown')
       except:
           statuses.append('Unknown')
  
   status_df = pd.DataFrame({
       'Test': df['test_name'],
       'Status': statuses
   })
  
   # Count the number in each category
   status_counts = status_df['Status'].value_counts().reset_index()
   status_counts.columns = ['Status', 'Count']
  
   # Define colors for each status
   colors = {
       'Normal': 'lightgreen',
       'Above Range': 'salmon',
       'Below Range': 'lightskyblue',
       'Unknown': 'lightgray'
   }
  
   fig = px.bar(status_counts, x='Status', y='Count',
                title='Test Results Status',
                color='Status',
                color_discrete_map=colors)
  
   return fig


def create_test_gauge_charts(df):
   """Create gauge charts for each test showing where the value falls in the reference range"""
   if 'reference_range' not in df.columns:
       return None
  
   figs = []
   for i, row in df.iterrows():
       try:
           test_name = row['test_name']
           value = row['value']
           range_str = row['reference_range']
          
           # Determine range for gauge
           if '<' in range_str:
               threshold = float(range_str.replace('<', '').strip())
               min_val = 0  # Assume 0 as minimum
               max_val = threshold * 2  # Double the threshold as maximum
              
               # Define the color thresholds
               green_threshold = threshold
               yellow_threshold = threshold * 1.5
              
               # Create gauge
               fig = go.Figure(go.Indicator(
                   mode = "gauge+number",
                   value = value,
                   domain = {'x': [0, 1], 'y': [0, 1]},
                   title = {'text': test_name},
                   gauge = {
                       'axis': {'range': [min_val, max_val]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [min_val, green_threshold], 'color': "lightgreen"},
                           {'range': [green_threshold, yellow_threshold], 'color': "gold"},
                           {'range': [yellow_threshold, max_val], 'color': "salmon"}
                       ],
                       'threshold': {
                           'line': {'color': "red", 'width': 4},
                           'thickness': 0.75,
                           'value': threshold
                       }
                   }
               ))
              
           elif '>' in range_str:
               threshold = float(range_str.replace('>', '').strip())
               min_val = 0  # Assume 0 as minimum
               max_val = threshold * 2  # Double the threshold as maximum
              
               # Define the color thresholds
               green_threshold = threshold
              
               # Create gauge
               fig = go.Figure(go.Indicator(
                   mode = "gauge+number",
                   value = value,
                   domain = {'x': [0, 1], 'y': [0, 1]},
                   title = {'text': test_name},
                   gauge = {
                       'axis': {'range': [min_val, max_val]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [min_val, threshold/2], 'color': "salmon"},
                           {'range': [threshold/2, threshold], 'color': "gold"},
                           {'range': [threshold, max_val], 'color': "lightgreen"}
                       ],
                       'threshold': {
                           'line': {'color': "green", 'width': 4},
                           'thickness': 0.75,
                           'value': threshold
                       }
                   }
               ))
              
           elif '-' in range_str:
               lower, upper = map(float, range_str.split('-'))
               min_val = max(0, lower - (upper - lower))  # Ensure min is not negative
               max_val = upper + (upper - lower)
              
               # Create gauge
               fig = go.Figure(go.Indicator(
                   mode = "gauge+number",
                   value = value,
                   domain = {'x': [0, 1], 'y': [0, 1]},
                   title = {'text': test_name},
                   gauge = {
                       'axis': {'range': [min_val, max_val]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [min_val, lower], 'color': "salmon"},
                           {'range': [lower, upper], 'color': "lightgreen"},
                           {'range': [upper, max_val], 'color': "salmon"}
                       ],
                       'threshold': {
                           'line': {'color': "red", 'width': 4},
                           'thickness': 0.75,
                           'value': value
                       }
                   }
               ))
           else:
               continue
              
           fig.update_layout(height=250)
           figs.append(fig)
       except:
           continue
  
   return figs


# Function to display custom loading animation
def display_loading_animation(text="Processing..."):
   # Custom CSS for animated loading indicator
   st.markdown("""
   <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;">
       <svg width="60" height="60" viewBox="0 0 50 50">
           <path fill="#3498db" d="M25,5A20.14,20.14,0,0,1,45,22.88a2.51,2.51,0,0,0,2.49,2.26h0A2.52,2.52,0,0,0,50,22.33a25.14,25.14,0,0,0-50,0,2.52,2.52,0,0,0,2.5,2.81h0A2.51,2.51,0,0,0,5,22.88,20.14,20.14,0,0,1,25,5Z">
               <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.6s" repeatCount="indefinite"/>
           </path>
       </svg>
       <div style="color: #3498db; font-size: 18px; font-weight: bold; text-align: center; margin-top: 15px;">
           {text}
       </div>
   </div>
   """.format(text=text), unsafe_allow_html=True)


# Keep original RDS/S3 functions
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


def load_summary_from_s3(filename):
   s3 = boto3.client(
       's3',
       aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
       aws_secret_access_key=st.secrets["AWS_SECRET_KEY"],
       region_name=st.secrets.get("AWS_REGION", "us-east-1")
   )
   key = f"summaries/{filename}-summary.txt"
   try:
       obj = s3.get_object(Bucket=st.secrets["S3_BUCKET_NORMAL"], Key=key)
       return obj["Body"].read().decode("utf-8")
   except Exception as e:
       return f"⏳ Summary not available yet. (EC2 may still be processing)\n\nError: {e}"
  
def notify_ec2_to_process(filename):        
   s3 = boto3.client(
       's3',
       aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
       aws_secret_access_key=st.secrets["AWS_SECRET_KEY"],
       region_name=st.secrets.get("AWS_REGION", "us-east-2")
   )
   s3.put_object(
       Bucket=st.secrets["S3_BUCKET_NORMAL"],
       Key=f"to-process/{filename}.txt",
       Body=filename.encode('utf-8')
   )


# Main UI Function
def main():
   st.set_page_config(
       page_title="HealthInsight - Bloodwork Analyzer",
       page_icon="🩸",
       layout="wide",
       initial_sidebar_state="expanded",
   )


   # Custom CSS for styling
   st.markdown("""
   <style>
       /* Main background and text colors */
       .main {
           background-color: #f8f9fa;
           color: #2c3e50;
       }
      
       /* Header styling */
       h1, h2, h3 {
           color: #3498db;
           font-family: 'Helvetica Neue', sans-serif;
       }
      
       /* Button styling */
       .stButton>button {
           background-color: #3498db;
           color: white;
           border-radius: 5px;
           border: none;
           padding: 10px 24px;
           font-weight: bold;
           transition: all 0.3s;
       }
      
       .stButton>button:hover {
           background-color: #2980b9;
           box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
       }
      
       /* Card-like containers */
       .css-1r6slb0 {
           border-radius: 10px;
           background-color: white;
           padding: 15px;
           box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
           margin-bottom: 15px;
       }
      
       /* Status indicators */
       .normal-status {
           color: #27ae60;
           font-weight: bold;
       }
      
       .warning-status {
           color: #f39c12;
           font-weight: bold;
       }
      
       .alert-status {
           color: #e74c3c;
           font-weight: bold;
       }
      
       /* File uploader styling */
       .uploadFile {
           border: 2px dashed #3498db;
           border-radius: 10px;
           padding: 15px;
       }
      
       /* Sidebar adjustments */
       .css-1aumxhk {
           background-color: #2c3e50;
       }
      
       /* Dataframe styling */
       .dataframe {
           border-radius: 5px;
           overflow: hidden;
           border: none;
       }
      
       /* Expander styling */
       .streamlit-expanderHeader {
           background-color: #f1f7fd;
           border-radius: 5px;
       }
      
       /* Footer */
       .footer {
           margin-top: 20px;
           padding-top: 10px;
           border-top: 1px solid #e0e0e0;
           text-align: center;
           font-size: 14px;
           color: #7f8c8d;
       }
      
       /* Glossary styling */
       .glossary-item {
           margin-bottom: 10px;
       }
      
       .glossary-term {
           font-weight: bold;
           color: #3498db;
       }
   </style>
   """, unsafe_allow_html=True)


   # Sidebar
   with st.sidebar:
       # Use inline SVG instead of external URL for logo
       st.markdown("""
       <div style="display: flex; justify-content: center; margin-bottom: 20px;">
           <svg width="150" height="150" viewBox="0 0 150 150" xmlns="http://www.w3.org/2000/svg">
               <circle cx="75" cy="75" r="70" fill="#3498db" />
               <path d="M75,30 L75,120 M45,50 L105,50 M45,100 L105,100" stroke="white" stroke-width="8" stroke-linecap="round" />
               <circle cx="75" cy="75" r="15" fill="white" />
               <path d="M45,75 C45,60 105,60 105,75 C105,90 45,90 45,75 Z" fill="#e74c3c" opacity="0.7" />
           </svg>
       </div>
       """, unsafe_allow_html=True)
      
       st.title("HealthInsight")
       st.markdown("## Bloodwork Analyzer")
       st.markdown("Understand your lab results without the extra copay.")
       st.markdown("---")
      
       st.markdown("### How it works")
       st.markdown("""
       <div style="background-color: rgba(52, 152, 219, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
           <div style="display: flex; align-items: center; margin-bottom: 8px;">
               <div style="background-color: #3498db; color: white; width: 24px; height: 24px; border-radius: 12px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">1</div>
               <div>Upload your bloodwork CSV file</div>
           </div>
       </div>
      
       <div style="background-color: rgba(52, 152, 219, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
           <div style="display: flex; align-items: center; margin-bottom: 8px;">
               <div style="background-color: #3498db; color: white; width: 24px; height: 24px; border-radius: 12px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">2</div>
               <div>Our system analyzes your results</div>
           </div>
       </div>
      
       <div style="background-color: rgba(52, 152, 219, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
           <div style="display: flex; align-items: center; margin-bottom: 8px;">
               <div style="background-color: #3498db; color: white; width: 24px; height: 24px; border-radius: 12px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">3</div>
               <div>View visualizations and explanations</div>
           </div>
       </div>
      
       <div style="background-color: rgba(52, 152, 219, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
           <div style="display: flex; align-items: center; margin-bottom: 8px;">
               <div style="background-color: #3498db; color: white; width: 24px; height: 24px; border-radius: 12px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">4</div>
               <div>Track changes over time</div>
           </div>
       </div>
       """, unsafe_allow_html=True)
      
       st.markdown("---")
      
       st.markdown("### About")
       st.markdown("""
       HealthInsight helps you understand your blood test results through
       data visualization and plain-language explanations.


       This tool is for educational purposes only and does not provide medical advice.
       """)
      
       # Add a glossary in a expandable section
       with st.expander("📚 Medical Terms Glossary"):
           st.markdown("""
           <div class="glossary-item">
               <span class="glossary-term">CBC:</span> Complete Blood Count - measures different cells in your blood
           </div>
          
           <div class="glossary-item">
               <span class="glossary-term">CMP:</span> Comprehensive Metabolic Panel - measures kidney function, liver function, etc.
           </div>
          
           <div class="glossary-item">
               <span class="glossary-term">Hemoglobin:</span> Protein in red blood cells that carries oxygen
           </div>
          
           <div class="glossary-item">
               <span class="glossary-term">LDL:</span> Low-Density Lipoprotein - often called "bad cholesterol"
           </div>
          
           <div class="glossary-item">
               <span class="glossary-term">HDL:</span> High-Density Lipoprotein - often called "good cholesterol"
           </div>
           """, unsafe_allow_html=True)


   # Main UI
   col1, col2 = st.columns([2, 1])
  
   with col1:
       st.markdown("""
       <h1 style="color: #3498db; margin-bottom: 0px;">
           <span style="font-size: 36px;">📊</span> Bloodwork Analysis Dashboard
       </h1>
       """, unsafe_allow_html=True)
  
   with col2:
       st.markdown("""
       <div style="background-color: #f1f7fd; padding: 10px; border-radius: 5px; text-align: center; margin-top: 10px;">
           <span style="color: #3498db; font-weight: bold;">💡 Tip:</span> Have your CSV ready with columns for test names, values, and reference ranges
       </div>
       """, unsafe_allow_html=True)
  
   st.markdown("""
   <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 20px;">
       <h3 style="color: #3498db; margin-top: 0;">📄 Upload Your Blood Test Results</h3>
       <p>Upload a CSV with test names, results, and reference ranges to visualize and better understand your health data.</p>
   </div>
   """, unsafe_allow_html=True)


   # File upload section with better styling
   upload_col1, upload_col2 = st.columns([3, 1])
  
   with upload_col1:
       uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
  
   with upload_col2:
       use_sample = st.checkbox("Use sample data", help="Use our sample data if you don't have a CSV file")


   df = None


   if uploaded_file or use_sample:
       if uploaded_file:
           notify_ec2_to_process(uploaded_file.name)


           st.success("✅ File successfully uploaded!")
           file_bytes = uploaded_file.read()
           file_buffer = io.BytesIO(file_bytes)


           # Upload to S3
           with st.spinner("☁️ Uploading file to secure cloud storage..."):
               success = upload_to_s3(
                   file_buffer=file_buffer,
                   filename=uploaded_file.name,
                   bucket=st.secrets["S3_BUCKET_RAW"],
                   aws_access_key=st.secrets["AWS_ACCESS_KEY"],
                   aws_secret_key=st.secrets["AWS_SECRET_KEY"],
                   region=st.secrets.get("AWS_REGION", "us-east-1")
               )


               if success:
                   st.success("🔒 File securely stored in cloud database")


           # Read CSV
           with st.spinner("🔍 Processing your bloodwork data..."):
               try:
                   df = pd.read_csv(io.BytesIO(file_bytes))
                   st.success(f"📊 Successfully analyzed {len(df)} test results")
               except Exception as e:
                   st.error(f"❌ Error reading CSV: {e}")
                   st.stop()


       elif use_sample:
           st.info("🧪 Using sample bloodwork data...")
           # Create loading animation
           display_loading_animation("Preparing sample data...")
           time.sleep(1)
          
           df = pd.DataFrame({
               'panel_category': [
                   'CBC', 'CBC', 'CBC',
                   'CMP', 'CMP', 'CMP',
                   'Lipid Panel', 'Lipid Panel', 'Lipid Panel', 'Lipid Panel',
                   'Vitamins', 'Hormones'
               ],
               'test_name': [
                   'Hemoglobin', 'White Blood Cells', 'Platelets',
                   'Glucose', 'ALT', 'Creatinine',
                   'Total Cholesterol', 'HDL Cholesterol', 'LDL Cholesterol', 'Triglycerides',
                   'Vitamin D', 'TSH'
               ],
               'date': ['2023-05-15'] * 12,
               'value': [14.2, 6.8, 250.0,
                        92.0, 25.0, 0.9,
                        185.0, 55.0, 110.0, 120.0,
                        38.0, 2.5],
               'unit': ['g/dL', 'k/μL', 'k/μL',
                       'mg/dL', 'U/L', 'mg/dL',
                       'mg/dL', 'mg/dL', 'mg/dL', 'mg/dL',
                       'ng/mL', 'mIU/L'],
               'reference_range': [
                   '13.0-17.0', '4.5-11.0', '150.0-450.0',
                   '70.0-99.0', '7.0-55.0', '0.6-1.2',
                   '< 200.0', '> 40.0', '< 130.0', '< 150.0',
                   '30.0-100.0', '0.4-4.0'
               ]
           })


           sample_buffer = io.BytesIO(df.to_csv(index=False).encode('utf-8'))
           upload_to_s3(
               sample_buffer,
               filename="sample_data.csv",
               bucket=st.secrets["S3_BUCKET_NORMAL"],
               aws_access_key=st.secrets["AWS_ACCESS_KEY"],
               aws_secret_key=st.secrets["AWS_SECRET_KEY"]
           )
           st.success("📤 Sample data uploaded to S3")


       # Data Preview with nicer formatting
       st.markdown("""
       <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin: 20px 0;">
           <h3 style="color: #3498db; margin-top: 0;">📋 Data Preview</h3>
       </div>
       """, unsafe_allow_html=True)
      
       # Apply custom formatting to dataframe
       st.dataframe(df, use_container_width=True)
      
       # Button with better styling
       if st.button("Generate Visualizations and Summary", key="generate_button", help="Click to analyze your bloodwork data"):
           st.markdown("""
           <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-top: 20px;">
               <h3 style="color: #3498db; margin-top: 0;">🔍 Summary and Insights</h3>
           </div>
           """, unsafe_allow_html=True)
          
           # Create tabs for organizing visualizations - REMOVED OVERVIEW TAB
           tab1, tab2 = st.tabs(["📈 Detailed Analysis", "💬 Summary"])
          
           with tab1:
               st.markdown("### Detailed Test Analysis")
              
               # If panel categories exist, create a selectbox to filter by panel
               if 'panel_category' in df.columns:
                   panels = ['All Panels'] + sorted(df['panel_category'].unique().tolist())
                   selected_panel = st.selectbox("Select Test Panel", panels)
                  
                   if selected_panel != 'All Panels':
                       filtered_df = df[df['panel_category'] == selected_panel]
                   else:
                       filtered_df = df
               else:
                   filtered_df = df
              
               # Create gauge charts for each test
               st.markdown("### Individual Test Analysis")
               gauge_charts = create_test_gauge_charts(filtered_df)
               if gauge_charts:
                   # Display charts in a grid
                   col1, col2 = st.columns(2)
                   for i, fig in enumerate(gauge_charts):
                       if i % 2 == 0:
                           with col1:
                               st.plotly_chart(fig, use_container_width=True)
                       else:
                           with col2:
                               st.plotly_chart(fig, use_container_width=True)
              
               # Detailed results table with styling
               st.markdown("### Detailed Results Table")
              
               # Create a more visually informative table
               if 'reference_range' in filtered_df.columns:
                   # Create a status column
                   result_df = filtered_df.copy()
                   result_df['status'] = ""
                  
                   for i, row in result_df.iterrows():
                       try:
                           range_str = row['reference_range']
                           value = row['value']
                          
                           if '<' in range_str:
                               threshold = float(range_str.replace('<', '').strip())
                               if value <= threshold:
                                   result_df.at[i, 'status'] = "✅ Normal"
                               else:
                                   result_df.at[i, 'status'] = "⚠️ High"
                           elif '>' in range_str:
                               threshold = float(range_str.replace('>', '').strip())
                               if value >= threshold:
                                   result_df.at[i, 'status'] = "✅ Normal"
                               else:
                                   result_df.at[i, 'status'] = "⚠️ Low"
                           elif '-' in range_str:
                               lower, upper = map(float, range_str.split('-'))
                               if value < lower:
                                   result_df.at[i, 'status'] = "⚠️ Low"
                               elif value > upper:
                                   result_df.at[i, 'status'] = "⚠️ High"
                               else:
                                   result_df.at[i, 'status'] = "✅ Normal"
                           else:
                               result_df.at[i, 'status'] = "❓ Unknown"
                       except:
                           result_df.at[i, 'status'] = "❓ Unknown"
                  
                   # Display the styled dataframe
                   display_cols = ['test_name', 'value', 'unit', 'reference_range', 'status']
                   if 'panel_category' in result_df.columns:
                       display_cols = ['panel_category'] + display_cols
                  
                   st.dataframe(result_df[display_cols], use_container_width=True)
          
           with tab2:
               summary = ""
               if uploaded_file:
                   st.markdown("### 💬 AI-Generated Summary")
                   st.info("Looking for AI analysis of your bloodwork...")
                  
                   summary = load_summary_from_s3(uploaded_file.name)
                   st.markdown(f"""
                   <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                       <h4 style="color: #3498db; margin-top: 0;">Healthcare AI Analysis</h4>
                       <div style="margin-top: 15px; white-space: pre-line; color: #2c3e50;">
                           {summary}
                       </div>
                   </div>
                   """, unsafe_allow_html=True)
               else:
                   # Sample summary for demo purposes
                   st.markdown("### 💬 AI-Generated Summary")
                  
                   sample_summary = """
                   Based on the sample bloodwork results:
                  
                   ✅ Most values are within normal ranges, indicating generally good health
                  
                   🔍 Key observations:
                   - Glucose is in the normal range but near the upper limit
                   - HDL Cholesterol (good cholesterol) is at a healthy level
                   - LDL Cholesterol and Total Cholesterol are at acceptable levels
                  
                   💡 Suggestions:
                   - Continue regular monitoring of glucose levels
                   - Maintain current diet and exercise habits that support healthy cholesterol
                   - Consider discussing Vitamin D levels with your healthcare provider
                  
                   Remember: This is an educational analysis only and not medical advice. Always consult with your healthcare provider for proper interpretation of your lab results.
                   """
                  
                   st.markdown(f"""
                   <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                       <h4 style="color: #3498db; margin-top: 0;">Sample Healthcare AI Analysis</h4>
                       <div style="margin-top: 15px; white-space: pre-line; color: #2c3e50;">
                           {sample_summary}
                       </div>
                   </div>
                   """, unsafe_allow_html=True)
                  
                   summary = sample_summary
              
               # Add panel distribution to the summary tab
               if 'panel_category' in df.columns:
                   st.markdown("### Test Categories")
                   panel_fig = create_panel_distribution(df)
                   if panel_fig:
                       st.plotly_chart(panel_fig, use_container_width=True)
              
               # Save plot and summary to database
               plot_buf = generate_result_plot(df)
               save_to_rds(summary, plot_buf.getvalue(), uploaded_file.name if uploaded_file else "sample_data.csv")
              
               st.success("✅ Analysis complete! Summary and visualizations saved to database.")
              
               # Simple recommendations based on data
               st.markdown("### 🔍 Next Steps")
               st.markdown("""
               <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                   <div style="flex: 1; background-color: #f1f7fd; padding: 15px; border-radius: 10px; min-width: 200px;">
                       <h4 style="margin-top: 0; color: #3498db;">📋 Share with Provider</h4>
                       <p>Download this analysis to share with your healthcare provider at your next appointment.</p>
                   </div>
                  
                   <div style="flex: 1; background-color: #f1f7fd; padding: 15px; border-radius: 10px; min-width: 200px;">
                       <h4 style="margin-top: 0; color: #3498db;">📆 Follow Up</h4>
                       <p>Schedule regular blood tests to monitor your health trends over time.</p>
                   </div>
               </div>
               """, unsafe_allow_html=True)


   else:
       # Show helpful placeholder content
       st.info("Please upload a CSV file or select the sample data option to continue.")
      
       st.markdown("""
       <div style="background-color: #f1f7fd; padding: 20px; border-radius: 10px; margin-top: 20px;">
           <h4 style="color: #3498db; margin-top: 0;">CSV Format Guide</h4>
           <p>For best results, your CSV file should include these columns:</p>
           <ul>
               <li><strong>test_name</strong>: Name of the blood test (e.g., "Hemoglobin")</li>
               <li><strong>value</strong>: Your test result value</li>
               <li><strong>unit</strong>: Unit of measurement (e.g., "g/dL")</li>
               <li><strong>reference_range</strong>: Normal range for the test (e.g., "13.0-17.0")</li>
               <li><strong>panel_category</strong>: (Optional) Category of the test (e.g., "CBC")</li>
               <li><strong>date</strong>: (Optional) Date of the test</li>
           </ul>
       </div>
      
       <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-top: 20px;">
           <h4 style="color: #3498db; margin-top: 0;">Sample CSV Preview</h4>
           <div style="overflow-x: auto;">
               <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                   <thead style="background-color: #f1f7fd;">
                       <tr>
                           <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">panel_category</th>
                           <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">test_name</th>
                           <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">date</th>
                           <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">value</th>
                           <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">unit</th>
                           <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">reference_range</th>
                       </tr>
                   </thead>
                   <tbody>
                       <tr>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">CBC</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Hemoglobin</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">2023-05-15</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">14.2</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">g/dL</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">13.0-17.0</td>
                       </tr>
                       <tr>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Lipid Panel</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">LDL Cholesterol</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">2023-05-15</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">110.0</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">mg/dL</td>
                           <td style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">< 130.0</td>
                       </tr>
                   </tbody>
               </table>
           </div>
       </div>
       """, unsafe_allow_html=True)


   # Footer with disclaimer
   st.markdown("""
   <div class="footer">
       <p><strong>Disclaimer:</strong> This tool is for educational and informational purposes only. It is not intended to provide medical advice.</p>
       <p>© 2025 HealthInsight - Bloodwork Analyzer</p>
   </div>
   """, unsafe_allow_html=True)


if __name__ == "__main__":
   main()

