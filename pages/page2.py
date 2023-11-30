import streamlit as st
import time


def dashboard(parameters):
    title = (parameters.get("eventClick").get("event").get("title"))
    start = (parameters.get("eventClick").get("event").get("start"))
    end = (parameters.get("eventClick").get("event").get("end"))
    st.session_state['line'] = title + "/" + start + "/" + end 

if __name__ == "__main__":
    
    
    if st.session_state:
        st.text(st.session_state.line)

    else:
        data_load_state = st.text('You have to choose a data period from Home...')



    
