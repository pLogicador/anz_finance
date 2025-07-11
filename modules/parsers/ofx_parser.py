import os
import pandas as pd
import ofxparse

def parse_ofx_files(folder_path: str) -> pd.DataFrame:
    df = pd.DataFrame()
    for extrato in os.listdir(folder_path):
        try:
            with open(os.path.join(folder_path, extrato), "rb") as ofx_file:
                ofx = ofxparse.OfxParser.parse(ofx_file)

            transactions_data = []
            for account in ofx.accounts:
                for transaction in account.statement.transactions:
                    transactions_data.append({
                        "Data": transaction.date,
                        "Valor": float(transaction.amount),
                        "Descrição": transaction.memo,
                        "ID": transaction.id,
                    })

            df_temp = pd.DataFrame(transactions_data)
            if not df_temp.empty:
                df_temp["Data"] = df_temp["Data"].apply(lambda x: x.date())
                df = pd.concat([df, df_temp], ignore_index=True)
            else:
                print(f"[DEBUG] No transactions in: {extrato}")
        except Exception as e:
            print(f"[ERROR] Failed to process {extrato}: {e}")
    return df
