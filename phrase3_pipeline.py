import pandas as pd
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from vertexai.generative_models import Part
from vertexai.generative_models import Content, GenerationConfig
import base64
import json
import os
import streamlit as st
from google.auth import credentials

# Retrieve the base64-encoded credentials from Streamlit secrets
credentials_base64 = st.secrets["google_credential"]

# Decode the base64 string to get the actual credentials
credentials_json = base64.b64decode(credentials_base64).decode("utf-8")

# Write the decoded credentials to a temporary file
with open("/tmp/google_credential.json", "w") as f:
    f.write(credentials_json)

# Authenticate with Google Cloud using the credentials file for BigQuery
bq_client = bigquery.Client.from_service_account_json("/tmp/google_credential.json")

# Load the credentials object (instead of passing the file directly to vertexai)
from google.oauth2 import service_account
google_credentials = service_account.Credentials.from_service_account_file("/tmp/google_credential.json")

# Initialize Vertex AI with the credentials object
project_id = "ba882-group-10"  # Replace this with your actual Google Cloud project ID
vertexai.init(project=project_id, credentials=google_credentials)

# Initialize GenerativeModel
model = GenerativeModel(model_name="gemini-1.5-flash-002")
generation_config = GenerationConfig(temperature=0)

# Streamlit UI setup
st.title('CDC Database Text to SQL Tool')
img_erd='https://raw.githubusercontent.com/eshentong/streamlit-cdc/main/project_erd.png'
# st.image(img_erd, caption="CDC Database ERD", use_column_width=True)
with st.sidebar:
    st.image(img_erd, caption="Sidebar CDC Database ERD")

join_logic = """
SELECT *
FROM `ba882-group-10`.cdc_data.cdc_occurrences_staging AS o
JOIN `ba882-group-10`.cdc_data.disease_dic AS d
ON o.Disease = CAST(d.disease_code AS STRING)
JOIN `ba882-group-10`.cdc_data.symptom AS s
ON o.Disease = s.Disease
JOIN `ba882-group-10`.demographic_data.census_data AS c
ON o.Region= c.State
"""

# Fetch data from BigQuery and keep the result as dictionaries (RowIterator)
df = bq_client.query(join_logic).result()

sql_query1 = """
SELECT table_name, column_name, data_type
FROM `ba882-group-10.cdc_data.INFORMATION_SCHEMA.COLUMNS`
"""
sql_query2 = """
SELECT table_name, column_name, data_type
FROM `ba882-group-10.demographic_data.INFORMATION_SCHEMA.COLUMNS`
"""

# Fetch schema information as dictionaries
schema_df1 = bq_client.query(sql_query1).result()
schema_df2 = bq_client.query(sql_query2).result()

# Convert RowIterator to dictionaries
schema_dict1 = [dict(row) for row in schema_df1]
schema_dict2 = [dict(row) for row in schema_df2]

# Combine the schema dictionaries
schema_dict = schema_dict1 + schema_dict2

# Get the schema in a format for the model
schema_records = json.dumps(schema_dict)

# Get user input for the SQL query generation
user = st.text_input('Enter your text below to see the SQL code')

# Create the prompt for the model
prompt = f"""
### System prompt
You are a SQL expert.  For the user's input, generate a SQL query given the schema, join logic, and mega table context provided.
The data includes diseases and cases in the U.S. from the beginning of 2023, and it refreshes weekly.
Return a valid JSON with a key SQL. The value of the SQL key should be the query to be executed against the database.

Only use the table names and columns mentioned in the schema. 
For aggregations, reference columns in the SELECT clause. 
Use CAST where necessary. Ensure functions are compatible with BigQuery.

### Schema
{schema_records}

### Join Logic
{join_logic}

### Mega Table Context
{df}

### User prompt
{user}

### SQL prompt
"""

# Create the user prompt content
user_prompt_content = Content(
    role="user",
    parts=[
        Part.from_text(prompt),
    ],
)

# Get the response from the model
response = model.generate_content(user_prompt_content, generation_config=generation_config)
response.text

# Initialize sql_query to None in case the parsing fails
sql_query = None

# Clean up the response to extract the SQL query
cleaned_response = response.text.strip()

# Remove any unwanted markers such as ```json (if the response includes those)
if cleaned_response.startswith('```json'):
    cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()

# Ensure that the cleaned response is a valid JSON string
if cleaned_response:
    # Step 1: Parse the cleaned response as JSON
    try:
        parsed_json = json.loads(cleaned_response)

        # Step 2: Extract the SQL query from the parsed JSON
        sql_query = parsed_json.get('SQL')

        if sql_query:
            # Display the SQL query
            st.write("Generated SQL Query:")
            st.write(sql_query)
        else:
            st.write("Error: No 'SQL' key found in the response.")

    except json.JSONDecodeError as e:
        st.write(f"Error decoding JSON: {e}")
        st.write("Cleaned response (unable to decode as JSON):")
        st.write(cleaned_response)
else:
    st.write("Cleaned response is empty. Please check the input or model response.")

# Step 3: Execute the SQL query and show the results
if sql_query:
    try:
        outcome = bq_client.query(sql_query).result().to_dataframe()
        st.write(outcome.head())
    except Exception as e:
        st.write(f"Error executing SQL query: {e}")


# Clean up the response to extract the SQL query
# cleaned_response = response.text

# if cleaned_response.startswith('```json'):
#     cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()

# # Step 2: Now, remove any additional escape characters
# cleaned_response = cleaned_response.replace('\\', '')  # Remove escape slashes
# cleaned_response = cleaned_response.replace('\n', '')  # Remove newlines

# # Step 3: Parse the cleaned string as JSON
# try:
#     parsed_json = json.loads(cleaned_response)
    
#     # Step 4: Extract the SQL query from the JSON
#     sql_query = parsed_json.get('SQL')
    
#     if sql_query:
#         print("Generated SQL Query:")
#         print(sql_query)
#     else:
#         print("Error: No 'SQL' key found in the response.")
        
# except json.JSONDecodeError as e:
#     print(f"Error decoding JSON: {e}")
#     print("Cleaned response (unable to decode as JSON):")
#     print(cleaned_response)

# # Execute the SQL query and show the results
# if sql_query:
#     outcome = bq_client.query(sql_query).result().to_dataframe()
#     st.write(outcome)