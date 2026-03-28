import streamlit as st
import pandas as pd
import numpy as np

# 1. SAYFA AYARLARI VE TASARIM
st.set_page_config(page_title="Line Analiz v2.3", layout="wide", page_icon="📊")

# Modern UI için Custom CSS
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 900; color: #1E293B; }
    .stButton>button { border-radius: 15px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
    .cover-card {
        padding: 20px;
        border-radius: 25px;
        background-color: white;
        border: 1px solid #E2E8F0;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. LIFESTYLE HAFIZASI (Session State)
# Uygulama yenilense bile bu veriler oturum boyunca korunur
if 'lifestyles' not in st.session_state:
    st.session_state['lifestyles'] = {
        "WOMAN": [],
        "MAN": [],
        "GIRL": [],
        "BOY": []
    }

# 3. YARDIMCI FONKSİYONLAR
def get_column(df, patterns):
    """Excel kolonlarını esnek bir şekilde eşleştirir."""
    for pattern in patterns:
        for col in df.columns:
            if pattern.lower() in str(col).lower():
                return col
    return None

# 4. SIDEBAR - DOSYA YÜKLEME VE FİLTRELER
st.sidebar.header("📁 Veri Kaynağı")
uploaded_file = st.sidebar.file_uploader("Excel dosyasını buraya bırakın", type=['xlsx'])

if uploaded_file:
    # Veriyi oku
    df_raw = pd.read_excel(uploaded_file)
    
    # Kolon eşleştirme operasyonu
    col_line = get_column(df_raw, ["Line", "Urun Grubu", "Koleksiyon"])
    col_amount = get_column(df_raw, ["Net Amount", "Ciro", "Tutar", "Amount"])
    col_qty = get_column(df_raw, ["Net Quantity", "Adet", "Satis"])
    col_stock = get_column(df_raw, ["Stock", "Mevcut Stok", "Stok"])
    col_div = get_column(df_raw, ["Division", "Merch Group", "Bolum"])

    if not all([col_line, col_amount, col_qty, col_stock, col_div]):
        st.error("⚠️ Excel kolonları otomatik eşleşemedi. Lütfen kolon isimlerini kontrol edin.")
        st.stop()

    # Kategori Filtresi
    st.sidebar.divider()
    all_categories = df_raw[col_div].unique().tolist()
    selected_cat = st.sidebar.selectbox("Merch Group Seçin", all_categories)
    
    # Seçili kategori verisi
    cat_df = df_raw[df_raw[col_div] == selected_cat].copy()
    
    # LIFESTYLE YÖNETİMİ (Sidebar Altı)
    st.sidebar.divider()
    with st.sidebar.expander("✨ Lifestyle Yönetimi", expanded=False):
        new_ls_name = st.text_input("Yeni Lifestyle Adı")
        ls_lines = st.multiselect("Paketleri Seç", cat_df[col_line].unique())
        if st.button("Sisteme Kaydet"):
            if new_ls_name and ls_lines:
                st.session_state['lifestyles'][selected_cat].append({
                    "name": new_ls_name,
                    "lines": ls_lines
                })
                st.success(f"{new_ls_name} kaydedildi!")
    
    # 5. ANA EKRAN - LIFESTYLE BUTONLARI
    st.subheader(f"🏷️ {selected_cat} - Lifestyle Hızlı Seçim")
    
    active_ls_lines = []
    ls_options = st.session_state['lifestyles'].get(selected_cat, [])
    
    cols = st.columns(len(ls_options) + 1)
    with cols[0]:
        if st.button("TÜMÜ", use_container_width=True):
            active_ls_lines = []
            
    for i, ls in enumerate(ls_options):
        with cols[i+1]:
            if st.button(ls['name'], use_container_width=True):
                active_ls_lines = ls['lines']
                st.toast(f"{ls['name']} aktif edildi!")

    # Filtreleme Uygula
    if active_ls_lines:
        display_df = cat_df[cat_df[col_line].isin(active_ls_lines)]
    else:
        display_df = cat_df

    # 6. METRİKLER VE TOP 5
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    total_sales = display_df[col_amount].sum()
    total_qty = display_df[col_qty].sum()
    total_stock = display_df[col_stock].sum()
    
    m1.metric("KATEGORİ CİRO", f"{total_sales:,.0f} TL")
    m2.metric("SATILAN ADET", f"{total_qty:,.0f}")
    m3.metric("TOPLAM STOK", f"{total_stock:,.0f}")
    m4.metric("AKTİF PAKET", len(display_df[col_line].unique()))

    # Line Bazlı Özet Tablo Hesaplama
    line_summary = display_df.groupby(col_line).agg({
        col_amount: 'sum',
        col_qty: 'sum',
        col_stock: 'sum'
    }).reset_index()

    line_summary['Pay %'] = (line_summary[col_amount] / total_sales * 100).round(1)
    # Cover Hesabı (Stok / Satış)
    line_summary['Cover'] = (line_summary[col_stock] / line_summary[col_qty]).replace([np.inf, -np.inf], 99).round(1)
    line_summary = line_summary.sort_values(col_amount, ascending=False)

    # TOP 5 GÖRSEL KARTLAR
    st.write("### 🏆 Top 5 Performans")
    top_5 = line_summary.head(5)
    t_cols = st.columns(5)
    
    for idx, (i, row) in enumerate(top_5.iterrows()):
        with t_cols[idx]:
            cover_val = row['Cover']
            # v2.2 Renk Skalası: <6 Kırmızı, 6-8 Mavi, >8 Turuncu
            color = "#EF4444" if cover_val < 6 else "#2563EB" if cover_val <= 8 else "#F59E0B"
            
            st.markdown(f"""
                <div class="cover-card">
                    <p style='font-size:10px; font-weight:900; color:#64748B;'>#{idx+1} {row[col_line][:15]}</p>
                    <p style='font-size:18px; font-weight:900; margin:5px 0;'>{row[col_amount]:,.0f} TL</p>
                    <div style='background-color:{color}15; color:{color}; padding:5px; border-radius:10px; font-size:12px; font-weight:bold;'>
                        COVER: {cover_val}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # 7. DETAYLI VERİ TABLOSU
    st.divider()
    st.write("### 📊 Tüm Paket Detayları")
    
    # Stilize tablo için dataframe hazırlığı
    styled_df = line_summary.copy()
    styled_df.columns = ["Paket Adı", "Ciro (TL)", "Satış Adet", "Stok", "Ciro Payı %", "Cover"]
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ciro (TL)": st.column_config.NumberColumn(format="%d TL"),
            "Cover": st.column_config.ProgressColumn(min_value=0, max_value=15, format="%.1f")
        }
    )

    # Alt Kırılım (Drill-down)
    st.sidebar.divider()
    selected_line_detail = st.sidebar.selectbox("Paket Detayı İncele", line_summary[col_line].unique())
    if selected_line_detail:
        st.write(f"#### 🔍 {selected_line_detail} - Model Kırılımı")
        detail_data = display_df[display_df[col_line] == selected_line_detail]
        st.table(detail_data.head(10))

else:
    # Boş Ekran Görünümü
    st.info("👋 Hoş Geldiniz! Analize başlamak için sol taraftan Excel dosyanızı yükleyin.")
    st.markdown("""
        **Nasıl Kullanılır?**
        1. Excel dosyasını yükleyin.
        2. Merch grubunuzu seçin.
        3. Lifestyle tanımlamak için paketleri seçip 'Kaydet'e basın.
        4. Artık o lifestyle butonuyla saniyeler içinde analiz yapabilirsiniz.
    """)