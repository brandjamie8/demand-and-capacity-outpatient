import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


st.title("Historic Waiting List")

st.markdown("""
This page analyses the historic waiting list data and provides a predicted starting point for future capacity planning.

- **Baseline Period Selection:** Choose a period that represents typical additions and removals to the waiting list. The model uses data from this period to simulate future changes.
- **Modelling Start Date:** Select a future date after the latest available data. The model predicts the waiting list size up to this date.
""")

# Define consistent colors for data types
color_map = {
    'Historic Total Waiting List': '#006cb5',
    'Actual Total Waiting List': 'lightblue',
    'Actual': '#006cb5',
    'Predicted Total Waiting List': '#f5136f',
    'Predicted': '#f5136f',
    'additions to waiting list': 'orange',
    'removals from waiting list': 'purple',
    'Mean Prediction': '#f5136f'
}


# Check if data is available in session state
if st.session_state.waiting_list_df is not None and st.session_state.procedure_df is not None:
    waiting_list_df = st.session_state.waiting_list_df

    # Ensure required columns are present
    waiting_list_required_columns = ['month', 'specialty', 'additions to waiting list', 'removals from waiting list', 'total waiting list']

    if all(column in waiting_list_df.columns for column in waiting_list_required_columns):

        # Select specialty
        specialties = waiting_list_df['specialty'].unique()
        if st.session_state.selected_specialty is None:
            st.session_state.selected_specialty = specialties[0]

        col1, _, _ = st.columns(3)
        with col1:
            selected_specialty = st.selectbox('Select Specialty', specialties, index=list(specialties).index(st.session_state.selected_specialty), key='specialty_select')

        # Save the selected specialty to session state
        st.session_state.selected_specialty = selected_specialty

        # Filter data based on selected specialty
        waiting_list_specialty_df = waiting_list_df[waiting_list_df['specialty'] == selected_specialty]
        # Convert 'month' column to datetime and adjust to end of month
        waiting_list_specialty_df['month'] = pd.to_datetime(waiting_list_specialty_df['month']).dt.to_period('M').dt.to_timestamp('M')
        # Sort by month
        waiting_list_specialty_df = waiting_list_specialty_df.sort_values('month')

        ### **1. Additions and Removals Plot (fig1)**
        st.subheader("Additions and Removals from Waiting List Over Time")
        fig1 = px.line(
            waiting_list_specialty_df,
            x='month',
            y=['additions to waiting list', 'removals from waiting list'],
            labels={'value': 'Number of Patients', 'variable': 'Legend'},
            title='Additions and Removals from Waiting List',
            height=600,
            color_discrete_map=color_map
        )

        fig1.update_traces(line=dict(width=3))

        # Display fig1 before the baseline date selections
        fig1_placeholder = st.empty()
        fig1_placeholder.plotly_chart(fig1, use_container_width=True)

        ### **2. Baseline Period Selection**
        st.subheader("Baseline Period Selection")
        st.write("""
        Select the start and end dates for the baseline period. The model will use data from this period to simulate future additions and removals from the waiting list. The selected period should reflect typical activity.
        """)

        max_date = waiting_list_specialty_df['month'].max()
           
        col1, col2, _, _ = st.columns(4)
        with col1:
            baseline_start_date = st.date_input(
                'Baseline Start Date',
                value = max_date - pd.DateOffset(months=5)
            )
        with col2:
            baseline_end_date = st.date_input(
                'Baseline End Date',
                value = max_date
            )

        # Convert selected dates to datetime
        baseline_start_date = pd.to_datetime(baseline_start_date).to_period('M').to_timestamp('M')
        baseline_end_date = pd.to_datetime(baseline_end_date).to_period('M').to_timestamp('M')

        baseline_months = (baseline_end_date.year - baseline_start_date.year) * 12 + (baseline_end_date.month - baseline_start_date.month)
        
        if 'baseline_start_date' not in st.session_state:
            st.session_state.baseline_start_date = baseline_start_date

        if 'baseline_end_date' not in st.session_state:
            st.session_state.baseline_end_date = baseline_end_date

        if 'baseline_months' not in st.session_state:
            st.session_state.baseline_months = baseline_months
        
        # Update fig1 to highlight the baseline period if dates are selected
        if baseline_start_date != baseline_end_date:
            fig1.add_vrect(
                x0=baseline_start_date,
                x1=baseline_end_date,
                fillcolor="LightGrey",
                opacity=0.5,
                layer="below",
                line_width=0,
            )
            fig1.add_trace(
                go.Scatter(
                    x=[baseline_start_date, baseline_end_date],
                    y=[None, None],
                    mode='markers',
                    marker=dict(color='LightGrey'),
                    name='Baseline Period',
                    showlegend=True
                )
            )
            # Re-display fig1 with the baseline highlight
            fig1_placeholder.plotly_chart(fig1, use_container_width=True)

        ### **3. Waiting List Over Time Plot (fig2)**
        st.subheader("Total Size of the Waiting List Over Time")

        # Initialize fig2 without predictions
        fig2 = px.line(
            waiting_list_specialty_df,
            x='month',
            y='total waiting list',
            labels={'total waiting list': 'Total Waiting List'},
            title='Total Size of the Waiting List',
            height=600,
            color_discrete_map=color_map
        )
        fig2.update_traces(line=dict(width=3))
        
        # Display fig2
        fig2_placeholder = st.empty()
        fig2_placeholder.plotly_chart(fig2, use_container_width=True)

        st.write("""
        Select the date from which you want the model to start predicting the waiting list size. This date should be after the latest month in the data.
        """)

        # Get the maximum date from the DataFrame
        max_date = waiting_list_specialty_df['month'].max()
        
        # Calculate the next March after max_date
        if max_date.month >= 3:
            next_march_year = max_date.year + 1
        else:
            next_march_year = max_date.year
        
        # Set the last day of March as the default value
        default_model_start_date = pd.Timestamp(year=next_march_year, month=3, day=31)
        
        # Check if 'model_start_date' is already in session state
        if 'model_start_date' not in st.session_state:
            # Initialize with default value if not set
            st.session_state.model_start_date = default_model_start_date
        
        col1, _, _ = st.columns(3)
        with col1:
            # Use the value from session state for the date input
            model_start_date = st.date_input(
                'Start Date for Modeling',
                value=st.session_state.model_start_date
            )
        
        # Update session state with the selected date
        st.session_state.model_start_date = model_start_date
        
        # Convert modeling start date to datetime
        model_start_date = pd.to_datetime(st.session_state.model_start_date).to_period('M').to_timestamp('M')


        
        # Latest month in the data
        latest_month_in_data = waiting_list_specialty_df['month'].max()

        ### **5. Add Prediction Line to fig2 and Print Prediction Message**
        if model_start_date > latest_month_in_data:
            # Calculate the number of months to predict
            num_future_months = (model_start_date.year - latest_month_in_data.year) * 12 + \
                                (model_start_date.month - latest_month_in_data.month)

            # Proceed with prediction if the number of months is positive
            if num_future_months > 0:
                # Filter the baseline data
                baseline_data = waiting_list_specialty_df[
                    (waiting_list_specialty_df['month'] >= baseline_start_date) &
                    (waiting_list_specialty_df['month'] <= baseline_end_date)
                ]

                if baseline_data.empty:
                    st.error("No data available in the selected baseline period.")
                else:
                    # Get the last known total waiting list size
                    last_total_waiting_list = waiting_list_specialty_df.iloc[-1]['total waiting list']

                    # Create date range for future months, including the modeling start date
                    future_months = pd.date_range(
                        start=latest_month_in_data + pd.offsets.MonthEnd(1),
                        end=model_start_date,
                        freq='M'
                    )

                    
                    # Initialize a DataFrame to store total waiting list sizes for each simulation
                    simulation_results = pd.DataFrame({'month': future_months})

                    num_simulations = 100
                    
                    for sim in range(num_simulations):
                        current_total = last_total_waiting_list
                        predicted_totals = []
                        for month in future_months:
                            sampled_addition = baseline_data['additions to waiting list'].sample(n=1).values[0]
                            sampled_removal = baseline_data['removals from waiting list'].sample(n=1).values[0]
                            current_total = current_total + sampled_addition - sampled_removal
                            predicted_totals.append(current_total)
                        # Add the predicted totals to the DataFrame
                        simulation_results[f'simulation_{sim+1}'] = predicted_totals
                    
                    # Calculate percentiles for the predictions
                    percentiles = [5, 25, 50, 75, 95]
                    percentile_values = simulation_results.filter(like='simulation_').quantile(q=[p/100 for p in percentiles], axis=1).T
                    percentile_values.columns = [f'percentile_{p}' for p in percentiles]
    
                    # Merge percentiles with simulation_results
                    simulation_results = pd.concat([simulation_results[['month']], percentile_values], axis=1)
    
                    # Use the 50th percentile (median) as the average prediction
                    predictions_df = simulation_results[['month', 'percentile_50']].rename(columns={'percentile_50': 'total waiting list'})
                    predictions_df['Data Type'] = 'Predicted'

                    # Prepare combined data
                    actual_data = waiting_list_specialty_df.copy()
                    actual_data['Data Type'] = 'Actual'

                    combined_df = pd.concat([actual_data, predictions_df], ignore_index=True)

                    # Update fig2 with predictions
                    fig2 = px.line(
                        combined_df,
                        x='month',
                        y='total waiting list',
                        color='Data Type',
                        line_dash='Data Type',
                        labels={'total waiting list': 'Total Waiting List', 'month': 'Month'},
                        title='Total Size of the Waiting List with Predictions',
                        height=600,
                        color_discrete_map=color_map
                    )
                    fig2.update_traces(line=dict(width=3))
                    
                    # Add shaded areas for the percentiles
                    fig2.add_traces([
                        go.Scatter(
                            name='5th-95th Percentile',
                            x=simulation_results['month'].tolist() + simulation_results['month'][::-1].tolist(),
                            y=simulation_results['percentile_95'].tolist() + simulation_results['percentile_5'][::-1].tolist(),
                            fill='toself',
                            fillcolor='rgba(200, 200, 200, 0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            hoverinfo="skip",
                            showlegend=True
                        ),
                        go.Scatter(
                            name='25th-75th Percentile',
                            x=simulation_results['month'].tolist() + simulation_results['month'][::-1].tolist(),
                            y=simulation_results['percentile_75'].tolist() + simulation_results['percentile_25'][::-1].tolist(),
                            fill='toself',
                            fillcolor='rgba(160, 160, 160, 0.3)',
                            line=dict(color='rgba(255,255,255,0)'),
                            hoverinfo="skip",
                            showlegend=True
                        )
                    ])
                    
                    # Customize line styles
                    fig2.update_traces(
                        line=dict(width=3),
                        selector=dict(mode='lines')
                    )

                    fig2.update_traces(
                        line=dict(dash='dash', width=4),
                        selector=dict(name='Predicted')
                    )

                    # Re-display fig2 with predictions
                    fig2_placeholder.plotly_chart(fig2, use_container_width=True)

                    # Access the percentile values for the last predicted month
                    last_month_data = simulation_results.iloc[-1]
                    percentile_5 = last_month_data['percentile_5']
                    percentile_25 = last_month_data['percentile_25']
                    percentile_50 = last_month_data['percentile_50']  # Median
                    percentile_75 = last_month_data['percentile_75']
                    percentile_95 = last_month_data['percentile_95']
                    
                    # Display the prediction in larger font
                    st.markdown(f"### Predicted Waiting List Size: **{percentile_50:.0f}**")
                    
                    st.write(f"""
                    - **Prediction Date:** {model_start_date.strftime('%b %Y')}
                    - **Expected Range (50% probability):** {percentile_25:.0f} to {percentile_75:.0f}
                    - **Expected Range (90% probability):** {percentile_5:.0f} to {percentile_95:.0f}
                    """)
                    st.write(f"This will be the starting position for modelling the impact of future capacity.")
                    st.session_state['waiting_list_start'] = percentile_50
                    
        st.write(f"")
        ### **6. Validation of Prediction Methodology**
        st.subheader("Validation of Total Waiting List Prediction Methodology")
        
        st.write("""
        This section validates the prediction methodology by using data from the 6 months before the baseline period to predict the baseline period. 
        The results are averaged over multiple simulations, with the mean prediction plotted as a line, and the 50th and 95th percentiles displayed as shaded areas.
        The entire historic waiting list data is also included in the chart for context.
        """)
        
        # Define the validation period (6 months before baseline start)
        validation_start_date = baseline_start_date - pd.DateOffset(months=6)
        validation_end_date = baseline_start_date - pd.DateOffset(months=1)
        
        # Filter validation data
        validation_data = waiting_list_specialty_df[
            (waiting_list_specialty_df['month'] >= validation_start_date) &
            (waiting_list_specialty_df['month'] <= validation_end_date)
        ]
        
        if validation_data.empty:
            st.error("No data available in the validation period.")
        else:
            # Filter baseline data
            actual_baseline_data = waiting_list_specialty_df[
                (waiting_list_specialty_df['month'] >= baseline_start_date) &
                (waiting_list_specialty_df['month'] <= baseline_end_date)
            ]
            
            # Initialize a DataFrame to store predictions for each simulation
            simulation_results = pd.DataFrame({'month': actual_baseline_data['month']})
            num_simulations = 100  # Number of simulations
        
            for sim in range(num_simulations):
                current_total = validation_data.iloc[-1]['total waiting list']  # Last total from validation period
                simulated_totals = []
                for _, row in actual_baseline_data.iterrows():
                    sampled_addition = validation_data['additions to waiting list'].sample(n=1).values[0]
                    sampled_removal = validation_data['removals from waiting list'].sample(n=1).values[0]
                    current_total = current_total + sampled_addition - sampled_removal
                    simulated_totals.append(current_total)
                simulation_results[f'simulation_{sim + 1}'] = simulated_totals
        
            # Calculate percentiles and mean
            percentiles = [5, 25, 50, 75, 95]
            percentile_values = simulation_results.filter(like='simulation_').quantile(
                q=[p / 100 for p in percentiles], axis=1).T
            percentile_values.columns = [f'percentile_{p}' for p in percentiles]
            simulation_results = pd.concat([simulation_results[['month']], percentile_values], axis=1)
        
            # Include all historic waiting list data
            historic_data = waiting_list_specialty_df[['month', 'total waiting list']].rename(
                columns={'total waiting list': 'Historic Total Waiting List'}
            )
        
            # Combine data for visualization
            actual_baseline = actual_baseline_data[['month', 'total waiting list']].rename(
                columns={'total waiting list': 'Actual Total Waiting List'}
            )
            comparison_df = pd.merge(
                historic_data, actual_baseline, on='month', how='outer'
            )
        
            # Plot all data and percentiles
            st.subheader("Comparison of Historic, Actual Baseline, and Predicted Baseline")
            fig_validation = px.line(
                comparison_df.melt(id_vars='month', var_name='Data Type', value_name='Total Waiting List'),
                x='month',
                y='Total Waiting List',
                color='Data Type',
                labels={'Total Waiting List': 'Total Waiting List', 'month': 'Month'},
                title='Validation of Baseline Prediction Methodology',
                height=600,
                color_discrete_map=color_map
            )

            fig_validation.update_traces(line=dict(width=3))
        
            # Add shaded areas for percentiles
            fig_validation.add_traces([
                go.Scatter(
                    name='5th-95th Percentile',
                    x=simulation_results['month'].tolist() + simulation_results['month'][::-1].tolist(),
                    y=simulation_results['percentile_95'].tolist() + simulation_results['percentile_5'][::-1].tolist(),
                    fill='toself',
                    fillcolor='rgba(200, 200, 200, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    hoverinfo="skip",
                    showlegend=True
                ),
                go.Scatter(
                    name='25th-75th Percentile',
                    x=simulation_results['month'].tolist() + simulation_results['month'][::-1].tolist(),
                    y=simulation_results['percentile_75'].tolist() + simulation_results['percentile_25'][::-1].tolist(),
                    fill='toself',
                    fillcolor='rgba(160, 160, 160, 0.3)',
                    line=dict(color='rgba(255,255,255,0)'),
                    hoverinfo="skip",
                    showlegend=True
                )
            ])
        
            # Add mean prediction line
            fig_validation.add_trace(
                go.Scatter(
                    name='Mean Prediction',
                    x=simulation_results['month'],
                    y=simulation_results['percentile_50'],
                    mode='lines',
                    line=dict(color='#f5136f', width=3, dash='dash')
                )
            )
            
            st.plotly_chart(fig_validation, use_container_width=True)
        
            # Calculate evaluation metrics
            comparison_actual_predicted = pd.merge(
                actual_baseline_data,
                simulation_results[['month', 'percentile_50']].rename(columns={'percentile_50': 'Predicted Total Waiting List'}),
                on='month'
            )
            mae = (comparison_actual_predicted['total waiting list'] - comparison_actual_predicted['Predicted Total Waiting List']).abs().mean()
            mse = ((comparison_actual_predicted['total waiting list'] - comparison_actual_predicted['Predicted Total Waiting List']) ** 2).mean()
        
            st.write(f"**Mean Absolute Error (MAE):** {mae:.2f}")
            st.write(f"**Mean Squared Error (MSE):** {mse:.2f}")
            st.write("""
            A lower MAE and MSE indicate better predictive accuracy. Use this information to assess the reliability of the model.
            """)
            
            # Compare final month mean prediction to actual value
            final_month = comparison_actual_predicted.iloc[-1]
            final_actual = final_month['total waiting list']
            final_predicted = final_month['Predicted Total Waiting List']
            st.write(f"**Final Month Comparison:** The actual value for the final month is {final_actual:.0f}, "
                     f"Mean predicted value is {final_predicted:.0f}.")

    else:
        st.error("Uploaded files do not contain the required columns.")
else:
    st.write("Please upload the Waiting List Data in the sidebar on the **Home** page.")
