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
            color_discrete_sequence=px.colors.qualitative.Safe  # Consistent colors for clarity
        )

        # Highlight the baseline period in the chart
        if baseline_start != baseline_end:
            fig.add_vrect(
                x0=baseline_start,
                x1=baseline_end,
                fillcolor="LightGrey",
                opacity=0.5,
                layer="below",
                line_width=0,
            )

        st.plotly_chart(fig, use_container_width=True)
        
          
          
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



        # Comparison: Number of Referrals vs. First Appointments (scaled for 12 months)
        st.subheader("Comparison of Referrals vs. First Appointments (Scaled to 12-Month Equivalent)")
        num_baseline_months = (baseline_end.year - baseline_start.year) * 12 + (baseline_end.month - baseline_start.month) + 1
        total_referrals_baseline = specialty_referral_df[(specialty_referral_df['month'] >= baseline_start) & (specialty_referral_df['month'] <= baseline_end)]['referrals'].sum()
        total_referrals_scaled = (total_referrals_baseline / num_baseline_months) * 12

        total_first_appointments = baseline_summary.loc[baseline_summary['appointment_type'] == 'RTT First', 'appointments_attended'].sum()
        total_first_appointments_scaled = (total_first_appointments / num_baseline_months) * 12

        st.write(f"**Total Referrals for Next Year (Scaled):** {int(total_referrals_scaled)}")
        st.write(f"**Total RTT First Appointments Attended for Next Year (Scaled):** {int(total_first_appointments_scaled)}")

        if total_first_appointments_scaled >= total_referrals_scaled:
            st.success("There is enough capacity for referrals based on the baseline attended first appointments. The waiting list is expected to decrease.")
        else:
            st.warning("There is not enough capacity for referrals based on the baseline attended first appointments. The waiting list is expected to increase.")

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
        available_capacity = total_first_appointments_scaled / baseline_utilisation_rate / (1 - baseline_dna_rate)

        st.write(f"**Baseline Utilisation Rate:** {baseline_utilisation_rate * 100:.2f}%")
        st.write(f"**Baseline DNA Rate:** {baseline_dna_rate * 100:.2f}%")
        st.write(f"**Number of Available Appointments Needed to Achieve {int(total_first_appointments_scaled)} Attended Appointments:** {int(available_capacity)}")

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

        # Calculate the number of attended appointments with adjusted rates, capped by available capacity
        adjusted_attended_appointments = min(available_capacity * adjusted_utilisation_rate * (1 - adjusted_dna_rate), available_capacity)
        st.write(f"**Projected Number of Attended Appointments with Adjusted Rates:** {int(adjusted_attended_appointments)}")

        if adjusted_attended_appointments >= total_referrals_scaled:
            st.success("With the adjusted utilisation and DNA rates, the projected capacity is sufficient for the referrals.")
        else:
            st.warning("With the adjusted utilisation and DNA rates, the projected capacity is not sufficient for the referrals.")

        # Grand Total Summary Chart
        st.subheader("Grand Total Summary")
        
        grand_total_data = {
            'Category': [
                'Baseline Attended (12-Month)', 
                'Available Capacity (Baseline Rates)', 
                'Adjusted Attended (Adjusted Rates)'
            ],
            'Appointments': [
                int(total_first_appointments_scaled), 
                int(available_capacity), 
                int(adjusted_attended_appointments)
            ]
        }
        
        grand_total_df = pd.DataFrame(grand_total_data)
        
        # Create bar chart for grand total summary
        fig_grand_total = px.bar(
            grand_total_df,
            x='Category',
            y='Appointments',
            title='Grand Total Summary of Capacity Analysis',
            labels={'Appointments': 'Number of Appointments'},
            text='Appointments',
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        
        # Add dotted line for the number of referrals (as expected demand)
        fig_grand_total.add_shape(
            type='line',
            x0=-0.5,
            y0=total_referrals_scaled,
            x1=2.5,
            y1=total_referrals_scaled,
            line=dict(color='red', width=2, dash='dot'),
            name='Total Referrals'
        )
        
        fig_grand_total.add_annotation(
            x=1,
            y=total_referrals_scaled,
            text=f"Total Referrals: {int(total_referrals_scaled)}",
            showarrow=False,
            yshift=10,
            font=dict(size=12, color='red')
        )

        # Update layout to ensure readability and display the chart
        fig_grand_total.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        fig_grand_total.update_layout(
            xaxis_title='',
            yaxis_title='Number of Appointments',
            yaxis_tickformat=',',
            title_x=0.5
        )
        
        st.plotly_chart(fig_grand_total, use_container_width=True)

        # Next Step
        st.markdown("""
        ## Next Steps
        After assessing whether the existing and adjusted capacities are sufficient, proceed to calculate the optimal capacity required to meet forecasted demand.
        Navigate to the next page to perform a **detailed demand vs capacity comparison** and evaluate potential waiting list impacts.
        """)

    else:
        st.error("Referral or appointment data is missing required columns.")
else:
    st.error("Please complete the **Referral Demand** and **Appointment Data Upload** sections to proceed.")
