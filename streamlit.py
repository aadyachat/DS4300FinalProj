import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

# Load RDS credentials from secrets.toml
rds_config = {
    "host": st.secrets["RDS_HOST"],
    "database": st.secrets["RDS_DB"],
    "user": st.secrets["RDS_USER"],
    "password": st.secrets["RDS_PASSWORD"],
    "port": st.secrets.get("RDS_PORT", 5432)  # optional
}

# Connect to RDS
@st.cache_resource(ttl=600)
def get_connection():
    return psycopg2.connect(**rds_config)

conn = get_connection()

# Load data
@st.cache_data(ttl=300)
def fetch_data():
    return pd.read_sql("SELECT * FROM lab_results", conn)

df = fetch_data()

# Streamlit UI
st.title("🩺 Lab Results Dashboard")
st.dataframe(df)

# Bar chart
st.subheader("Test Results Overview")
fig, ax = plt.subplots(figsize=(10, 5))
df.plot(kind='bar', x='test_name', y='value', ax=ax)
st.pyplot(fig)

# Health summary
st.subheader("Health Summary")
explanations = df['explanation'].unique()
for exp in explanations:
    st.write(exp)

conn.close()
