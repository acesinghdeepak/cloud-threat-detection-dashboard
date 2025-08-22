import time
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Threat Detection Dashboard", page_icon="🛡️", layout="wide")
st.title("🛡️ Real-Time Threat Detection Dashboard")
st.caption("Shows anomalies detected from streaming logs (Isolation Forest)")

data_dir = Path("data")
anomalies_csv = data_dir / "anomalies.csv"
logs_jsonl = data_dir / "logs.jsonl"

refresh_sec = st.sidebar.slider("Auto-refresh (seconds)", 2, 30, 5)
st.sidebar.write("Make sure the **generator** and **stream processor** are running.")

placeholder = st.empty()

def load_anomalies():
    if anomalies_csv.exists() and anomalies_csv.stat().st_size > 0:
        try:
            df = pd.read_csv(anomalies_csv)
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def load_recent_logs(n=2000):
    if logs_jsonl.exists():
        # read tail of file (best-effort)
        try:
            with open(logs_jsonl, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                # read last ~200KB
                offset = max(0, size - 200_000)
                f.seek(offset)
                tail = f.read().decode(errors="ignore").splitlines()[-n:]
            rows = []
            for ln in tail:
                try:
                    rows.append(pd.read_json(ln, typ="series"))
                except Exception:
                    pass
            return pd.DataFrame(rows)
        except Exception:
            pass
    return pd.DataFrame()

while True:
    dfA = load_anomalies()
    with placeholder.container():
        c1, c2, c3 = st.columns(3)
        total_anom = len(dfA)
        last_10m = 0
        if total_anom:
            # crude recent count by timestamp string grouping
            last_10m = total_anom  # simplified for starter
        c1.metric("Total Anomalies", total_anom)
        c2.metric("Anomalies (approx.) last 10m", last_10m)
        c3.metric("Distinct Source IPs (anomalies)", dfA["src_ip"].nunique() if total_anom else 0)

        if total_anom:
            st.subheader("Recent Anomalies")
            st.dataframe(dfA.tail(200), use_container_width=True, height=300)
            st.subheader("Anomalies by Destination Port")
            port_counts = dfA["dest_port"].value_counts().reset_index()
            port_counts.columns = ["dest_port","count"]
            st.bar_chart(port_counts.set_index("dest_port"))
        else:
            st.info("No anomalies yet. Keep the generator and stream processor running...")

    time.sleep(refresh_sec)