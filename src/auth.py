import streamlit as st

@st.dialog(title="Log in", width="large")
def Login():

    Username = st.text_input(label="Username", placeholder="Input username.")
    Password = st.text_input(label="Password", placeholder="Input password.", type="password")

    if st.button(label="Submit"):
        if Username != "root" or Password != "secret":
            st.warning(body="Wrong username or password!")
        else:
            st.session_state["logged_in"] = True
            st.switch_page("./src/overview.py")

@st.dialog(title="Sign in", width="Large")
def Signin():
    pass

if st.session_state.get("logged_in"):
    st.session_state.update({"logged_in": False})
    st.switch_page("./src/overview.py")
    st.rerun()
else:
    Login()
