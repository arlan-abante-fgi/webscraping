import pandas as pd

file_path = 'Traffic Report Campaign Performance 2024-10-27 (1).xlsx'

df = pd.read_excel(file_path)

df.head(5)