import streamlit as st

# Function to hide the cookie consent pop-up
def hide_cookie_consent():
    st.write('<script>document.querySelector("#cookie-consent").style.display = "none";</script>', unsafe_allow_html=True)

# Display the cookie consent pop-up
if st.button("Accept Cookies", key="cookie-consent"):
    hide_cookie_consent()

# Display the cookie consent message
if st.session_state.show_cookie_consent:
    st.write("This website uses cookies to ensure you get the best experience on our website.")
    st.write("By clicking 'Accept Cookies', you agree to our use of cookies.")

# Display the rest of your Streamlit application here
