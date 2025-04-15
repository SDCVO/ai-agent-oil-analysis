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