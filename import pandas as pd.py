import pandas as pd

D1_PATH = "/Users/noah/Desktop/starting5_v9/app/static/json/cbb25.csv"
df_d1 = pd.read_csv(D1_PATH)

# Inspect columns to find correct names
print(df_d1.columns)