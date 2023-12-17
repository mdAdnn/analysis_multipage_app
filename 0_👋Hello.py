import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="PGxAnalyzer",
    page_icon="💊",
)

st.write("# Welcome to PGxAnalyzer")

st.sidebar.success("Select a page to begin")

st.markdown(
    """
    - Understanding the genetic basis of drug response is a key step towards precision medicine.
    - PGxAnalyzer aims to predict the response of a drug given the genetic profile of a patient. 
    - This web app allows you to upload a file containing the genetic profile of a patient and returns the drug recommendations for the desired star allele.
    - Check out the **Help** page for more information.
"""
)