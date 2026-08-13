import pandas as pd

def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    if "ID" in df.columns:
        df = df.drop(columns=["ID"])
    df["Data"] = pd.to_datetime(df["Data"])
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)
    df["Data"] = df["Data"].dt.date
    return df

def filter_transactions(df: pd.DataFrame, month: str, categories: list) -> pd.DataFrame:
    filtered = df[df["Mês"] == month]
    if categories:
        filtered = filtered[filtered["Categorias"].isin(categories)]
    return filtered
