# TEXT TO SQL UTILIZING GEMINI 1.5

Taking advantage of the Google Cloud Platform ecosystem, I utilized prompting and context to help Gen-AI to turn text inputs into SQL queries.

## Google Cloud Platform Integration
Utilizing the google secret manager, our group was able to generate key-value pairs for BigQuery access. After transforming the JSON file to Base64-encoded, we were able to utilize Streamlit to access BigQuery database.
Additionally, the project was made extremely easy with the integration of Gemini, which is a key part to our Text to SQL update. The Google-ecosystem allows easy integration and connection, making this process easier than usual.

## Text to SQL Prompting
In order for Gemini 1.5 to better understand the two dynamic datasets ba882-group-10.cdc_data and ba882-group-10.demographic_data, we designed four contextual information which was taken into consideration as parts of the prompt.
- Join Logic: in this contextual information, we joined all viable tables, indicating joining logic and foreign/primary keys for each table.
- Mega Table: this is the output of the previous item, showcasing gen-AI the combined table
- Schema Output: this contextual information showcases the data type of each table, further allowing the SQL operations to work successfully. This is important as several foreign keys have different data types across different tables.
- ML Table Description: Along the app testings, we realized that the Gen-AI does not perform as well for any inputs asking for the machine learning information. Hence,  to help Gemini to better understand these tables, we added in table descriptions for ML related tables created in phrase three.

## Deploying Github Repo Using Streamlit 
Utilizing the deployment, requirement and workflow yaml file on https://github.com/eshentong/streamlit-cdc, we were able to build a Streamlit app that takes in text input, considering prompt, which includes text prompting and contexts, and eventually outputs SQL query, and fetches query result from BigQuery.
