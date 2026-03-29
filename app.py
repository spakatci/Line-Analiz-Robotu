import streamlit as st
import pandas as pd
import numpy as np
import re

# 1. SAYFA AYARLARI VE MODERN TEMA
st.set_page_config(page_title="Line Analiz v2.5", layout="wide", page_icon="📊")

# Modern UI Tasarımı (CSS)
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
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 12px;
        padding: 10px 20px;
        transition: all 0.3s;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 900;
        color: #1E293B;
    }
    
    .metric-label {
        font-size: 11px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. LIFESTYLE HAFIZASI
if 'lifestyles' not in st.session_state:
    st.session_state['lifestyles'] = {}

# 3. HASSAS SAYISAL TEMİZLEME
def clean_numeric_refined(series):
    if series.dtype == 'object':
        series = series.astype(str).str.strip()
        series = series.replace(r'[^\d.,-]', '', regex=True)
        
        def parse_value(val):
            try:
                if not val or val == 'nan': return 0.0
                if '.' in val and ',' in val:
                    val = val.replace('.', '').replace(',', '.')
                elif ',' in val:
                    val = val.replace(',', '.')
                return float(val)
            except:
                return 0.0
        
        return series.apply(parse_value)
    return pd.to_numeric(series, errors='coerce').fillna(0)

# 4. GELİŞTİRİLMİŞ VERİ İŞLEME FONKSİYONU
def process_data(file):
    try:
        # Başlık tespiti
        df_preview = pd.read_excel(file, nrows=15, header=None)
        header_row = 0
        keywords = ['line', 'ciro', 'amount', 'stock', 'stok', 'division', 'merch', 'adet', 'qty', 'sub division']
        
        for i, row in df_preview.iterrows():
            row_str = " ".join(str(val).lower() for val in row.values)
            if any(key in row_str for key in keywords):
                header_row = i
                break
        
        df = pd.read_excel(file, header=header_row)
        
        # Kolon Eşleştirme Sözlüğü (Öncelik: Sub Division)
        mapping = {
            'Line': ['Product Line', 'Line', 'Urun Grubu', 'Koleksiyon', 'LINE', 'Ürün Grubu', 'Model Grubu', 'Paket'],
            'Amount': ['Net Amount', 'Ciro', 'Tutar', 'Amount', 'CIRO', 'Net Tutar', 'Satış Tutarı', 'Satis Tutari', 'Ciro (Net)'],
            'Qty': ['Net Quantity', 'Sales Qty', 'Adet', 'Satis', 'ADET', 'Satış Adedi', 'Satis Adedi', 'Miktar'],
            'Stock': ['Stock', 'Mevcut Stok', 'Quantity', 'Stok', 'STOK', 'Kalan Stok', 'Mevcut', 'Depo Stok'],
            'Div': ['Sub Division', 'Merch Group', 'Alt Bolum', 'Division', 'BOLUM', 'Bölüm', 'Ana Grup', 'Merch Grup'],
        }

        final_cols = {}
        for key, patterns in mapping.items():
            for col in df.columns:
                if any(p.lower() == str(col).lower().strip() or p.lower() in str(col).lower() for p in patterns):
                    final_cols[key] = col
                    break
        
        # Kritik kolon kontrolü
        required = ['Line', 'Amount', 'Qty', 'Stock', 'Div']
        missing = [r for r in required if r not in final_cols]
        if missing:
            st.error(f"Eşleşmeyen Sütunlar: {missing}. Lütfen Excel başlıklarını kontrol edin.")
            return None, None

        # Sayısal Temizlik
        df[final_cols['Amount']] = clean_numeric_refined(df[final_cols['Amount']])
        df[final_cols['Qty']] = clean_numeric_refined(df[final_cols['Qty']])
        df[final_cols['Stock']] = clean_numeric_refined(df[final_cols['Stock']])

        # Merch Grup Temizliği
        df[final_cols['Div']] = df[final_cols['Div']].astype(str).str.strip().str.upper()
        
        return df, final_cols
    except Exception as e:
        st.error(f"Dosya okuma hatası: {e}")
        return None, None

# 5. SIDEBAR - YÜKLEME VE FİLTRELEME
st.sidebar.markdown("### 📥 Dosya Yükle")
uploaded_file = st.sidebar.file_uploader("Excel (.xlsx)", type=['xlsx'])

if uploaded_file:
    df, cols = process_data(uploaded_file)
    
    if df is not None:
        # 1. MERCH GRUP SEÇİMİ (Sub Division Verileri)
        all_merch_groups = sorted(df[cols['Div']].unique())
        selected_merch = st.sidebar.selectbox("🎯 Merch Grup Seçin (Sub Division)", all_merch_groups)
        
        # Filtrelenmiş Veri Seti
        cat_df = df[df[cols['Div']] == selected_merch].copy()
        
        # 2. LIFESTYLE YÖNETİMİ
        st.sidebar.divider()
        with st.sidebar.expander("🆕 Lifestyle Tanımla"):
            ls_name = st.text_input("Lifestyle İsmi")
            available_lines = sorted([str(x) for x in cat_df[cols['Line']].dropna().unique()])
            ls_lines = st.multiselect("Paketleri Seç", available_lines)
            
            if st.button("KAYDET"):
                if ls_name and ls_lines:
                    if selected_merch not in st.session_state['lifestyles']:
                        st.session_state['lifestyles'][selected_merch] = []
                    st.session_state['lifestyles'][selected_merch].append({"name": ls_name, "lines": ls_lines})
                    st.success(f"{ls_name} eklendi!")
                    st.rerun()

        # 6. ANA EKRAN - LIFESTYLE FİLTRELERİ
        st.markdown(f"### 🏷️ {selected_merch} Analiz Paneli")
        
        ls_list = st.session_state['lifestyles'].get(selected_merch, [])
        active_lines = []
        
        if ls_list:
            cols_btn = st.columns(max(len(ls_list) + 1, 6))
            with cols_btn[0]:
                if st.button("TÜMÜ", use_container_width=True, type="primary"):
                    active_lines = []
            
            for i, ls in enumerate(ls_list):
                if i+1 < len(cols_btn):
                    with cols_btn[i+1]:
                        if st.button(ls['name'], key=f"btn_{i}", use_container_width=True):
                            active_lines = ls['lines']
        
        # Filtre Uygulama
        display_df = cat_df[cat_df[cols['Line']].astype(str).isin(active_lines)] if active_lines else cat_df

        # 7. ÖZET METRİKLER VE GENEL COVER
        t_amount = display_df[cols['Amount']].sum()
        t_qty = display_df[cols['Qty']].sum()
        t_stock = display_df[cols['Stock']].sum()
        
        # GENEL COVER HESAPLAMA: Toplam Stok / Toplam Satış
        genel_cover = t_stock / t_qty if t_qty > 0 else (99 if t_stock > 0 else 0)
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='main-card'><span class='metric-label'>TOPLAM CİRO</span><br><span class='metric-value'>{t_amount:,.0f} TL</span></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='main-card'><span class='metric-label'>SATIŞ ADEDİ</span><br><span class='metric-value'>{t_qty:,.0f}</span></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='main-card'><span class='metric-label'>STOK ADEDİ</span><br><span class='metric-value'>{t_stock:,.0f}</span></div>", unsafe_allow_html=True)
        with m4:
            # Genel Cover rengi
            c_color = "#3B82F6" if 6 <= genel_cover <= 9 else ("#EF4444" if genel_cover < 6 else "#F59E0B")
            st.markdown(f"<div class='main-card'><span class='metric-label'>GENEL COVER</span><br><span class='metric-value' style='color:{c_color}'>{genel_cover:.1f}</span></div>", unsafe_allow_html=True)

        # 8. PERFORMANS ANALİZİ (Line Bazlı)
        line_analysis = display_df.groupby(cols['Line']).agg({
            cols['Amount']: 'sum',
            cols['Qty']: 'sum',
            cols['Stock']: 'sum'
        }).reset_index()
        
        # Line bazlı Cover Hesabı: (Line Toplam Stok / Line Toplam Satış)
        line_analysis['Cover'] = line_analysis.apply(
            lambda x: x[cols['Stock']] / x[cols['Qty']] if x[cols['Qty']] > 0 else (99 if x[cols['Stock']] > 0 else 0), axis=1
        ).round(1)
        
        line_analysis = line_analysis.sort_values(cols['Amount'], ascending=False)

        # 9. DETAY TABLO
        st.markdown("### 📊 Detaylı Veri Tablosu")
        st.dataframe(
            line_analysis.rename(columns={
                cols['Line']: 'Paket / Line',
                cols['Amount']: 'Ciro',
                cols['Qty']: 'Satış Adet',
                cols['Stock']: 'Stok Adet'
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ciro": st.column_config.NumberColumn(format="%d TL"),
                "Cover": st.column_config.NumberColumn(format="%.1f")
            }
        )
else:
    st.info("Devam etmek için lütfen bir Excel dosyası yükleyin.")
