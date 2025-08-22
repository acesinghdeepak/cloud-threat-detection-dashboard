import argparse, json, os
from generate_logs import generate_log

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=5000)
    ap.add_argument("--out", default="data/logs.jsonl")
    args = ap.parse_args()

    os.makedirs("data", exist_ok=True)
    with open(args.out, "w") as f:
        for _ in range(args.rows):
            f.write(json.dumps(generate_log()) + "\n")
    print(f"[bootstrap] wrote {args.rows} rows to {args.out}")

if __name__ == "__main__":
    main()