# Python Test File 3: Data Processing
# Expected: Extract imports and main logic

import pandas as pd
import numpy as np
from datetime import datetime

data = {
    'Name': ['Anna', 'Ben', 'Clara'],
    'Alter': [25, 30, 28],
    'Gehalt': [50000, 65000, 55000]
}

df = pd.DataFrame(data)
average_salary = df['Gehalt'].mean()
print(f"Durchschnittsgehalt: {average_salary}")
