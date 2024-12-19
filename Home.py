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
    # Load referral and appointment data
    referral_df = pd.read_csv("data/waiting_list_opa.csv")
    appointment_df = pd.read_csv("data/appointments_opa.csv")

    # Save loaded data to session state
    st.session_state.referral_df = referral_df
    st.session_state.appointment_df = appointment_df

    # Initialize selected specialty if not already set in session state
    if 'selected_specialty' not in st.session_state:
        st.session_state.selected_specialty = None

    # Set available specialties from the referral data
    specialties = referral_df['specialty'].unique()

    # Let the user select a specialty
    if st.session_state.selected_specialty is None:
        st.session_state.selected_specialty = specialties[0]  # Default to the first specialty

    selected_specialty = st.selectbox('Select Specialty', specialties, index=list(specialties).index(st.session_state.selected_specialty))
    
    # Save the selected specialty to session state
    st.session_state.selected_specialty = selected_specialty

    # Display a preview of the referral data
    st.subheader("Waiting List Data Preview")
    st.write("Here are the first few rows of the Waiting List Data:")
    st.dataframe(referral_df.head())

    # Display a preview of the appointment data
    st.subheader("Appointment Data Preview")
    st.write("Here are the first few rows of the Appointment Data:")
    st.dataframe(appointment_df.head())

except FileNotFoundError as e:
    st.error(f"Error loading data: {e}. Please ensure the CSV files are located in the correct directory.")

st.sidebar.header('Data Files Loaded Successfully')
