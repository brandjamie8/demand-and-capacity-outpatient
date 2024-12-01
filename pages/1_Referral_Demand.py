import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Referral Demand Analysis")

if 'referral_df' in st.session_state and st.session_state.referral_df is not None:
    referral_df = st.session_state.referral_df

    # Ensure required columns are present
    required_columns = ['month', 'specialty', 'priority', 'referrals']
    if all(column in referral_df.columns for column in required_columns):
        specialties = referral_df['specialty'].unique()
        
        if st.session_state.selected_specialty is None:
            st.session_state.selected_specialty = specialties[0]

        selected_specialty = st.selectbox('Select Specialty', specialties, index=list(specialties).index(st.session_state.selected_specialty))

        # Save the selected specialty to session state
        st.session_state.selected_specialty = selected_specialty

        # Filter referral data based on selected specialty
        specialty_referral_df = referral_df[referral_df['specialty'] == selected_specialty].copy()
        specialty_referral_df.loc[:, 'month'] = pd.to_datetime(specialty_referral_df['month']).dt.to_period('M').dt.to_timestamp('M')

        st.subheader(f"Referral Trends for {selected_specialty}")
        fig = px.line(
            specialty_referral_df,
            x='month',
            y='referrals',
            color='priority',
            labels={'referrals': 'Number of Referrals'},
            title=f'Referrals Over Time for {selected_specialty}'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Allow user to select baseline period
        st.subheader("Baseline Period Selection")
        min_date = specialty_referral_df['month'].min()
        max_date = specialty_referral_df['month'].max()
        baseline_start = st.date_input('Baseline Start Date', value=min_date, min_value=min_date, max_value=max_date)
        baseline_end = st.date_input('Baseline End Date', value=max_date, min_value=min_date, max_value=max_date)

        # Convert baseline dates to datetime
        baseline_start = pd.to_datetime(baseline_start).to_period('M').to_timestamp('M')
        baseline_end = pd.to_datetime(baseline_end).to_period('M').to_timestamp('M')

        # Filter the referral data based on the selected baseline period
        baseline_referral_df = specialty_referral_df[(specialty_referral_df['month'] >= baseline_start) & (specialty_referral_df['month'] <= baseline_end)]

        if not baseline_referral_df.empty:
            total_referrals_baseline = baseline_referral_df['referrals'].sum()
            st.write(f"**Total Referrals in Baseline Period:** {total_referrals_baseline}")
        else:
            st.error("No data available for the selected baseline period.")
    else:
        st.error("Referral data is missing required columns.")
else:
    st.write("Please upload the **Referral Data CSV** file in the **Home** page.")
