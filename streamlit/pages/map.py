import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap

st.set_page_config(layout="wide")
st.title("🗺️ Geospatial Visualization")

# Caching function for loading data
@st.cache_data
def load_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.error(f"❌ Error loading file: {e}")
        return None

# Function to create map markers with popup info
@st.cache_data
def create_map(df, lat_col, lon_col, popup_columns):
    m = folium.Map(location=[df[lat_col].mean(), df[lon_col].mean()], zoom_start=12)
    for _, row in df.iterrows():
        popup_info = "<br>".join([f"<b>{col}:</b> {row.get(col, 'N/A')}" for col in popup_columns])
        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            popup=popup_info,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)
    return m

# Function to create heatmap
@st.cache_data
def create_heatmap(df, lat_col, lon_col):
    m_heat = folium.Map(location=[df[lat_col].mean(), df[lon_col].mean()], zoom_start=12)
    heat_data = df[[lat_col, lon_col]].dropna().values.tolist()
    HeatMap(heat_data).add_to(m_heat)
    return m_heat

# Data loading section
if 'df' not in st.session_state:
    st.warning("Please upload your data from the Home page.")
    st.sidebar.title("Upload your data")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx'])
    df = None
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None:
            st.sidebar.success("✅ File uploaded successfully!")
            st.session_state['df'] = df
else:
    df = st.session_state.df

# If data is loaded
if df is not None:
    st.subheader("📍 Select Latitude and Longitude Columns")

    col1, col2 = st.columns(2)
    with col1:
        lat_col = st.selectbox("Latitude Column", options=[''] + list(df.columns))
    with col2:
        lon_col = st.selectbox("Longitude Column", options=[''] + list(df.columns))

    if lat_col and lon_col:
        df = df.dropna(subset=[lat_col, lon_col])
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
        df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
        df = df.dropna(subset=[lat_col, lon_col])  # Drop rows that failed conversion

        # Choose columns for popup info
        st.subheader("📝 Choose Columns to Display on Map Popups")
        popup_columns = st.multiselect("Select columns to include in marker popup info", options=df.columns.tolist())

        # Chunking logic for large datasets
        chunk_size = 1000
        total_rows = df.shape[0]
        total_chunks = (total_rows // chunk_size) + (1 if total_rows % chunk_size != 0 else 0)

        if total_chunks > 1:
            st.warning(f"Large dataset detected ({total_rows} rows). Displaying in chunks of {chunk_size}.")
            chunk_index = st.slider("Select data chunk", min_value=1, max_value=total_chunks, value=1)
            start = (chunk_index - 1) * chunk_size
            end = start + chunk_size
            df_chunk = df.iloc[start:end]
        else:
            df_chunk = df

        # Create and display the interactive map
        st.subheader("📍 Interactive Location Map")
        m = create_map(df_chunk, lat_col, lon_col, popup_columns)
        st_folium(m, width=1200)

        # Create and display the heatmap
        st.subheader("🔥 Heatmap of Immigrant Concentration")
        m_heat = create_heatmap(df_chunk, lat_col, lon_col)
        st_folium(m_heat, width=1200)

else:
    st.info("Please upload a dataset from the Home page or above to begin.")