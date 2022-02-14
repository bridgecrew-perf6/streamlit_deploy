import streamlit as st

st.title("Body Mass Index")

# input number
st.write("""
# Input number
""")
number = st.number_input("Number", value=0, min_value=0, max_value=100)
st.write(f"You entered: {number}")

