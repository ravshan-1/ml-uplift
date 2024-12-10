import streamlit as st

st.set_page_config(page_title="ML Uplift", page_icon="📈", layout="wide")
st.session_state.setdefault(key="logged_in", default=False)
st.session_state.setdefault(key="file_uploaded", default=False)

st.title(body="📈 ML Uplift", anchor=False)

if st.session_state.get("logged_in"):
    auth_title = "Logout"
    auth_icon = ":material/logout:"
else:
    auth_title = "Login"
    auth_icon = ":material/login:"

pg = st.navigation(
    {
        "Your account": [
            st.Page("./src/auth.py", title=auth_title, icon=auth_icon),
            st.Page("./src/settings.py", title="Settings", icon=":material/settings:"),
        ],
        "ML Uplift": [
            st.Page("./src/overview.py", title="Overview", icon=":material/stacked_bar_chart:"),
            st.Page("./src/model.py", title="Model", icon=":material/rocket_launch:"),
        ]
    }
)

pg.run()
