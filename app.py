import yfinance as yf
import streamlit as st
import pandas as pd
import time

def main():
    """Main function to run the Streamlit app"""
    # Page configuration
    st.set_page_config(
        page_title="HealthInsight - Bloodwork Analyzer",
        page_icon="🩸",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for a more professional look
    st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .upload-section {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .header-section {
            margin-bottom: 2rem;
        }
        .info-section {
            background-color: #e9f7fe;
            border-left: 4px solid #3498db;
            padding: 1.5rem;
            border-radius: 0 10px 10px 0;
            margin-bottom: 2rem;
        }
        .disclaimer-section {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            border-radius: 0 5px 5px 0;
            font-size: 0.9rem;
            margin-top: 2rem;
        }
        h1 {
            color: #2c3e50;
            font-weight: 700;
        }
        h2, h3 {
            color: #34495e;
        }
    </style>
    """, unsafe_allow_html=True)

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
        
        This tool is for educational purposes only and does not provide
        medical advice.
        """)

    # Main content
    st.markdown('<div class="header-section">', unsafe_allow_html=True)
    st.title("Bloodwork Analysis Dashboard")
    st.markdown("Upload your blood test results to visualize and better understand your health data")
    st.markdown('</div>', unsafe_allow_html=True)

    # Information section
    st.markdown('<div class="info-section">', unsafe_allow_html=True)
    st.markdown("""
    ### Why Use HealthInsight?

    Many people receive blood test results but don't fully understand what the numbers mean or how they change over time.
    HealthInsight helps you:

    - **Visualize** your results in an easy-to-understand format
    - **Track** changes in your bloodwork over time
    - **Compare** your results to standard reference ranges
    - **Understand** what each biomarker means for your health

    No medical background required - just upload your data and gain insights.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.header("Upload Your Blood Test Results")

    st.markdown("""
    Please upload your bloodwork results in CSV format. The file should contain:
    - Test names/biomarkers
    - Your results
    - Reference/normal ranges (if available)
    - Date of the test
    """)

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file containing your blood test results",
        type="csv",
        help="The file must be in CSV format. Most labs can provide your results in this format upon request."
    )

    # Sample data option
    st.markdown("#### Don't have a file ready?")
    use_sample = st.checkbox("Use sample data instead")

    # Processing logic
    if uploaded_file is not None or use_sample:
        
        if uploaded_file is not None:
            st.success("File successfully uploaded!")
            # Here you would process the actual uploaded file
            # For now, we'll just show a processing indicator
            
            with st.spinner('Processing your bloodwork data...'):
                time.sleep(2)  # Simulate processing time
                st.markdown("#### File details:")
                file_details = {
                    "Filename": uploaded_file.name,
                    "File size": f"{round(uploaded_file.size/1024, 2)} KB",
                    "Upload time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                for k, v in file_details.items():
                    st.write(f"**{k}:** {v}")
                    
                # Here we would actually read and validate the CSV
                try:
                    df = pd.read_csv(uploaded_file)
                    st.write(f"Successfully read {len(df)} test results.")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                    st.stop()
                    
        elif use_sample:
            st.info("Using sample bloodwork data for demonstration")
            with st.spinner('Loading sample data...'):
                time.sleep(1)  # Simulate loading time
                
                # Create sample data
                df = pd.DataFrame({
                    'Test': ['Hemoglobin', 'White Blood Cells', 'Platelets', 'Glucose', 'Cholesterol', 'HDL', 'LDL', 'Triglycerides'],
                    'Result': [14.2, 6.8, 250, 92, 185, 55, 110, 120],
                    'Lower Limit': [13.0, 4.5, 150, 70, None, 40, None, None],
                    'Upper Limit': [17.0, 11.0, 450, 99, 200, 60, 130, 150],
                    'Units': ['g/dL', 'k/μL', 'k/μL', 'mg/dL', 'mg/dL', 'mg/dL', 'mg/dL', 'mg/dL'],
                    'Date': ['2023-05-15', '2023-05-15', '2023-05-15', '2023-05-15', '2023-05-15', '2023-05-15', '2023-05-15', '2023-05-15']
                })
        
        # Show next steps - this is where we would add visualization code in the future
        st.markdown("### Next Steps")
        st.info("Your data is ready for analysis. In the full application, interactive visualizations and interpretations would appear here.")
        
        # Preview of the data
        st.markdown("### Data Preview")
        st.dataframe(df)
        
        # Placeholder for future visualization - just showing a button for now
        if st.button("Generate Visualizations"):
            st.markdown("### Future Visualization Placeholders")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Results vs. Reference Ranges")
                st.image("https://via.placeholder.com/400x300.png?text=Results+Chart")
                
            with col2:
                st.markdown("#### Historical Trends")
                st.image("https://via.placeholder.com/400x300.png?text=Trends+Chart")

            # Add more future visualization placeholders as needed
            st.markdown("#### Biomarker Correlations")
            st.image("https://via.placeholder.com/800x400.png?text=Correlation+Chart")
    else:
        st.info("Please upload a CSV file or select the sample data option to continue.")

    # Medical disclaimer
    st.markdown('<div class="disclaimer-section">', unsafe_allow_html=True)
    st.markdown("""
    **Disclaimer:** This tool is for educational and informational purposes only. It is not intended to provide medical advice, diagnosis, 
    or treatment. Always consult with a qualified healthcare provider regarding any medical questions or conditions. 
    The creators of this tool are not responsible for any health decisions made based on its output.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("Not for Clinical Use")

# This is the standard boilerplate that calls the main function.
if __name__ == '__main__':
    main()