import streamlit as st
import time
from st_pages import Page, show_pages, add_page_title, hide_pages
from datetime import datetime, timedelta
import pandas
import numpy as np
import matplotlib.pyplot as plt
from influxdb_client import InfluxDBClient

st.set_page_config(layout="wide")

hide_pages(["Dashboard"])


def dashboard(parameters):
    title = (parameters.get("eventClick").get("event").get("title"))
    start = (parameters.get("eventClick").get("event").get("start"))
    end = (parameters.get("eventClick").get("event").get("end"))
    st.session_state['title'] = title 
    st.session_state['start'] = start
    st.session_state['end'] = end

def influxCall(start, end, mac, value):
    org    = 'UPM'
    database = 'SSL'
    retention_policy = 'autogen'
    bucket = f'{database}/{retention_policy}'
    tokenv2 = 'ssIDtGLVLBG94SCPbMlWvHgKGn3uUWECTs4A95I_ACn2NKTsDvLCu2-39EQnaPJFkht3flBAV7rG6kE8x9YQkQ=='
    start = start.replace(' ','T') + '.000000000Z'
    end = end.replace(' ','T') + '.000000000Z'
    with InfluxDBClient(url='https://apiivm78.etsii.upm.es:8086',\
                token=tokenv2,org=org, timeout= 5000_000) as client:
        query = 'from(bucket:"SSL/autogen")\
                |> range(start: ' + start + ', stop: ' + end + ')\
                |> filter(fn:(r) => r._measurement == "sensoria_socks")\
                |> filter(fn:(r) => r._field== "' + value + '")\
                |> filter(fn: (r) => r["mac"] == "' + mac + '")\
                |> group(columns: ["_field", "lat", "lng"]) \
                |> pivot(rowKey:["_time","lat","lng"], columnKey: ["_field"], valueColumn: "_value") \
                |> drop(columns: ["table", "_start", "_stop"]) '
        

        result = client.query_api().query(org=org, query=query)
        res = pandas.DataFrame()
        pandas.options.display.max_columns = 0

        for i in result:
            rs = []
            for row in i.records:
                rs.append(row.values)
            res = pandas.concat([res, pandas.DataFrame(rs)], axis=0)
        res = res.drop(res.columns[[0]], axis=1)
        client.close()
    return res

def drawLeftie(df_l):
    st.header("Left")
    st.dataframe(df_l)
    st.header("Presicion (Left)")
    precL = df_l[['_time', 'S0', 'S1', 'S2']]
    st.line_chart(precL, x="_time", y=['S0', 'S1', 'S2'])
    st.header("Acceleration (Left)")
    accL = df_l[['_time', 'Ax','Ay','Az','modA']]
    st.line_chart(accL, x="_time", y=['Ax','Ay','Az','modA'])
    st.header("Gyroscope (Left)")
    gyrL = df_l[['_time', 'Gx','Gy','Gz','modG']]
    st.line_chart(gyrL, x="_time", y=['Gx','Gy','Gz','modG'])
    st.header("Magnetometer (Left)")
    magL = df_l[['_time', 'Mx', 'My', 'Mz']]
    st.line_chart(magL, x="_time", y=['Mx', 'My', 'Mz'])

def drawRightie(df_r):
    st.header("Right")
    st.dataframe(df_r)
    st.header("Presicion (Right)")
    precR = df_r[['_time', 'S0', 'S1', 'S2']]
    st.line_chart(precR, x="_time", y=['S0', 'S1', 'S2'])
    st.header("Acceleration (Right)")
    accR = df_r[['_time', 'Ax','Ay','Az','modA']]
    st.line_chart(accR, x="_time", y=['Ax','Ay','Az','modA'])
    st.header("Gyroscope (Right)")
    gyrR = df_r[['_time', 'Gx','Gy','Gz','modG']]
    st.line_chart(gyrR, x="_time", y=['Gx','Gy','Gz','modG'])
    st.header("Magnetometer (Right)")
    magR = df_r[['_time', 'Mx', 'My', 'Mz']]
    st.line_chart(magR, x="_time", y=['Mx', 'My', 'Mz'])


