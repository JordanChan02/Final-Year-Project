%%writefile streamlit/pages/map.py

import streamlit as st
import pandas as pd
import folium
import tempfile
import os
import zipfile
from streamlit_folium import st_folium
from folium.plugins import HeatMap

try:
    import geopandas as gpd
except ImportError:
    gpd = None

st.set_page_config(layout="wide")
st.title("🗺️ Geospatial Visualization")

# Caching function for loading data
def _load_tabular(uploaded_file):
    fname = uploaded_file.name.lower()
    if fname.endswith(('.xlsx', '.xls')):
        return pd.read_excel(uploaded_file)
    elif fname.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    return None

@st.cache_data
# Load CSV/Excel or unpack and load Shapefile
def load_data(uploaded_file):
    try:
        fname = uploaded_file.name.lower()
        # Tabular data
        tab = _load_tabular(uploaded_file)
        if tab is not None:
            return tab
        # Geospatial data via shapefile
        if gpd and fname.endswith('.shp'):
            return gpd.read_file(uploaded_file)
        if gpd and fname.endswith('.zip'):
            # Write zip to temp and unpack
            temp_dir = tempfile.mkdtemp()
            zpath = os.path.join(temp_dir, uploaded_file.name)
            with open(zpath, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            with zipfile.ZipFile(zpath, 'r') as z:
                z.extractall(temp_dir)
            # Find .shp
            shp_files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.lower().endswith('.shp')]
            if not shp_files:
                st.sidebar.error("❌ No .shp file found in ZIP archive.")
                return None
            gdf = gpd.read_file(shp_files[0])
            # Extract centroid coords
            gdf['lat'] = gdf.geometry.centroid.y
            gdf['lon'] = gdf.geometry.centroid.x
            return gdf
    except Exception as e:
        st.sidebar.error(f"❌ Error loading file: {e}")
    return None

# Function to create map markers
@st.cache_data
def create_map(df, lat_col, lon_col, popup_columns, zoom_start=12):
    center = [df[lat_col].mean(), df[lon_col].mean()]
    m = folium.Map(location=center, zoom_start=zoom_start)
    for _, row in df.iterrows():
        popup = "<br>".join([f"<b>{col}:</b> {row.get(col, 'N/A')}" for col in popup_columns])
        folium.Marker(location=[row[lat_col], row[lon_col]], popup=popup,
                      icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)
    return m

# Function to create heatmap
@st.cache_data
def create_heatmap(df, lat_col, lon_col, zoom_start=12):
    center = [df[lat_col].mean(), df[lon_col].mean()]
    m = folium.Map(location=center, zoom_start=zoom_start)
    data = df[[lat_col, lon_col]].dropna().values.tolist()
    HeatMap(data).add_to(m)
    return m

def create_map_from_gdf(gdf, lat_col, lon_col, popup_columns, zoom_start=12):
    m = folium.Map(location=[gdf[lat_col].mean(), gdf[lon_col].mean()], zoom_start=zoom_start)
    for _, row in gdf.iterrows():
        popup_info = "<br>".join([f"<b>{col}:</b> {row.get(col, 'N/A')}" for col in popup_columns])
        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            popup=popup_info,
            icon=folium.Icon(color="green", icon="plus-sign")
        ).add_to(m)
    return m


# Sidebar: Upload main dataset
st.sidebar.title("Upload Main Data")
uploaded_main = st.sidebar.file_uploader(
    "Choose CSV, Excel, Shapefile (.shp) or ZIP of shapefile", 
    type=['csv','xlsx','xls','shp','zip'], key='main')

if uploaded_main:
    df_main = load_data(uploaded_main)
    if df_main is not None:
        st.sidebar.success("✅ Main data loaded!")
        st.subheader("📍 Main Dataset: Coordinate Selection")
        cols = [''] + list(df_main.columns)
        c1, c2 = st.columns(2)
        with c1:
            lat_main = st.selectbox("Latitude Column", options=cols, key='lat_main')
        with c2:
            lon_main = st.selectbox("Longitude Column", options=cols, key='lon_main')
        if lat_main and lon_main:
            df = df_main.dropna(subset=[lat_main, lon_main])
            df[lat_main] = pd.to_numeric(df[lat_main], errors='coerce')
            df[lon_main] = pd.to_numeric(df[lon_main], errors='coerce')
            df = df.dropna(subset=[lat_main, lon_main])
            st.subheader("📝 Main Popup Columns")
            popup_main = st.multiselect("Select popup columns", options=df.columns, key='popup_main')
            # Chunk handling
            chunk_size=1000; total=df.shape[0]; chunks=(total//chunk_size)+(1 if total%chunk_size else 0)
            if chunks>1:
                idx = st.slider("Main chunk",1,chunks, key='chunk_main')
                df = df.iloc[(idx-1)*chunk_size:idx*chunk_size]
            # Display
            st.subheader("📍 Main Map")
            st_folium(create_map(df, lat_main, lon_main, popup_main), width=1200)
            st.subheader("🔥 Main Heatmap")
            st_folium(create_heatmap(df, lat_main, lon_main), width=1200)

# Sidebar: Upload POI dataset
st.sidebar.title("Upload POI Data")
uploaded_poi = st.sidebar.file_uploader(
    "Choose CSV, Excel, Shapefile (.shp) or ZIP of shapefile for POI", 
    type=['csv','xlsx','xls','shp','zip'], key='poi')

if uploaded_poi:
    df_poi = load_data(uploaded_poi)
    if df_poi is not None:
        st.sidebar.success("✅ POI data loaded!")
        st.subheader("📍 POI Dataset: Coordinate Selection")
        cols_p = [''] + list(df_poi.columns)
        p1, p2 = st.columns(2)
        with p1:
            lat_poi = st.selectbox("POI Latitude Column", options=cols_p, key='lat_poi')
        with p2:
            lon_poi = st.selectbox("POI Longitude Column", options=cols_p, key='lon_poi')
        if lat_poi and lon_poi:
            poi = df_poi.dropna(subset=[lat_poi, lon_poi])
            poi[lat_poi] = pd.to_numeric(poi[lat_poi], errors='coerce')
            poi[lon_poi] = pd.to_numeric(poi[lon_poi], errors='coerce')
            poi = poi.dropna(subset=[lat_poi, lon_poi])
            st.subheader("📝 POI Popup Columns")
            popup_poi = st.multiselect("Select POI popup columns", options=poi.columns, key='popup_poi')
            st.subheader("📍 POI Map")
            st_folium(create_map_from_gdf(poi, lat_poi, lon_poi, popup_poi), width=1200)
else:
    if not uploaded_main:
        st.info("Upload a dataset to visualize geospatial data.")
