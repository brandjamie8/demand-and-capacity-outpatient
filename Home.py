import streamlit as st
import pandas as pd

st.set_page_config(
    page_title='Outpatient Demand and Capacity Analysis',
    page_icon='📊',
    layout='wide'
)

st.title('Welcome to the Outpatient Demand and Capacity Analysis App')

st.write("""
This application allows you to analyse outpatient (non-admitted) demand and capacity, focusing on specialties and appointments.
Use the navigation on the left to select different sections of the analysis.
""")

# Load data from CSV files (located in the same directory as this script or in a data folder in the repository)
try:
    # Load referral data
    referral_df = pd.read_csv("data/referral_data_trended.csv")
    appointment_df = pd.read_csv("data/appointment_data_trended.csv")

    # Save loaded data to session state
    st.session_state.referral_df = referral_df
    st.session_state.appointment_df = appointment_df

    # Display a preview of the referral data
    st.subheader("Referral Data Preview")
    st.write("Here are the first few rows of the Referral Data:")
    st.dataframe(referral_df.head())

    # Display a preview of the appointment data
    st.subheader("Appointment Data Preview")
    st.write("Here are the first few rows of the Appointment Data:")
    st.dataframe(appointment_df.head())

except FileNotFoundError as e:
    st.error(f"Error loading data: {e}. Please ensure the CSV files are located in the correct directory.")

st.sidebar.header('Data Files Loaded Successfully')
