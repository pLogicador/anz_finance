import os
import glob
import pandas as pd
import ofxparse
from io import BytesIO


def _extract_transactions(ofx) -> list[dict]:
    """Flatten every account/transaction in a parsed OFX object into row dicts."""
    rows = []
    for account in ofx.accounts:
        for transaction in account.statement.transactions:
            rows.append({
                "Data": transaction.date,
                "Valor": float(transaction.amount),
                "Descrição": transaction.memo,
                "ID": transaction.id,
            })
    return rows


def _finalize(df_temp: pd.DataFrame) -> pd.DataFrame:
    df_temp["Data"] = df_temp["Data"].apply(lambda x: x.date())
    return df_temp


def parse_ofx_files(folder: str) -> pd.DataFrame:
    """Parse every .ofx file inside `folder` into a single transactions DataFrame."""
    df = pd.DataFrame()
    for path in sorted(glob.glob(os.path.join(folder, "*.ofx"))):
        try:
            with open(path, "rb") as fh:
                ofx = ofxparse.OfxParser.parse(fh)
            df_temp = pd.DataFrame(_extract_transactions(ofx))
            if not df_temp.empty:
                df = pd.concat([df, _finalize(df_temp)], ignore_index=True)
        except Exception as e:
            print(f"[ERROR] Failed to process {path}: {e}")
    return df


def parse_ofx_files_from_upload(files) -> pd.DataFrame:
    df = pd.DataFrame()
    for uploaded_file in files:
        try:
            ofx = ofxparse.OfxParser.parse(BytesIO(uploaded_file.getvalue()))
            df_temp = pd.DataFrame(_extract_transactions(ofx))
            if not df_temp.empty:
                df = pd.concat([df, _finalize(df_temp)], ignore_index=True)
        except Exception as e:
            print(f"[ERROR] Failed to process {uploaded_file.name}: {e}")
    return df
