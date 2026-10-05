import streamlit as st
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
import streamlit.components.v1 as components

st.set_page_config(page_title="Raw Materials Store - PMB", layout="wide")
st.title("📦 Raw Materials Store - Complete System")

PRODUCT_STAGES = {
    "Cornflakes": ["Good Product", "For Cooking", "For Sorting", "For Sieving", "For Porridge"],
    "Branflakes": ["Good Product", "Sorting", "Sieving", "For Cooking", "For Kibbling"],
    "High Protein Bran": ["Good Product", "For Cooking", "Sorting", "Kibbling"],
    "Multigrain Bran": ["Good Product", "For Cooking", "Sorting", "Kibbling"],
    "Wheat Flakes": ["Good Product", "Sorting", "Kibbling"],
    "Toasted Barley": ["Good Product", "For Cooking", "Sorting", "Kibbling"],
    "Rolled Barley": ["Good Product", "For Cooking", "Sorting", "Kibbling"],
    "Toasted Wheat": ["Good Product", "For Cooking", "Sorting", "Kibbling"],
    "Granola Original": ["Good Product", "Sorting"],
    "Spar Granola Triple Chocolate": ["Good Product", "Sorting"],
    "Chocolate Corn": ["Good Product", "Sorting"],
}
EXTERNAL_MATERIALS = ["Corn Grits", "Barley", "Wheat", "Sugar", "Digestive Bran"]

if 'receipts' not in st.session_state:
    st.session_state.receipts = pd.DataFrame(columns=["Date","Source","Material","Stage","Qty_kg","From","Batch_No","Barcode_ID"])
if 'issues' not in st.session_state:
    st.session_state.issues = pd.DataFrame(columns=["Date","Material","Stage","Qty_kg","Issued_To","Barcode_ID"])

def make_qr(data_str):
    qr = qrcode.make(data_str)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def get_balance():
    if st.session_state.receipts.empty:
        return pd.DataFrame()
    rec = st.session_state.receipts.groupby(["Material","Stage","Barcode_ID"])["Qty_kg"].sum().reset_index().rename(columns={"Qty_kg":"IN"})
    if st.session_state.issues.empty:
        rec["Balance"] = rec["IN"]
        return rec
    iss = st.session_state.issues.groupby(["Material","Stage","Barcode_ID"])["Qty_kg"].sum().reset_index().rename(columns={"Qty_kg":"OUT"})
    bal = pd.merge(rec, iss, on=["Material","Stage","Barcode_ID"], how="left").fillna(0)
    bal["Balance"] = bal["IN"] - bal["OUT"]
    return bal

scanner_html = """
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<div style="width:100%; max-width:400px; margin:auto;">
  <div id="reader" style="width:100%"></div>
  <div id="result" style="margin-top:15px; padding:10px; background:#e8f5e9; border-radius:8px; font-weight:bold; font-size:16px; text-align:center;">Waiting for scan...</div>
  <button onclick="copyResult()" style="margin-top:10px; padding:8px 15px; background:green; color:white; border:none; border-radius:5px; width:100%;">COPY CODE</button>
</div>
<script>
  let lastResult = "";
  function onScanSuccess(decodedText, decodedResult) {
    if (decodedText!== lastResult) {
      lastResult = decodedText;
      document.getElementById('result').innerHTML = "✅ SCANNED: " + decodedText;
    }
  }
  function copyResult(){
    navigator.clipboard.writeText(lastResult);
    alert("Copied: " + lastResult + "\\nPaste it in the box below!");
  }
  let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: {width: 250, height: 250} }, false);
  html5QrcodeScanner.render(onScanSuccess);
</script>
"""

tab1, tab2, tab3, tab4 = st.tabs(["➕ RECEIVE + QR", "📷 AUTO SCAN", "➖ ISSUE TO BAGGING", "📊 STOCK BALANCE"])

