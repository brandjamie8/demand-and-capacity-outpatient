import streamlit as st
import pandas as pd

st.title("Demand vs Capacity")

# Assuming referral and appointment data are in session state
if 'referral_df' in st.session_state and 'appointment_df' in st.session_state:
    referral_df = st.session_state.referral_df
    appointment_df = st.session_state.appointment_df
    selected_specialty = st.session_state.selected_specialty

    # Calculate total referrals for next year (use forecasting logic if needed)
    total_referrals = referral_df[referral_df['specialty'] == selected_specialty]['referrals'].sum()
    total_appointments = appointment_df[appointment_df['specialty'] == selected_specialty]['appointments completed'].sum()

    st.subheader("Demand vs Capacity Comparison")
    st.write(f"**Total Referrals for Next Year:** {total_referrals}")
    st.write(f"**Total Available Appointments:** {total_appointments}")

    if total_appointments >= total_referrals:
        st.success("Capacity meets or exceeds the demand.")
    else:
        st.warning("Capacity does not meet the demand.")
else:
    st.write("Please ensure you have uploaded referral and appointment data on the **Home** page.")
