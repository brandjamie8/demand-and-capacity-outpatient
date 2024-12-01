import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Capacity Analysis")

if 'appointment_df' in st.session_state and st.session_state.appointment_df is not None:
    appointment_df = st.session_state.appointment_df

    required_columns = ['month', 'specialty', 'appointment type', 'appointments completed', 'did not attend rate']
    if all(column in appointment_df.columns for column in required_columns):
        selected_specialty = st.session_state.selected_specialty

        # Filter appointment data based on selected specialty
        specialty_appointment_df = appointment_df[appointment_df['specialty'] == selected_specialty].copy()
        specialty_appointment_df.loc[:, 'month'] = pd.to_datetime(specialty_appointment_df['month']).dt.to_period('M').dt.to_timestamp('M')

        st.subheader(f"Appointment Capacity Analysis for {selected_specialty}")

        # Baseline Period Selection
        min_date = specialty_appointment_df['month'].min()
        max_date = specialty_appointment_df['month'].max()
        baseline_start = st.date_input('Baseline Start Date', value=min_date, min_value=min_date, max_value=max_date)
        baseline_end = st.date_input('Baseline End Date', value=max_date, min_value=min_date, max_value=max_date)

        # Convert baseline dates to datetime
        baseline_start = pd.to_datetime(baseline_start).to_period('M').to_timestamp('M')
        baseline_end = pd.to_datetime(baseline_end).to_period('M').to_timestamp('M')

        # Filter data based on baseline period
        baseline_appointment_df = specialty_appointment_df[(specialty_appointment_df['month'] >= baseline_start) & (specialty_appointment_df['month'] <= baseline_end)]

        if baseline_appointment_df.empty:
            st.error("No data available for the selected baseline period.")
        else:
            # Split capacity into RTT first, RTT follow-up, and non-RTT appointments
            appointment_types = ['RTT first', 'RTT follow-up', 'non-RTT']
            baseline_appointment_df['appointment type'] = pd.Categorical(baseline_appointment_df['appointment type'], categories=appointment_types, ordered=True)

            # Calculate total appointments for each type
            total_appointments = baseline_appointment_df.groupby('appointment type', observed=True)['appointments completed'].sum().reset_index()

            # Display baseline appointment capacity
            st.write("**Baseline Appointment Capacity Breakdown**")
            st.write(total_appointments)

            # User Input for Ratios and Utilization
            st.subheader("Adjust Capacity Ratios and Utilization")

            col1, col2, col3 = st.columns(3)
            with col1:
                rtt_first_ratio = st.number_input('RTT First Ratio', min_value=0.0, max_value=1.0, value=0.3, step=0.01)
            with col2:
                rtt_followup_ratio = st.number_input('RTT Follow-up Ratio', min_value=0.0, max_value=1.0, value=0.5, step=0.01)
            with col3:
                non_rtt_ratio = st.number_input('Non-RTT Ratio', min_value=0.0, max_value=1.0, value=0.2, step=0.01)

            if (rtt_first_ratio + rtt_followup_ratio + non_rtt_ratio) != 1.0:
                st.warning("Ratios should sum to 1.0 for accurate capacity calculations.")

            col1, col2 = st.columns(2)
            with col1:
                utilization_rate = st.slider('Utilization Rate (%)', min_value=0, max_value=100, value=85) / 100.0
            with col2:
                dna_rate = st.slider('Did Not Attend (DNA) Rate (%)', min_value=0, max_value=100, value=10) / 100.0

            # Calculate available appointments for next year
            total_appointments_baseline = baseline_appointment_df['appointments completed'].sum()
            total_available_appointments_next_year = total_appointments_baseline * 12 / len(pd.date_range(start=baseline_start, end=baseline_end, freq='M'))

            # Adjust based on ratios and utilization
            available_rtt_first = total_available_appointments_next_year * rtt_first_ratio * utilization_rate * (1 - dna_rate)
            available_rtt_followup = total_available_appointments_next_year * rtt_followup_ratio * utilization_rate * (1 - dna_rate)
            available_non_rtt = total_available_appointments_next_year * non_rtt_ratio * utilization_rate * (1 - dna_rate)

            st.write("**Projected Capacity for Next Year**")
            st.write(f"- RTT First Appointments: {available_rtt_first:.0f}")
            st.write(f"- RTT Follow-up Appointments: {available_rtt_followup:.0f}")
            st.write(f"- Non-RTT Appointments: {available_non_rtt:.0f}")

            # Bar Chart of Projected Capacity
            projected_capacity = {
                'Appointment Type': ['RTT First', 'RTT Follow-up', 'Non-RTT'],
                'Available Appointments': [available_rtt_first, available_rtt_followup, available_non_rtt]
            }
            projected_capacity_df = pd.DataFrame(projected_capacity)

            fig_capacity = px.bar(
                projected_capacity_df,
                x='Appointment Type',
                y='Available Appointments',
                title='Projected Appointment Capacity for Next Year',
                text='Available Appointments'
            )
            fig_capacity.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            st.plotly_chart(fig_capacity, use_container_width=True)

    else:
        st.error("Appointment data is missing required columns.")
else:
    st.write("Please upload the **Appointment Data CSV** file in the **Home** page.")
