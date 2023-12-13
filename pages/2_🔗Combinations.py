import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Drug Combinations",
    page_icon="link-45deg",
)

st.write("# Drug Combinations")

disclaimer = """
<div style='text-align: justify; font-size:10px'>
Disclaimer:<br>
The recommendations provided in this report are generated based on the available data and algorithms. It is crucial to note that these recommendations should only be considered as supplementary information and not as a substitute for professional medical advice. This report is intended for use by qualified healthcare professionals, and decisions regarding patient care should be made in consultation with a licensed medical practitioner. The information presented here may not encompass all aspects of an individual's medical history or current health condition.<br>
The developers and providers of this report disclaim any liability for the accuracy, completeness, or usefulness of the recommendations, and they are not responsible for any adverse consequences resulting from the use of this information.<br>
Patients and healthcare providers are encouraged to exercise their professional judgment and consider individual patient characteristics when making medical decisions.
</div>
"""

st.markdown(disclaimer, unsafe_allow_html=True)
