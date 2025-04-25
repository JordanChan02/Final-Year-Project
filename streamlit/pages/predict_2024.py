%%writefile streamlit/pages/predict_2024.py

import streamlit as st
import pandas as pd
import joblib

REQUIRED_COLUMNS = [
    'Gender', 'One_Way_Permit_Application_Category',
    'Social_Welfare_Department', 'Receive_Communications',
    'Knows_Cantonese', 'Education',
    'Had_Long_Term_Work_in_Mainland_Before_Arrival', 'Occupation',
    'Settlement_Father', 'Settlement_Mother',
    'Number_of_Biological_Children', 'age', 'Year', 'Month', 'Day',
    'address_latitude', 'address_longitude', 'origin_address_latitude',
    'origin_address_longitude'
]

@st.cache_resource
def load_model(name):
    return joblib.load(f"streamlit/mmodels/{name.lower()}_2024.pkl")

@st.cache_data
def process_input(df, drop_column=None):
    if drop_column and drop_column in df.columns:
        df = df.drop(columns=[drop_column])
    
    numeric_df = df.select_dtypes(exclude='object')
    object_df = df.select_dtypes(include='object')
    
    # Convert all object columns to strings, then get dummies
    if not object_df.empty:
        object_df = object_df.astype(str)
        dummy_df = pd.get_dummies(object_df)
        processed_df = pd.concat([numeric_df, dummy_df], axis=1)
    else:
        processed_df = numeric_df
    
    return processed_df

# Streamlit UI Setup
st.set_page_config("Predictive Modeling Interface", layout="wide")
st.title("🔍 Predictive Modeling Interface")

st.sidebar.header("Prediction Settings")
input_type = st.sidebar.radio("Select Input Type", ("Upload File", "Manual Input"))
model_choice = st.sidebar.selectbox("Model", ["RandomForest", "XGBoost"])

input_df = None
drop_col = None

# Upload Section
if input_type == "Upload File":
    uploaded_file = st.sidebar.file_uploader("Upload File (CSV or XLSX)", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.session_state.df = df
        except Exception as e:
            st.error(f"Failed to read file: {e}")
    
    if 'df' in st.session_state:
        df = st.session_state.df
        st.write("📄 Uploaded Data Preview", df.head())

        drop_col = st.selectbox("Which column is the service label?", ["None"] + list(df.columns))
        drop_col = None if drop_col == "None" else drop_col
        input_df = df.copy()
        input_df = process_input(input_df, drop_column=drop_col)

# Manual Input Section
else:
    st.subheader("Manual Input")
    manual_data = {}
    for col in REQUIRED_COLUMNS:
        if col in ['Number_of_Biological_Children', 'age', 'Year', 'Month', 'Day',
                   'address_latitude', 'address_longitude',
                   'origin_address_latitude', 'origin_address_longitude']:
            manual_data[col] = st.number_input(col, value=0.0)
        else:
            manual_data[col] = st.text_input(col, "")

    input_df = pd.DataFrame([manual_data])
    input_df = process_input(input_df)

# Prediction Controls
if input_df is not None and not input_df.empty:
    st.markdown("## 🔮 Prediction Options")
    prediction_mode = st.radio("Choose prediction mode:", ("Predict All", "Step-by-Step"))
    model = load_model(model_choice)

    try:
        # Align with model features
        model_features = (
            model.feature_names_in_
            if hasattr(model, "feature_names_in_")
            else model.get_booster().feature_names
        )

        missing_cols = [col for col in model_features if col not in input_df.columns]
        for col in missing_cols:
            input_df[col] = 0
        input_df = input_df[model_features]

        if prediction_mode == "Step-by-Step":
            if "row_index" not in st.session_state:
                st.session_state.row_index = 0

            total_rows = len(input_df)
            current_index = st.session_state.row_index

            if current_index < total_rows:
                st.write(f"🔢 Predicting row {current_index + 1} of {total_rows}")
                if st.button("Predict This One"):
                    prediction = model.predict(input_df.iloc[[current_index]])
                    st.success(f"🎯 Predicted: {prediction[0]}")
                if st.button("Next One"):
                    st.session_state.row_index += 1
                    st.rerun()
            else:
                st.info("✅ All rows have been predicted.")

        else:  # Predict All
            if st.button("Predict All Rows"):
                predictions = model.predict(input_df)
                results = input_df.copy()
                results["Predicted_Service_Type"] = predictions
                st.dataframe(results)
                st.success("✅ Batch prediction complete!")

    except Exception as e:
        st.error(f"Prediction error: {e}")
