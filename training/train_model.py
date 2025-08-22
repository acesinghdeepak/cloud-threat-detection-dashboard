import argparse, json, os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from joblib import dump

def ipv4_to_int(ip):
    try:
        parts = [int(x) for x in ip.split(".")]
        return (parts[0]<<24) + (parts[1]<<16) + (parts[2]<<8) + parts[3]
    except:
        return 0

def load_jsonl(path, limit=None):
    rows = []
    with open(path, "r") as f:
        for i, line in enumerate(f):
            try:
                rows.append(json.loads(line))
            except:
                continue
            if limit and i+1 >= limit:
                break
    return pd.DataFrame(rows)

def featurize(df: pd.DataFrame):
    df = df.copy()
    # parse timestamp to hour
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
    # categorical to numeric
    df["protocol_num"] = (df["protocol"] == "UDP").astype(int)
    df["action_num"] = (df["action"] == "ALLOW").astype(int)
    # ip -> integer
    df["src_ip_int"] = df["src_ip"].apply(ipv4_to_int)
    df["dest_ip_int"] = df["dest_ip"].apply(ipv4_to_int)
    # keep numeric subset
    feat = df[[
        "src_port","dest_port","bytes_transferred",
        "hour","protocol_num","action_num","src_ip_int","dest_ip_int"
    ]].astype(float).fillna(0.0)
    return feat

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to logs.jsonl")
    ap.add_argument("--model_path", default="models/isolation_forest.pkl")
    ap.add_argument("--contamination", type=float, default=0.02, help="Expected anomaly proportion")
    args = ap.parse_args()

    df = load_jsonl(args.input)
    if df.empty:
        raise SystemExit("No data found. Run bootstrap or generator first.")

    X = featurize(df)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    model = IsolationForest(n_estimators=200, contamination=args.contamination, random_state=42)
    model.fit(Xs)

    # Save a dict with both scaler and model
    os.makedirs(os.path.dirname(args.model_path), exist_ok=True)
    dump({"scaler": scaler, "model": model}, args.model_path)
    print(f"[train] saved model to {args.model_path} (n={len(X)})")

if __name__ == "__main__":
    main()