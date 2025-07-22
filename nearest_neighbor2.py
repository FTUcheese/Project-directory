import pandas as pd

# Read the Dataframe (ckd.csv) and show the columns for debugging
df = pd.read_csv('ckd.csv')
print('DEBUG: Columns are:', list(df.columns))
df.columns = [col.strip().lower() for col in df.columns]
print('DEBUG: Cleaned columns are:', list(df.columns))

# Print first few rows as well
print(df.head())
