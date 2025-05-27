import pandas as pd

df = pd.read_csv("sample_data.csv")
assert not df.empty, "Dataset is empty!"
print("Test passed.")