with tab1:
    source = st.radio("Source", ["EXTERNAL - Supplier", "INTERNAL - Production"], horizontal=True)
    c1,c2,c3,c4 = st.columns(4)
    if "EXTERNAL" in source:
        with c1: mat = st.selectbox("External Material", EXTERNAL_MATERIALS)
        with c2: qty = st.number_input("Qty kg", 1, value=1000, key="rq1")
        with c3: supplier = st.text_input("Supplier Name")
        with c4:
            batch = st.text_input("GRN No", value=f"EXT-{datetime.now().strftime('%Y%m%d%H%M')}")
            if st.button("RECEIVE + GENERATE QR", type="primary"):
                barcode_id = f"{mat}|Raw|{batch}|{qty}kg"
                new = {"Date":datetime.now().strftime("%Y-%m-%d %H:%M"),"Source":"External","Material":mat,"Stage":"Raw","Qty_kg":qty,"From":supplier,"Batch_No":batch,"Barcode_ID":barcode_id}
                st.session_state.receipts = pd.concat([st.session_state.receipts, pd.DataFrame([new])], ignore_index=True)
                st.success(f"Received {qty}kg {mat}")
                st.image(make_qr(barcode_id), caption=barcode_id, width=220)
    else:
        with c1: prod = st.selectbox("Product", list(PRODUCT_STAGES.keys()))
        with c2: stage = st.selectbox("Stage", PRODUCT_STAGES[prod])
        with c3: qty = st.number_input("Qty kg", 1, value=100, key="rq2")
        with c4:
            dept = st.text_input("From Dept", placeholder="Cooking Dept")
            batch = st.text_input("Batch No", value=f"INT-{datetime.now().strftime('%Y%m%d%H%M')}", key="b2")
            if st.button("RECEIVE + GENERATE QR", key="btn2", type="primary"):
                barcode_id = f"{prod}|{stage}|{batch}|{qty}kg"
                new = {"Date":datetime.now().strftime("%Y-%m-%d %H:%M"),"Source":"Internal","Material":prod,"Stage":stage,"Qty_kg":qty,"From":dept,"Batch_No":batch,"Barcode_ID":barcode_id}
                st.session_state.receipts = pd.concat([st.session_state.receipts, pd.DataFrame([new])], ignore_index=True)
                st.success(f"Received {qty}kg {prod} - {stage}")
                st.image(make_qr(barcode_id), caption=barcode_id, width=220)

with tab2:
    st.subheader("📱 Scan with Phone")
    components.html(scanner_html, height=600)
    scanned_input = st.text_input("📋 Paste Scanned Code Here", placeholder="After scan, click COPY CODE then paste here")
    if st.button("🔍 SEARCH & ISSUE"):
        found = st.session_state.receipts[st.session_state.receipts["Barcode_ID"]==scanned_input]
        if not found.empty:
            st.success(f"FOUND: {found.iloc[0]['Material']} - {found.iloc[0]['Stage']}")
            bal = get_balance()
            b = bal[bal["Barcode_ID"]==scanned_input]
            if not b.empty:
                st.metric("Balance", f"{b.iloc[0]['Balance']} kg")
        else:
            st.error("Not found - receive first")

with tab3:
    bal = get_balance()
    if bal.empty:
        st.warning("No stock yet")
    else:
        avail = bal[bal["Balance"]>0]
        issue_mat = st.selectbox("Material", sorted(avail["Material"].unique()))
        stages = avail[avail["Material"]==issue_mat]
        issue_stage = st.selectbox("Stage", stages["Stage"].unique(), key="stg")
        batch_sel = st.selectbox("Batch Barcode", stages[stages["Stage"]==issue_stage]["Barcode_ID"].tolist())
        current = stages[stages["Barcode_ID"]==batch_sel]["Balance"].values[0]
        st.metric("Available", f"{current} kg")
        qty = st.number_input("Qty to Issue", 1, max_value=int(current), value=10)
        to = st.selectbox("Issued To", ["Bagging Dept", "Cooking Dept", "Sorting Dept", "Kibbling Dept", "Production"])
        if st.button("🔴 ISSUE STOCK", type="primary"):
            new_issue = {"Date":datetime.now().strftime("%Y-%m-%d %H:%M"),"Material":issue_mat,"Stage":issue_stage,"Qty_kg":qty,"Issued_To":to,"Barcode_ID":batch_sel}
            st.session_state.issues = pd.concat([st.session_state.issues, pd.DataFrame([new_issue])], ignore_index=True)
            st.success(f"Issued {qty}kg to {to}")
            st.balloons()

with tab4:
    bal = get_balance()
    if not bal.empty:
        st.write("**Ready for Bagging (Good Product Only)**")
        good = bal[(bal["Stage"]=="Good Product") & (bal["Balance"]>0)]
        st.dataframe(good, use_container_width=True)
        st.divider()
        st.write("**All Stock Balance**")
        st.dataframe(bal[bal["Balance"]>0].sort_values(["Material","Stage"]), use_container_width=True)
        st.divider()
        for idx, row in bal[bal["Balance"]>0].iterrows():
            with st.expander(f"{row['Material']} - {row['Stage']} - {row['Balance']}kg"):
                st.image(make_qr(row['Barcode_ID']), width=150)
                st.code(row['Barcode_ID'])
        st.download_button("Download Balance CSV", bal.to_csv(index=False).encode('utf-8'), "stock_balance.csv")
    else:
        st.info("No stock yet - receive first")
