import streamlit as st
import pandas as pd
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(".env")

st.set_page_config(
    layout="wide",
    page_title="Analysis",
    page_icon="🔎"
)

# Retrieve the DATABASE_URL from the environment
DATABASE_URL = os.environ.get("db_url")

# Check if the database URL is set
if DATABASE_URL is None:
    st.error("DATABASE_URL environment variable is not set.")

conn = psycopg2.connect(DATABASE_URL)

# Custom Streamlit app header
st.markdown(
    """
    <div style='display: flex; background-color: #ADD8E6; padding: 10px; border-radius: 10px;'>
        <h1 style='margin-right: 20px; color: purple;'>PGxAnalyzer</h1>
        <img src='https://www.hbku.edu.qa/sites/default/files/media/images/hbku_2021.svg' style='align-self: flex-end; width: 200px; margin-left: auto;'>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if 'selected_gene_symbol' not in st.session_state:
    st.session_state.selected_gene_symbol = "None"
if 'selected_diplotype' not in st.session_state:
    st.session_state.selected_diplotype = "None"
if 'selected_drug' not in st.session_state:
    st.session_state.selected_drug = "None"
if 'result_df' not in st.session_state:
    st.session_state.result_df = pd.DataFrame()

# File uploader and select boxes in a single row
file_col, gene_col, diplotype_col, drug_col = st.columns([4, 2, 2, 2])

# File uploader
uploaded_file = file_col.file_uploader("Choose a .txt file", type="txt")

# Note:
st.write("#")
st.write('''
         On this page you can upload a text file containing the genetic information of a patient in the following format: **"name"**, **"id"**, **"gene symbol"**, **"diplotype"** (separated by a comma).
         The file should contain one gene symbol and diplotype per line. The app will return the drug recommendations for the desired star allele.
         In the dropdown menu you can select the gene symbol and diplotype for which you want to get the recommendations. You can also select a drug name (optional) to filter the results by drug name.
         You can also just check the recommendations of specific drug by only selecting the drug name and make sure the gene symbol is selected as "None".
         To get a better understanding of the system kindly download the sample text file from **"main page"** and upload it on **Home Page**.
''')
st.write('''
        **Note:** Kindly use only 'ID' for confidentiality and security reasons while using real patients data.
        If there are combinations of phenotypes in the recommendation output file kindly refer next page **'Combinations'** (example for genes such as ***CYP2C19, CYP2B6, TPMT, CYP2D6*** or the drugs such as ***Sertraline, Amitriptyline, Clomipramine, Doxepin*** ) for more detailed recommendations.
''')

def process_jsonb_columns(df):
    for col in df.columns:
        if isinstance(df[col][0], dict):
            df[col] = df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))
    return df

def execute_custom_query(selected_gene_symbol, selected_diplotypes, selected_drug):
    print(f"Selected Gene Symbol: {selected_gene_symbol}")
    print(f"Selected Diplotypes: {selected_diplotypes}")
    print(f"Selected Drug: {selected_drug}")
    
    if selected_gene_symbol == "None" and selected_diplotypes == "None" and selected_drug == "None":
        # Return all data if "None" is selected in all dropdowns
        print("No input selected")
    elif selected_gene_symbol and selected_diplotypes and selected_drug and selected_drug != "None":
        # Construct the SQL query for gene symbol, diplotypes, and drug
        sql_query = f"""
            SELECT DISTINCT ON (p.drugid)
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
            WHERE dp.diplotype ->> '{selected_gene_symbol}' = '{selected_diplotypes}'
                AND dr.name = '{selected_drug}'
                AND r.activityscore @> dp.activityscore
                AND r.classification <> 'No Recommendation'
                AND r.drugrecommendation <> 'No recommendation'
            ORDER BY p.drugid, r.classification;
        """
    elif selected_gene_symbol and selected_diplotypes:
        # Construct the SQL query for gene symbol and diplotypes without filtering by drug name
        sql_query = f"""
            SELECT DISTINCT ON (p.drugid)
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
            WHERE dp.diplotype ->> '{selected_gene_symbol}' = '{selected_diplotypes}'
                AND r.activityscore @> dp.activityscore
                AND r.classification <> 'No Recommendation'
                AND r.drugrecommendation <> 'No recommendation'
            ORDER BY p.drugid, r.classification;
        """
    elif selected_drug:
        sql_query = f"""
            select distinct d.name,
	            d.drugid,
	            r.drugrecommendation,
	            r.classification,
	            r.phenotypes
            from cpic.drug d
            join cpic.recommendation r on d.drugid = r.drugid
            where name = '{selected_drug}'
            AND r.classification <> 'No Recommendation'
            AND r.drugrecommendation <> 'No recommendation'
            ORDER BY d.drugid, r.classification;
        """
    else:
        # Handle other cases or provide a default query
        sql_query = ""

    # Execute the SQL query
    if sql_query:
        cur = conn.cursor()
        cur.execute(sql_query)

        # Fetch the results
        result = cur.fetchall()

        # Convert the results to a Pandas DataFrame
        df = pd.DataFrame(result, columns=[desc[0] for desc in cur.description])

        return df
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no query is selected

def main():
    try:
        cur = conn.cursor()

        # Query to get all unique gene symbols from cpic.gene_result table
        cur.execute("SELECT DISTINCT genesymbol FROM cpic.gene_result WHERE genesymbol IN ('CYP2C9', 'SLCO1B1', 'CYP2D6', 'TPMT', 'CYP2B6', 'CYP3A5', 'NUDT15', 'UGT1A1', 'CYP2C19')")
        gene_symbols = ["None"] + sorted([row[0] for row in cur.fetchall()])

        # Create the second popover for simplified diplotypes related to the selected gene symbol
        with st.expander("Select Gene Symbol"):
            selected_gene_symbol = gene_col.selectbox("Select Gene Symbol", gene_symbols, key='selected_gene_symbol')
        
        if st.session_state.selected_gene_symbol != selected_gene_symbol:
            st.session_state.selected_gene_symbol = selected_gene_symbol
        
        # Query to get all unique diplotypes for the selected gene symbol from cpic.diplotype_phenotype table
        cur.execute(f"SELECT DISTINCT diplotype->>'{selected_gene_symbol}' AS simplified_diplotype FROM cpic.diplotype_phenotype WHERE jsonb_exists(diplotype, '{selected_gene_symbol}')")
        diplotypes = ["None"] + sorted([row[0] for row in cur.fetchall()])
        st.session_state.diplotypes = diplotypes

        # Create the third dropdown for diplotypes
        with st.expander("Select Diplotype"):
            selected_diplotypes = diplotype_col.selectbox("Select Diplotype", diplotypes, key='selected_diplotypes')
        
        if st.session_state.selected_diplotypes != selected_diplotypes:
            st.session_state.selected_diplotypes = selected_diplotypes

        # Query to get all unique drugs
        cur.execute("SELECT DISTINCT name FROM cpic.drug WHERE name IN ('efavirenz','sertraline','trimipramine','lansoprazole','citalopram','clomipramine','escitalopram','doxepin','pantoprazole','imipramine','amitriptyline','omeprazole','dexlansoprazole','fluvastatin','fosphenytoin','phenytoin','celecoxib','lornoxicam','tenoxicam','meloxicam','flurbiprofen','ibuprofen','piroxicam','tamoxifen','tramadol','vortioxetine','codeine','desipramine','paroxetine','atomoxetine','venlafaxine','fluvoxamine','hydrocodone','nortriptyline','tacrolimus','mercaptopurine','thioguanine','azathioprine','atazanavir','atorvastatin','lovastatin','pitavastatin','pravastatin','rosuvastatin','simvastatin','irinotecan','cisplatin') ORDER BY name")
        drugs = ["None"] + sorted([row[0] for row in cur.fetchall()])

        # Create the third dropdown for drugs
        with st.expander("Select Drug"):
            selected_drug = drug_col.selectbox("Select Drug", drugs, key='selected_drug')
            if st.session_state.selected_drug != selected_drug:
                st.session_state.selected_drug = selected_drug

        # Add a submit button
        if diplotype_col.button("Submit"):
            # Execute the custom query with the selected drug name
            result_df = execute_custom_query(selected_gene_symbol, selected_diplotypes, selected_drug)

            # Check if the DataFrame is not empty before processing
            if not result_df.empty:
                # Sort the DataFrame by the 'name' column
                result_df = result_df.sort_values(by='name')
                # Process JSONB columns
                result_df = process_jsonb_columns(result_df)

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

            # Check if there are results to add to the HTML report
            if not result_df.empty:
                # Add the result DataFrame to the HTML report with styling to fit the page
                html_report = f"<a name='{selected_gene_symbol}_{selected_diplotypes}'></a>\n"
                html_report += f"<h3>Results for  {selected_gene_symbol}, {selected_diplotypes}</h3>\n"
                html_report += "<div style='overflow-x:auto;'>\n"
                html_report += result_df.to_html(index=False, escape=False, classes='report-table', table_id='report-table', justify='center')
                html_report = html_report.replace('<th>', '<th style="background-color: #ADD8E6; color: black;">')
                html_report += "\n"
                html_report += "</div>\n"

                # Display the HTML report
                st.markdown(html_report, unsafe_allow_html=True)
            
            else:
                st.warning(f"No results found for Genesymbol: {selected_gene_symbol}, Diplotype: {selected_diplotypes}")

    except Exception as e:
        st.error(f"Error: {str(e)}")

    finally:
        # Close cursor and connection if they are defined
        if cur:
            cur.close()

if uploaded_file is not None:
    # Read the content of the file and decode bytes to string
    file_contents = uploaded_file.read().decode('utf-8')

    # Extract name, id, and timestamp
    lines = file_contents.split('\n')
    name = lines[0].split(':')[-1].strip()
    user_id = lines[1].split(':')[-1].strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Initialize the HTML string
    html_report = ""

    # Assume the file content contains genesymbol and diplotype separated by a comma
    pairs = [line.split(',') for line in lines[3:]]

    queried_genes = []  # Move the initialization here

    # Display name, id, and timestamp at the top
    if name:
        st.write(f"**Name:** {name}")
    else:
        st.write(f"**Name:** Not Provided")
    st.write(f"**ID:** {user_id}")
    st.write(f"**Timestamp:** {timestamp}")

    # Initialize a list to store genes with no results
    genes_with_no_results = []

    # Initialize a list to store gene symbols with strong classification
    strong_classification_genes = []

    # Display the queried genes at the beginning
    st.write("**Queried genes:**")
    for pair in pairs:
        if len(pair) == 2:
            genesymbol, diplotype = pair
            st.write(f"{genesymbol} {diplotype}")

    for idx, pair in enumerate(pairs, start=1):
        # Check if the pair contains both genesymbol and diplotype
        if len(pair) == 2:
            genesymbol, diplotype = pair

            # Execute the SQL query with the provided genesymbol and diplotype
            result_df = execute_custom_query(genesymbol.strip(), diplotype.strip(), selected_drug="None")

            # Check if the DataFrame is not empty before processing
            if not result_df.empty:
                # Process columns with JSONB format to remove {}
                for col in result_df.columns:
                    if isinstance(result_df[col][0], dict):
                        result_df[col] = result_df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))

                # Add the result DataFrame to the HTML report
                html_report += f"""
<div>
    <h4><strong>Gene:</strong> {genesymbol}</h4>
    <h4><strong>Diplotype:</strong> {diplotype}</h4>
</div>
"""
                # Highlight the "name" column if it contains any of the specified drugs
                html_report += result_df.to_html(index=False, escape=False, classes='report-table', table_id=f'report-table-{genesymbol}_{diplotype}', justify='center') 
                html_report = html_report.replace('<th>', '<th style="background-color: #ADD8E6; color: black;">')
                html_report += "\n"

                # Check if the classification is strong
                if "Strong" in result_df["classification"].values:
                    # Add the gene symbol and diplotype as a tuple to the list for strong classification
                    strong_classification_genes.append(f"{genesymbol} {diplotype}")
            else:
                # Add the gene symbol and diplotype to a list of genes with no results
                genes_with_no_results.append(f"{genesymbol}, {diplotype}")

    # Display genes with no results
    if genes_with_no_results:
        st.write("**Queries with no result:**")
        for gene in genes_with_no_results:
            st.write(gene)

    # Display genes with strong classification
    if strong_classification_genes:
        st.write("**Queries with Strong Classification:**")
        for gene in strong_classification_genes:
            st.write(gene)

        html_report += "<br>\n"
    
    st.write("#")
    # Display the entire HTML report
    st.markdown(html_report, unsafe_allow_html=True)
    st.write("#")

    # Disclaimer text
    disclaimer = """
    <div style='text-align: justify; font-size:10px'>
    Disclaimer:<br>
    The recommendations provided in this report are generated based on the available data and algorithms. It is crucial to note that these recommendations should only be considered as supplementary information and not as a substitute for professional medical advice. This report is intended for use by qualified healthcare professionals, and decisions regarding patient care should be made in consultation with a licensed medical practitioner. The information presented here may not encompass all aspects of an individual's medical history or current health condition.<br>
    The developers and providers of this report disclaim any liability for the accuracy, completeness, or usefulness of the recommendations, and they are not responsible for any adverse consequences resulting from the use of this information.<br>
    Patients and healthcare providers are encouraged to exercise their professional judgment and consider individual patient characteristics when making medical decisions.
    </div>
    """

    st.markdown(disclaimer, unsafe_allow_html=True)

    # Function to read the HTML template
    def read_html_template(file_path):  
        with open(file_path, 'r') as file:
            template = file.read()
        return template

    # Path to your HTML template
    template_path = 'index.html'

    # Read the HTML template
    html_report = read_html_template(template_path)

    # Replace placeholders with actual values
    html_report = html_report.replace('{{name}}', name)
    html_report = html_report.replace('{{user_id}}', user_id)
    html_report = html_report.replace('{{timestamp}}', timestamp)
    html_report = html_report.replace('{{disclaimer}}', disclaimer)
    queried_genes_html = "<ul>" + "".join([f"<li>{gene}</li>" for gene in queried_genes]) + "</ul>"
    no_results_html = "<ul>" + "".join([f"<li>{gene}</li>" for gene in genes_with_no_results]) + "</ul>"
    strong_classification_html = "<ul>" + "".join([f"<li>{gene}</li>" for gene in strong_classification_genes]) + "</ul>"

    html_report = html_report.replace('{{queried_genes}}', queried_genes_html)
    html_report = html_report.replace('{{no_results}}', no_results_html)
    html_report = html_report.replace('{{strong_classification}}', strong_classification_html)

    for idx, pair in enumerate(pairs, start=1):
        # Check if the pair contains both genesymbol and diplotype
        if len(pair) == 2:
            genesymbol, diplotype = pair

            # Execute the SQL query with the provided genesymbol and diplotype
            result_df = execute_custom_query(genesymbol.strip(), diplotype.strip(), selected_drug="None")

            # Check if the DataFrame is not empty before processing
            if not result_df.empty:
                # Process columns with JSONB format to remove {}
                for col in result_df.columns:
                    if isinstance(result_df[col][0], dict):
                        result_df[col] = result_df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))

                # Add the result DataFrame to the HTML report
                html_report += f"""
<div style="font-size: 20px;">
    <p><strong>Gene:</strong> {genesymbol}</p>
    <p><strong>Diplotype:</strong> {diplotype}</p>
</div>
"""
                # Highlight the "name" column if it contains any of the specified drugs
                html_report += result_df.to_html(index=False, escape=False, classes='report-table', table_id=f'report-table-{genesymbol}_{diplotype}', justify='center')
                html_report = html_report.replace('<th>', '<th style="background-color: #ADD8E6; color: black;">')
                html_report += "\n"

    st.write("#")

    # Add download button for the HTML report
    st.download_button(
        label="Download Report",
        data = html_report,
        file_name="full_report.html",
        mime="text/html"
    )
   
if __name__ == "__main__":
    main()
