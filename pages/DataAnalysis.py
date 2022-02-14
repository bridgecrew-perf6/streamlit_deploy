import streamlit as st

from utils.cache.s3 import s3_query

st.title("Data Analysis")

res = s3_query.read_value('sql_query')
st.write(res)
