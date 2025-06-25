
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import io
from datetime import date

####################################Setting  Mainpage
st.subheader("Data Processor")

#####Processor Target

source = st.radio("Select Source", ["FP1.0", "FP2.0"], horizontal=True)

####################################Setting Sidebar
st.sidebar.header("Settings")

######for nature
default_nature = "FP2.0" if source == "FP2.0" else "Repayment"

#Dropdownlist and add "Costom"
nature_options = ["Repayment","FP2.0","Drawdown", "Rollover", "Other"]
default_index = nature_options.index(default_nature)

selected_nature = st.sidebar.selectbox("Nature", nature_options, index=default_index)

# If Other
if selected_nature == "Other":
    custom_nature = st.sidebar.text_input("Custom nature name")
    nature_input = custom_nature
else:
    nature_input = selected_nature

#Show
st.sidebar.write("nature value：", nature_input)

#######For Maker
Maker_name = st.sidebar.text_input("Maker Name")

#######Other supplementary details

today = date.today().strftime('%Y-%m-%d')

##################################For FP1.O Data
def parse_text_to_dataframes(text):
    lines = text.strip().split('\n')
    data = {}
    current_section = None
    current_key = None

    for line in lines:
        if line.strip() == "":
            continue
        if not current_section or line.endswith('Details') or line.endswith('Information') or line.endswith('Transaction') or line.endswith('Items'):
            current_section = line.strip()
            data[current_section] = {}
            current_key = None
        else:
            if current_key is None:
                current_key = line.strip()
            else:
                data[current_section][current_key] = line.strip()
                current_key = None
    dfs = {section: pd.DataFrame(list(info.items()), columns=['Key', 'Value']) for section, info in data.items()}


    data = {
        "Date": [today],
        "Repayment Date": [dfs["Payment Details"].loc[dfs["Payment Details"]["Key"] == "Payment Date", "Value"].values[0]],
        "Trade Code": [dfs["Payment Details"].loc[dfs["Payment Details"]["Key"] == "Trade Code", "Value"].values[0]],
        "Nature": [nature_input],
        "Funder Code": [dfs["Funder Information"].loc[dfs["Funder Information"]["Key"] == "Sub Account Number", "Value"].values[0]],
        "Currency": [dfs["Payment Details"].loc[dfs["Payment Details"]["Key"] == "Payment Currency", "Value"].values[0]],
        "Principal": [dfs["Funder Transaction"].loc[dfs["Funder Transaction"]["Key"] == "Repayment", "Value"].values[0]],
        "Interest": [dfs["Funder Transaction"].loc[dfs["Funder Transaction"]["Key"] == "Interest", "Value"].values[0]],
        "Platform Fee": [dfs["Funder Transaction"].loc[dfs["Funder Transaction"]["Key"] == "Platform Fee", "Value"].values[0]],
        "Spreading": [dfs["FundPark Transaction"].loc[dfs["FundPark Transaction"]["Key"] == "FundPark Spreading", "Value"].values[0]],
        "Total Amount": [dfs["Payment Details"].loc[dfs["Payment Details"]["Key"] == "Actual Received Amount", "Value"].values[0]],
        "Sub": [abs(float(dfs["Waive Items"].loc[dfs["Waive Items"]["Key"] == "Bank Charge", "Value"].values[0]))],
        "Transfer Acc": [""],
        "CSV": [""],
        "Maker": [Maker_name]
    }

    df = pd.DataFrame(data)
    return df



###################################For FP2.0 Data
def fp2_parse_raw_data(raw_data):
    # Split according to the title number
    sections = raw_data.split('\n')
    fp2_parsed_data = {}
    current_section = None

    for line in sections:
        if line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ')):
            current_section = line.strip()
            fp2_parsed_data[current_section] = {}
        elif current_section:
            key_value = line.split('\t')
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()
                fp2_parsed_data[current_section][key] = value
    
        # Convert the parsed data dictionary to a pandas DataFrame

    # 构建目标格式的 DataFrame
    data = {
        "Date": [today],
        "Repayment Date": [fp2_parsed_data["1. Repayment Details"]["Repayment Date"]],
        "Trade Code": [fp2_parsed_data["1. Repayment Details"]["Trade Code"]],
        "Nature": [nature_input],
        "Funder Code": [fp2_parsed_data["2. Settlement to Funder"]["Funder sub account no"]],
        "Currency": [fp2_parsed_data["1. Repayment Details"]["Payment Currency"]],
        "Principal": [fp2_parsed_data["2. Settlement to Funder"]["Settled Loan Amount"]],
        "Interest": [fp2_parsed_data["2. Settlement to Funder"]["Settled Interest"]],
        "Platform Fee": [fp2_parsed_data["2. Settlement to Funder"]["Settled PF"]],
        "Spreading": [fp2_parsed_data["3. FundPark Allocation"]["FundPark Allocation Amount"]],
        "Total Amount": [fp2_parsed_data["1. Repayment Details"]["Actual Received Amount"]],
        "Sub": [""],
        "Transfer Acc": [""],
        "CSV": [""],
        "Maker": [Maker_name],
        "Checker":[""],
        "Approver":["N/A"]
    }

    df = pd.DataFrame(data)
    return df


####################For the main page

if "raw_input" not in st.session_state:
    st.session_state.raw_input = ""

# 定义清除函数
def clear_text():
    st.session_state.raw_input = ""

# 文本输入框，绑定到 session_state
raw_input = st.text_area("Paste Your Data Here", height=300, key="raw_input")

# 按钮操作

col1, col2, _ = st.columns([1, 1, 0.1])

with col1:
    output_button = st.button("Output")

with col2:
    clean_button = st.button("Clean", on_click=clear_text)


if output_button:
    if raw_input.strip():
        if source == 'FP1.0':
            df = parse_text_to_dataframes(raw_input)
        elif source == 'FP2.0':
            df = fp2_parse_raw_data(raw_input)

        st.dataframe(df)

        # 获取第二行（或第一行）
        if len(df) > 1:
            second_row = df.iloc[1]
        else:
            second_row = df.iloc[0]

        # 转换为字符串（制表符分隔）
        row_str = '\t'.join([str(v) for v in second_row.values])

       
        # 插入更符合 Streamlit 风格的按钮
        styled_button = f"""
        <style>
            .copy-btn {{
                background-color: #f63366;
                color: white;
                border: none;
                padding: 0.5em 1em;
                border-radius: 0.5em;
                font-size: 1em;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }}
            .copy-btn:hover {{
                background-color: #c42d54;
            }}
            .copy-msg {{
                margin-top: 0.5em;
                color: green;
                font-weight: bold;
            }}
        </style>
        <button class="copy-btn" onclick="navigator.clipboard.writeText(`{row_str}`); document.getElementById('copied').innerText='Copied';">
            Copy the trade info
        </button>
        <div id="copied" class="copy-msg"></div>
        """

        components.html(styled_button, height=120)
    else:
        st.warning("please paste the data first")
