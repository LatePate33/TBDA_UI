import streamlit as st
import time
import numpy as np
import mysql.connector as con
from streamlit_calendar import calendar
from streamlit_extras.switch_page_button import switch_page
from pages.page2 import dashboard
from st_pages import Page, show_pages, add_page_title, hide_pages

st.set_page_config(layout="wide")

hide_pages(["Dashboard"])

timeslots = []

connection = con.connect(
    host=st.secrets["host"],
    user=st.secrets["username"],
    password=st.secrets["password"],
    database=st.secrets["database"],
)

mycur = connection.cursor()

mycur.execute("SELECT * FROM `actividad-G01`")

results = mycur.fetchall()

for x in results:
    start = x[4].strftime("%Y-%m-%dT%H:%M:%S")
    end = x[5].strftime("%Y-%m-%dT%H:%M:%S")

    dict = {
        "title": x[1],
        "start": start,
        "end": end,
        "color": "#000000",
        "borderColor": "#0000FF",
        "resourceId": "dataS04",
    }
    timeslots.append(dict)

connection.close()

connection = con.connect(
    host=st.secrets["host"],
    user=st.secrets["username"],
    password=st.secrets["password"],
    database=st.secrets["database"],
)

mycur = connection.cursor()

mycur.execute("SELECT * FROM `steps-G01`")

results = mycur.fetchall()

for x in results:
    start = x[3].strftime("%Y-%m-%dT%H:%M:%S")
    end = x[4].strftime("%Y-%m-%dT%H:%M:%S")
    RorL = x[2]

    bordercolor = "#00FF00"

    if RorL == "C9:7B:84:76:32:14":
        title = "R-04"
        group = "walk0RS04"
    if RorL == "E0:52:B2:8B:2A:C2":
        title = "L-04"
        group = "walk1LS04"

    dict = {
        "title": title,
        "start": start,
        "end": end,
        "color": "#000000",
        "borderColor": bordercolor,
        "resourceId": group,
    }
    timeslots.append(dict)

connection.close()


calendar_resources = [
    {"id": "dataS04", "dataset": "S-04", "title": "Data"},
    {"id": "walk1LS04", "dataset": "S-04", "title": "Walking Left"},
    {"id": "walk0RS04", "dataset": "S-04", "title": "Walking Right"},
]



calendar_options = {
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "resourceTimelineDay,dayGridWeek,dayGridMonth",
    },
    "slotMinTime": "00:00:00",
    "slotMaxTime": "24:00:00",
    "initialView": "dayGridMonth",
    "resources": calendar_resources,
    "resourceGroupField": "dataset",
}
calendar_events = {
    "timeZone": "UTC",
    "events": timeslots,
}
custom_css = """
    .fc-event-past {
        opacity: 0.8;
    }
    .fc-event-time {
        font-style: italic;
    }
    .fc-event-title {
        font-weight: 700;
    }
    .fc-toolbar-title {
        font-size: 2rem;
    }
    
    .fc-timeline-event-harness {
        position: absolute;
        top: 0px !important;
    }
    .fc-timeline-lane-frame {
        height: 40px !important;
    }
    .fc-datagrid-cell-frame {
        height: 40px !important;
    }

    .fc-resourceTimelineDay-view {
        height: 300px !important;
    }
    
"""

information = st.container(border=True)
information.header("InnoSock Insight")
information.write("*Improving human life since 2023*")
information.divider()
information.write(":large_blue_circle: Data Available")
information.write(":large_green_circle: Good Walking")
information.write(":red_circle: Bad Walking")
information.divider()
information.header("Instructions")
information.write("You have 3 calendar views (month, week, day)")
information.write("You can move with the arrows (< >) located below")
information.write("The datapoints are clickable, where data can be displayed")

calendar = calendar(
    events=calendar_events,
    options=calendar_options,
    custom_css=custom_css,
    callbacks=["eventClick"],
)

#calendar.write("""<div class='CLASSNAME'/>""", unsafe_allow_html=True)

if calendar != {}:
    dashboard(calendar)

# st.write(calendar)

if calendar != {}:
    switch_page("dashboard")
