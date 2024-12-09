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
        forecasted_referrals_df['forecasted_referrals'] = forecasted_referrals_df['forecasted_referrals'].round()
        forecasted_total = forecasted_referrals_df['forecasted_referrals'].sum()
    else:
        st.error("Please complete the referral demand analysis to forecast referrals.")

    st.write(f"**Total Forecasted Referrals for Next Year:** {forecasted_total:.0f}")
    st.write(forecasted_referrals_df)

    # Ratios for waiting list removals
    st.subheader("Appointment Type Ratios Based on Waiting List Removals")
    rtt_first_to_followup_ratio = st.session_state.first_followup_removals_ratio
    rtt_first_to_non_rtt_ratio = st.session_state.first_non_rtt_removals_ratio

    st.write(f"**RTT First to Follow-up Ratio (Waiting List Removals):** {rtt_first_to_followup_ratio:.2f}")
    st.write(f"**RTT First to Non-RTT Ratio (Waiting List Removals):** {rtt_first_to_non_rtt_ratio:.2f}")

    # Calculate required appointments
    rtt_first_demand = forecasted_total  # Total referrals equal RTT First demand
    rtt_followup_demand = round(rtt_first_demand * rtt_first_to_followup_ratio)
    non_rtt_demand = round(rtt_first_demand * rtt_first_to_non_rtt_ratio)

    # Display methodology
    st.write("The required number of first appointments attended should at least be equal to the total forecasted referrals. Follow-up and Non-RTT appointments are calculated using the ratios derived from waiting list removals.")

    # Baseline Appointment Capacity
    st.subheader("Baseline and Projected Capacity Comparison")

    if ('available_rtt_first' in st.session_state and 'available_rtt_followup' in st.session_state and 'available_non_rtt' in st.session_state):
        available_rtt_first = int(round(st.session_state.available_rtt_first))
        available_rtt_followup = int(round(st.session_state.available_rtt_followup))
        available_non_rtt = int(round(st.session_state.available_non_rtt))

        # Create a DataFrame to compare demand and capacity
        comparison_data = {
            'Appointment Type': ['RTT First', 'RTT Follow-up', 'Non-RTT'],
            'Required Appointments': [rtt_first_demand, rtt_followup_demand, non_rtt_demand],
            'Future Attended Appointments (Baseline Scaled to 12 Months)': [available_rtt_first, available_rtt_followup, available_non_rtt]
        }
        comparison_df = pd.DataFrame(comparison_data)

        # Bar Chart to compare required vs available appointments
        fig_comparison = px.bar(
            comparison_df,
            x='Appointment Type',
            y=['Required Appointments', 'Future Attended Appointments (Baseline Scaled to 12 Months)'],
            barmode='group',
            title='Required vs Available Appointments for Next Year',
            labels={'value': 'Number of Appointments', 'Appointment Type': 'Type'},
            text_auto=True
        )
        st.plotly_chart(fig_comparison, use_container_width=True)

        col1, _ = st.columns(2)
        with col1:
           comparison_df.columns = ['Appointment Type', 'Required Appointments', 'Future Attended Appointments\n(Baseline Scaled to 12 Months)']
           st.table(comparison_df)

       
        # Highlight Capacity Gaps
        st.write("**Capacity Gaps**")
        gaps_exist = False
        for index, row in comparison_df.iterrows():
            if row['Future Attended Appointments (Baseline Scaled to 12 Months)'] < row['Required Appointments']:
                gaps_exist = True
                gap = row['Required Appointments'] - row['Future Attended Appointments (Baseline Scaled to 12 Months)']
                st.warning(f"Capacity gap for {row['Appointment Type']}: {gap:.0f} appointments")

        if not gaps_exist:
            st.info("There are no capacity gaps. Current capacity is sufficient to meet forecasted demand.")

        # Evaluate waiting list impact
        if gaps_exist:
            st.write("The capacity gaps indicate that the waiting list is likely to grow. This will be explored further on the next page under **Waiting List Dynamics**.")
        else:
            st.write("Since there are no capacity gaps, the waiting list is likely to shrink, assuming referrals remain consistent. This will be analyzed further under **Waiting List Dynamics**.")

    else:
        st.error("Please complete the capacity analysis to project next year's capacity.")

else:
    st.write("Please upload the required data files in the **Home** page.")
