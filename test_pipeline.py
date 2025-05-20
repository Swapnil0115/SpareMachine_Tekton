import pandas as pd

df = pd.read_csv("data/sample.csv")
assert not df.empty, "Dataset is empty!"
print("Test passed.")
