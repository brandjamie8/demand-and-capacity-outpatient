import streamlit as st 
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress

st.title("Referral Demand Analysis")

if 'referral_df' in st.session_state and st.session_state.referral_df is not None:
    referral_df = st.session_state.referral_df

    # Ensure required columns are present
    required_columns = ['month', 'specialty', 'priority', 'referrals']
    if all(column in referral_df.columns for column in required_columns):
        # Consistent order of priorities
        priority_order = ['2-week wait', 'Urgent', 'Routine']
        
        selected_specialty = st.session_state.selected_specialty

        # Filter referral data based on selected specialty
        specialty_referral_df = referral_df[referral_df['specialty'] == selected_specialty].copy()
        specialty_referral_df.loc[:, 'month'] = pd.to_datetime(specialty_referral_df['month']).dt.to_period('M').dt.to_timestamp('M')

        # Set the priority category order
        specialty_referral_df['priority'] = pd.Categorical(specialty_referral_df['priority'], categories=priority_order, ordered=True)

        st.subheader(f"Referral Trends for {selected_specialty}")

        # Default baseline period as the last 6 months of available data
        max_date = specialty_referral_df['month'].max()
        default_baseline_start = max_date - pd.DateOffset(months=5)  # Last 6 months

        # Allow user to adjust baseline period
        baseline_start = st.date_input('Baseline Start Date', value=default_baseline_start, min_value=specialty_referral_df['month'].min(), max_value=max_date)
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
            y='referrals',
            color='priority',
            labels={'referrals': 'Number of Referrals'},
            title=f'Referrals Over Time for {selected_specialty}',
            color_discrete_sequence=px.colors.qualitative.Prism  # Different color scheme without red
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
            fig.add_trace(
                go.Scatter(
                    x=[baseline_start, baseline_end],
                    y=[None, None],
                    mode='markers',
                    marker=dict(color='LightGrey'),
                    name='Baseline Period',
                    showlegend=True
                )
            )

        st.plotly_chart(fig, use_container_width=True)

        # Extrapolate baseline referrals to a year's worth
        if not baseline_referral_df.empty:
            num_baseline_months = (baseline_end.year - baseline_start.year) * 12 + (baseline_end.month - baseline_start.month) + 1
            total_referrals_baseline = baseline_referral_df['referrals'].sum()
            baseline_yearly_referrals = (total_referrals_baseline / num_baseline_months) * 12
            st.write(f"**Total Referrals (12-Month Equivalent):** {baseline_yearly_referrals:.0f}")

            # Calculate percentage of each referral priority in the baseline period
            priority_percentages = baseline_referral_df.groupby('priority', observed=False)['referrals'].sum() / total_referrals_baseline * 100

            st.write("**Percentage of Referrals by Priority in Baseline Period:**")
            for priority in priority_order:
                if priority in priority_percentages:
                    st.write(f"- **{priority}:** {priority_percentages[priority]:.2f}%")

            # Create a bar chart for total referrals (12-month equivalent) by priority
            baseline_priority_totals = baseline_referral_df.groupby('priority')['referrals'].sum() / num_baseline_months * 12
            baseline_priority_totals = baseline_priority_totals.reindex(priority_order)  # Ensure consistent priority order

            fig_baseline = px.bar(
                baseline_priority_totals.reset_index(),
                x='priority',
                y='referrals',
                title='Total Referrals (12-Month Equivalent) by Priority',
                labels={'referrals': 'Number of Referrals', 'priority': 'Priority'},
                text='referrals',
                color='priority',
                color_discrete_sequence=px.colors.qualitative.Prism  # Same colors as the line chart
            )
            fig_baseline.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            st.plotly_chart(fig_baseline, use_container_width=True)

        # Determine trends for each priority and forecast increase
        st.subheader("Referral Trend Analysis")

        priority_trend_data = []
        for priority in priority_order:
            priority_df = specialty_referral_df[specialty_referral_df['priority'] == priority]
            if not priority_df.empty:
                priority_df = priority_df.sort_values('month')
                x = priority_df['month'].map(pd.Timestamp.toordinal)
                y = priority_df['referrals']

                # Perform linear regression
                slope, intercept, r_value, p_value, std_err = linregress(x, y)

                # Calculate trend increase percentage for next year
                if slope > 0:
                    avg_monthly_referrals = y.mean()
                    trend_increase_percentage = (slope * 12) / avg_monthly_referrals * 100
                else:
                    trend_increase_percentage = 0

                priority_trend_data.append({
                    'priority': priority,
                    'trend_increase_percentage': trend_increase_percentage
                })

                st.write(f"**{priority} referrals trend increase:** {trend_increase_percentage:.2f}%")

        # Calculate the forecasted referrals for the next year including the trend increase
        st.subheader("Forecasted Referrals for the Next Year")

        forecasted_referrals = []
        for data in priority_trend_data:
            priority = data['priority']
            trend_increase_percentage = data['trend_increase_percentage']
            baseline_priority_referrals = (baseline_referral_df[baseline_referral_df['priority'] == priority]['referrals'].sum() / num_baseline_months) * 12

            # Apply increase if trend is positive
            if trend_increase_percentage > 0:
                forecasted_priority_referrals = baseline_priority_referrals * (1 + trend_increase_percentage / 100)
            else:
                forecasted_priority_referrals = baseline_priority_referrals

            forecasted_referrals.append({
                'priority': priority,
                'forecasted_referrals': forecasted_priority_referrals
            })

        # Create a DataFrame for forecasted referrals
        forecasted_df = pd.DataFrame(forecasted_referrals)

        # Save the forecasted data and total to session state
        st.session_state['forecasted_referrals'] = forecasted_df
        st.session_state['forecasted_total'] = forecasted_df['forecasted_referrals'].sum()
        
        # Plot forecasted referrals split by priority
        fig_forecast = px.bar(
            forecasted_df,
            x='priority',
            y='forecasted_referrals',
            title='Forecasted Referrals for the Next Year (Split by Priority)',
            labels={'forecasted_referrals': 'Number of Referrals', 'priority': 'Priority'},
            text='forecasted_referrals',
            color='priority',
            color_discrete_sequence=px.colors.qualitative.Prism  # Same colors as the line chart
        )
        fig_forecast.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        st.plotly_chart(fig_forecast, use_container_width=True)

        # Display total forecasted referrals
        total_forecasted_referrals = forecasted_df['forecasted_referrals'].sum()
        st.write(f"**Total Forecasted Referrals for Next Year:** {total_forecasted_referrals:.0f}")

    else:
        st.error("Referral data is missing required columns.")
else:
    st.write("Please upload the **Referral Data CSV** file in the **Home** page.")
