import streamlit as st
import pandas as pd

st.title("Capacity Analysis")

if 'appointment_df' in st.session_state and st.session_state.appointment_df is not None:
    appointment_df = st.session_state.appointment_df

    required_columns = ['month', 'specialty', 'appointment type', 'appointments completed', 'did not attend rate']
    if all(column in appointment_df.columns for column in required_columns):
        selected_specialty = st.session_state.selected_specialty

        # Filter appointment data based on the selected specialty
        specialty_appointment_df = appointment_df[appointment_df['specialty'] == selected_specialty].copy()
        specialty_appointment_df.loc[:, 'month'] = pd.to_datetime(specialty_appointment_df['month']).dt.to_period('M').dt.to_timestamp('M')

        st.subheader(f"Appointment Capacity Analysis for {selected_specialty}")

        # Show capacity breakdown by appointment type
        # Explicitly pass observed=True to silence FutureWarning
        appointment_summary = specialty_appointment_df.groupby('appointment type', observed=True)['appointments completed'].sum().reset_index()

        st.write(appointment_summary)
    else:
        st.error("Appointment data is missing required columns.")
else:
    st.write("Please upload the **Appointment Data CSV** file in the **Home** page.")
