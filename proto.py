import streamlit as st
import pandas as pd

from var.callables import upload_file
from var.callables import close_file
from var.callables import filter_df

st.set_page_config(layout="wide")
st.session_state.setdefault(key="is_file_uploaded", default=False)
st.session_state.setdefault(key="is_editmode_active", default=False)

st.title(body=":chart_with_upwards_trend: ML Uplift", anchor=False)

column1, column2 = st.columns([0.8, 0.2])

# Version
with column1:
    st.markdown(body=":grey[v1.0.0]")

# Upload/Close
with column2:
    if st.session_state.get("is_file_uploaded"):
        st.button(
            label="**:x: Close file**",
            on_click=close_file,
            use_container_width=True,
        )
    else:
        st.button(
            label="**:open_file_folder: Upload file**",
            on_click=upload_file,
            use_container_width=True,
        )

# Table Preview
if st.session_state.get("is_file_uploaded") and not st.session_state.get("is_editmode_active"):
    st.dataframe(data=st.session_state.get("df").head(20), height=450)

    column1, column2 = st.columns([0.8, 0.2])
    
    # File name
    with column1:
        st.markdown(f":grey[{st.session_state.get("xlsx_file").name}]")

    # Filter/Edit
    with column2:
        temp1, temp2 = st.columns(2)
        # Filter
        with temp1:
            st.button(
                label="**:wrench: Filter**",
                on_click=filter_df,
                use_container_width=True,
            )
        
        # Edit
        with temp2:
            st.button(
                label="**:pencil: Edit**",
                on_click=lambda: st.session_state.update({"is_editmode_active": True}),
                use_container_width=True,
            )

    #Predict
    with column2:
        st.button(
            label="**Predict**",
            on_click=None,
            use_container_width=True,
        )

# Apply filter

# Edit Mode
if st.session_state.get("is_file_uploaded") and st.session_state.get("is_editmode_active"):
    df = st.data_editor(st.session_state["df"], height=600)

    column1, column2 = st.columns([0.8, 0.2])

    # File name
    with column1:
        st.markdown(f":grey[{st.session_state.get("xlsx_file").name}]")

    # Save
    with column2:
        st.button(
            label="**:white_check_mark: Save**",
            on_click=lambda: st.session_state.update({"is_editmode_active": False, "df": df}),
            use_container_width=True,
        )
