import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress
import numpy as np

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


        
        # Display baseline period
        baseline_start = st.session_state.baseline_start_date
        baseline_end = st.session_state.baseline_end_date
        num_baseline_months = (pd.to_datetime(baseline_end).to_period('M') - pd.to_datetime(baseline_start).to_period('M')).n + 1

        # Filter data for the baseline period
        baseline_df = specialty_referral_df[
            (specialty_referral_df['month'] >= pd.to_datetime(baseline_start)) &
            (specialty_referral_df['month'] <= pd.to_datetime(baseline_end))
        ]

        # Display total and scaled baseline referrals
        total_baseline_additions = baseline_df['additions'].sum()
        baseline_scaled_additions = (total_baseline_additions / num_baseline_months) * 12
        st.write(f"**Total Baseline Referrals:** {total_baseline_additions:.0f}")
        st.write(f"**Annualized Baseline Referrals:** {baseline_scaled_additions:.0f}")

        # --- Analyze Model Fit ---
        st.subheader("Model Fit: Baseline Average vs. Trend Line")
        pre_baseline_df = specialty_referral_df[
            (specialty_referral_df['month'] < pd.to_datetime(baseline_start))
        ].tail(12)  # Use the last 12 months before the baseline

        if pre_baseline_df.empty or pre_baseline_df.shape[0] < 2:
            st.warning("Not enough data points before the baseline period to perform regression analysis.")
        else:
            # Perform regression on pre-baseline data
            pre_months_ordinal = pre_baseline_df['month'].map(pd.Timestamp.toordinal)
            slope, intercept, _, _, _ = linregress(pre_months_ordinal, pre_baseline_df['additions'])

            # Predict baseline demand using regression
            baseline_months_ordinal = baseline_df['month'].map(pd.Timestamp.toordinal)
            predicted_regression = intercept + slope * baseline_months_ordinal
            predicted_average = [baseline_scaled_additions / 12] * len(baseline_months_ordinal)

            # Calculate errors
            actual_baseline = baseline_df['additions']
            error_regression = np.mean(np.abs(actual_baseline - predicted_regression))
            error_average = np.mean(np.abs(actual_baseline - predicted_average))

            # Determine best fit
            st.write(f"**Mean Absolute Error (Regression):** {error_regression:.2f}")
            st.write(f"**Mean Absolute Error (Average):** {error_average:.2f}")
            best_fit = "Average" if error_average < error_regression else "Regression"
            st.write(f"**Best Fit Model:** {best_fit}")

            # Plot baseline fit
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=baseline_df['month'], y=actual_baseline, mode='lines+markers', name='Actual Demand'))
            fig.add_trace(go.Scatter(x=baseline_df['month'], y=predicted_average, mode='lines', name='Predicted (Average)', line=dict(dash='dash')))
            fig.add_trace(go.Scatter(x=baseline_df['month'], y=predicted_regression, mode='lines', name='Predicted (Regression)', line=dict(dash='dot')))
            st.plotly_chart(fig, use_container_width=True)

        # --- Predict Future Demand ---
        st.subheader("Predict Future Demand")
        future_months = pd.date_range(start=pd.to_datetime(st.session_state.model_start_date), periods=12, freq='M')
        if best_fit == "Average":
            future_predictions = [baseline_scaled_additions / 12] * len(future_months)
        else:
            future_months_ordinal = future_months.map(pd.Timestamp.toordinal)
            future_predictions = intercept + slope * future_months_ordinal

        # Create DataFrame for future predictions
        future_df = pd.DataFrame({
            'month': future_months,
            'predicted_demand': future_predictions
        })

        # Display future predictions
        st.write(f"**Total Predicted Demand for Next 12 Months:** {future_df['predicted_demand'].sum():.0f}")

        # Plot future predictions
        fig_future = go.Figure()
        fig_future.add_trace(go.Scatter(x=specialty_referral_df['month'], y=specialty_referral_df['additions'], mode='lines+markers', name='Historical Demand'))
        fig_future.add_trace(go.Scatter(x=future_df['month'], y=future_df['predicted_demand'], mode='lines+markers', name='Predicted Demand'))
        st.plotly_chart(fig_future, use_container_width=True)
    else:
        st.error("Referral data is missing required columns.")
else:
    st.write("Please upload the **Referral Data CSV** file in the **Home** page.")
