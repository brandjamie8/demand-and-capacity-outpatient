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

            # Calculate a year's worth of appointments from the baseline period
            num_baseline_months = len(pd.date_range(start=baseline_start, end=baseline_end, freq='M'))
            scaling_factor = 12 / num_baseline_months
            yearly_appointments = total_appointments.copy()
            yearly_appointments['appointments completed'] *= scaling_factor

            st.write("**Baseline Appointment Capacity Breakdown (Scaled to 12 Months)**")
            st.write(yearly_appointments)

            # Determine if there is enough capacity for referrals (one first appointment per referral)
            if 'forecasted_total' in st.session_state:
                total_forecasted_referrals = st.session_state['forecasted_total']
                rtt_first_appointments = yearly_appointments[yearly_appointments['appointment type'] == 'RTT first']['appointments completed'].values[0]

                if rtt_first_appointments >= total_forecasted_referrals:
                    st.success("There is enough RTT first appointment capacity for forecasted referrals.")
                else:
                    st.warning("There is NOT enough RTT first appointment capacity for forecasted referrals.")

            # User Input for Utilization and DNA Rate
            st.subheader("Adjust Utilisation and DNA Rate")

            col1, col2 = st.columns(2)
            with col1:
                utilization_rate = st.slider('Utilisation Rate (%)', min_value=0, max_value=100, value=85) / 100.0
            with col2:
                dna_rate = st.slider('Did Not Attend (DNA) Rate (%)', min_value=0, max_value=100, value=10) / 100.0

            # Calculate the required available appointments based on utilization and DNA rates
            yearly_appointments['appointments needed'] = yearly_appointments['appointments completed'] / (utilization_rate * (1 - dna_rate))

            st.write("**Projected Required Available Appointment Capacity for Next Year**")
            st.write(yearly_appointments[['appointment type', 'appointments needed']])

            # Save relevant variables to session state for next page
            st.session_state['available_rtt_first'] = yearly_appointments[yearly_appointments['appointment type'] == 'RTT first']['appointments needed'].values[0]
            st.session_state['available_rtt_followup'] = yearly_appointments[yearly_appointments['appointment type'] == 'RTT follow-up']['appointments needed'].values[0]
            st.session_state['available_non_rtt'] = yearly_appointments[yearly_appointments['appointment type'] == 'non-RTT']['appointments needed'].values[0]

            # Bar Chart for Projected Capacity
            fig_capacity = px.bar(
                yearly_appointments,
                x='appointment type',
                y='appointments needed',
                title='Projected Required Available Appointment Capacity for Next Year',
                text='appointments needed',
                labels={'appointments needed': 'Number of Appointments', 'appointment type': 'Appointment Type'},
                color='appointment type',
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_capacity.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            st.plotly_chart(fig_capacity, use_container_width=True)

    else:
        st.error("Appointment data is missing required columns.")
else:
    st.write("Please upload the **Appointment Data CSV** file in the **Home** page.")
