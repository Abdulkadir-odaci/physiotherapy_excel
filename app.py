import streamlit as st
import pandas as pd
import os
from datetime import date

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

# Initialize session state for saved rows if it doesn't exist
if 'saved_rows' not in st.session_state:
    st.session_state.saved_rows = pd.DataFrame()

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

# Create tabs
tab1, tab2 = st.tabs(["Zoeken", "Opgeslagen Resultaten"])

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
            
        # Get the column indices for important columns based on our analysis
        pathologie_col = df.columns[4]  # Text version of pathologie (index 4)
        omschrijving_path_col = df.columns[6]  # Omschrijving pathologieën column (index 6)
        
        # Fill empty "omschrijving pathologieën" cells with the corresponding "pathologie" text values
        # First check if the column exists
        if omschrijving_path_col in df.columns and pathologie_col in df.columns:
            # For each row, if omschrijving_path is empty, fill it with pathologie text value
            df[omschrijving_path_col] = df.apply(
                lambda row: row[pathologie_col] if pd.isna(row[omschrijving_path_col]) or row[omschrijving_path_col] == '' 
                else row[omschrijving_path_col], 
                axis=1
            )
        
        # SIDEBAR: Filter based on omschrijving pathologieën column
        with st.sidebar:
            st.title("DCSPH Filters")
            
            # Filter by Omschrijving Pathologieën
            st.markdown("### Selecteer Omschrijving Pathologieën")
            
            if omschrijving_path_col not in df.columns:
                st.error(f"Kolom '{omschrijving_path_col}' niet gevonden in het Excel-bestand.")
            else:
                # Get unique values for Omschrijving Pathologieën dropdown, filtering out None/NaN
                unique_omschrijving_path = [val for val in df[omschrijving_path_col].unique() if pd.notna(val) and val != ""]
                unique_omschrijving_path.sort()
                
                selected_omschrijving_path = st.selectbox(
                    "Selecteer een waarde:",
                    options=unique_omschrijving_path,
                    index=None,
                    placeholder="Selecteer een waarde..."
                )
                
                # Reset button at the bottom of sidebar
                if st.button("Reset Filters", type="primary", use_container_width=True):
                    st.rerun()

        # TAB 1: Search and Results
        with tab1:
            st.title("DCSPH Gegevens Viewer")
            
            # Check if filter is selected to display results
            if selected_omschrijving_path:
                # Apply filter to get final results
                final_filtered_df = df[df[omschrijving_path_col] == selected_omschrijving_path]
                
                # Display filters that were applied
                st.markdown("## Toegepaste Filters")
                
                st.markdown(f"**Omschrijving Pathologieën:** {selected_omschrijving_path}")
                
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
                    if st.button("Sla Resultaten Op", type="primary"):
                        # Check if DataFrame is already in saved_rows (to avoid duplicates)
                        if st.session_state.saved_rows.empty:
                            # If saved_rows is empty, just assign the current DataFrame
                            st.session_state.saved_rows = final_filtered_df.copy()
                            st.success("Resultaten zijn opgeslagen. Bekijk ze in de tab 'Opgeslagen Resultaten'.")
                        else:
                            # Check if any of these rows are already saved
                            # For simplicity, we'll check if DCSPH codes are the same
                            if 'DCSPH' in st.session_state.saved_rows.columns and 'DCSPH' in final_filtered_df.columns:
                                existing_codes = set(st.session_state.saved_rows['DCSPH'].astype(str))
                                new_codes = set(final_filtered_df['DCSPH'].astype(str))
                                
                                if any(code in existing_codes for code in new_codes):
                                    st.warning("Sommige resultaten zijn al opgeslagen. Alleen nieuwe resultaten worden toegevoegd.")
                                    
                                    # Filter out already saved rows
                                    new_rows = final_filtered_df[~final_filtered_df['DCSPH'].astype(str).isin(existing_codes)]
                                    
                                    if not new_rows.empty:
                                        # Append only new rows
                                        st.session_state.saved_rows = pd.concat([st.session_state.saved_rows, new_rows], ignore_index=True)
                                        st.success(f"{len(new_rows)} nieuwe resultaten opgeslagen.")
                                    else:
                                        st.info("Alle resultaten zijn al opgeslagen.")
                                else:
                                    # No duplicates, append all rows
                                    st.session_state.saved_rows = pd.concat([st.session_state.saved_rows, final_filtered_df], ignore_index=True)
                                    st.success(f"{len(final_filtered_df)} resultaten opgeslagen.")
                            else:
                                # If DCSPH column doesn't exist, just append (might cause duplicates)
                                st.session_state.saved_rows = pd.concat([st.session_state.saved_rows, final_filtered_df], ignore_index=True)
                                st.success(f"{len(final_filtered_df)} resultaten opgeslagen.")
                    
                else:
                    st.warning("Geen overeenkomende records gevonden met de geselecteerde filters.")
            else:
                st.info("Selecteer een waarde voor Omschrijving Pathologieën in het filtermenu aan de linkerkant om resultaten te zien.")
            
        # TAB 2: Saved Results
        with tab2:
            st.title("Opgeslagen Resultaten")
            
            if st.session_state.saved_rows.empty:
                st.info("Nog geen resultaten opgeslagen. Gebruik de 'Zoeken' tab om resultaten te vinden en op te slaan.")
            else:
                # Display count of saved records
                st.markdown(f"**Aantal opgeslagen records:** {len(st.session_state.saved_rows)}")
                
                # Get relevant information columns (same as in tab 1)
                relevant_cols = ["DCSPH", df.columns[1], df.columns[2], df.columns[3], df.columns[4], 
                                df.columns[5], df.columns[6], df.columns[7], 
                                df.columns[8], df.columns[9]]
                
                # Only include columns that actually exist
                available_cols = [col for col in relevant_cols if col in st.session_state.saved_rows.columns]
                
                # Format column names for display
                formatted_saved_df = st.session_state.saved_rows[available_cols].copy()
                
                # Ensure DCSPH column is displayed as integer without any formatting
                if 'DCSPH' in formatted_saved_df.columns:
                    formatted_saved_df['DCSPH'] = formatted_saved_df['DCSPH'].astype(str).str.replace('.', '').str.replace(',', '')
                    formatted_saved_df['DCSPH'] = pd.to_numeric(formatted_saved_df['DCSPH'], errors='coerce').fillna(0).astype(int)
                
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
                formatted_saved_df = formatted_saved_df.rename(columns={col: column_mapping.get(col, col) for col in available_cols})
                
                # Display the saved data
                if 'DCSPH Code' in formatted_saved_df.columns:
                    formatted_saved_df['DCSPH Code'] = formatted_saved_df['DCSPH Code'].apply(lambda x: f"{int(x)}" if pd.notnull(x) else "")
                
                st.dataframe(
                    formatted_saved_df,
                    use_container_width=True,
                    hide_index=True,
                    height=500
                )
                
                # Add clear button to remove all saved results
                if st.button("Wis Alle Opgeslagen Resultaten", type="secondary"):
                    st.session_state.saved_rows = pd.DataFrame()
                    st.success("Alle opgeslagen resultaten zijn gewist.")
                    st.rerun()
                
                # Add download button for saved results
                csv = st.session_state.saved_rows[available_cols].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Opgeslagen Resultaten als CSV",
                    data=csv,
                    file_name=f"dcsph_opgeslagen_resultaten_{date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    else:
        st.error("Kon de gegevens niet laden. Controleer het Excel-bestand.")
        
else:
    st.error(f"Bestand '{file_path}' niet gevonden. Zorg ervoor dat het Excel-bestand de naam 'lijst.xlsx' heeft en zich in dezelfde map bevindt als deze applicatie.")