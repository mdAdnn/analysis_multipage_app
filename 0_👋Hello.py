import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import base64

# Set page configuration
st.set_page_config(
    layout="wide",
    page_title="PGxAnalyzer",
    page_icon="💊",
)

# Connect to database
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

# Welcome message
st.write("# Welcome to PGxAnalyzer")

# Sidebar message
st.sidebar.success("Select a page to begin")

# Brief introduction
st.markdown(
    """
    - Understanding the genetic basis of drug response is a key step towards precision medicine.
    - PGxAnalyzer aims to predict the response of a drug given the genetic profile of a patient. 
    - This web app allows you to upload a file containing the genetic profile of a patient and returns the drug recommendations for the desired star allele.
    - Kindly use a masked 'Name' and 'ID' for confidentiality and security reasons while using real patients data.
    - If there are combinations of phenotypes in the recommendation output while making a query on **Home Page** kindly refer next page **'Combinations'** (example for genes such as ***CYP2C19, CYP2B6, TPMT, CYP2D6*** etc.) for more detailed recommendations.
    - You can also download the sample text file below which can be used to upload on **Home Page** and get a better understanding of the system.
    - Check out the **Help** page for more information.
"""
)

# Function to create a download link
if st.button("Sample text file"):
    # Read input text file
    with open("sample data/input_values.txt", "r") as file:
        input_text = file.read()

    # Create a download link
    href = f'<a href="data:text/plain;base64,{base64.b64encode(input_text.encode()).decode()}" download="input_values.txt">Download Sample File</a>'
    st.markdown(href, unsafe_allow_html=True)

# Sample data
if st.button("Sample data"):
    # Read input text file
    with open("sample data/input_values.txt", "r") as file:
        input_text = file.read()

    def process_jsonb_columns(df):
        for col in df.columns:
            if isinstance(df[col][0], dict):
                df[col] = df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))
        return df
    
    st.markdown('''
        **Note:** The sample data 'Name', 'ID' is for demonstration purposes only. Any resemblance to real persons name is purely coincidental.
    ''')

    # Extract name, id, and timestamp
    lines = input_text.split('\n')  # Replace "file_contents" with "input_text"
    name = lines[0].split(':')[-1].strip()
    user_id = lines[1].split(':')[-1].strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Initialize the HTML string
    html_report = ""

    # Assume the file content contains genesymbol and diplotype separated by a comma
    pairs = [line.split(',') for line in lines[3:]]

    queried_genes = []  # Move the initialization here

    # Display name, id, and timestamp at the top
    st.write(f"**Name:** {name}")
    st.write(f"**ID:** {user_id}")
    st.write(f"**Timestamp:** {timestamp}")

    # Initialize a list to store gene symbols with strong classification
    strong_classification_genes = []

    # Display the heading outside the loop
    st.write("**Queries with Strong Classification:**")


    # Connect to your PostgreSQL database (assuming you have a connection established)
    conn = init_connection()
    cur = conn.cursor()

    # Execute the SQL query for each pair of genesymbol and diplotype
    for idx, pair in enumerate(pairs, start=1):
        # Check if the pair contains both genesymbol and diplotype
        if len(pair) == 2:
            genesymbol, diplotype = pair

            # Execute the custom SQL query
            query = """
                SELECT DISTINCT ON (p.drugid)
                    dp.diplotype,
                    r.activityscore,
                    r.phenotypes,
                    dp.ehrpriority,
                    p.drugid,
                    dr.name,
                    r.population,
                    r.drugrecommendation,
                    r.classification
                FROM cpic.gene_result_diplotype d
                JOIN cpic.gene_result_lookup l ON d.functionphenotypeid = l.id
                JOIN cpic.gene_result gr ON l.phenotypeid = gr.id
                JOIN cpic.pair p ON gr.genesymbol = p.genesymbol
                JOIN cpic.drug dr ON p.drugid = dr.drugid
                JOIN cpic.recommendation r ON dr.drugid = r.drugid
                JOIN cpic.diplotype_phenotype dp ON r.phenotypes @> dp.phenotype
                WHERE dp.diplotype ->> %s = %s
                    AND r.activityscore @> dp.activityscore
                    AND r.classification <> 'No Recommendation'
                    AND r.drugrecommendation <> 'No recommendation'
                ORDER BY p.drugid, r.classification;
            """

            # Execute the query with parameters
            cur.execute(query, (genesymbol, diplotype))

            # Fetch the results
            result_df = pd.DataFrame(cur.fetchall(), columns=["diplotype", "activityscore", "phenotypes", "ehrpriority", "drugid", "name", "population", "drugrecommendation", "classification"])

            # Check if the DataFrame is not empty before processing
            if not result_df.empty:
                # Process columns with JSONB format to remove {}
                for col in result_df.columns:
                    if isinstance(result_df[col][0], dict):
                        result_df[col] = result_df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))

                # Add the result DataFrame to the HTML report
                html_report += f"<h3>Results for {genesymbol}, {diplotype}</h3>\n"
                html_report += result_df.to_html(index=False, escape=False, classes='report-table', table_id=f'report-table-{genesymbol}_{diplotype}', justify='center') 
                html_report = html_report.replace('<th>', '<th style="background-color: #ADD8E6; color: black;">')
                html_report += "\n"

                # Check if the classification is strong
                if "Strong" in result_df["classification"].values:
                    # Display the queried genesymbol and diplotype with strong classification
                    st.write(f"- {genesymbol} {diplotype}")

                    # Add the gene symbol and diplotype as a tuple to the list
                    strong_classification_genes.append((genesymbol, diplotype))

                # Add a space after each result
                html_report += "<br>\n"

    # Close the database connection
    conn.close()

    # Display the entire HTML report
    st.markdown(html_report, unsafe_allow_html=True)

    st.write("#")

    # End the report with reduced font size
    label = """
    <div style='text-align: justify; font-size:10px'>
    <strong>Disclaimer:</strong><br>
    Genotypes were called using Aldy, Actionable drug interactions were collected from CPIC database.<br>
    The recommendations provided in this report are generated based on the available data and algorithms. It is crucial to note that these recommendations should only be considered as supplementary information and not as a substitute for professional medical advice. This report is intended for use by qualified healthcare professionals, and decisions regarding patient care should be made in consultation with a licensed medical practitioner. The information presented here may not encompass all aspects of an individual's medical history or current health condition.<br>
    The developers and providers of this report disclaim any liability for the accuracy, completeness, or usefulness of the recommendations, and they are not responsible for any adverse consequences resulting from the use of this information.<br>
    Patients and healthcare providers are encouraged to exercise their professional judgment and consider individual patient characteristics when making medical decisions.
    </div>
    """

    st.markdown(label, unsafe_allow_html=True)