import streamlit as st
import yfinance as yf 
from snowflake.snowpark import Session
import pandas as pd
import json
import plotly.express as px
import openai
from datetime import datetime,timedelta

st.title('Stock analyze')
ticker = st.sidebar.selectbox('Stock',['QS','TSLA','MSFT','NVDA','T','AAPL','AMD'])
name = 'Stock name: ' + ticker
today = datetime.today()
sub_day = timedelta(days=7) 
today_sub = today - sub_day


start_date = st.sidebar.date_input('Start Date',value=today_sub,max_value=today_sub)
end_date = st.sidebar.date_input('End Date',max_value=today)

data = yf.download(ticker,start=start_date, end=end_date)
fig = px.line(data, x = data.index, y = data['Adj Close'],title=name)
st.plotly_chart(fig)


st.header('Price movement')
st.write(data)


ticker_name = ticker + '.csv'
st.sidebar.download_button(label='Download data',data=data.to_csv(),file_name=ticker_name)
    
with open('creds.json') as f:
    conection_para = json.load(f)
session = Session.builder.configs(conection_para).create()
st.sidebar.success("Connected to Snowflake!")

files = st.sidebar.file_uploader("Choose a CSV file", type={"csv"})
if files is not None:
    try:
        file_pd = pd.read_csv(files)
        table_name = files.name[0:-4]
        table_name = table_name.upper()
        snowDf = session.write_pandas(file_pd,table_name,auto_create_table=True,overwrite=True)
        st.sidebar.success("Uploaded to Snowflake!")
    except Exception as e:
        st.sidebar.warning("Fail")
        st.sidebar.write(e)


st.title("Ask chat :D")
openai.api_key = st.secrets["OPENAI_API_KEY"]

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("What is up?")
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in openai.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        ):
            full_response += (response.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    
    



