import pandas as pd
from config.paths import DATA_DIR

df = pd.read_csv(DATA_DIR / 'topic_info.csv')
with open(DATA_DIR / 'topics_summary.txt', 'w', encoding='utf-8') as f:
    f.write(df[['Topic', 'Count', 'Name', 'Representation']].head(15).to_string())
print("Saved summary.")
