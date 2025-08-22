import argparse, json, time, os, io
import pandas as pd
import numpy as np
from joblib import load
from datetime import datetime

def ipv4_to_int(ip):
    try:
        parts = [int(x) for x in ip.split(".")]
        return (parts[0]<<24) + (parts[1]<<16) + (parts[2]<<8) + parts[3]
    except:
        return 0

def featurize_row(d):
    # compute numeric features consistent with training
    try:
        hour = int(datetime.strptime(d["timestamp"], "%Y-%m-%d %H:%M:%S").hour)
    except Exception:
        hour = 0
    protocol_num = 1 if d.get("protocol") == "UDP" else 0
    action_num = 1 if d.get("action") == "ALLOW" else 0
    src_ip_int = ipv4_to_int(d.get("src_ip","0.0.0.0"))
    dest_ip_int = ipv4_to_int(d.get("dest_ip","0.0.0.0"))
    vec = [
        float(d.get("src_port",0)),
        float(d.get("dest_port",0)),
        float(d.get("bytes_transferred",0)),
        float(hour),
        float(protocol_num),
        float(action_num),
        float(src_ip_int),
        float(dest_ip_int),
    ]
    return np.array(vec, dtype=float)

def tail_f(path):
    with open(path, "r") as f:
        # seek to end
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue
            yield line

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log_file", required=True)
    ap.add_argument("--model_path", required=True)
    ap.add_argument("--out", default="data/anomalies.jsonl")
    ap.add_argument("--csv", default="data/anomalies.csv")
    ap.add_argument("--score_threshold", type=float, default=0.0, help="IsolationForest: -1=anomaly, 1=normal. We still keep raw score.")
    args = ap.parse_args()

    bundle = load(args.model_path)
    scaler = bundle["scaler"]
    model = bundle["model"]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    print(f"[stream] watching {args.log_file}; writing anomalies to {args.out} and {args.csv}")

    # Prepare CSV header if not exists
    if not os.path.exists(args.csv):
        with open(args.csv, "w") as cf:
            cf.write("timestamp,src_ip,dest_ip,src_port,dest_port,protocol,action,bytes_transferred,score,pred\n")

    for line in tail_f(args.log_file):
        try:
            d = json.loads(line)
        except Exception:
            continue
        x = featurize_row(d).reshape(1, -1)
        xs = scaler.transform(x)
        # predict: -1 anomaly, 1 normal
        pred = int(model.predict(xs)[0])
        score = float(model.score_samples(xs)[0])  # lower = more anomalous

        # keep only anomalies (pred == -1)
        if pred == -1:
            with open(args.out, "a") as f:
                f.write(json.dumps({**d, "score": score, "pred": int(pred)}) + "\n")
            with open(args.csv, "a") as cf:
                cf.write(f'{d["timestamp"]},{d["src_ip"]},{d["dest_ip"]},{d["src_port"]},{d["dest_port"]},{d["protocol"]},{d["action"]},{d["bytes_transferred"]},{score},{pred}\n')

if __name__ == "__main__":
    main()