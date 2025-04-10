import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="FYP - Interactive Dashboard", layout="wide")
st.title("📊 FYP - Interactive Data Analysis")

# PART 1: File upload
st.sidebar.title("Upload your data")
uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx'])

# Initialize df
df = None

@st.cache_data
def load_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        return None
    except Exception as e:
        st.sidebar.error(f"❌ Error loading file: {e}")
        return None

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.sidebar.success("✅ File uploaded successfully!")
    # Store the DataFrame in session_state
    st.session_state['df'] = df

# PART 2: Show raw data
if df is not None:
    show_raw_data = st.checkbox("Show raw data", value=False)
    if show_raw_data:
        st.subheader("📄 Raw Data")
        st.dataframe(df, use_container_width=True)

    # PART 3: Filter & Visualizations
    st.subheader("Filter & Visualize Data")
    target_col = st.selectbox("Select target column for visualizations", options=[''] + list(df.columns))
    if target_col:
        plt.figure(figsize=(10, 5))
        if df[target_col].nunique() > 2:
            st.subheader(f"Histogram of {target_col}")
            sns.histplot(df[target_col])
        else:
            st.subheader(f"Count plot of {target_col}")
            sns.countplot(x=target_col, data=df)
        st.pyplot(plt.gcf())
        plt.clf()

    # PART 4: Summary Statistics (Detailed)
    st.subheader("📌 Detailed Summary Statistics")
    attribute_stats = st.selectbox("Select attribute for summary stats", options=[''] + list(df.columns))
    if attribute_stats:
        st.write("**Describe:**")
        st.write(df[attribute_stats].describe(include='all'))
        
        st.write("**Additional Info:**")
        non_null = df[attribute_stats].notnull().sum()
        unique = df[attribute_stats].nunique()
        dtype = df[attribute_stats].dtype
        st.markdown(f"""
        - **Non-null count:** {non_null}
        - **Unique values:** {unique}
        - **Data type:** {dtype}
        """)

    # PART 6: Trend Analysis
    st.subheader("📈 Trend Analysis")
    trend_service_col = st.selectbox("Select service column (target)", options=[''] + list(df.columns))
    time_col = st.selectbox("Select time column for trend", options=[''] + ['Year', 'Month', 'Day'])
    trend_mode = st.selectbox("How to display trend?", ["Sum All Classes", "Separate Classes"])

    if trend_service_col and time_col:
        trend_df = df[[trend_service_col, time_col]].dropna()
        if df[time_col].dtype in ['int64', 'int32']:
            trend_df[time_col] = trend_df[time_col].astype(str)

        if trend_mode == "Separate Classes":
            if df[trend_service_col].dtype == 'object' or df[trend_service_col].nunique() < 10:
                trend_grouped = trend_df.groupby([time_col, trend_service_col]).size().reset_index(name='Count')
                st.subheader(f"{trend_service_col} Count by {time_col} (Separate Classes)")
                fig = px.bar(trend_grouped, x=time_col, y='Count', color=trend_service_col, barmode='group')
            else:
                trend_grouped = trend_df.groupby([time_col, trend_service_col]).size().reset_index(name='Count')
                fig = px.line(trend_grouped, x=time_col, y='Count', color=trend_service_col, markers=True)
                st.subheader(f"Value Distribution by {time_col} (Separate Classes)")
        else:
            if df[trend_service_col].dtype == 'object' or df[trend_service_col].nunique() < 10:
                trend_grouped = trend_df.groupby(time_col).size().reset_index(name='Total Count')
                fig = px.bar(trend_grouped, x=time_col, y='Total Count')
                st.subheader(f"Total Count of {trend_service_col} by {time_col}")
            else:
                trend_grouped = trend_df.groupby(time_col)[trend_service_col].mean().reset_index()
                fig = px.line(trend_grouped, x=time_col, y=trend_service_col, markers=True)
                st.subheader(f"Average {trend_service_col} by {time_col} (Summed)")

        st.plotly_chart(fig, use_container_width=True)
else:
    st.write("📂 Please upload a dataset in the sidebar to begin.")

# Sidebar instructions
st.sidebar.markdown("---")
st.sidebar.info("Upload a `.xlsx` or `.csv` file, then explore filtering, visualizations, and trends.")