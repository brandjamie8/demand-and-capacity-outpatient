import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Historic Non-Admitted Waiting List")

st.markdown("""
This page analyses the historic non-admitted waiting list data and provides a predicted starting point for future capacity planning.

- **Baseline Period Selection:** Choose a period that represents typical additions and removals to the waiting list. The model uses data from this period to simulate future changes.
- **Modelling Start Date:** Select a future date after the latest available data. The model predicts the waiting list size up to this date.
""")

# Check if data is available in session state
if ('referral_df' in st.session_state and st.session_state.referral_df is not None) and \
   ('appointment_df' in st.session_state and st.session_state.appointment_df is not None):

    # Load the data from session state
    referral_df = st.session_state.referral_df
    appointment_df = st.session_state.appointment_df
    selected_specialty = st.session_state.selected_specialty

    # Ensure required columns are present in both datasets
    referral_required_columns = ['month', 'specialty', 'referrals']
    appointment_required_columns = ['month', 'specialty', 'removals', 'waiting_list']

    if all(column in referral_df.columns for column in referral_required_columns) and \
       all(column in appointment_df.columns for column in appointment_required_columns):

        # Select specialty
        specialties = referral_df['specialty'].unique()
        if st.session_state.get('selected_specialty') is None:
            st.session_state.selected_specialty = specialties[0]

        col1, _, _ = st.columns(3)
        with col1:
            selected_specialty = st.selectbox('Select Specialty', specialties, index=list(specialties).index(st.session_state.selected_specialty), key='specialty_select')

        # Save the selected specialty to session state
        st.session_state.selected_specialty = selected_specialty

        # Filter data based on selected specialty
        referral_specialty_df = referral_df[referral_df['specialty'] == selected_specialty]
        appointment_specialty_df = appointment_df[appointment_df['specialty'] == selected_specialty]

        # Aggregate referrals by month and specialty
        referral_specialty_df = referral_specialty_df.groupby(['month', 'specialty'], as_index=False).sum()

        # Merge the data
        merged_df = pd.merge(appointment_specialty_df, referral_specialty_df, on=['month', 'specialty'], how='inner')
        # Convert 'month' column to datetime and adjust to end of month
        merged_df['month'] = pd.to_datetime(merged_df['month'], errors='coerce').dt.to_period('M').dt.to_timestamp('M')
        # Drop rows with NaT in 'month'
        merged_df = merged_df.dropna(subset=['month'])
        # Sort by month
        merged_df = merged_df.sort_values('month')

        ### **1. Additions and Removals Plot**
        st.subheader("Additions (Referrals) and Removals Over Time")
        fig1 = px.line(
            merged_df,
            x='month',
            y=['referrals', 'removals'],
            labels={'value': 'Number of Patients', 'variable': 'Legend'},
            title='Additions and Removals from Non-Admitted Waiting List',
            height=600  # Adjust the height as needed
        )

        # Display fig1 before the baseline date selections
        fig1_placeholder = st.empty()
        fig1_placeholder.plotly_chart(fig1, use_container_width=True)

        ### **2. Baseline Period Selection**
        st.subheader("Baseline Period Selection")
        st.write("""
        Select the start and end dates for the baseline period. The model will use data from this period to simulate future additions and removals from the waiting list. The selected period should reflect typical activity.
        """)

        max_date = merged_df['month'].max()

        col1, col2, _, _ = st.columns(4)
        with col1:
            baseline_start_date = st.date_input(
                'Baseline Start Date',
                value=max_date - pd.DateOffset(months=5) if pd.notnull(max_date) else None
            )
        with col2:
            baseline_end_date = st.date_input(
                'Baseline End Date',
                value=max_date if pd.notnull(max_date) else None
            )

        # Convert selected dates to datetime
        if baseline_start_date and baseline_end_date:
            baseline_start_date = pd.to_datetime(baseline_start_date).to_period('M').to_timestamp('M')
            baseline_end_date = pd.to_datetime(baseline_end_date).to_period('M').to_timestamp('M')

            # Highlight the baseline period in the chart
            if baseline_start_date != baseline_end_date:
                fig1.add_vrect(
                    x0=baseline_start_date,
                    x1=baseline_end_date,
                    fillcolor="LightGrey",
                    opacity=0.5,
                    layer="below",
                    line_width=0,
                )
                fig1_placeholder.plotly_chart(fig1, use_container_width=True)

        ### **3. Waiting List Over Time Plot**
        st.subheader("Total Size of the Waiting List Over Time")

        # Plot total waiting list over time
        fig2 = px.line(
            merged_df,
            x='month',
            y='waiting_list',
            labels={'waiting_list': 'Total Waiting List'},
            title='Total Size of the Non-Admitted Waiting List',
            height=600  # Adjust the height as needed
        )

        # Display fig2
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.error("Uploaded files do not contain the required columns.")
else:
    st.write("Please upload the Referral and Appointment Data in the sidebar on the **Home** page.")
