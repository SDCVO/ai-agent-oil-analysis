import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import src.model as model
import src.agent as agent
import json


st.set_page_config(page_title="Analysis Solution - MVP", page_icon="🇦🇮", layout="wide") 
c1, c2 = st.columns(2)
    
c1.title("AI-Powered Oil Solution")
fiter_date = c2.number_input(label="Months to load", value=1, min_value=1, max_value=24, step=1) 

# data_raw = pd.read_csv("data/data.csv")
data_raw = pd.read_csv("data/data.csv")


# SIDEBAR
location_list = data_raw['location'].unique()
current_location = st.sidebar.selectbox(label="Select a Location", options=location_list, placeholder="Select a location")

fleet_list = data_raw[data_raw['location'] == current_location]['equipment_type'].unique()
current_fleet = st.sidebar.selectbox(label="Select a Fleet", options=fleet_list, placeholder="Select a fleet")

#TODO: Add an overview of the fleet
# st.sidebar.container(height=280)

equipment_list = data_raw[data_raw['location'] == current_location][data_raw['equipment_type'] == current_fleet]['equipment_number'].unique()
current_equipment = st.sidebar.selectbox(label="Select a Equipment", options=equipment_list, placeholder="Select a equipment")

component_list = data_raw[data_raw['location'] == current_location][data_raw['equipment_type'] == current_fleet][data_raw['equipment_number'] == current_equipment]['component'].unique()
current_component = st.sidebar.selectbox(label="Select a Component", options=component_list, placeholder="Select a component")

data = data_raw[data_raw['location'] == current_location][data_raw['equipment_type'] == current_fleet][data_raw['equipment_number'] == current_equipment][data_raw['component'] == current_component]

cut_date = (datetime.today() - timedelta(days=(int(fiter_date)* 30)))
cut_date = cut_date.strftime("%Y-%m-%d")
data = data[data['sample_date'] >= cut_date]

data['anomaly'] = data.apply(lambda row: model.classify_anomaly(row=row), axis=1) 

#TODO: Query database for anomaly list
anomaly_list = data['anomaly'].iloc[0]
plotting_elements_base = ['al', 'cr', 'cu', 'fe', 'ni', 'pb', 'si', 'sn', 'viscosity_at_100c']
plotting_elements = st.multiselect("Select Plotting Elements", options=plotting_elements_base, default=anomaly_list)

#TODO: Try use plotly for vertical lines
plotting_chart = st.line_chart(
    data=data,
    x='sample_date',
    y=plotting_elements,
    x_label='Date',
    y_label='PPM')

def highlight_anomaly(val):
    if val >= 100:
        return 'background-color: red'
    elif val >= 50:
        return 'background-color: yellow'

st.dataframe(data.style.applymap(model.highlight_anomaly, subset=plotting_elements_base), hide_index=True)

def plot_metric(label, value, delta, delta_color='normal', border=True):
    return st.metric(
    label=label,
    value=round(value, 2),
    delta=round(delta, 2),
    delta_color=delta_color,
    border=border)

def divide_into_chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


df_diff = data.copy()
df_diff = model.calculate_difference(df_diff)
df_diff = df_diff.sort_values(by=['sample_date'], ascending=False).copy()

ca, cb, cc = st.columns(3)

for chunk in divide_into_chunks(plotting_elements_base, 3):
    with ca:
        plot_metric(
            label=chunk[0].capitalize(),
            value=df_diff[chunk[0]].iloc[0],
            delta=df_diff[f'{chunk[0]}_diff'].iloc[0],
            delta_color='off'
            )
    with cb:
        plot_metric(
            label=chunk[2].capitalize(),
            value=df_diff[chunk[1]].iloc[0],
            delta=df_diff[f'{chunk[1]}_diff'].iloc[0],
            delta_color='off'
            )
    with cc:
        plot_metric(
            label=chunk[2].capitalize(),
            value=df_diff[chunk[2]].iloc[0],
            delta=df_diff[f'{chunk[2]}_diff'].iloc[0],
            delta_color='off'
            )

uploaded_file = st.sidebar.file_uploader(label="Upload your CSV or Excel file :blue-badge[New!]", type=["csv", "xlsx"])

st.markdown(
    """
<style>
div[data-testid="stDialog"] div[role="dialog"]:has(.big-dialog) {
    width: 90vw;
    height: 80vh;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.dialog(title="Preview your data", width='large')
def preview_file(uploaded_file):
    st.write("🔍 Sample of your data:")
    st.html("<span class='big-dialog'></span>")
    st.dataframe(uploaded_file)

@st.dialog(title="🔍 Preview your processed data", width='large')
def wait_for_process():
    st.html("<span class='big-dialog'></span>")
    with st.spinner("Generating cleaning plan..."):
            try:
                sample_data = df_uploaded_file
                if is_mocked:
                    with open('data/plan_sample.txt', mode='r') as file:
                        plan_str = file.read()
                    st.toast('Getting mocked plan!')
                else:
                    plan_str = agent.get_cleaning_plan(sample_data, backend=backend, model='qwen2.5:3b')
                plan = json.loads(plan_str)
                st.session_state["cleaning_plan"] = plan
                st.success("Cleaning plan generated!")
            except Exception as e:
                st.error(f"Failed to generate plan: {e}")

    with st.spinner("Cleaning dataset..."):
            try:
                cleaned_df = agent.apply_cleaning_plan(df_uploaded_file.copy(), st.session_state["cleaning_plan"])
                st.session_state["cleaned_df"] = cleaned_df
                st.success("Cleaning complete!")
                st.dataframe(st.session_state['cleaned_df'])
            except Exception as e:
                st.error(f"Failed to apply cleaning plan: {e}")


if uploaded_file:
    is_mocked = st.sidebar.toggle('Demonstration', value=False)
    backend = st.sidebar.selectbox("Select backend", ["ollama", "openai"])

    try:
        if uploaded_file.name.endswith(".csv"):
            df_uploaded_file = pd.read_csv(uploaded_file)
        else:
            df_uploaded_file = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    if st.sidebar.button("🔍 Preview Data"):
        preview_file(df_uploaded_file)

    if st.sidebar.button("✅ Apply Plan to Dataset"):
        wait_for_process()
        try:
            data_raw = pd.concat([data_raw, st.session_state['cleaned_df']])
        except KeyError:
            print('Error Concatenating Data')