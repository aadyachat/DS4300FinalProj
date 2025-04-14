import pandas as pd
import os

def preprocess_bloodwork_data(file_path):
    """
    Simple preprocessing of bloodwork data to standardize test names and units.
    Saves processed data to a CSV file in the 'preprocessed_data' folder.
    """
    df = pd.read_csv(file_path)
    # Standardized test names mapping
    test_name_mapping = {
        'WHITE BLOOD CELL COUNT': 'WBC',
        'WHITE BLOOD CELL COUNT (WBC)': 'WBC',
        'WBC COUNT': 'WBC',
        'RED BLOOD CELL COUNT': 'RBC',
        'RED BLOOD CELL COUNT (RBC)': 'RBC', 
        'RBC COUNT': 'RBC',
        'HEMOGLOBIN': 'Hemoglobin',
        'HEMOGLOBIN (HGB)': 'Hemoglobin',
        'HGB': 'Hemoglobin',
        'GLUCOSE': 'Glucose',
        'CALCIUM': 'Calcium',
        'SODIUM': 'Sodium',
        'POTASSIUM': 'Potassium',
        'TOTAL CHOLESTEROL': 'Total Cholesterol',
        'CHOLESTEROL': 'Total Cholesterol',
        'LDL CHOLESTEROL': 'LDL Cholesterol',
        'LDL-C': 'LDL Cholesterol',
        'LDL': 'LDL Cholesterol',
        'HDL CHOLESTEROL': 'HDL Cholesterol',
        'HDL-C': 'HDL Cholesterol',
        'HDL': 'HDL Cholesterol',
        'TSH (THYROID STIMULATING HORMONE)': 'TSH',
        'THYROID STIMULATING HORMONE': 'TSH',
        'TSH': 'TSH',
        'FREE T4': 'Free T4',
        'T4, FREE': 'Free T4',
        'FT4': 'Free T4'
    }
    
    # Target units for each test
    target_units = {
        'WBC': '10^3/uL',
        'RBC': '10^6/uL',
        'Hemoglobin': 'g/dL',
        'Glucose': 'mg/dL',
        'Calcium': 'mg/dL',
        'Sodium': 'mmol/L',
        'Total Cholesterol': 'mg/dL',
        'LDL Cholesterol': 'mg/dL',
        'HDL Cholesterol': 'mg/dL',
        'TSH': 'mIU/L',
        'Free T4': 'ng/dL'
    }
    
    # Unit conversion functions
    def convert_value(value, from_unit, to_unit, test):
        value = float(value)
        
        # Convert WBC count
        if test == 'WBC':
            if 'x10^9/L' in from_unit or '10^9/L' in from_unit:
                return value  # Equivalent to 10^3/uL
        
        # Convert RBC count
        if test == 'RBC':
            if 'x10^12/L' in from_unit or '10^12/L' in from_unit:
                return value  # Equivalent to 10^6/uL
        
        # Convert Glucose
        if test == 'Glucose' and 'mmol/L' in from_unit and 'mg/dL' in to_unit:
            return value * 18.0
        
        # Convert Free T4
        if test == 'Free T4' and 'pmol/L' in from_unit and 'ng/dL' in to_unit:
            return value / 12.87
        
        # If no specific conversion needed, return original
        return value
    
    # Standardize test names (case insensitive)
    for i, row in df.iterrows():
        test = row['test_name'].strip().upper()
        if test in test_name_mapping:
            df.at[i, 'test_name'] = test_name_mapping[test]
    
    # Standardize units and convert values if needed
    for i, row in df.iterrows():
        test = row['test_name']
        if test in target_units:
            current_unit = row['unit'].strip()
            target_unit = target_units[test]
            
            # Only convert if units are different
            if current_unit != target_unit:
                df.at[i, 'value'] = convert_value(row['value'], current_unit, target_unit, test)
                df.at[i, 'unit'] = target_unit
    
    # Ensure values are numeric and properly rounded
    df['value'] = pd.to_numeric(df['value'], errors='coerce').round(2)
    
    # Create the preprocessed_data directory if it doesn't exist
    if not os.path.exists('preprocessed_data'):
        os.makedirs('preprocessed_data')
    
    # Extract the filename from the path and create the output path
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_path = f"preprocessed_data/{base_filename}_cleaned.csv"
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Preprocessed data saved to {output_path}")
    
    return df

folder_path = "bloodtest_data/"
for file in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file)
    preprocess_bloodwork_data(file_path)
