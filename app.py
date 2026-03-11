# app.py — Dashboard Plan Kangkung PRO (Versi Rapi & Simple)
import streamlit as st
import pandas as pd
import requests
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# ==================== CONFIG ====================
st.set_page_config(page_title="Plan Kangkung PRO", page_icon="Leaf", layout="wide")

# CSS custom untuk tabel rapi + teks kecil
st.markdown("""
<style>
    .small-table th {
        font-size: 0.9rem !important;
        background-color: #263238 !important;
        color: #00e676 !important;
        text-align: center !important;
        padding: 8px !important;
    }
    .small-table td {
        font-size: 0.85rem !important;
        padding: 6px 8px !important;
        text-align: center !important;
    }
    .highlight-23-25 {background-color: #e8f5e9 !important; color: #2e7d32 !important; font-weight: bold;}
    .highlight-26plus {background-color: #ffebee !important; color: #c62828 !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# === SET WAKTU JAKARTA ===
jakarta_tz = ZoneInfo("Asia/Jakarta")
today = datetime.now(jakarta_tz).date()           # hanya tanggal
now_jakarta = datetime.now(jakarta_tz)            # tanggal + jam (kalau butuh)

st.write(f"Tanggal hari ini (WIB): **{today.strftime('%d-%m-%Y')}**")

# ==================== BACA DATA ====================
file = Path("Plan_Kangkung_Daily.xlsx")
if not file.exists():
    st.error("File Plan_Kangkung_Daily.xlsx tidak ditemukan!")
    st.stop()

df = pd.read_excel(file, sheet_name="dash")

# Konversi semua kolom tanggal
date_cols = ["tanggal", "panen_plan", "p1", "p2", "p3", "c1", "c2", "panen_aktual"]
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

#WIB
df_today = df[df["tanggal"].dt.date == today]

# ==================== FUNGSI KEBUN ====================
def get_kebun(bedeng):
    if pd.isna(bedeng): return "Tidak Diketahui"
    kode = str(bedeng).strip().upper()[:2]
    mapping = {"SB": "Sawangan Bawah", "SA": "Sawangan Atas", "BS": "Bojongsari",
               "TA": "Tuloh Atas", "TB": "Tuloh Bawah"}
    return mapping.get(kode, "Lainnya")

df["kebun"] = df["bedeng"].apply(get_kebun)

# Umur hari
df["umur_hari"] = (pd.to_datetime(today) - df["tanggal"]).dt.days
df["umur_hari"] = df["umur_hari"].astype("Int64")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("Filter Tanggal update")
    daily_date = st.date_input("Tanggal Perawatan", today)
    tanam_date = st.date_input("Tanggal Tanam", today)
    
    st.markdown("---")
    st.subheader("Historis")
    col1, col2 = st.columns(2)
    with col1:
        start_tanam = st.date_input("Dari", today, key="s1")
    with col2:
        end_tanam = st.date_input("Sampai", today, key="s2")

# ==================== HEADER ====================
st.markdown(f"""
<h3 style='text-align:center; color:#2e8b57;'>PLAN KANGKUNG DAILY</h1>
<p style='text-align:center; color:#888;'>Update: {today.strftime('%d %B %Y')}</p>
""", unsafe_allow_html=True)

# ==================== PERAWATAN & TANAM ====================
c1, c2 = st.columns([2, 1])

with c1:
    with st.expander(f"Perawatan Hari Ini — {daily_date.strftime('%d/%m/%Y')}", expanded=True):
        def beds(col): 
            return df[df[col].dt.date == daily_date]["bedeng"].dropna().tolist() if col in df.columns else []
        
        treatments = {
            "P1": (beds("p1"), "#d32f2f"),
            "P2": (beds("p2"), "#00bfa5"),
            "P3": (beds("p3"), "#1976d2"),
            "C1": (beds("c1"), "#388e3c"),
            "C2": (beds("c2"), "#f57c00"),
        }
        
        cols = st.columns(5)
        for i, (label, (lst, color)) in enumerate(treatments.items()):
            with cols[i]:
                st.markdown(f"<div style='background:{color};color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;'>{label}</div>", unsafe_allow_html=True)
                if lst:
                    st.code("\n".join(lst), language=None)
                else:
                    st.caption("—")

with c2:
    with st.expander(f"Penanaman Hari Ini — {tanam_date.strftime('%d/%m/%Y')}", expanded=True):

        tanam_hari_ini = df[df["tanggal"].dt.date == tanam_date]

        if not tanam_hari_ini.empty:
            for _, r in tanam_hari_ini.iterrows():
                st.markdown(
                    f"<div style='padding:6px 4px;font-size:15px;'>"
                    f"<b>{r['bedeng']}</b> — {get_kebun(r['bedeng'])}"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Tidak ada penanaman.")


# ==================== KALENDER PERAWATAN ====================

# with st.expander("📅 Kalender Jadwal Perawatan Mingguan / Bulan (Pupuk Daun & Pupuk Cor)", expanded=False):

#     col_filter, col_view = st.columns([1, 2])

#     with col_filter:
#         filter_option = st.selectbox(
#             "Filter Jenis Perawatan",
#             options=["Semua", "Pupuk Daun (P)", "Pupuk Cor (C)"],
#             index=0,
#             key="filter_kalender_perawatan"
#         )

#     # Mapping warna sesuai dengan yang sudah ada
#     color_map = {
#         "P1": "#d32f2f",
#         "P2": "#00bfa5",
#         "P3": "#1976d2",
#         "C1": "#388e3c",
#         "C2": "#f57c00",
#     }

#     # Kumpulkan semua events dari kolom p1,p2,p3,c1,c2
#     events = []

#     for col in ["p1", "p2", "p3", "c1", "c2"]:
#         if col not in df.columns:
#             continue

#         treated = df[df[col].notna()][["bedeng", col]].copy()
#         treated["date_str"] = treated[col].dt.strftime("%Y-%m-%d")

#         for _, row in treated.iterrows():
#             label = col.upper()  # P1, C2, dll
#             bedeng_list = row["bedeng"]

#             if isinstance(bedeng_list, str):
#                 bedeng_list = [bedeng_list]
#             elif pd.isna(bedeng_list):
#                 continue

#             title = f"{label}: {', '.join(bedeng_list)}"

#             events.append({
#                 "title": title,
#                 "start": row["date_str"],
#                 "backgroundColor": color_map.get(label, "#999999"),
#                 "borderColor": color_map.get(label, "#999999"),
#                 "textColor": "white",
#                 "extendedProps": {
#                     "type": "P" if col.startswith("p") else "C",
#                     "kode": label
#                 }
#             })

#     # Filter event sesuai pilihan user
#     if filter_option == "Pupuk Daun (P)":
#         events = [e for e in events if e["extendedProps"]["type"] == "P"]
#     elif filter_option == "Pupuk Cor (C)":
#         events = [e for e in events if e["extendedProps"]["type"] == "C"]

#     # Import calendar component
#     from streamlit_calendar import calendar

#     calendar_options = {
#         "initialView": "dayGridMonth",
#         "headerToolbar": {
#             "left": "prev,next today",
#             "center": "title",
#             "right": "dayGridMonth,dayGridWeek",
#         },
#         "selectable": True,
#         "editable": False,
#         "height": "700px",
#         "locale": "id",
#     }

#     cal_data = calendar(
#         events=events,
#         options=calendar_options,
#         key="perawatan_calendar"
#     )

#     # Info klik event
#     if cal_data and "eventClick" in cal_data:
#         event_info = cal_data["eventClick"]["event"]
#         st.info(
#             f"Detail: {event_info['title']} "
#             f"pada {event_info['start']}"
#         )


# ==================== BEDENG HARUS PANEN (TABEL RAPI) ====================
with st.expander("Bedeng Harus Panen per Kebun (Umur > 22 hari)", expanded=True):

    # 1️⃣ Ambil hanya tanam yang BELUM panen
    df_active = df[
        df["panen_aktual"].isna() &
        df["tanggal"].notna()
    ].copy()

    # 2️⃣ Urutkan per bedeng dari tanam TERBARU
    df_active = df_active.sort_values(
        ["bedeng", "tanggal"],
        ascending=[True, False]
    )

    # 3️⃣ Ambil 1 baris TERBARU per bedeng
    df_active = df_active.drop_duplicates(
        subset="bedeng",
        keep="first"
    )

    # 4️⃣ Filter umur panen
    df_hp = df_active[df_active["umur_hari"] > 22].copy()

    # ================= TAMPILAN =================
    df_hp["prefix"] = df_hp["bedeng"].str[:2].str.upper()
    kebun_order = ["TA", "TB", "SA", "SB", "BS"]

    kebun_data = {}
    for kode in kebun_order:
        sub = df_hp[df_hp["prefix"] == kode][
            ["bedeng", "umur_hari"]
        ].sort_values("umur_hari", ascending=False)

        kebun_data[kode] = [
            f"{r.bedeng} – {int(r.umur_hari)}"
            for r in sub.itertuples()
        ]

    # Padding kolom
    max_rows = max((len(v) for v in kebun_data.values()), default=0)
    for k in kebun_data:
        kebun_data[k] += [""] * (max_rows - len(kebun_data[k]))

    table_df = pd.DataFrame(kebun_data)

    def highlight_hp(val):
        if not val:
            return ""
        umur = int(val.split("–")[-1])
        if umur > 25:
            return "background-color:#ff5252;color:white;font-weight:bold"
        if 21 <= umur <= 25:
            return "background-color:#c8e6c9;color:#1b5e20;font-weight:bold"
        return ""

    st.dataframe(
        table_df.style.applymap(highlight_hp),
        use_container_width=True,
        hide_index=True
    )


# ==================== BEDENG AKTIF ====================
with st.expander("Bedeng Aktif Saat Ini", expanded=False):
    df_aktif = df[df["panen_aktual"].isna() & df["tanggal"].notna()].copy()
    df_aktif = df_aktif[["bedeng", "kebun", "tanggal", "umur_hari"]].sort_values("umur_hari", ascending=False)

    kebun_opt = ["Semua"] + sorted(df_aktif["kebun"].unique())
    pilih = st.selectbox("Filter Kebun", kebun_opt, key="aktif")
    if pilih != "Semua":
        df_aktif = df_aktif[df_aktif["kebun"] == pilih]

    view = df_aktif.copy()
    view["Tanggal Tanam"] = view["tanggal"].dt.strftime("%d/%m/%Y")
    view = view[["bedeng", "kebun", "Tanggal Tanam", "umur_hari"]].rename(columns={"umur_hari": "Umur (hari)"})

    def color_aktif(val):
        if pd.isna(val): return ""
        val = int(val)
        if 23 <= val <= 25: return "background-color: #e8f5e9; color: #2e7d32; font-weight:bold"
        if val >= 26: return "background-color: #ffebee; color: #c62828; font-weight:bold"
        return ""

    styled = view.style.applymap(color_aktif, subset=["Umur (hari)"])
    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.caption(f"Total bedeng aktif: **{len(df_aktif)}**")

from datetime import datetime, timedelta

# ==================== HASIL PANEN (SECTION BARU) ===============

with st.expander("Hasil Panen", expanded=False):

    # --- Default tanggal: kemarin ---
    default_tgl = (datetime.now() - timedelta(days=1)).date()

    colA, colB = st.columns([2, 10])

    with colA:
        tgl_filter = st.date_input(
            "Tanggal Panen",
            value=default_tgl
        )

    # ==================== PREPARE DATA ====================

    df_hasil = df.copy()

    df_hasil["panen_aktual"] = pd.to_datetime(df_hasil["panen_aktual"], errors="coerce")
    df_hasil["tanggal"] = pd.to_datetime(df_hasil["tanggal"], errors="coerce")

    df_hasil = df_hasil[df_hasil["panen_aktual"].notna()].copy()

    df_hasil = df_hasil[df_hasil["panen_aktual"].dt.date == tgl_filter]

    df_hasil = df_hasil.sort_values("panen_aktual").head(18)

    df_hasil["umur_panen"] = (df_hasil["panen_aktual"] - df_hasil["tanggal"]).dt.days

    # ==================== STANDARD & VARIANCE ====================

    STANDARD_BEDENG = 14.55

    df_hasil["standard"] = STANDARD_BEDENG
    df_hasil["variance_kg"] = df_hasil["net"] - df_hasil["standard"]
    df_hasil["variance_pct"] = (df_hasil["variance_kg"] / df_hasil["standard"]) * 100

    if df_hasil.empty:
        st.info("Tidak ada data panen untuk tanggal tersebut.")

    else:

        # ==================== DATA VIEW ====================

        df_view = df_hasil[[
            "panen_aktual", "kebun", "bedeng", "umur_panen",
            "gross", "net", "waste",
            "standard", "variance_kg", "variance_pct"
        ]].copy()

        df_view["panen_aktual"] = df_view["panen_aktual"].dt.strftime("%d/%m/%Y")

        # ==================== FORMAT ANGKA ====================

        num_cols = ["gross", "net", "waste", "standard", "variance_kg"]

        for col in num_cols:
            df_view[col] = df_view[col].map(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        df_view["variance_pct"] = df_view["variance_pct"].map(
            lambda x: f"{x:.1f}%".replace(".", ",")
        )

        # ==================== STYLE ====================

        def highlight_variance(val):
            try:
                val = float(str(val).replace(",", "."))
                if val < 0:
                    return "color: red"
            except:
                pass
            return ""

        styled_df = (
            df_view.style
            .map(highlight_variance, subset=["variance_kg", "variance_pct"])
            .set_properties(subset=num_cols + ["variance_pct"], **{"text-align": "right"})
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

        # ==================== TOTAL ====================

        st.markdown("### Total & Average")

        total_gross = df_hasil["gross"].sum()
        total_net = df_hasil["net"].sum()
        total_waste = df_hasil["waste"].sum()

        avg_gross = df_hasil["gross"].mean()
        avg_net = df_hasil["net"].mean()
        avg_var_kg = df_hasil["variance_kg"].mean()
        avg_var_pct = df_hasil["variance_pct"].mean()

        def fmt(x):
            return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def fmt_pct(x):
            return f"{x:.1f}%".replace(".", ",")

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Gross", fmt(total_gross))
        col2.metric("Total Net", fmt(total_net))
        col3.metric("Total Waste", fmt(total_waste))

        st.markdown("### Average per Bedeng")

        col4, col5, col6, col7 = st.columns(4)

        col4.metric("Avg Gross", fmt(avg_gross))
        col5.metric("Avg Net", fmt(avg_net))
        col6.metric("Avg Variance (kg)", fmt(avg_var_kg))
        col7.metric("Avg Variance (%)", fmt_pct(avg_var_pct))

# ==================== TABEL LENGKAP ====================
with st.expander("Tabel Lengkap Semua Data (Riwayat)", expanded=False):
    # Ambil semua data dulu (default)
    df_full = df.copy()

    # Cek apakah user sudah mengubah filter tanggal di sidebar
    # Jika "Dari" atau "Sampai" masih default (hari ini), anggap belum difilter → tampilkan semua
    if start_tanam != today or end_tanam != today:
        # User sudah mengubah salah satu filter → terapkan rentang
        df_full = df_full[
            (df_full["tanggal"].dt.date >= start_tanam) &
            (df_full["tanggal"].dt.date <= end_tanam)
        ]
    # Jika keduanya masih today → otomatis tampilkan SEMUA data (tidak difilter)

    # Format tanggal untuk tampilan
    df_disp = df_full.copy()
    for c in date_cols:
        if c in df_disp.columns:
            df_disp[c] = df_disp[c].dt.strftime("%d/%m/%Y").replace("<NA>", "-")

    # Urutkan dari yang terbaru
    df_disp = df_disp.sort_values("tanggal", ascending=False).reset_index(drop=True)

    # Tampilkan dengan rapi
    st.dataframe(
        df_disp,
        use_container_width=True,
        hide_index=True,
        column_config={col: st.column_config.TextColumn(col) for col in df_disp.columns}
    )

    # Info jumlah baris
    st.caption(f"Menampilkan **{len(df_disp)}** baris data"
               + (f" (difilter: {start_tanam.strftime('%d/%m/%Y')} – {end_tanam.strftime('%d/%m/%Y')})" 
                  if (start_tanam != today or end_tanam != today) else ""))

# ==================== AI DATA ANALYST ====================

with st.expander("AI Data Analyst (Tanya Data)", expanded=False):

    import requests

    st.caption("Tanyakan apa saja tentang data dashboard")

    # Chat history
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    # tampilkan chat sebelumnya
    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # input pertanyaan
    question = st.chat_input("Contoh: berapa total panen kemarin?")

    if question:

        # tampilkan pertanyaan user
        st.session_state.ai_messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        # ====================
        # RINGKASAN DATA UNTUK AI
        # ====================

        try:

            data_info = f"""
Total baris data: {len(df)}

Kolom tersedia:
{", ".join(df.columns)}

Contoh data:
{df.head(10).to_string(index=False)}
"""

        except Exception as e:
            data_info = f"Error membaca dataframe: {e}"

        # ====================
        # PROMPT UNTUK AI
        # ====================

        prompt = f"""
Anda adalah AI Data Analyst untuk dashboard pertanian LuckyFarm.

Gunakan hanya data berikut untuk menjawab pertanyaan.

{data_info}

Instruksi:
- Jawab dengan singkat
- Jika data tidak tersedia, katakan "Data tidak tersedia"

Pertanyaan user:
{question}
"""

        # ====================
        # REQUEST KE OLLAMA
        # ====================

        try:

            with st.spinner("AI sedang menganalisis data..."):

                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "phi3",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 200,
                            "temperature": 0.2
                        }
                    },
                    timeout=300
                )

                result = response.json()

                answer = result.get("response", "AI tidak memberikan jawaban.")

        except Exception as e:
            answer = f"AI error: {e}"

        # tampilkan jawaban AI
        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.ai_messages.append(
            {"role": "assistant", "content": answer}
        )
# ==================== FOOTER ====================
st.markdown("<br><hr><p style='text-align:center;color:#888;font-size:0.9em;'>"
            "Dashboard Plan Kangkung PRO • PPIC-Eddy</p>", unsafe_allow_html=True)
