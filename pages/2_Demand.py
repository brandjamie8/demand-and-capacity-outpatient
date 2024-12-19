import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("Referral Demand Analysis")

if 'referral_df' in st.session_state and st.session_state.referral_df is not None:
    referral_df = st.session_state.referral_df

    # Ensure required columns are present
    required_columns = ['month', 'specialty', 'additions']
    if all(column in referral_df.columns for column in required_columns):
        selected_specialty = st.session_state.selected_specialty

        # Filter referral data based on selected specialty
        specialty_referral_df = referral_df[referral_df['specialty'] == selected_specialty].copy()
        specialty_referral_df['month'] = pd.to_datetime(specialty_referral_df['month']).dt.to_period('M').dt.to_timestamp('M')

        # Sort data by month to fix line chart order
        specialty_referral_df.sort_values('month', inplace=True)

        st.subheader(f"Referral Trends for {selected_specialty}")

        # Default baseline period as the last 6 months of available data
        max_date = specialty_referral_df['month'].max()
        default_baseline_start = max_date - pd.DateOffset(months=5)  # Last 6 months

        col1, col2, _, _ = st.columns(4)
        with col1:
            baseline_start = st.date_input('Baseline Start Date', value=default_baseline_start, min_value=specialty_referral_df['month'].min(), max_value=max_date)
        with col2:
            baseline_end = st.date_input('Baseline End Date', value=max_date, min_value=specialty_referral_df['month'].min(), max_value=max_date)

        # Convert baseline dates to datetime
        baseline_start = pd.to_datetime(baseline_start).to_period('M').to_timestamp('M')
        baseline_end = pd.to_datetime(baseline_end).to_period('M').to_timestamp('M')

        # Filter the referral data based on the selected baseline period
        baseline_referral_df = specialty_referral_df[(specialty_referral_df['month'] >= baseline_start) & (specialty_referral_df['month'] <= baseline_end)]

        # Plot referral trends and highlight the baseline period
        fig = px.line(
            specialty_referral_df,
            x='month',
            y='additions',
            labels={'additions': 'Number of Referrals'},
            title=f'Referrals Over Time for {selected_specialty}'
        )

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

        # Extrapolate baseline referrals to a year's worth
        if not baseline_referral_df.empty:
            num_baseline_months = (baseline_end.year - baseline_start.year) * 12 + (baseline_end.month - baseline_start.month) + 1
            total_referrals_baseline = baseline_referral_df['additions'].sum()
            baseline_yearly_referrals = (total_referrals_baseline / num_baseline_months) * 12
            st.write(f"**Total Referrals (12-Month Equivalent):** {baseline_yearly_referrals:.0f}")

        # Display total referrals for baseline period
        if not baseline_referral_df.empty:
            st.subheader("Baseline Referral Summary")
            st.write(f"**Total Referrals in Baseline Period ({baseline_start:%Y-%m} to {baseline_end:%Y-%m}):** {total_referrals_baseline:.0f}")

    else:
        st.error("Referral data is missing required columns.")
else:
    st.write("Please upload the **Referral Data CSV** file in the **Home** page.")
