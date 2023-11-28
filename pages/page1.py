import streamlit as st
import time
import numpy as np
import mysql.connector as con
from streamlit_calendar import calendar
from streamlit_extras.switch_page_button import switch_page


timeslots = []

connection = con.connect(
    host = "apiivm78.etsii.upm.es",
    user = "TBDA",
    password = "UPM#2324",
    database = "sclerosisTBDA"
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
    }
    timeslots.append(dict)    

calendar_options = {
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "timelineDay,dayGridWeek,dayGridMonth",
    },
    "slotMinTime": "00:00:00",
    "slotMaxTime": "24:00:00",
    "initialView": "dayGridMonth"
}
calendar_events = {
    "timeZone": 'UTC',
    "events": timeslots
}
custom_css="""
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
"""

calendar = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, callbacks=['eventClick'])
st.write(calendar)

# # # Add a text input widget
# user_input = st.text_input("Enter your name", "Your Name")

# # Display a greeting
# st.write(f"Hello, {user_input}!")

# # Add a slider for selecting a number
# number = st.slider("Pick a number", 0, 100, 50)
# st.write(f"You selected: {number}")

# # Add a button
# if st.button("Click me"):
#     st.write("Button clicked!")

# progress_bar = st.sidebar.progress(0)
# status_text = st.sidebar.empty()
# last_rows = np.random.randn(1, 1)
# chart = st.line_chart(last_rows)

# for i in range(1, 101):
#     new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
#     status_text.text("%i%% Complete" % i)
#     chart.add_rows(new_rows)
#     progress_bar.progress(i)
#     last_rows = new_rows
#     time.sleep(0.05)

# progress_bar.empty()

# # Streamlit widgets automatically run the script from top to bottom. Since
# # this button is not connected to any other logic, it just causes a plain
# # rerun.
# st.button("Re-run")


