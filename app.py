import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

# Initialize session state for saved results if it doesn't exist
if 'saved_results' not in st.session_state:
    st.session_state.saved_results = []

# Set page configuration with a Dutch title
st.set_page_config(
    page_title="DCSPH Gegevens Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #0D47A1;
        font-weight: 500;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .stProgress .st-emotion-cache-mybnsg {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Define the file path for the Excel file
file_path = "lijst.xlsx"

# Function to load the data
@st.cache_data
def load_data(file_path):
    """Load Excel data with caching to improve performance"""
    try:
        # Load the 'DCSPH Aanspraakcode' sheet with no thousands separator
        # Note the trailing space in the sheet name
        df = pd.read_excel(file_path, sheet_name="DCSPH Aanspraakcode ", header=2)
        
        # Convert DCSPH column to integer without any formatting
        if 'DCSPH' in df.columns:
            # Convert to string first to remove any formatting, then to integer
            df['DCSPH'] = df['DCSPH'].astype(str).str.replace('.', '').str.replace(',', '')
            # Convert back to numeric (as integer)
            df['DCSPH'] = pd.to_numeric(df['DCSPH'], errors='coerce').fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Fout bij het laden van Excel-bestand: {e}")
        return None

# Check if the file exists
if os.path.exists(file_path):
    # Load the data
    with st.spinner("Gegevens laden..."):
        df = load_data(file_path)
    
    if df is not None:
        # Clean column names by stripping whitespace
        df.columns = df.columns.str.strip()
        
        # Convert DCSPH column to integer without any formatting
        if 'DCSPH' in df.columns:
            # Convert to string first to remove any formatting, then to integer
            df['DCSPH'] = df['DCSPH'].astype(str).str.replace('.', '').str.replace(',', '')
            # Convert back to numeric (as integer)
            df['DCSPH'] = pd.to_numeric(df['DCSPH'], errors='coerce').fillna(0).astype(int)
        
        # SIDEBAR: All filters go here
        with st.sidebar:
            st.title("DCSPH Filters")
            
            # Step 1: Filter by Omschrijving
            st.markdown("### 1. Selecteer Omschrijving")
            
            omschrijving_col = next((col for col in df.columns if col.strip() == "Omschrijving"), None)
            
            if not omschrijving_col:
                st.error("Kolom 'Omschrijving' niet gevonden in het Excel-bestand.")
            else:
                # Get unique values for Omschrijving dropdown, filtering out None/NaN
                unique_omschrijving = [val for val in df[omschrijving_col].unique() if pd.notna(val) and val != ""]
                unique_omschrijving.sort()
                
                selected_omschrijving = st.selectbox(
                    "Selecteer een waarde:",
                    options=unique_omschrijving,
                    index=None,
                    placeholder="Selecteer een waarde..."
                )
                
                if selected_omschrijving:
                    # Filter by the selected Omschrijving for next steps
                    filtered_by_omschrijving = df[df[omschrijving_col] == selected_omschrijving]
                    
                    # Step 2: Filter by pathologie (text version)
                    st.markdown("### 2. Selecteer Pathologie")
                    
                    # Column index 4 contains the text version of pathologie
                    pathologie_text_col = df.columns[4]  # From our analysis
                    
                    if pathologie_text_col not in df.columns:
                        st.error(f"Kolom voor pathologie tekst niet gevonden.")
                    else:
                        # Get unique values for the pathologie dropdown from the filtered data
                        unique_pathologie = filtered_by_omschrijving[pathologie_text_col].dropna().unique().tolist()
                        unique_pathologie.sort()
                        
                        selected_pathologie = st.selectbox(
                            "Selecteer een waarde:",
                            options=unique_pathologie,
                            index=None,
                            placeholder="Selecteer een waarde..."
                        )
                        
                        if selected_pathologie:
                            # Filter by the selected Pathologie for next step
                            filtered_by_path = filtered_by_omschrijving[
                                filtered_by_omschrijving[pathologie_text_col] == selected_pathologie
                            ]
                            
                            # Step 3: Filter by lichaamslocalisatie (text version)
                            st.markdown("### 3. Selecteer Lichaamslocalisatie")
                            
                            # Column index 3 contains the text version of lichaamslocalisatie
                            lichaamslocalisatie_text_col = df.columns[3]  # From our analysis
                            
                            if lichaamslocalisatie_text_col not in df.columns:
                                st.error(f"Kolom voor lichaamslocalisatie tekst niet gevonden.")
                            else:
                                # Get unique values for the lichaamslocalisatie dropdown from the filtered data
                                unique_lichaamslocalisatie = filtered_by_path[lichaamslocalisatie_text_col].dropna().unique().tolist()
                                unique_lichaamslocalisatie.sort()
                                
                                selected_lichaamslocalisatie = st.selectbox(
                                    "Selecteer een waarde:",
                                    options=unique_lichaamslocalisatie,
                                    index=None,
                                    placeholder="Selecteer een waarde..."
                                )
                                
                                # Reset button at the bottom of sidebar
                                if st.button("Reset Filters", type="primary", use_container_width=True):
                                    st.rerun()

        # MAIN PAGE: Display results here
        st.title("DCSPH Gegevens Viewer")
        
        # Check if there are saved results without any current filters
        if not (selected_omschrijving and selected_pathologie and selected_lichaamslocalisatie) and st.session_state.saved_results:
            st.markdown("## Opgeslagen Resultaten")
            
            # Create a table with saved search criteria
            saved_data = []
            for i, result in enumerate(st.session_state.saved_results):
                saved_data.append({
                    "Nummer": i+1,
                    "Tijd": result["timestamp"],
                    "Datum": result["date"],
                    "Omschrijving": result["omschrijving"],
                    "Pathologie": result["pathologie"],
                    "Lichaamslocalisatie": result["lichaamslocalisatie"],
                    "Aantal Records": result["count"]
                })
            
            saved_df = pd.DataFrame(saved_data)
            st.dataframe(saved_df, use_container_width=True, hide_index=True)
            
            # Allow viewing a specific saved result
            if len(st.session_state.saved_results) > 0:
                selected_result_index = st.selectbox(
                    "Selecteer een opgeslagen resultaat om te bekijken:",
                    options=range(1, len(st.session_state.saved_results) + 1),
                    format_func=lambda x: f"Resultaat {x} - {st.session_state.saved_results[x-1]['timestamp']} - {st.session_state.saved_results[x-1]['omschrijving']}"
                )
                
                if selected_result_index:
                    # Display the selected saved result
                    result_data = st.session_state.saved_results[selected_result_index-1]["data"]
                    
                    st.markdown(f"### Resultaat {selected_result_index} Details")
                    st.markdown(f"**Omschrijving:** {st.session_state.saved_results[selected_result_index-1]['omschrijving']}")
                    st.markdown(f"**Pathologie:** {st.session_state.saved_results[selected_result_index-1]['pathologie']}")
                    st.markdown(f"**Lichaamslocalisatie:** {st.session_state.saved_results[selected_result_index-1]['lichaamslocalisatie']}")
                    
                    # Display the data
                    st.dataframe(result_data, use_container_width=True, hide_index=True, height=400)
            
            # Add option to clear saved results
            if st.button("Opgeslagen Resultaten Wissen", type="secondary"):
                st.session_state.saved_results = []
                st.rerun()
            
        # Check if all filters are selected to display results
        elif selected_omschrijving and selected_pathologie and selected_lichaamslocalisatie:
            # Apply all filters to get final results
            final_filtered_df = df[
                (df[omschrijving_col] == selected_omschrijving) & 
                (df[pathologie_text_col] == selected_pathologie) &
                (df[lichaamslocalisatie_text_col] == selected_lichaamslocalisatie)
            ]
            
            # Display filters that were applied
            st.markdown("## Toegepaste Filters")
            
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                st.markdown(f"**Omschrijving:** {selected_omschrijving}")
            with filter_col2:
                st.markdown(f"**Pathologie:** {selected_pathologie}")
            with filter_col3:
                st.markdown(f"**Lichaamslocalisatie:** {selected_lichaamslocalisatie}")
            
            st.markdown("---")
            
            # Display results section
            st.markdown("## Resultaten")
            
            if not final_filtered_df.empty:
                # Display count
                st.markdown(f"**Aantal gevonden records:** {len(final_filtered_df)}")
                
                # Get relevant information columns
                # First check what columns are available as relevant information
                relevant_cols = ["DCSPH", df.columns[1], df.columns[2], df.columns[3], df.columns[4], 
                                df.columns[5], df.columns[6], df.columns[7], 
                                df.columns[8], df.columns[9]]
                
                # Only include columns that actually exist
                available_cols = [col for col in relevant_cols if col in final_filtered_df.columns]
                
                # Format column names for display
                formatted_df = final_filtered_df[available_cols].copy()
                
                # Ensure DCSPH column is displayed as integer without any formatting
                if 'DCSPH' in formatted_df.columns:
                    # Convert to string first to remove any formatting, then to integer
                    formatted_df['DCSPH'] = formatted_df['DCSPH'].astype(str).str.replace('.', '').str.replace(',', '')
                    # Convert back to numeric (as integer)
                    formatted_df['DCSPH'] = pd.to_numeric(formatted_df['DCSPH'], errors='coerce').fillna(0).astype(int)
                
                column_mapping = {
                    "DCSPH": "DCSPH Code",
                    df.columns[1]: "Lichaamsloc. Code",
                    df.columns[2]: "Pathologie Code",
                    df.columns[3]: "Lichaamslocalisatie",
                    df.columns[4]: "Pathologie",
                    df.columns[5]: "Status DCSPH",
                    df.columns[6]: "Omschrijving Pathologieën",
                    df.columns[7]: "Bekken FT Pathologieën",
                    df.columns[8]: "Maximale Termijn",
                    df.columns[9]: "Andere Voorwaarden"
                }
                formatted_df = formatted_df.rename(columns={col: column_mapping.get(col, col) for col in available_cols})
                
                # Display the data in a clean table format with horizontal scrolling
                # Explicitly format the DCSPH column to display as plain integers without separators
                if 'DCSPH Code' in formatted_df.columns:
                    formatted_df['DCSPH Code'] = formatted_df['DCSPH Code'].apply(lambda x: f"{int(x)}" if pd.notnull(x) else "")
                
                st.dataframe(
                    formatted_df, 
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                # Add save button for the results
                if st.button("Resultaten Opslaan", type="primary"):
                    # Create a dictionary with the search criteria and results
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    saved_result = {
                        "timestamp": timestamp,
                        "date": date.today().strftime("%d-%m-%Y"),
                        "omschrijving": selected_omschrijving,
                        "pathologie": selected_pathologie,
                        "lichaamslocalisatie": selected_lichaamslocalisatie,
                        "count": len(final_filtered_df),
                        "data": final_filtered_df.copy()
                    }
                    # Add to saved results
                    st.session_state.saved_results.append(saved_result)
                    st.success(f"Resultaten opgeslagen! ({timestamp})")
                
            else:
                st.warning("Geen overeenkomende records gevonden met de geselecteerde filters.")
        
            # Display saved results section
            if st.session_state.saved_results:
                st.markdown("---")
                st.markdown("## Opgeslagen Resultaten")
                
                # Create a table with saved search criteria
                saved_data = []
                for i, result in enumerate(st.session_state.saved_results):
                    saved_data.append({
                        "Nummer": i+1,
                        "Tijd": result["timestamp"],
                        "Datum": result["date"],
                        "Omschrijving": result["omschrijving"],
                        "Pathologie": result["pathologie"],
                        "Lichaamslocalisatie": result["lichaamslocalisatie"],
                        "Aantal Records": result["count"]
                    })
                
                saved_df = pd.DataFrame(saved_data)
                st.dataframe(saved_df, use_container_width=True, hide_index=True)
        
    else:
        st.error("Kon de gegevens niet laden. Controleer het Excel-bestand.")
        
else:
    st.error(f"Bestand '{file_path}' niet gevonden. Zorg ervoor dat het Excel-bestand de naam 'lijst.xlsx' heeft en zich in dezelfde map bevindt als deze applicatie.")