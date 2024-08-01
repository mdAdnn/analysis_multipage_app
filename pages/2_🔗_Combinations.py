import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(".env")

st.set_page_config(
    layout="wide",
    page_title="Drug Combinations",
    page_icon="link-45deg",
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

# Dropdown menu to select gene, diplotype and drug
gene_col, diplotype_col, drug_col = st.columns([3, 3, 3])

def process_jsonb_columns(df):
    for col in df.columns:
        if isinstance(df[col][0], dict):
            df[col] = df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))
    return df

st.write("In the dropdown menu you can select the gene symbol and diplotype for which you want to get the recommendations. You can also select a drug name (optional) to filter the results by drug name. If you do not select a drug name, the results will be displayed for all drugs. Click on the 'Submit' button to get the results. If you want to see the recommendations specific to a drug, select the drug name and make sure the gene symbol is selected as 'None' and click on the 'Submit' button.")
st.write("**Note:** There are various phenotypic combinations that have similar Drug recommendations. The table below lists all of the suggestions for each phenotypic combination. Kindly refer to the results based on your actual phenotype combination.")
st.markdown('If you need further deatils of the similar recommendations, kindly contact us at [fcb.adnan10@gmail.com](mailto:)')

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
            SELECT DISTINCT
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
            SELECT DISTINCT
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
        cur.execute("SELECT DISTINCT genesymbol FROM cpic.gene_result WHERE genesymbol IN ('CYP2C9', 'SLCO1B1', 'CYP2D6', 'TPMT', 'CYP2B6', 'CYP3A5', 'NUDT15', 'UGT1A1', 'CYP2C19')")
        gene_symbols = ["None"] + sorted([row[0] for row in cur.fetchall()])

        # Create the second popover for simplified diplotypes related to the selected gene symbol
        with st.expander("Select Gene Symbol"):
            selected_gene_symbol = gene_col.selectbox("Select Gene Symbol", gene_symbols)
        
        # Query to get all unique diplotypes for the selected gene symbol from cpic.diplotype_phenotype table
        cur.execute(f"SELECT DISTINCT diplotype->>'{selected_gene_symbol}' AS simplified_diplotype FROM cpic.diplotype_phenotype WHERE jsonb_exists(diplotype, '{selected_gene_symbol}')")
        diplotypes = ["None"] + sorted([row[0] for row in cur.fetchall()])

        # Create the second popover for simplified diplotypes related to the selected gene symbol
        with st.expander("Select Diplotypes"):
            selected_diplotypes = diplotype_col.selectbox("Diplotypes", diplotypes)

        # Create third dropdown for drugs
        cur.execute("SELECT DISTINCT name FROM cpic.drug where name IN ('efavirenz','sertraline','trimipramine','lansoprazole','citalopram','clomipramine','escitalopram','doxepin','pantoprazole','imipramine','amitriptyline','omeprazole','dexlansoprazole','fluvastatin','fosphenytoin','phenytoin','celecoxib','lornoxicam','tenoxicam','meloxicam','flurbiprofen','ibuprofen','piroxicam','tamoxifen','tramadol','vortioxetine','codeine','desipramine','paroxetine','atomoxetine','venlafaxine','fluvoxamine','hydrocodone','nortriptyline','tacrolimus','mercaptopurine','thioguanine','azathioprine','atazanavir','atorvastatin','lovastatin','pitavastatin','pravastatin','rosuvastatin','simvastatin','irinotecan','cisplatin') order by name")
        drugs = ["None"] + sorted([row[0] for row in cur.fetchall()])

        # Create the third dropdown for drugs
        with st.expander("Select Drug"):
            selected_drug = drug_col.selectbox("Select Drug", drugs)

        # Add a submit button
        if diplotype_col.button("Submit"):
            # Execute the custom query with the selected drug name
            result_df = execute_custom_query(selected_gene_symbol, selected_diplotypes, selected_drug)

            # Check if the DataFrame is not empty before processing
            if not result_df.empty:
                # Process JSONB columns
                result_df = process_jsonb_columns(result_df)

                # Display the total number of results
                st.write(f"Total number of results: {len(result_df)}")

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
        # Close cursor and connection
        cur.close()

    st.write("#")

    disclaimer = """
    <div style='text-align: justify; font-size:10px'>
    Disclaimer:<br>
    The recommendations provided in this report are generated based on literature and intended only for research pursposes. It is crucial to note that these recommendations should only be considered as supplementary information and not as a substitute for professional medical advice. This report is intended for use by qualified healthcare professionals, and decisions regarding patient care should be made in consultation with a licensed medical practitioner. The information presented here may not encompass all aspects of an individual's medical history or current health condition.<br>
    The developers and providers of this report disclaim any liability for the accuracy, completeness, or usefulness of the recommendations, and they are not responsible for any adverse consequences resulting from the use of this information.<br>
    Patients and healthcare providers are encouraged to exercise their professional judgment and consider individual patient characteristics when making medical decisions.
    </div>
    """

    st.markdown(disclaimer, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
