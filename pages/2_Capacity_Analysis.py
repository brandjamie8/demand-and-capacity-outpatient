import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("Capacity Analysis")

# Ensure necessary session state data is available
if 'referral_df' in st.session_state and st.session_state.referral_df is not None and \
   'appointment_df' in st.session_state and st.session_state.appointment_df is not None:

    # Load the data from session state
    referral_df = st.session_state.referral_df
    appointment_df = st.session_state.appointment_df
    selected_specialty = st.session_state.selected_specialty

    # Ensure required columns are present in both datasets
    referral_required_columns = ['month', 'specialty', 'priority', 'referrals']
    appointment_required_columns = ['month', 'specialty', 'appointment_type', 'appointments_attended']

    if all(column in referral_df.columns for column in referral_required_columns) and \
       all(column in appointment_df.columns for column in appointment_required_columns):

        # Filter data for selected specialty
        specialty_referral_df = referral_df[referral_df['specialty'] == selected_specialty].copy()
        specialty_appointment_df = appointment_df[appointment_df['specialty'] == selected_specialty].copy()

        # Convert 'month' to datetime and set as month-end
        specialty_referral_df['month'] = pd.to_datetime(specialty_referral_df['month']).dt.to_period('M').dt.to_timestamp('M')
        specialty_appointment_df['month'] = pd.to_datetime(specialty_appointment_df['month']).dt.to_period('M').dt.to_timestamp('M')

        # Default baseline period as the last 6 months of available data
        max_date = specialty_appointment_df['month'].max()
        default_baseline_start = max_date - pd.DateOffset(months=5)  # Last 6 months

        # Allow user to adjust baseline period
        st.subheader("Select Baseline Period")
        baseline_start = st.date_input('Baseline Start Date', value=default_baseline_start, min_value=specialty_appointment_df['month'].min(), max_value=max_date)
        baseline_end = st.date_input('Baseline End Date', value=max_date, min_value=specialty_appointment_df['month'].min(), max_value=max_date)

        # Convert baseline dates to datetime
        baseline_start = pd.to_datetime(baseline_start).to_period('M').to_timestamp('M')
        baseline_end = pd.to_datetime(baseline_end).to_period('M').to_timestamp('M')

        # Filter data based on the selected baseline period
        baseline_appointment_df = specialty_appointment_df[(specialty_appointment_df['month'] >= baseline_start) & (specialty_appointment_df['month'] <= baseline_end)]

        # Plot all monthly appointments as a line chart
        st.subheader("Monthly Appointments Attended")
        fig = px.line(
            specialty_appointment_df,
            x='month',
            y='appointments_attended',
            color='appointment_type',
            labels={'appointments_attended': 'Number of Appointments Attended', 'appointment_type': 'Appointment Type'},
            title='Monthly Appointments Attended by Type',
            line_group='appointment_type',
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Safe  # Consistent colors for clarity
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary of appointments during the baseline period
        st.subheader("Baseline Summary of Appointments Attended")
        baseline_summary = baseline_appointment_df.groupby('appointment_type')['appointments_attended'].sum().reset_index()
        baseline_summary['appointments_attended'] = baseline_summary['appointments_attended'].astype(int)

        # Calculate grand total
        grand_total_baseline = baseline_summary['appointments_attended'].sum()
        baseline_summary = baseline_summary.append({'appointment_type': 'Total', 'appointments_attended': grand_total_baseline}, ignore_index=True)

        st.table(baseline_summary)

        # Comparison: Number of Referrals vs. Number of First Appointments
        st.subheader("Comparison of Referrals vs. First Appointments")
        baseline_referrals = specialty_referral_df[(specialty_referral_df['month'] >= baseline_start) & (specialty_referral_df['month'] <= baseline_end)]
        total_referrals = baseline_referrals['referrals'].sum()
        total_first_appointments = baseline_summary.loc[baseline_summary['appointment_type'] == 'RTT First', 'appointments_attended'].sum()

        st.write(f"**Total Referrals in Baseline Period:** {int(total_referrals)}")
        st.write(f"**Total RTT First Appointments Attended in Baseline Period:** {int(total_first_appointments)}")

        if total_first_appointments >= total_referrals:
            st.success("There is enough capacity for referrals based on the baseline attended first appointments.")
        else:
            st.warning("There is not enough capacity for referrals based on the baseline attended first appointments.")

        # Utilisation and DNA Rate Analysis
        st.subheader("Utilisation and DNA Rate Analysis")
        st.write("""
        Some appointments are never booked and some are never attended, so the number of available appointment capacity must be higher.
        The following analysis shows the existing utilisation rate and DNA rate, and translates this into the number of appointments needed.
        """)

        # Inputs for utilisation and DNA rates
        baseline_utilisation_rate = 0.85  # Example baseline utilisation rate (e.g., 85%)
        baseline_dna_rate = 0.1  # Example baseline DNA rate (e.g., 10%)

        # Calculate available capacity needed based on utilisation and DNA rates
        attended_appointments = total_first_appointments
        available_capacity = attended_appointments / ((1 - baseline_dna_rate) * baseline_utilisation_rate)

        st.write(f"**Baseline Utilisation Rate:** {baseline_utilisation_rate * 100:.2f}%")
        st.write(f"**Baseline DNA Rate:** {baseline_dna_rate * 100:.2f}%")
        st.write(f"**Number of Available Appointments Needed (to achieve {int(attended_appointments)} attended appointments):** {int(available_capacity)}")

        # Allow user to adjust utilisation and DNA rates
        st.subheader("Adjust Utilisation and DNA Rates")
        adjusted_utilisation_rate = st.slider(
            "Adjusted Utilisation Rate (%)",
            min_value=0.0,
            max_value=1.0,
            value=baseline_utilisation_rate,
            step=0.01
        )
        adjusted_dna_rate = st.slider(
            "Adjusted DNA Rate (%)",
            min_value=0.0,
            max_value=1.0,
            value=baseline_dna_rate,
            step=0.01
        )

        # Projected number of attended appointments based on adjusted rates
        projected_available_capacity = attended_appointments / ((1 - adjusted_dna_rate) * adjusted_utilisation_rate)
        st.write(f"**Projected Number of Available Appointments Needed (Adjusted Rates):** {int(projected_available_capacity)}")

        if projected_available_capacity >= total_referrals:
            st.success("With the adjusted utilisation and DNA rates, the projected capacity is sufficient for the referrals.")
        else:
            st.warning("With the adjusted utilisation and DNA rates, the projected capacity is not sufficient for the referrals.")

        # Grand Total for All Metrics
        st.subheader("Grand Total Summary")
        st.write(f"**Total Attended Appointments in Baseline:** {int(total_first_appointments)}")
        st.write(f"**Total Available Capacity Required (Baseline):** {int(available_capacity)}")
        st.write(f"**Total Available Capacity Required (Adjusted Rates):** {int(projected_available_capacity)}")

        # Next Step
        st.markdown("""
        ## Next Steps
        After assessing whether the existing and adjusted capacities are sufficient, proceed to calculate the optimal capacity required to meet forecasted demand.
        """)

    else:
        st.error("Referral or appointment data is missing required columns.")
else:
    st.error("Please complete the **Referral Demand** and **Appointment Data Upload** sections to proceed.")
