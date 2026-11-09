
import pandas as pd

df = pd.read_csv("data/raw/psf_analysis.csv")

print("\nLAST 10 PLANES:")
print(df.tail(10).to_string(index=False))

print("\nHIGHEST PEAK:")
print(df.loc[df["peak_intensity"].idxmax()].to_string())

print("\nLOWEST PEAK:")
print(df.loc[df["peak_intensity"].idxmin()].to_string())
