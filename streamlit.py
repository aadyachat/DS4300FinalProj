import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

# Connect to RDS
conn = psycopg2.connect(
    host='your-rds-endpoint',
    database='your-db-name',
    user='your-username',
    password='your-password'
)

df = pd.read_sql("SELECT * FROM lab_results", conn)

st.title("🩺 Lab Results Dashboard")
st.dataframe(df)

# Bar chart: value vs. normal range
st.subheader("Test Results Overview")
fig, ax = plt.subplots(figsize=(10, 5))
df.plot(kind='bar', x='test_name', y='value', ax=ax)
st.pyplot(fig)

# Show explanation
st.subheader("Health Summary")
explanations = df['explanation'].unique()
for exp in explanations:
    st.write(exp)

conn.close()
