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
if 'appointments_df' in st.session_state and st.session_state.appointments_df is not None:
    appointments_df = st.session_state.appointments_df

    # Ensure required columns are present
    required_columns = ['month', 'specialty', 'referrals', 'removals', 'waiting_list']

    if all(column in appointments_df.columns for column in required_columns):

        # Select specialty
        specialties = appointments_df['specialty'].unique()
        if st.session_state.get('selected_specialty') is None:
            st.session_state.selected_specialty = specialties[0]

        col1, _, _ = st.columns(3)
        with col1:
            selected_specialty = st.selectbox('Select Specialty', specialties, index=list(specialties).index(st.session_state.selected_specialty), key='specialty_select')

        # Save the selected specialty to session state
        st.session_state.selected_specialty = selected_specialty

        # Filter data based on selected specialty
        specialty_df = appointments_df[appointments_df['specialty'] == selected_specialty]
        # Convert 'month' column to datetime and adjust to end of month
        specialty_df['month'] = pd.to_datetime(specialty_df['month']).dt.to_period('M').dt.to_timestamp('M')
        # Sort by month
        specialty_df = specialty_df.sort_values('month')

        ### **1. Additions and Removals Plot**
        st.subheader("Additions (Referrals) and Removals Over Time")
        fig1 = px.line(
            specialty_df,
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

        max_date = specialty_df['month'].max()

        col1, col2, _, _ = st.columns(4)
        with col1:
            baseline_start_date = st.date_input(
                'Baseline Start Date',
                value=max_date - pd.DateOffset(months=5)
            )
        with col2:
            baseline_end_date = st.date_input(
                'Baseline End Date',
                value=max_date
            )

        # Convert selected dates to datetime
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
            specialty_df,
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
    st.write("Please upload the Appointment Data in the sidebar on the **Home** page.")
