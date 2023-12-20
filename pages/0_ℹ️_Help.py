import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(
    layout="wide",
    page_title="Help",
    page_icon="info-lg",
)

st.write("# User Assistance")

st.write("## How to use the **Main Page**?")
st.markdown('''
    - You can upload the **.txt** file by clicking the **Browse files** button.
    - After uploading the file, click **Submit** to see the recommendations.
    - The **.txt** file should contain the Patients Name, ID, followed by Gene Symbols and Diplotypes in the following format:
''')

# BEGIN: ed8c6549bwf9
st.code('''
    name: John Doe
    id: 123456
    genesymbol,diplotype
    CYP2D6,*19/*38
    CYP2C9,*2/*4
    TPMT,*1/*11
    SLCO1B1,*1/*14
    CYP2B6,*5/*38
    CYP3A5,*6/*7
''', language='text')


st.write("## How to see the possible combinations and recommendations?")
st.markdown("- Select the desired **Gene Symbol** from the dropdown menu.")

# Add the image for selecting the gene symbol
st.image("images/select gene symbol.png")

st.markdown('''
    - After selecting the **Gene Symbol**, list of **Diplotypes** associated with the genotype will be shown in the dropdown menu.
    - Select the desired **Diplotypes** from the dropdown menu.
''')

# Add the image for selecting the diplotypes
st.image("images/select diplotype.png")

st.markdown('''
    - After selecting the **Diplotypes**, you can click **Submit** to see all the possible drug recommendations for the selected gene and its diplotype.
    - You can also select the **Drug** from the dropdown menu to see the recommendations for the selected drug.
''')

st.write("For further assistance, kindly contact us at [fcb.adnan10@gmail.com](mailto:)")
