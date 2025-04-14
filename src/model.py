
columns = ['al', 'cr', 'cu', 'fe', 'ni', 'pb', 'si', 'sn', 'viscosity_at_100c']
def classify_anomaly(row):
    anomalies = []
    for col in columns:
        if row[col] >= 50: 
            anomalies.append(col)
    
    if anomalies:
        return anomalies
    else:
        return None

def highlight_anomaly(val):
    if val >= 100:
        return 'background-color: rgb(99, 8, 8)'
    elif val >= 50:
        return 'background-color: rgb(99, 63, 8)'

def calculate_difference(df, column = columns):
    df = df.sort_values(by=['sample_date'], ascending=True)
    for col in columns:
        shifted_col = df[col].shift(1)

        diff_col_name = f"{col}_diff"
        df[diff_col_name] = df[col] - shifted_col
    
    return df