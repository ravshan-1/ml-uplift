import pandas as pd
import streamlit as st

from scripts.predict import predict
from scripts import add_to_full_promo
from utils.azure import upload_promo_raw

if not st.session_state.get("logged_in"):
    st.switch_page("./src/auth.py")

if not st.session_state.get("file_uploaded"):
    file = st.file_uploader(label="Choose a file", type=["xlsx"])
    
    if st.button(label="Submit") and file:
        st.session_state["file"] = file
        st.session_state["week_num"] = file.name.split('_')[-1].split('.')[0]
        
        with st.status(label="Processing...", expanded=True) as status:
            st.write("Uploading data...")
            upload_promo_raw(file)

            st.write("Updating promo info...")
            add_to_full_promo.run_script()

            status.update(label="Complete!", state="complete", expanded=False)
            
else:

    _, colm = st.columns([0.9, 0.1], vertical_alignment="center")

    with colm:
        if st.button(label="**Close file**", use_container_width=True):
            st.session_state["file_uploaded"] = False
            st.rerun()

    promo_week_tab, _ = st.tabs(["📅 Promo Week", "⚙️ Model Settings"])

    with promo_week_tab:
        st.dataframe(pd.read_excel(st.session_state["file"]), use_container_width=True)

        if st.button(label="**Predict**", use_container_width=True):
            predict(st.session_state.get("week_num"))