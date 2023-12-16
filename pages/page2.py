import streamlit as st
import time
from st_pages import Page, show_pages, add_page_title, hide_pages
from datetime import datetime, timedelta
import pandas
import numpy as np
import matplotlib.pyplot as plt
from influxdb_client import InfluxDBClient
from streamlit_javascript import st_javascript
from scipy.fftpack import fft, ifft
from scipy.signal import find_peaks, firwin, lfilter
from scipy.integrate import trapz

st.set_page_config(layout="wide")

hide_pages(["Dashboard"])

def moving_average(x, w):
    """calculate moving average with window size w"""
    return np.convolve(x, np.ones(w), 'valid') / w

def area(x, y, cutoff):
    idx = x <= cutoff
    xData = np.array(x[idx])
    yData = np.array(y[idx])
    area = trapz(y=yData, x=xData)
    return area

def picos(df, fs, col):
    
    tdt = df
    X = fft(tdt[col].to_numpy())
    N = len(X)
    n = np.arange(N)
    T = N/fs
    freq = n/T
    LN = N // 2
    # finding picks
    a = firwin(5, cutoff=1/10, window="hamming")
    vl = lfilter(a, 1, np.abs(X)[1:(LN)]/max(np.abs(X)[1:(LN)]))
    peaks = find_peaks(vl, prominence=0.3)[0]
    # finding areas
    areas = pandas.DataFrame({'cutoff': [0.5, 0.6, 1., 1.5, 2., 2.5], 'area': np.nan})
    for idx in areas.index:
        ctoff = areas.loc[idx, 'cutoff']
        areas.loc[idx, 'area'] = area(freq[1:LN], vl, ctoff)
    return {'peaks': pandas.DataFrame({'idx': peaks, 'frq': freq[peaks], 'vals': vl[peaks]}),
            'raw': pandas.DataFrame({'t': tdt['_time'].to_numpy(), 'sig': tdt[col].to_numpy()}),
            'rfft': pandas.DataFrame({'freq': freq[1:LN], 'fft': np.abs(X)[1:LN]}),
            'sfft': pandas.DataFrame({'freq': freq[1:LN], 'fft': vl}),
            'areas': areas}

def find_dat_pks(tdtF):
    fs = 1. / tdtF['_time'].diff().median().total_seconds()
    cols = ['modG', 'modA', 'S0', 'S1', 'S2']
    Tresd = {}
    for ics in cols:
        resd = picos(tdtF, fs, ics)
        Tresd[ics] = resd
    return Tresd

def dashboard(parameters):
    title = (parameters.get("eventClick").get("event").get("title"))
    start = (parameters.get("eventClick").get("event").get("start"))
    end = (parameters.get("eventClick").get("event").get("end"))
    st.session_state['title'] = title 
    st.session_state['start'] = start
    st.session_state['end'] = end

