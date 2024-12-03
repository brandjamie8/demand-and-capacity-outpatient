import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Demand vs Capacity Comparison")

# Check if data is available in session state
if ('referral_df' in st.session_state and st.session_state.referral_df is not None) and \
   ('appointment_df' in st.session_state and st.session_state.appointment_df is not None):

    referral_df = st.session_state.referral_df
    appointment_df = st.session_state.appointment_df
    selected_specialty = st.session_state.selected_specialty

    # Baseline Referral Analysis
    st.subheader(f"Referral Demand Forecast for {selected_specialty}")

    # Get forecasted referral data from session state or calculate it again
    if 'forecasted_referrals' in st.session_state:
        forecasted_referrals_df = st.session_state['forecasted_referrals']
        forecasted_total = forecasted_referrals_df['forecasted_referrals'].sum()
    else:
        st.error("Please complete the referral demand analysis to forecast referrals.")

    st.write(f"**Total Forecasted Referrals for Next Year:** {forecasted_total:.0f}")
    st.write(forecasted_referrals_df)

    # Baseline Appointment Capacity
    st.subheader("Baseline and Projected Capacity Comparison")

    if ('available_rtt_first' in st.session_state and 'available_rtt_followup' in st.session_state and 'available_non_rtt' in st.session_state):
        available_rtt_first = st.session_state.available_rtt_first
        available_rtt_followup = st.session_state.available_rtt_followup
        available_non_rtt = st.session_state.available_non_rtt

        # Calculate total forecasted demand by appointment type
        rtt_first_demand = forecasted_referrals_df[forecasted_referrals_df['priority'] == '2-week wait']['forecasted_referrals'].sum()
        rtt_followup_demand = forecasted_referrals_df[forecasted_referrals_df['priority'] == 'Urgent']['forecasted_referrals'].sum()
        non_rtt_demand = forecasted_referrals_df[forecasted_referrals_df['priority'] == 'Routine']['forecasted_referrals'].sum()

        # Create a DataFrame to compare demand and capacity
        comparison_data = {
            'Appointment Type': ['RTT First', 'RTT Follow-up', 'Non-RTT'],
            'Required Appointments': [rtt_first_demand, rtt_followup_demand, non_rtt_demand],
            'Available Appointments': [available_rtt_first, available_rtt_followup, available_non_rtt]
        }
        comparison_df = pd.DataFrame(comparison_data)

        # Bar Chart to compare required vs available appointments
        fig_comparison = px.bar(
            comparison_df,
            x='Appointment Type',
            y=['Required Appointments', 'Available Appointments'],
            barmode='group',
            title='Required vs Available Appointments for Next Year',
            labels={'value': 'Number of Appointments', 'Appointment Type': 'Type'},
            text_auto=True
        )
        st.plotly_chart(fig_comparison, use_container_width=True)

        # Highlight Capacity Gaps
        st.write("**Capacity Gaps**")
        for index, row in comparison_df.iterrows():
            if row['Available Appointments'] < row['Required Appointments']:
                gap = row['Required Appointments'] - row['Available Appointments']
                st.warning(f"Capacity gap for {row['Appointment Type']}: {gap:.0f} appointments")

    else:
        st.error("Please complete the capacity analysis to project next year's capacity.")

else:
    st.write("Please upload the required data files in the **Home** page.")
