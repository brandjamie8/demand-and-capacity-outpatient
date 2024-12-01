import streamlit as st
import pandas as pd

st.set_page_config(
    page_title='Outpatient Demand and Capacity Analysis',
    page_icon='📊',
    layout='wide'
)

st.title('Welcome to the Outpatient Demand and Capacity Analysis App')

st.write("""
This application allows you to analyze outpatient (non-admitted) demand and capacity, focusing on specialties and appointments.
Use the navigation on the left to select different sections of the analysis.
""")

# Initialize session state variables
if 'referral_df' not in st.session_state:
    st.session_state.referral_df = None

if 'appointment_df' not in st.session_state:
    st.session_state.appointment_df = None

if 'selected_specialty' not in st.session_state:
    st.session_state.selected_specialty = None

# Sidebar Uploaders
st.sidebar.header('Upload Data Files')

referral_file = st.sidebar.file_uploader(
    "Upload Referral Data CSV",
    type='csv',
    key='referral_file'
)

appointment_file = st.sidebar.file_uploader(
    "Upload Appointment Data CSV",
    type='csv',
    key='appointment_file'
)

# Save uploaded files to session state
if referral_file is not None:
    st.session_state.referral_df = pd.read_csv(referral_file)
    st.subheader("Referral Data Preview")
    st.write("Here are the first few rows of the Referral Data:")
    st.dataframe(st.session_state.referral_df.head())
else:
    st.write("Please upload the **Referral Data CSV** file in the sidebar.")

if appointment_file is not None:
    st.session_state.appointment_df = pd.read_csv(appointment_file)
    st.subheader("Appointment Data Preview")
    st.write("Here are the first few rows of the Appointment Data:")
    st.dataframe(st.session_state.appointment_df.head())
else:
    st.write("Please upload the **Appointment Data CSV** file in the sidebar.")
