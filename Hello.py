import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Pharmacogenomic Drug Response Prediction",
    page_icon="💊",
)

st.write("# Welcome to Pharmacogenomic Drug Response Prediction")

st.sidebar.success("Select a page to begin")

st.markdown(
    """
    Understanding the genetic basis of drug response is a key step towards precision medicine.
    Pharmacogenomic drug response prediction is a machine learning task that aims to predict the response of a drug
    given the genetic profile of a patient. This web app allows you to explore the performance of different machine
    learning models on this task.
    ### Want to download the data?
    - Check out [cpic-data.git](https://github.com/cpicpgx/cpic-data/releases)
    - Can check out the [CPIC website](https://cpicpgx.org/guidelines/) for more information
"""
)