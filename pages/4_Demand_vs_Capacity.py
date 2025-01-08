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

    if 'forecasted_total' in st.session_state:
        forecasted_total = st.session_state.forecasted_total
    else:
        st.error("Please complete the referral demand analysis to forecast referrals.")

    # Ratios for waiting list removals
    st.subheader("Appointment Type Ratios Based on Waiting List Removals")
    rtt_first_to_followup_ratio = st.session_state.first_followup_removals_ratio
    rtt_first_to_non_rtt_ratio = st.session_state.first_non_rtt_removals_ratio

    st.write(f"**RTT First to Follow-up Ratio (Waiting List Removals):** {rtt_first_to_followup_ratio:.2f}")
    st.write(f"**RTT First to Non-RTT Ratio (Waiting List Removals):** {rtt_first_to_non_rtt_ratio:.2f}")

    # Calculate required appointments
    rtt_first_demand = forecasted_total
    rtt_followup_demand = round(rtt_first_demand * rtt_first_to_followup_ratio)
    non_rtt_demand = round(rtt_first_demand * rtt_first_to_non_rtt_ratio)

    # Sliders to Adjust Appointment Percentages
    st.subheader("Adjust Appointment Capacity Distribution")
    st.write("Use the sliders below to adjust the percentage allocation of appointments for RTT First, RTT Follow-up, and Non-RTT.")

    col1, col2, col3 = st.columns(3)
    with col1:
        pct_rtt_first = st.slider("RTT First (%)", min_value=0, max_value=100, value=50, step=1)
    with col2:
        pct_rtt_followup = st.slider("RTT Follow-up (%)", min_value=0, max_value=100, value=30, step=1)
    with col3:
        pct_non_rtt = st.slider("Non-RTT (%)", min_value=0, max_value=100, value=20, step=1)

    total_percentage = pct_rtt_first + pct_rtt_followup + pct_non_rtt
    if total_percentage != 100:
        st.error("The percentages must add up to 100%. Please adjust the sliders.")
    else:
        # Recalculate available appointments based on percentages
        total_available_capacity = st.session_state.available_rtt_first + st.session_state.available_rtt_followup + st.session_state.available_non_rtt

        allocated_rtt_first = int(round(total_available_capacity * (pct_rtt_first / 100)))
        allocated_rtt_followup = int(round(total_available_capacity * (pct_rtt_followup / 100)))
        allocated_non_rtt = int(round(total_available_capacity * (pct_non_rtt / 100)))

        comparison_data = {
            'Appointment Type': ['RTT First', 'RTT Follow-up', 'Non-RTT'],
            'Required Appointments': [rtt_first_demand, rtt_followup_demand, non_rtt_demand],
            'Future Attended Appointments (Adjusted)': [allocated_rtt_first, allocated_rtt_followup, allocated_non_rtt]
        }
        comparison_df = pd.DataFrame(comparison_data)

        # Display Table
        st.table(comparison_df)

        # Check Capacity Gaps
        st.subheader("Capacity Gap Analysis")
        gaps_exist = False
        for index, row in comparison_df.iterrows():
            if row['Future Attended Appointments (Adjusted)'] < row['Required Appointments']:
                gaps_exist = True
                gap = row['Required Appointments'] - row['Future Attended Appointments (Adjusted)']
                st.warning(f"Capacity gap for {row['Appointment Type']}: {gap:.0f} appointments")

        if not gaps_exist:
            st.success("The adjusted capacity meets or exceeds the required appointments!")
        else:
            st.error("Capacity gaps still exist. Adjust the percentages or consider increasing capacity.")

        # Bar Chart for Visual Comparison
        fig_comparison = px.bar(
            comparison_df,
            x='Appointment Type',
            y=['Required Appointments', 'Future Attended Appointments (Adjusted)'],
            barmode='group',
            title='Adjusted Capacity vs Required Appointments',
            labels={'value': 'Number of Appointments', 'Appointment Type': 'Type'},
            text_auto=True
        )
        st.plotly_chart(fig_comparison, use_container_width=True)

else:
    st.write("Please upload the required data files in the **Home** page.")
