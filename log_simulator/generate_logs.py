import argparse
import json
import random
import time
from datetime import datetime, timedelta

PROTOCOLS = ["TCP", "UDP"]
COMMON_PORTS = [22, 53, 80, 123, 443, 3306, 8080, 5432, 6379]
ACTIONS = ["ALLOW", "DENY"]

PRIVATE_NETS = [
    ("10.0.0.0", "10.255.255.255"),
    ("172.16.0.0", "172.31.255.255"),
    ("192.168.0.0", "192.168.255.255"),
]

def ip_to_int(ip):
    parts = [int(x) for x in ip.split(".")]
    return (parts[0]<<24) + (parts[1]<<16) + (parts[2]<<8) + parts[3]

def int_to_ip(n):
    return ".".join(str((n >> (8*i)) & 0xFF) for i in [3,2,1,0])

def random_ip(private=False):
    if private and random.random() < 0.8:
        # pick a private subnet 80% of the time for source IPs
        start, end = random.choice(PRIVATE_NETS)
        s, e = ip_to_int(start), ip_to_int(end)
        return int_to_ip(random.randint(s, e))
    else:
        return ".".join(str(random.randint(1, 254)) for _ in range(4))

def generate_log():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    src_ip = random_ip(private=True)
    dest_ip = random_ip(private=False)
    src_port = random.randint(1024, 65535)
    dest_port = random.choices(COMMON_PORTS + [random.randint(1024,65535)], weights=[10,7,12,5,12,5,6,4,3,2])[0]
    protocol = random.choice(PROTOCOLS)
    action = random.choices(ACTIONS, weights=[0.85, 0.15])[0]  # ALLOW more common
    bytes_transferred = max(40, int(abs(random.gauss(1500, 800))))

    # occasional "spiky" traffic to simulate anomalies
    if random.random() < 0.01:
        bytes_transferred *= random.randint(10, 50)
        action = "ALLOW"
    # occasional suspicious denied SSH
    if random.random() < 0.015:
        dest_port = 22
        action = "DENY"

    return {
        "timestamp": now,
        "src_ip": src_ip,
        "dest_ip": dest_ip,
        "src_port": src_port,
        "dest_port": dest_port,
        "protocol": protocol,
        "action": action,
        "bytes_transferred": bytes_transferred
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to-file", default="data/logs.jsonl", help="Output JSONL file path")
    ap.add_argument("--rate", type=float, default=2.0, help="logs per second (approx)")
    args = ap.parse_args()

    interval = 1.0 / max(0.1, args.rate)
    print(f"[generator] writing logs to {args.to_file} at ~{args.rate} logs/sec ... (Ctrl+C to stop)")
    with open(args.to_file, "a", buffering=1) as f:
        try:
            while True:
                log = generate_log()
                f.write(json.dumps(log) + "\n")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[generator] stopped.")

if __name__ == "__main__":
    main()