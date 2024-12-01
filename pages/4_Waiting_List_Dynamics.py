import streamlit as st

st.title("Waiting List Dynamics")

st.write("""
In this section, we analyze the waiting list changes over the next year.
""")

if 'total_demand_cases' in st.session_state:
    # Input the waiting list start, additions, and removals
    waiting_list_start = st.number_input('Waiting List at Start of Year', min_value=0, value=500)
    waiting_list_additions = st.session_state.total_demand_cases
    waiting_list_removals = st.number_input('Number Removed from Waiting List During the Year', min_value=0, value=800)

    # Calculate end-of-year waiting list
    waiting_list_end = waiting_list_start + waiting_list_additions - waiting_list_removals
    st.write(f"**Waiting List at End of Year:** {waiting_list_end}")
else:
    st.write("Please complete the previous sections.")
