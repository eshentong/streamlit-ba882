import streamlit as st

# Check if a specific secret exists
if "google_credential" in st.secrets:
    st.write("Secret 'google_credential' found!")
else:
    st.write("Secret 'google_credential' not found.")


