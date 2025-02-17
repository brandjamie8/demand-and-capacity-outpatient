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
    referral_required_columns = ['month', 'specialty', 'additions', 'removals']
    appointment_required_columns = ['month', 'specialty', 'appointment_type', 'appointments_attended']

    if all(column in referral_df.columns for column in referral_required_columns) and \
       all(column in appointment_df.columns for column in appointment_required_columns):

        # Filter data for selected specialty
        specialty_referral_df = referral_df[referral_df['specialty'] == selected_specialty].copy()
        specialty_appointment_df = appointment_df[appointment_df['specialty'] == selected_specialty].copy()

        # Convert 'month' to datetime and set as month-end
        specialty_referral_df['month'] = pd.to_datetime(specialty_referral_df['month']).dt.to_period('M').dt.to_timestamp('M')
        specialty_appointment_df['month'] = pd.to_datetime(specialty_appointment_df['month']).dt.to_period('M').dt.to_timestamp('M')
        specialty_appointment_df.sort_values(by='month', inplace=True)

        # Default baseline period as the last 6 months of available data
        max_date = specialty_appointment_df['month'].max()
        default_baseline_start = max_date - pd.DateOffset(months=5)  # Last 6 months
          
        # Plot all monthly appointments as a line chart
        st.subheader(f"Monthly Appointments Attended for {selected_specialty}")
        # Allow user to adjust baseline period
        st.write("Select Baseline Period")

        col1, col2, _, _ = st.columns(4)  
        with col1:
           baseline_start = st.date_input('Baseline Start Date', value=default_baseline_start, min_value=specialty_appointment_df['month'].min(), max_value=max_date)
        with col2:
           baseline_end = st.date_input('Baseline End Date', value=max_date, min_value=specialty_appointment_df['month'].min(), max_value=max_date)

        # Convert baseline dates to datetime
        baseline_start = pd.to_datetime(baseline_start).to_period('M').to_timestamp('M')
        baseline_end = pd.to_datetime(baseline_end).to_period('M').to_timestamp('M')

        # Filter data based on the selected baseline period
        baseline_appointment_df = specialty_appointment_df[(specialty_appointment_df['month'] >= baseline_start) & (specialty_appointment_df['month'] <= baseline_end)]

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
        
        
          
        # Summary of appointments during the baseline period
        st.subheader("Baseline Summary of Appointments Attended (Scaled to 12 Months)")
      
        # Calculate the number of baseline months
        num_baseline_months = (baseline_end.year - baseline_start.year) * 12 + (baseline_end.month - baseline_start.month) + 1
      
        # Group the baseline data by appointment type and sum the appointments attended
        baseline_summary = baseline_appointment_df.groupby('appointment_type', observed=False)['appointments_attended'].sum().reset_index()
      
        # Scale the appointments to a 12-month equivalent
        baseline_summary['appointments_attended'] = (baseline_summary['appointments_attended'] / num_baseline_months) * 12
        baseline_summary['appointments_attended'] = baseline_summary['appointments_attended'].astype(int)
      
        # Reorder rows and format titles
        order = ['RTT First', 'RTT Follow-up', 'Non-RTT']
        baseline_summary['appointment_type'] = pd.Categorical(baseline_summary['appointment_type'], categories=order, ordered=True)
        baseline_summary = baseline_summary.sort_values('appointment_type')
      
        # Calculate grand total for the scaled values
        grand_total_baseline = baseline_summary['appointments_attended'].sum()
        total_row = pd.DataFrame({'appointment_type': ['Total'], 'appointments_attended': [grand_total_baseline]})
        baseline_summary = pd.concat([baseline_summary, total_row], ignore_index=True)
      
        # Display the table without index and make the "Total" row bold
        def highlight_total_row(row):
            return ['font-weight: bold' if row['appointment_type'] == 'Total' else '' for _ in row]

        col1, _ = st.columns(2)
        with col1:
           st.table(baseline_summary.style.apply(highlight_total_row, axis=1).set_properties(**{'text-align': 'left'}).set_caption("Baseline Appointments Summary (Scaled to 12 Months)"))



        # Add a section to analyze the ratio of RTT First to RTT Follow-up appointments
        st.subheader("First to Follow-up Ratio Analysis")
      
        # Calculate the RTT First to RTT Follow-up ratio from the displayed table
        rtt_first_attended = baseline_summary.loc[baseline_summary['appointment_type'] == 'RTT First', 'appointments_attended'].sum()
        rtt_followup_attended = baseline_summary.loc[baseline_summary['appointment_type'] == 'RTT Follow-up', 'appointments_attended'].sum()
        non_rtt_attended = baseline_summary.loc[baseline_summary['appointment_type'] == 'Non-RTT', 'appointments_attended'].sum()

        st.session_state.available_rtt_first = rtt_first_attended
        st.session_state.available_rtt_followup = rtt_followup_attended
        st.session_state.available_non_rtt = non_rtt_attended
          
        if rtt_first_attended > 0:
            rtt_first_to_followup_ratio_attended = rtt_followup_attended / rtt_first_attended
        else:
            rtt_first_to_followup_ratio_attended = None

        if rtt_first_attended > 0:
            rtt_first_to_non_rtt_ratio_attended = non_rtt_attended / rtt_first_attended
        else:
            rtt_first_to_non_rtt_ratio_attended = None          
      
        # Extract appointments for removals
        appointments_for_removals = baseline_appointment_df.groupby('appointment_type')['appointments_for_removals'].sum().reset_index()
        rtt_first_removals = appointments_for_removals.loc[appointments_for_removals['appointment_type'] == 'RTT First', 'appointments_for_removals'].sum()
        rtt_followup_removals = appointments_for_removals.loc[appointments_for_removals['appointment_type'] == 'RTT Follow-up', 'appointments_for_removals'].sum()
        non_rtt_removals = appointments_for_removals.loc[appointments_for_removals['appointment_type'] == 'Non-RTT', 'appointments_for_removals'].sum()
          
        if rtt_first_removals > 0:
            rtt_first_to_followup_ratio_removals = rtt_followup_removals / rtt_first_removals
        else:
            rtt_first_to_followup_ratio_removals = None

        if rtt_first_removals > 0:
            rtt_first_to_non_rtt_ratio_removals = non_rtt_removals / rtt_first_removals
        else:
            rtt_first_to_non_rtt_ratio_removals = None

        st.session_state.first_followup_removals_ratio = rtt_first_to_followup_ratio_removals
        st.session_state.first_non_rtt_removals_ratio = rtt_first_to_non_rtt_ratio_removals
          
        # Display ratios
        st.write("**RTT First to RTT Follow-up Ratios:**")
        st.write(f"- **Attended RTT Follow-up Appointments per RTT First Appointments:** {rtt_first_to_followup_ratio_attended:.2f}" if rtt_first_to_followup_ratio_attended is not None else "- **Attended Appointments:** Not calculable (no RTT First appointments)")
        st.write(f"- **RTT Follow-up Appointments Required per Clock Stop:** {rtt_first_to_followup_ratio_removals:.2f}" if rtt_first_to_followup_ratio_removals is not None else "- **Appointments for Removals:** Not calculable (no RTT First appointments for removals)")

        # Evaluate alignment
        if rtt_first_to_followup_ratio_attended is not None and rtt_first_to_followup_ratio_removals is not None:
            if abs(rtt_first_to_followup_ratio_attended - rtt_first_to_followup_ratio_removals) <= 0.1:
                st.success("The ratio of RTT First to RTT Follow-up appointments is well-aligned with the ratio required for removals. This suggests that the balance of appointment types aligns with what is needed to manage the waiting list.")
            elif rtt_first_to_followup_ratio_attended > rtt_first_to_followup_ratio_removals:
                st.warning("The ratio of RTT First to RTT Follow-up appointments is higher than the ratio required for removals. This might indicate an over-focus on first appointments, which could lead to a bottleneck in follow-ups.")
            else:
                st.warning("The ratio of RTT First to RTT Follow-up appointments is lower than the ratio required for removals. This could indicate insufficient follow-ups, potentially causing delays in clearing the waiting list.")
        else:
            st.error("One or both ratios could not be calculated. Ensure data availability for both attended appointments and removals to perform this analysis.")
   
        # Display ratios
        st.write("**RTT First to Non-RTT Ratios:**")
        st.write(f"- **Attended Non-RTT Appointments per RTT First Appointments:** {rtt_first_to_non_rtt_ratio_attended:.2f}" if rtt_first_to_non_rtt_ratio_attended is not None else "- **Attended Appointments:** Not calculable (no RTT First appointments)")
        st.write(f"- **Non-RTT Appointments Required per Clock Stop:** {rtt_first_to_non_rtt_ratio_removals:.2f}" if rtt_first_to_non_rtt_ratio_removals is not None else "- **Appointments for Removals:** Not calculable (no RTT First appointments for removals)")
   
        # Evaluate alignment
        if rtt_first_to_non_rtt_ratio_attended is not None and rtt_first_to_non_rtt_ratio_removals is not None:
            if abs(rtt_first_to_non_rtt_ratio_attended - rtt_first_to_non_rtt_ratio_removals) <= 0.1:
                st.success("The ratio of RTT First to Non-RTT appointments is well-aligned with the ratio required for removals. This suggests that the balance of appointment types aligns with what is needed to manage the waiting list.")
            elif rtt_first_to_non_rtt_ratio_attended > rtt_first_to_non_rtt_ratio_removals:
                st.warning("The ratio of RTT First to Non-RTT appointments is higher than the ratio required for removals. This might indicate an over-focus on first appointments, which could lead to a bottleneck in Non-RTT.")
            else:
                st.warning("The ratio of RTT First to Non-RTT appointments is lower than the ratio required for removals. This could indicate insufficient Non-RTT appointments, potentially causing delays in clearing the waiting list.")
        else:
            st.error("One or both ratios could not be calculated. Ensure data availability for both attended appointments and removals to perform this analysis.")

          
        # Comparison: Number of Referrals vs. First Appointments (scaled for 12 months)
        st.subheader("Comparison of Referrals vs. First Appointments (Scaled to 12-Month Equivalent)")
        num_baseline_months = (baseline_end.year - baseline_start.year) * 12 + (baseline_end.month - baseline_start.month) + 1
        total_first_appointments = baseline_summary.loc[baseline_summary['appointment_type'] == 'RTT First', 'appointments_attended'].sum()
        total_first_appointments_scaled = baseline_summary.loc[baseline_summary['appointment_type'] == 'RTT First', 'appointments_attended'].sum()
        total_referrals_scaled = st.session_state['forecasted_total']
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

        if total_referrals_scaled > available_capacity:
            st.error("The total referrals exceed even the available capacity if utilisation were 100% and DNAs were 0%. The number of appointments needs to increase.")
        elif total_referrals_scaled > total_first_appointments_scaled and total_referrals_scaled <= available_capacity:
            st.warning("The demand can be met if utilisation is increased and/or the DNA rate is reduced.")
        else:
            st.success("The capacity is sufficient, and the waiting list is expected to reduce.")
              
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
          
        fig_grand_total.update_layout(
              xaxis_title='',
              yaxis_title='Number of Appointments',
              yaxis_tickformat=',',
              title_x=0.5,
              title=''
        )
      
        st.plotly_chart(fig_grand_total, use_container_width=True)
      
        if adjusted_attended_appointments > total_referrals_scaled:
            st.success("The new rates would mean enough attended appointments to meet the referral demand, although unlikely to reduce the backlog significantly.")

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
