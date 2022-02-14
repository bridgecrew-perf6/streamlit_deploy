import streamlit as st

st.title("Text Classification")

# number input
res = st.number_input("Number Input1", value=0, format="%d")
# show
st.write(res)
