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
    appointment_required_columns = ['month', 'specialty', 'appointment_type', 'appointments_attended', 'waiting_list', 'removals', 'removals_other_than_treatment', 'rtt_firsts', 'rtt_followups', 'non_rtt_followups']

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

        # Calculate scaled appointments for 12 months equivalent
        num_baseline_months = (baseline_end.year - baseline_start.year) * 12 + (baseline_end.month - baseline_start.month) + 1
        scaling_factor = 12 / num_baseline_months
        scaled_appointments = baseline_appointment_df.groupby('appointment_type', observed=False)['appointments_attended'].sum() * scaling_factor
        scaled_appointments = scaled_appointments.reset_index()

        # Add grand total row
        grand_total_scaled = scaled_appointments['appointments_attended'].sum()
        total_row = pd.DataFrame({'appointment_type': ['Total'], 'appointments_attended': [grand_total_scaled]})
        scaled_appointments = pd.concat([scaled_appointments, total_row], ignore_index=True)

        # Display Baseline Summary of Scaled Appointments Attended
        st.subheader("Baseline Summary of Appointments Attended (Scaled to 12 Months)")
        st.table(scaled_appointments.style.set_caption("Baseline Appointments Summary (Scaled to 12 Months)").applymap(lambda x: 'font-weight: bold' if x == 'Total' else ''))

        # Waiting List Analysis
        st.subheader("Waiting List Analysis and Removal Ratios")
        waiting_list_summary = baseline_appointment_df.groupby('month').agg(
            waiting_list=('waiting_list', 'mean'),
            total_removals=('removals', 'sum'),
            removals_other_than_treatment=('removals_other_than_treatment', 'sum'),
            rtt_firsts=('rtt_firsts', 'sum'),
            rtt_followups=('rtt_followups', 'sum'),
            non_rtt_followups=('non_rtt_followups', 'sum')
        ).reset_index()

        # Display Waiting List Summary Table
        st.table(waiting_list_summary)

        # Ratio Analysis for Appointments
        st.subheader("Appointment Type Ratios vs. Attended Ratios")
        total_rtt_firsts = waiting_list_summary['rtt_firsts'].sum()
        total_rtt_followups = waiting_list_summary['rtt_followups'].sum()
        total_non_rtt_followups = waiting_list_summary['non_rtt_followups'].sum()

        total_appointments = total_rtt_firsts + total_rtt_followups + total_non_rtt_followups

        # Calculate ratios
        ratios = {
            'RTT First': total_rtt_firsts / total_appointments * 100 if total_appointments > 0 else 0,
            'RTT Follow-up': total_rtt_followups / total_appointments * 100 if total_appointments > 0 else 0,
            'Non-RTT Follow-up': total_non_rtt_followups / total_appointments * 100 if total_appointments > 0 else 0
        }

        st.write("**Ratios of Appointment Types (based on attended appointments):**")
        for appointment_type, ratio in ratios.items():
            st.write(f"- **{appointment_type}:** {ratio:.2f}%")

        # Ensure calculation of available appointments based on baseline utilization and DNA rates
        # These values will be saved to session state to be used on the next page
        available_rtt_first = scaled_appointments[scaled_appointments['appointment_type'] == 'RTT First']['appointments_attended'].values[0]
        available_rtt_followup = scaled_appointments[scaled_appointments['appointment_type'] == 'RTT Follow-up']['appointments_attended'].values[0]
        available_non_rtt = scaled_appointments[scaled_appointments['appointment_type'] == 'Non-RTT']['appointments_attended'].values[0]

        # Store available capacity in session state for the next page
        st.session_state.available_rtt_first = available_rtt_first
        st.session_state.available_rtt_followup = available_rtt_followup
        st.session_state.available_non_rtt = available_non_rtt

    else:
        st.error("Data is missing required columns.")
else:
    st.write("Please upload the required data files in the **Home** page.")
