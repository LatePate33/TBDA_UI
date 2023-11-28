import streamlit as st
import time


def dashboard(parameters):
    f = open("timeframe.txt", "w")
    title = (parameters.get("eventClick").get("event").get("title"))
    start = (parameters.get("eventClick").get("event").get("start"))
    end = (parameters.get("eventClick").get("event").get("end"))
    line = title + "/" + start + "/" + end 
    f.write(line)
    f.close()


f = open("timeframe.txt", "r")
st.write(f.read())
    
