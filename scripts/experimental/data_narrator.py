"""
Feature: Data Narrator (Table to Text)
Status: EXPERIMENTAL
Converts CSV/Excel tables into Markdown narratives for LLM context.
ADR: ADR-021-data-narrator.md
A/B-Test: ABT-N02
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

def narrate_table(
    df: pd.DataFrame,
    file_path: str,
    max_preview_rows: int = 20
) -> str:
    """
    Generates a natural language description (narrative) of a dataframe.
    Designed to give LLMs semantic understanding of tabular data.
    """
    narrative = []
    filename = Path(file_path).name

    # 1. Overview
    narrative.append(f"# Tabelle: {filename}")
    narrative.append(f"")
    narrative.append(f"## Übersicht")
    narrative.append(f"- **Zeilen:** {len(df)}")
    narrative.append(f"- **Spalten:** {', '.join(df.columns)}")
    
    # 2. Column Analysis
    narrative.append(f"")
    narrative.append(f"## Spalten-Analyse")

    for col in df.columns:
        try:
            col_type = df[col].dtype
            
            # Numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                stats = df[col].describe()
                narrative.append(
                    f"- **{col}** (Numerisch): "
                    f"Min={stats['min']:.2f}, Max={stats['max']:.2f}, "
                    f"Durchschnitt={stats['mean']:.2f}, Summe={df[col].sum():.2f}"
                )
            
            # Date
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                narrative.append(
                    f"- **{col}** (Datum): "
                    f"Von {df[col].min()} bis {df[col].max()}"
                )
                
            # Text / Categorical
            else:
                unique_count = df[col].nunique()
                # Get top 5 most frequent values
                top_values = df[col].value_counts().head(5).to_dict()
                # Format dictionary as string for markdown
                top_str = str(top_values).replace("{", "").replace("}", "")
                
                narrative.append(
                    f"- **{col}** (Text): {unique_count} eindeutige Werte. "
                    f"Häufigste: {top_str}"
                )
        except Exception as e:
            narrative.append(f"- **{col}**: Analyse fehlgeschlagen ({str(e)})")

    # 3. Preview
    narrative.append(f"")
    narrative.append(f"## Vorschau (erste {min(max_preview_rows, len(df))} Zeilen)")
    try:
        # Convert to markdown table, fill NaNs with empty string
        table_md = df.head(max_preview_rows).fillna("").to_markdown(index=False)
        narrative.append(table_md)
    except ImportError:
        # Fallback if tabulate not installed (should not happen in standard pandas envs)
        narrative.append(str(df.head(max_preview_rows)))

    # 4. Outliers / Highlights (Max/Min)
    narrative.append(f"")
    narrative.append(f"## Auffälligkeiten")
    
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                # Find row with Max value
                max_idx = df[col].idxmax()
                max_row = df.loc[max_idx]
                
                # Format row as dict string, truncating if too long
                row_dict = max_row.to_dict()
                row_str = str(row_dict)
                if len(row_str) > 200:
                    row_str = row_str[:200] + "..."
                    
                narrative.append(f"- Höchster Wert in **{col}**: {row_str}")
    except Exception:
        pass # Skip highlights if errors occur

    return "\n".join(narrative)
