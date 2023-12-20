import streamlit as st
import pandas as pd
import psycopg2
import os
from datetime import datetime

st.set_page_config(
    layout="wide",
    page_title="Analysis",
    page_icon="🔎"
)

# Access PostgreSQL credentials from secrets.toml
postgres_secrets = st.secrets["postgres"]

# Use the credentials in your PostgreSQL connection
db_username = postgres_secrets["user"]
db_password = postgres_secrets["password"]
db_host = postgres_secrets["host"]
db_port = postgres_secrets["port"]
db_name = postgres_secrets["database"]

conn = psycopg2.connect(user=db_username, password=db_password, host=db_host, port=db_port, database=db_name)

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

# File uploader and select boxes in a single row
file_col, gene_col, diplotype_col, drug_col = st.columns([4, 2, 2, 2])

# File uploader
uploaded_file = file_col.file_uploader("Choose a .txt file", type="txt")

# Note:
st.write("#")
st.write('''
        **Note:** Kindly use a masked 'Name' and 'ID' for confidentiality and security reasons while using real patients data.
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
        cur.execute("SELECT DISTINCT genesymbol FROM cpic.gene_result")
        gene_symbols = ["None"] + [row[0] for row in cur.fetchall()]

        # Create the first dropdown for gene symbols
        selected_gene_symbol = gene_col.selectbox("Select Gene Symbol", gene_symbols)

        # Query to get all unique diplotypes for the selected gene symbol from cpic.diplotype_phenotype table
        cur.execute(f"SELECT DISTINCT diplotype->>'{selected_gene_symbol}' AS simplified_diplotype FROM cpic.diplotype_phenotype WHERE jsonb_exists(diplotype, '{selected_gene_symbol}')")
        diplotypes = [row[0] for row in cur.fetchall()]

        # Create the second dropdown for simplified diplotypes related to the selected gene symbol
        selected_diplotypes = diplotype_col.selectbox("Select Diplotypes", diplotypes)

        # Create third dropdown for drugs
        cur.execute("SELECT DISTINCT name FROM cpic.drug")
        drugs = ["None"] + [row[0] for row in cur.fetchall()]
        selected_drug = drug_col.selectbox("Select Drug", drugs)

        # Add a submit button
        if diplotype_col.button("Submit"):
            # Execute the custom query with the selected drug name
            result_df = execute_custom_query(selected_gene_symbol, selected_diplotypes, selected_drug)

            # Check if the DataFrame is not empty before processing
            if not result_df.empty:
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
    st.write(f"**Name:** {name}")
    st.write(f"**ID:** {user_id}")
    st.write(f"**Timestamp:** {timestamp}")

    # Initialize a list to store gene symbols with strong classification
    strong_classification_genes = []

    # Display the heading outside the loop
    st.write("**Queries with Strong Classification:**")

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
                html_report += f"<h3>Results for {genesymbol}, {diplotype}</h3>\n"
                # Highlight the "name" column if it contains any of the specified drugs
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

if __name__ == "__main__":
    main()