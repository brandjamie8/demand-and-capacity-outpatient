import streamlit as st
import pandas as pd

st.title("Specialty Summary Table")

# Ensure both dataframes are available
if 'appointment_df' not in st.session_state or st.session_state.appointment_df is None:
    st.error("Appointment data is not available. Please upload the data in the previous section.")
    st.stop()

if 'referral_df' not in st.session_state or st.session_state.referral_df is None:
    st.error("Referral data is not available. Please upload the data in the previous section.")
    st.stop()

appointment_df = st.session_state.appointment_df
referral_df = st.session_state.referral_df

# Convert the 'month' column to datetime if not already
for df in [appointment_df, referral_df]:
    if not pd.api.types.is_datetime64_any_dtype(df['month']):
        df['month'] = pd.to_datetime(df['month'])

# User input for baseline period
st.subheader("Select Baseline Period")
min_date = max(referral_df['month'].min().date(), appointment_df['month'].min().date())
max_date = min(referral_df['month'].max().date(), appointment_df['month'].max().date())

col1, col2, _, _ = st.columns(4)
with col1:
    baseline_start = st.date_input("Baseline Start Month", '2024-04-01', min_value=min_date, max_value=max_date)
with col2:
    baseline_end = st.date_input("Baseline End Month", min_value=baseline_start, max_value=max_date)

# Validate baseline period
if baseline_start > baseline_end:
    st.error("Baseline start date must be before or equal to the end date.")
    st.stop()

# Filter dataframes for the baseline period
baseline_start = pd.to_datetime(baseline_start).to_period('M').to_timestamp('M')
baseline_end = pd.to_datetime(baseline_end).to_period('M').to_timestamp('M')

referral_baseline_df = referral_df[(referral_df['month'] >= baseline_start) & (referral_df['month'] <= baseline_end)]
appointment_baseline_df = appointment_df[(appointment_df['month'] >= baseline_start) & (appointment_df['month'] <= baseline_end)]

# Aggregate both dataframes by specialty
referral_aggregated = referral_baseline_df.groupby('specialty').agg({'referrals': 'sum'}).reset_index()
appointment_aggregated = appointment_baseline_df.groupby('specialty').agg({'removals': 'sum'}).reset_index()

# Merge the aggregated dataframes on 'specialty'
specialty_summary = pd.merge(referral_aggregated, appointment_aggregated, on='specialty', how='outer').fillna(0)

# Calculate the number of months in the baseline period
num_baseline_months = (baseline_end.year - baseline_start.year) * 12 + (baseline_end.month - baseline_start.month) + 1
scaling_factor = 12 / num_baseline_months

# Calculate extrapolated values
specialty_summary['Referrals (12-Month)'] = specialty_summary['referrals'] * scaling_factor
specialty_summary['Removals (12-Month)'] = specialty_summary['removals'] * scaling_factor

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

# Select relevant columns to display
columns_to_display = [
    'specialty', 
    'referrals',
    'removals',
    'Expected Change',
    'Referrals (12-Month)',
    'Removals (12-Month)'
]

# Rename columns for better readability
specialty_summary_display = specialty_summary[columns_to_display].rename(columns={
    'specialty': 'Specialty',
    'referrals': 'Referrals (Baseline)',
    'removals': 'Removals (Baseline)'
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
