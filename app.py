import streamlit as st
import pandas as pd
import numpy as np

# 1. SAYFA AYARLARI VE MODERN TEMA
st.set_page_config(page_title="Line Analiz v2.3", layout="wide", page_icon="📊")

# React Versiyonuna Yakın Görsel Tasarım (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    
    .main-card {
        background: white;
        padding: 24px;
        border-radius: 32px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    
    .stButton>button {
        border-radius: 16px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 11px;
        padding: 12px 24px;
        transition: all 0.3s;
    }

    /* Cover Renk Skalası Kartları */
    .metric-box {
        text-align: center;
        padding: 15px;
        border-radius: 20px;
        border: 1px solid #EDF2F7;
        background: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. LIFESTYLE HAFIZASI
if 'lifestyles' not in st.session_state:
    st.session_state['lifestyles'] = {"WOMAN": [], "MAN": [], "GIRL": [], "BOY": []}

# 3. HATA ÖNLEYİCİ VERİ İŞLEME FONKSİYONU
def process_data(file):
    try:
        # Excel'i oku (Header otomatik bulma denemesi)
        df = pd.read_excel(file)
        
        # Kolon Eşleştirme Sözlüğü (Senin Excel'indeki olası isimler)
        mapping = {
            'Line': ['Product Line', 'Line', 'Urun Grubu', 'Koleksiyon', 'LINE'],
            'Amount': ['Net Amount', 'Ciro', 'Tutar', 'Amount', 'CIRO'],
            'Qty': ['Net Quantity', 'Sales Qty', 'Adet', 'Satis', 'ADET'],
            'Stock': ['Stock', 'Mevcut Stok', 'Quantity', 'Stok', 'STOK'],
            'Div': ['Sub Division', 'Merch Group', 'Alt Bolum', 'Division', 'BOLUM'],
            'Style': ['Style', 'Model', 'Short Code', 'Code', 'STIL'],
            'Color': ['Color', 'Renk', 'RENK']
        }

        final_cols = {}
        for key, patterns in mapping.items():
            for col in df.columns:
                if any(p.lower() in str(col).lower().strip() for p in patterns):
                    final_cols[key] = col
                    break
        
        # Eksik kolon kontrolü
        required = ['Line', 'Amount', 'Qty', 'Stock', 'Div']
        missing = [r for r in required if r not in final_cols]
        if missing:
            st.error(f"Excel'de şu kolonlar bulunamadı: {missing}. Lütfen başlıkları kontrol edin.")
            return None, None

        # Veri Temizleme (Sayısal değerleri zorla)
        df[final_cols['Amount']] = pd.to_numeric(df[final_cols['Amount']], errors='coerce').fillna(0)
        df[final_cols['Qty']] = pd.to_numeric(df[final_cols['Qty']], errors='coerce').fillna(0)
        df[final_cols['Stock']] = pd.to_numeric(df[final_cols['Stock']], errors='coerce').fillna(0)

        # Kategori Normalleştirme
        def normalize_div(val):
            val = str(val).upper()
            if 'WOMAN' in val or 'KADIN' in val: return 'WOMAN'
            if 'MAN' in val or 'ERKEK' in val: return 'MAN'
            if 'GIRL' in val or 'KIZ' in val: return 'GIRL'
            if 'BOY' in val or 'ERKEK ÇOCUK' in val: return 'BOY'
            return 'OTHER'
        
        df['Normalized_Div'] = df[final_cols['Div']].apply(normalize_div)
        return df, final_cols
    except Exception as e:
        st.error(f"Dosya okunurken hata oluştu: {e}")
        return None, None

# 4. SIDEBAR - YÜKLEME VE YÖNETİM
st.sidebar.markdown("### 📥 Veri Girişi")
uploaded_file = st.sidebar.file_uploader("Excel Dosyası", type=['xlsx'])

if uploaded_file:
    df, cols = process_data(uploaded_file)
    
    if df is not None:
        # Merch Grup Seçimi
        categories = ["WOMAN", "MAN", "GIRL", "BOY"]
        selected_cat = st.sidebar.selectbox("Merch Group", categories)
        
        cat_df = df[df['Normalized_Div'] == selected_cat].copy()
        
        # Lifestyle Yönetimi
        st.sidebar.divider()
        with st.sidebar.expander("🆕 Yeni Lifestyle Tanımla"):
            ls_name = st.text_input("Lifestyle Adı")
            ls_lines = st.multiselect("Paketleri Seç", sorted(cat_df[cols['Line']].unique()))
            if st.button("KAYDET"):
                if ls_name and ls_lines:
                    st.session_state['lifestyles'][selected_cat].append({"name": ls_name, "lines": ls_lines})
                    st.success("Kaydedildi!")
                    st.rerun()

        # 5. ANA PANEL - LIFESTYLE BUTONLARI
        st.markdown(f"### 🏷️ {selected_cat} Lifestyle Seçimi")
        ls_options = st.session_state['lifestyles'].get(selected_cat, [])
        
        btn_cols = st.columns(len(ls_options) + 1)
        active_lines = []
        
        with btn_cols[0]:
            if st.button("TÜMÜ", use_container_width=True): active_lines = []
        
        for i, ls in enumerate(ls_options):
            with btn_cols[i+1]:
                if st.button(ls['name'], use_container_width=True):
                    active_lines = ls['lines']

        # Filtreleme
        display_df = cat_df[cat_df[cols['Line']].isin(active_lines)] if active_lines else cat_df

        # 6. ÜST METRİKLER (React Dashboard Tarzı)
        total_s = display_df[cols['Amount']].sum()
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='main-card'><p style='font-size:10px; font-weight:900; color:#94A3B8;'>CIRO</p><h2>{total_s:,.0f} TL</h2></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='main-card'><p style='font-size:10px; font-weight:900; color:#94A3B8;'>ADET</p><h2>{display_df[cols['Qty']].sum():,.0f}</h2></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='main-card'><p style='font-size:10px; font-weight:900; color:#94A3B8;'>PAKET</p><h2>{len(display_df[cols['Line']].unique())}</h2></div>", unsafe_allow_html=True)

        # 7. TOP 5 SIRALAMA (Renkli Coverlar)
        line_sum = display_df.groupby(cols['Line']).agg({cols['Amount']: 'sum', cols['Qty']: 'sum', cols['Stock']: 'sum'}).reset_index()
        line_sum['Cover'] = (line_sum[cols['Stock']] / line_sum[cols['Qty']]).replace([np.inf, -np.inf], 99).round(1)
        line_sum = line_sum.sort_values(cols['Amount'], ascending=False)

        st.markdown("### 🏆 Top 5 Performans")
        t_cols = st.columns(5)
        for idx, (i, row) in enumerate(line_sum.head(5).iterrows()):
            cv = row['Cover']
            # v2.2 Skalası
            color = "#EF4444" if cv < 6 else "#2563EB" if cv <= 8 else "#F59E0B"
            with t_cols[idx]:
                st.markdown(f"""
                <div style='background:white; padding:20px; border-radius:24px; border-bottom:4px solid {color}; box-shadow:0 4px 6px rgba(0,0,0,0.02);'>
                    <p style='font-size:10px; font-weight:900; color:#64748B; margin-bottom:5px;'>#{idx+1} {row[cols['Line']][:12]}</p>
                    <h4 style='margin:0;'>{row[cols['Amount']]:,.0f} TL</h4>
                    <p style='font-size:12px; font-weight:900; color:{color}; margin-top:10px;'>COVER: {cv}</p>
                </div>
                """, unsafe_allow_html=True)

        # 8. ANA TABLO
        st.markdown("### 📊 Detaylı Analiz")
        st.dataframe(
            line_sum.rename(columns={cols['Line']: 'Paket', cols['Amount']: 'Ciro', cols['Qty']: 'Satış', cols['Stock']: 'Stok'}),
            use_container_width=True,
            hide_index=True,
            column_config={"Ciro": st.column_config.NumberColumn(format="%d TL"), "Cover": st.column_config.NumberColumn(format="%.1f 📉")}
        )

else:
    st.markdown("""
        <div style='text-align:center; padding:100px;'>
            <h1 style='color:#E2E8F0; font-size:64px;'>📊</h1>
            <h2 style='color:#64748B;'>Analiz İçin Excel Yükleyin</h2>
            <p style='color:#94A3B8;'>Sol menüden dosyanızı seçerek başlayabilirsiniz.</p>
        </div>
    """, unsafe_allow_html=True)
