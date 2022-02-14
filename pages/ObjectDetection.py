import streamlit as st


st.title("Object Detection")

# number input
res = st.number_input("Number Input2", value=0, format="%d")
# show
st.write(res)
