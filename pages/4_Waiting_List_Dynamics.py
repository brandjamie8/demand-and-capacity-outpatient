import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("Waiting List Dynamics")

st.write("""
Analyse the dynamics of the waiting list over the year.
""")

# Check if necessary variables are available in session state
if 'forecasted_total' in st.session_state and \
   'available_rtt_first' in st.session_state and \
   'available_rtt_followup' in st.session_state and \
   'available_non_rtt' in st.session_state:

    # User Inputs for Starting Waiting List and Additions/Removals
    st.header("Input Waiting List Variables")

    if 'waiting_list_start' not in st.session_state:
        st.session_state.waiting_list_start = 500

    waiting_list_start = st.number_input(
        'Waiting List at the Start of the Year',
        min_value=0,
        value=st.session_state.waiting_list_start,
        key='input_waiting_list_start'
    )

    # Calculate waiting list additions from forecasted referrals
    waiting_list_additions = st.session_state['forecasted_total']
    st.write(f"**Total Waiting List Additions (Based on Forecasted Referrals):** {waiting_list_additions:.0f}")

    # Input for removals not related to treatment
    if 'other_removals' not in st.session_state:
        st.session_state.other_removals = 100

    other_removals = st.number_input(
        'Removals from Waiting List Not Related to Treatment (e.g., patient choice, administrative removals)',
        min_value=0,
        value=st.session_state.other_removals,
        key='input_other_removals'
    )

    # Calculate removals from treatment based on available appointment capacity
    available_rtt_first = st.session_state['available_rtt_first']
    available_rtt_followup = st.session_state['available_rtt_followup']
    available_non_rtt = st.session_state['available_non_rtt']

    # Assume each referral requires one RTT first appointment, and then potentially follow-up appointments
    treatment_removals = min(available_rtt_first, waiting_list_additions)

    st.write(f"**Removals from Waiting List Due to Treatment (Based on Available Capacity):** {treatment_removals:.0f}")

    # Calculate the end of year waiting list size
    waiting_list_end = waiting_list_start + waiting_list_additions - treatment_removals - other_removals

    st.write(f"**Waiting List at End of Year:** {waiting_list_end:.0f}")

    # Save calculation to session state
    st.session_state.waiting_list_end = waiting_list_end

    # Waterfall Chart for Waiting List Dynamics
    st.subheader('Waterfall Chart: Waiting List Dynamics')

    measure = ["absolute", "relative", "relative", "relative", "total"]

    x = ["Start of Year Waiting List", "Additions", "Removals (Treatment)", "Removals (Other)", "End of Year Waiting List"]
    y = [waiting_list_start, waiting_list_additions, -treatment_removals, -other_removals, waiting_list_end]

    text = [f"{val:.0f}" for val in y]

    waterfall_fig = go.Figure(go.Waterfall(
        name="Waiting List",
        orientation="v",
        measure=measure,
        x=x,
        y=y,
        textposition="outside",
        text=text,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "green"}},
        increasing={"marker": {"color": "red"}},
        totals={"marker": {"color": "blue"}}
    ))

    waterfall_fig.update_layout(
        title="Waiting List Dynamics Over the Year",
        showlegend=False
    )

    st.plotly_chart(waterfall_fig, use_container_width=True)

    # Analysis of Appointments Needed per RTT Pathway
    st.subheader("Analysis of Appointments Needed per RTT Pathway")

    st.write(f"**RTT First Appointments Needed:** {waiting_list_additions:.0f}")
    st.write(f"**RTT Follow-up Appointments (Available Capacity):** {available_rtt_followup:.0f}")
    st.write(f"**Non-RTT Appointments (Available Capacity):** {available_non_rtt:.0f}")

    # Highlighting the impact of adjustments made to appointment capacity
    st.subheader("Impact of Adjustments to Appointment Capacity on Waiting List")

    st.write("""
    The above waterfall chart and analysis highlight how changes in appointment capacity (first, follow-up, and non-RTT) can influence the size of the waiting list.
    The removals due to treatment are directly impacted by the number of available RTT first appointments, which are required for each referral.
    """)

else:
    st.error("Please complete the **Referral Demand** and **Capacity Analysis** sections to provide necessary data.")
