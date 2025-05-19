import pandas as pd

df = pd.read_csvs("data/sample.csv")
assert not df.empty, "Dataset is empty!"
print("Test passed.")