if __name__ == "__main__":

    def drawGraphs(title, start, end):
        values = ['S0', 'S1', 'S2', 'Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz', 'Mx', 'My', 'Mz']
        dfvalueL = pandas.DataFrame()
        dfvalueR = pandas.DataFrame()
        

        if (title=="S-04"):
            macR = "C9:7B:84:76:32:14"
            macL = "E0:52:B2:8B:2A:C2"

            try:

                for val in values:
                    temp = influxCall(start, end, macR, val)
                    dfvalueR = pandas.concat([dfvalueR,temp],axis=0,ignore_index=True)
                df_r = dfvalueR.pivot_table(index='_time', values=values)
                df_r.reset_index(inplace=True)
                df_r['modA'] = (df_r[['Ax','Ay','Az']]**2).sum(axis=1)**0.5
                df_r['modG'] = (df_r[['Gx','Gy','Gz']]**2).sum(axis=1)**0.5

            except:
                df_r = 0

            
            try:
            
                for val in values:
                    temp = influxCall(start, end, macL, val)
                    dfvalueL = pandas.concat([dfvalueL,temp],axis=0,ignore_index=True)
                df_l = dfvalueL.pivot_table(index='_time', values=values)
                df_l.reset_index(inplace=True)
                df_l['modA'] = (df_l[['Ax','Ay','Az']]**2).sum(axis=1)**0.5
                df_l['modG'] = (df_l[['Gx','Gy','Gz']]**2).sum(axis=1)**0.5

            except:
                df_l = 0

        
            
            data_container = st.container()
            with data_container:
                left_foot, right_foot = st.columns(2)
                try:
                    with left_foot:
                        drawLeftie(df_l)
                except:
                    with left_foot:
                        st.write("**No data**")
                try:
                    with right_foot:
                        drawRightie(df_r)
                except:
                    with right_foot:
                        st.write("**No data**")

        
        if (title=="R-04"):
            macR = "C9:7B:84:76:32:14"

            for val in values:
                temp = influxCall(start, end, macR, val)
                dfvalueR = pandas.concat([dfvalueR,temp],axis=0,ignore_index=True)
            df_r = dfvalueR.pivot_table(index='_time', values=values)
            df_r.reset_index(inplace=True)
            df_r['modA'] = (df_r[['Ax','Ay','Az']]**2).sum(axis=1)**0.5
            df_r['modG'] = (df_r[['Gx','Gy','Gz']]**2).sum(axis=1)**0.5
            
            drawRightie(df_r)

        if (title=="L-04"):
            macL = "E0:52:B2:8B:2A:C2"

            for val in values:
                temp = influxCall(start, end, macL, val)
                dfvalueL = pandas.concat([dfvalueL,temp],axis=0,ignore_index=True)
            df_l = dfvalueL.pivot_table(index='_time', values=values)
            df_l.reset_index(inplace=True)
            df_l['modA'] = (df_l[['Ax','Ay','Az']]**2).sum(axis=1)**0.5
            df_l['modG'] = (df_l[['Gx','Gy','Gz']]**2).sum(axis=1)**0.5

            
            drawLeftie(df_l)
            
    
    
    if st.session_state:
        
        datetime_start = datetime.strptime(st.session_state.start, "%Y-%m-%dT%H:%M:%S%z")
        datetime_end = datetime.strptime(st.session_state.end, "%Y-%m-%dT%H:%M:%S%z")

        starter = datetime.strftime(datetime_start, "%Y-%m-%d %H:%M:%S%z")
        ender = datetime.strftime(datetime_end, "%Y-%m-%d %H:%M:%S%z")

        st.title(f"Dataset: _{st.session_state.title}_")
        st.title(f"From: _{starter}_")
        st.title(f"To: _{ender}_")

        if ((datetime_end - datetime_start) < timedelta(0, 30)):

            selected = datetime.strftime(datetime_start, "%Y-%m-%d %H:%M:%S")
            selected_added = datetime.strftime(datetime_end, "%Y-%m-%d %H:%M:%S")

            drawGraphs(st.session_state.title, selected, selected_added)
        else:
            last_possible = datetime_end - timedelta(seconds=30)

            #st.write(f"**{start}** :arrow_forward: **{end}**")
            timeline = st.container()
    
            selected = timeline.slider("", min_value=datetime_start, max_value=last_possible, step=timedelta(0, 1), format="hh:mm:ss")
            selected_added = selected + timedelta(seconds=30)

            selected = datetime.strftime(selected, "%Y-%m-%d %H:%M:%S")
            selected_added = datetime.strftime(selected_added, "%Y-%m-%d %H:%M:%S")
            
            timeline.title((f"**{selected}** :arrow_forward: **{selected_added}**"))
            timeline.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

            ### Custom CSS for the sticky header
            st.markdown(
                """
            <style>
                div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
                    position: sticky;
                    top: 2.875rem;
                    background-color: white;
                    z-index: 999;
                    
                }
                
            </style>
                """,
                unsafe_allow_html=True
            )

            drawGraphs(st.session_state.title, selected, selected_added)

    else:
        data_load_state = st.text('Something went wrong...')



    
