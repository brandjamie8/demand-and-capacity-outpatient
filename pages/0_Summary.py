import streamlit as st
import pandas as pd

st.title("Specialty Summary Table")

# Ensure appointment data is available
if 'appointment_df' not in st.session_state or st.session_state.appointment_df is None:
    st.error("Appointment data is not available. Please upload the data in the previous section.")
    st.stop()

appointment_df = st.session_state.appointment_df

# Convert the 'month' column to datetime if not already
if not pd.api.types.is_datetime64_any_dtype(appointment_df['month']):
    appointment_df['month'] = pd.to_datetime(appointment_df['month'])

# User input for baseline period
st.subheader("Select Baseline Period")
min_date = appointment_df['month'].min().date()
max_date = appointment_df['month'].max().date()

col1, col2, _, _ = st.columns(4)
with col1:
    baseline_start = st.date_input("Baseline Start Month", min_value=min_date, max_value=max_date)
with col2:
    baseline_end = st.date_input("Baseline End Month", min_value=baseline_start, max_value=max_date)

# Validate baseline period
if baseline_start > baseline_end:
    st.error("Baseline start date must be before or equal to the end date.")
    st.stop()

# Filter appointment data for the baseline period
baseline_start = pd.to_datetime(baseline_start).to_period('M').to_timestamp('M')
baseline_end = pd.to_datetime(baseline_end).to_period('M').to_timestamp('M')

baseline_df = appointment_df[(appointment_df['month'] >= baseline_start) & (appointment_df['month'] <= baseline_end)]

# Get the number of months in the baseline period
num_baseline_months = baseline_df['month'].nunique()

# Check if there is sufficient data
if baseline_df.empty:
    st.error("No data available for the selected baseline period.")
    st.stop()

# Get referrals and removals grouped by specialty
specialty_summary = baseline_df.groupby('specialty').agg({
    'referrals': 'sum',
    'removals': 'sum',
    'sessions': 'sum',
    'cancelled sessions': 'sum',
    'minutes utilised': 'sum',
    'cases': 'sum'
}).reset_index()

# Calculate extrapolated values
scaling_factor = 12 / num_baseline_months
specialty_summary['Referrals (12-Month)'] = specialty_summary['referrals'] * scaling_factor
specialty_summary['Removals (12-Month)'] = specialty_summary['removals'] * scaling_factor
specialty_summary['Cases (12-Month)'] = specialty_summary['cases'] * scaling_factor

# Calculate deficit
specialty_summary['Deficit (12-Month)'] = specialty_summary['Referrals (12-Month)'] - specialty_summary['Removals (12-Month)']

# Add a message about the expected change to the waiting list
specialty_summary['Expected Change'] = specialty_summary.apply(
    lambda row: (
        f"Increase in waiting list by {row['Deficit (12-Month)']:.0f}" if row['Deficit (12-Month)'] > 0 else
        f"Decrease in waiting list by {-row['Deficit (12-Month)']:.0f}" if row['Deficit (12-Month)'] < 0 else
        "No change in waiting list"
    ),
    axis=1
)

# Determine capacity status message
session_duration_hours = 4
specialty_summary['Capacity Status'] = specialty_summary.apply(
    lambda row: (
        "Surplus capacity, waiting list will reduce" if row['Removals (12-Month)'] > row['Referrals (12-Month)'] else
        "Sufficient capacity to meet demand" if row['Removals (12-Month)'] == row['Referrals (12-Month)'] else
        "Insufficient capacity but more sessions would meet demand" if (row['sessions'] + row['cancelled sessions']) * session_duration_hours * 60 >= row['minutes utilised'] * scaling_factor else
        "Not meeting capacity, waiting list expected to grow"
    ),
    axis=1
)

# Select relevant columns to display
columns_to_display = [
    'specialty', 
    'referrals',
    'cases',
    'removals',
    'Expected Change',
    'Referrals (12-Month)',
    'Removals (12-Month)',
    'Capacity Status'
]

# Rename columns for better readability
specialty_summary_display = specialty_summary[columns_to_display].rename(columns={
    'specialty': 'Specialty',
    'referrals': 'Referrals (Baseline)',
    'removals': 'Removals (Baseline)',
    'cases': 'Cases (Baseline)'
})

# Display the summary table
st.header("Specialty Summary")
st.dataframe(specialty_summary_display)

# Add a download button for the table
st.download_button(
    label="Download Specialty Summary",
    data=specialty_summary_display.to_csv(index=False),
    file_name="specialty_summary.csv",
    mime="text/csv"
)