def influxCall(start, end, mac, value):
    org    = st.secrets["org"]
    database = st.secrets["ifdb"]
    retention_policy = st.secrets["ifrp"]
    bucket = f'{database}/{retention_policy}'
    tokenv2 = st.secrets["iftoken"]
    start = start.replace(' ','T') + '.000000000Z'
    end = end.replace(' ','T') + '.000000000Z'
    with InfluxDBClient(url=st.secrets["ifurl"],\
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

def drawLeftie(df_l, tresd, cols):
    if tresd != "null":
        st.header("Frequencies (Left)")
        pie = {}
        for ics in cols:
            j = 0
            resd = tresd[ics]
            freq = resd['rfft']['freq']
            valr = resd['rfft']['fft']
            sval = resd['sfft']['fft']
            # It is supposed that each foot for the same ActID are the next
            # Several groups of pairs of feets can be requested
            j = j + 1
            rj = j % 2
            if rj == 0:
                rj = 2
            if rj == 1:  # First time we start plotting we ask for the framework
                plt.figure(figsize=(12, 4))
            plt.subplot(120+rj)
            plt.plot(freq, valr/max(valr))
            plt.xlim(0, 5)
            plt.title(f'{ics}')  # Add the title based on the current ics
            st.pyplot(plt)
            plt.close()
            # if rj == 2:  # When ending the row we ask to show the two graphs
            #     st.pyplot(plt)
            #     print('*** Item: {}. ActID: {}'.format(ics))
            #     plt.close()
        # for ics in cols:
        #     print(resd['peaks'])
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

def drawRightie(df_r, tresd, cols):
    if tresd != "null":
        st.header("Frequencies (Right)")
        pie = {}
        for ics in cols:
            j = 0
            resd = tresd[ics]
            freq = resd['rfft']['freq']
            valr = resd['rfft']['fft']
            sval = resd['sfft']['fft']
            # It is supposed that each foot for the same ActID are the next
            # Several groups of pairs of feets can be requested
            j = j + 1
            rj = j % 2
            if rj == 0:
                rj = 2
            if rj == 1:  # First time we start plotting we ask for the framework
                plt.figure(figsize=(12, 4))
            plt.subplot(120+rj)
            plt.plot(freq, valr/max(valr))
            plt.xlim(0, 5)
            plt.title(f'{ics}')  # Add the title based on the current ics
            st.pyplot(plt)
            plt.close()
            # if rj == 2:  # When ending the row we ask to show the two graphs
            #     st.pyplot(plt)
            #     print('*** Item: {}. ActID: {}'.format(ics))
            #     plt.close()
        # for ics in cols:
        #     print(resd['peaks'])
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
                        drawLeftie(df_l, "null", "null")
                except:
                    with left_foot:
                        st.write("**No data**")
                try:
                    with right_foot:
                        drawRightie(df_r, "null", "null")
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

            Tresd = find_dat_pks(df_r)
            cols = ['modG','modA','S0','S1','S2']
            
            drawRightie(df_r, Tresd, cols)

        if (title=="L-04"):
            macL = "E0:52:B2:8B:2A:C2"

            for val in values:
                temp = influxCall(start, end, macL, val)
                dfvalueL = pandas.concat([dfvalueL,temp],axis=0,ignore_index=True)
            df_l = dfvalueL.pivot_table(index='_time', values=values)
            df_l.reset_index(inplace=True)
            df_l['modA'] = (df_l[['Ax','Ay','Az']]**2).sum(axis=1)**0.5
            df_l['modG'] = (df_l[['Gx','Gy','Gz']]**2).sum(axis=1)**0.5

            Tresd = find_dat_pks(df_l)
            cols = ['modG','modA','S0','S1','S2']

            drawLeftie(df_l, Tresd, cols)
            
    
    
    if st.session_state:
        
        datetime_start = datetime.strptime(st.session_state.start, "%Y-%m-%dT%H:%M:%S%z")
        datetime_end = datetime.strptime(st.session_state.end, "%Y-%m-%dT%H:%M:%S%z")

        starter = datetime.strftime(datetime_start, "%Y-%m-%d %H:%M:%S%z")
        ender = datetime.strftime(datetime_end, "%Y-%m-%d %H:%M:%S%z")

        st.title(f"Dataset: _{st.session_state.title}_")
        st.title(f"From: _{starter}_")
        st.title(f"To: _{ender}_")

        
        theme = st_javascript("""function darkMode(i){return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)}(1)""")
    
        if ((datetime_end - datetime_start) <= timedelta(0, 30)):

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
            if timeline.button("Show", type="primary"):
                drawGraphs(st.session_state.title, selected, selected_added)

            ### Custom CSS for the sticky header
            if theme:
                st.markdown(
                    """
                <style>
                    div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
                        position: sticky;
                        top: 2.875rem;
                        background-color: #0E1117;
                        z-index: 999;
                        
                    }
                    
                </style>
                    """,
                    unsafe_allow_html=True
                )
            else:
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

            #drawGraphs(st.session_state.title, selected, selected_added)

    else:
        data_load_state = st.text('Something went wrong...')



    
