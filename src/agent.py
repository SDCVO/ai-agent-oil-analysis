import requests
import json
import pandas as pd

from typing import Any, Hashable


def format_prompt(sample_data: dict[Hashable, Any]) -> str:
    return f"""
You are a smart data cleaning assistant. Your job is to identy and patterns in labels of equipments used in mining operations, including their model names.

Given the following sample data:
{json.dumps(sample_data, indent=2)}

Return ONLY A JSON object with a cleaning plan like, but not limeted to the following format. You should also detect another patterns for normalization
You are familiar with offers from vendors like: Caterpillar, Komatsu, Epiroc and others. Identify as much entries as possible.
{{
    "columns": {{
        "equipment_type": {{
        "normalize_labels": {{
            "CAT777G": "777G",
            "Caterpillar 777G": "777G",
            "777": "777G",
            "77": "777G",
            "77G": "777G",
            "Komatsu - PC2000": "PC2000",
            "Kom - 2000": "PC2000",
            "2000": "PC2000",
            "L135": "L1350",
            "Let-L1350": "L1350",
            "CAT 785": "785C",
            "CATERPILLAR 785": "785C",
            "785": "785C"
        }},
        "type": "category"
        }}
        "component": {{
        "normalize_labels": {{
            "Eng": "Engine",
            "Motor": "Engine",
            "MOTOR": "Engine",
            "Motor Diese": "Engine",
            "Mot. Diesel": "Engine",
            "Transmissão": "Transmission",
            "Transmissão de Tração": "Transmission",
            "Transmição": "Transmission",
            "Sis. Hid": "Hydraulic System",
            "Sistema Hidráulico": "Hydraulic System"
        }},
        "type": "category"
        }}
    }},
    "actions": [
        "remove_duplicates",
        "fill_missing_with: Unknown"
    ]
}}
"""


def query_ollama(prompt: str, model: str | None ="llama3", base_url: str="http://localhost:11434"): 
    url: str = f"{base_url}/api/chat"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "options": {
            # "temperature": 0,
        },
        "stream": False
    }
    response: requests.Response = requests.post(url=url, json=payload)
    response.raise_for_status()
    return response.json()["message"]["content"]


def get_cleaning_plan(sample_data: dict[Hashable, Any], backend: str="ollama", model: str | None = None) -> str:
    prompt = format_prompt(sample_data.to_dict(orient="records"))
    if backend == "ollama":
        return query_ollama(prompt=prompt, model=model or "llama3")
    else:
        raise ValueError(f"Unknown backend '{backend}'")
    



def apply_cleaning_plan(df: pd.DataFrame, plan: dict[str, Any]) -> pd.DataFrame:
    for col, ops in plan.get("columns", {}).items(): 
        if "normalize_labels" in ops:
            mapping = ops["normalize_labels"]
            print(mapping)
            df[col] = df[col].replace(mapping)

        if ops.get("type") == "category":
            df[col] = df[col].astype("category")

    for action in plan.get("actions", []):
        if action == "remove_duplicates":
            df = df.drop_duplicates()
    return df

def get_llm_suggestions(
    values: list[str],
    column_name: str,
    model: str = "llama3",
    base_url: str = "http://localhost:11434"
    ) -> dict[str, str]:
    """
    Use an LLM HTTP API (like Ollama) to group and normalize label variants for a column.

    Args:
        values (list[str]): Unique values from the column to normalize.
        column_name (str): Name of the column.
        model (str): Model name to use with the LLM provider.
        base_url (str): Base URL for the LLM HTTP API.

    Returns:
        dict[str, str]: Mapping from original values to canonical labels.
    """

    
    prompt = (
        f"""
You are a data cleaning assistant. Your task is to normalize categorical values for machine learning.

Given the following unique values from the column '{column_name}':

{values}

Group values that refer to the same real-world entity, even if they are written differently (e.g., typos, abbreviations, synonyms, different languages, or formatting).

For each group, choose the most standard, short, and human-readable label as the canonical label.

Return ONLY a valid JSON object mapping each original value to its canonical label. Do not include any explanation, markdown, or extra text.
All keys and values should be strings and in English.

Example output:
{{
    "Cat777G": "777G",
    "Caterpillar 777": "777G",
    "C-777G": "777G",
    "77G": "777G",
    "2000": "PC2000",
    "785": "785C",
}}

Another Example:
{{
    "Motor": "Engine",
    "Motor Diesel": "Engine",
    "Mot. Diesel": "Engine",
    "Transmissão": "Transmission",
    "Sistema Hidráulico": "Hydraulic System"
    "PTO": "PTO"
}}

"""
    )
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(f"{base_url}/api/generate", json=payload)
    response.raise_for_status()
    output = response.json().get("response", "")
    
    # Try to extract the dictionary from the output
    try:
        mapping = json.loads(output)
    except Exception:
        import re
        match = re.search(r'\{[\s\S]*\}', output)
        if match:
            mapping_str = match.group(0)
            mapping = eval(mapping_str)
        else:
            raise ValueError("No mapping found in LLM output.")
    return mapping

def normalize_columns_with_llm(
    df: pd.DataFrame,
    columns: list[str],
    model: str = "llama3",
    base_url: str = "http://localhost:11434") -> tuple[pd.DataFrame, dict[str, dict[str, str]]]:
    """
    Normalize multiple categorical columns in a DataFrame using LLM label suggestions via HTTP API.

    Args:
        df (pd.DataFrame): The DataFrame to normalize.
        columns (list[str]): List of column names to normalize.
        model (str): Model name to use with the LLM provider.
        base_url (str): Base URL for the LLM HTTP API.

    Returns:
        tuple[pd.DataFrame, dict[str, dict[str, str]]]: The normalized DataFrame and a mapping for each column.
    """
    mappings: dict[str, dict[str, str]] = {}
    for col in columns:
        unique_vals = df[col].unique().tolist()
        mapping: dict[str, str] = get_llm_suggestions(values=unique_vals, column_name=col, model=model, base_url=base_url)
        print(f'Generated suggestions with LLM for column "{col}": {mapping}')
        mappings[col] = mapping
        
        # Normalize the DataFrame using the mapping
        df[col] = df[col].replace(mapping)
    return df, mappings


def generate_cleaning_plan(df: pd.DataFrame, columns: list[str], model: str = "llama3", base_url: str = "http://localhost:11434") -> dict[str, dict[str, str]]:
    mappings: dict[str, dict[str, str]] = {}
    for col in columns:
        unique_vals: list[str] = df[col].unique().tolist()
        mapping: dict[str, str] = get_llm_suggestions(values=unique_vals, column_name=col, model=model, base_url=base_url)
        print(f'Generated suggestions with LLM for column "{col}": {mapping}')
        mappings[col] = mapping
    return mappings

def generate_df_from_cleaning_plan(cleaning_plan: dict[str, dict[str, str]]) -> pd.DataFrame:
    rows = []
    for label, mapping in cleaning_plan.items():
        for k, v in mapping.items():
            rows.append({'label': label, 'original': k, 'renamed': v})
    return pd.DataFrame(data=rows)


def apply_cleaning_plan(df_source: pd.DataFrame, df_mapping: pd.DataFrame) -> pd.DataFrame:
    for label in df_mapping['label'].unique():
        mapping_dict = df_mapping.set_index('original')['renamed'].to_dict()

        df_source[label] = df_source[label].map(mapping_dict).fillna(df_source[label])

    return df_source