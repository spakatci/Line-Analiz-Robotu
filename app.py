import streamlit as st
import pandas as pd
import numpy as np
import re

# 1. SAYFA AYARLARI VE MODERN TEMA
st.set_page_config(page_title="Line Analiz v2.8", layout="wide", page_icon="📊")

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
        series = series.astype(str).str.replace('₺', '', regex=False).str.strip()
        series = series.replace(r'[^\d.,-]', '', regex=True)
        
        def parse_value(val):
            try:
                if not val or val == 'nan' or val == '': return 0.0
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
        df_preview = pd.read_excel(file, nrows=15, header=None)
        header_row = 0
        keywords = ['line', 'net quantity', 'stock', 'division', 'style', 'code']
        
        for i, row in df_preview.iterrows():
            row_str = " ".join(str(val).lower() for val in row.values)
            if any(key in row_str for key in keywords):
                header_row = i
                break
        
        df = pd.read_excel(file, header=header_row)
        
        # Kolon Eşleştirme
        mapping = {
            'Line': ['Product Line', 'Line', 'Urun Grubu', 'Koleksiyon', 'LINE', 'Paket'],
            'Amount': ['Net Amount Wo Vat (TL)', 'Net Amount', 'Ciro', 'Tutar', 'Amount'],
            'Qty': ['Net Quantity', 'Sales Qty', 'Adet', 'Satis', 'Miktar'],
            'Stock': ['Stock', 'Mevcut Stok', 'Quantity', 'Stok', 'STOK'],
            'Div': ['Division', 'Merch Group', 'Main Group', 'Ana Grup'],
            'Style': ['Short Code', 'Style', 'Model', 'Kısa Kod', 'Kod', 'Model Kodu']
        }

        final_cols = {}
        for key, patterns in mapping.items():
            for col in df.columns:
                col_name_clean = str(col).strip()
                if any(p.lower() == col_name_clean.lower() for p in patterns):
                    final_cols[key] = col
                    break
            if key not in final_cols:
                for col in df.columns:
                    if any(p.lower() in str(col).lower() for p in patterns):
                        final_cols[key] = col
                        break
        
        required = ['Line', 'Amount', 'Qty', 'Stock', 'Div', 'Style']
        missing = [r for r in required if r not in final_cols]
        if missing:
            st.error(f"Eşleşmeyen Sütunlar: {missing}. Excel başlıklarını kontrol edin.")
            return None, None

        # Sayısal Temizlik
        df[final_cols['Amount']] = clean_numeric_refined(df[final_cols['Amount']])
        df[final_cols['Qty']] = clean_numeric_refined(df[final_cols['Qty']])
        df[final_cols['Stock']] = clean_numeric_refined(df[final_cols['Stock']])

        # Merch Grup Normalleştirme Fonksiyonu
        def normalize_merch(val):
            v = str(val).upper()
            if any(x in v for x in ['WOMAN', 'KADIN']): return 'WOMAN'
            if any(x in v for x in ['MAN', 'ERKEK']): return 'MAN'
            if any(x in v for x in ['BOY', 'ERKEK COCUK']): return 'BOY'
            if any(x in v for x in ['GIRL', 'KIZ COCUK']): return 'GIRL'
            return v
        
        # Orijinal Division sütununu koru, normalize edilmiş Merch değerini ayrı ekle
        df['Original_Div'] = df[final_cols['Div']].astype(str).str.strip().str.upper()
        df['Normalized_Merch'] = df[final_cols['Div']].apply(normalize_merch)
        
        return df, final_cols
    except Exception as e:
        st.error(f"Dosya okuma hatası: {e}")
        return None, None

# 5. SIDEBAR
st.sidebar.markdown("### 📥 Dosya Yükle")
uploaded_file = st.sidebar.file_uploader("Excel (.xlsx)", type=['xlsx'])

if uploaded_file:
    df, cols = process_data(uploaded_file)
    
    if df is not None:
        # 1. BİRİNCİ SEÇİM KUTUSU: Division Seçin
        all_divisions = sorted([x for x in df['Original_Div'].unique() if str(x) != 'NAN'])
        selected_division = st.sidebar.selectbox("🎯 Division Seçin", all_divisions)
        
        # Seçilen Division'a göre veriyi filtrele
        div_filtered_df = df[df['Original_Div'] == selected_division].copy()
        
        # 2. İKİNCİ SEÇİM KUTUSU: Merch Grup Seçin (Woman, Man vb.)
        merch_options = sorted(div_filtered_df['Normalized_Merch'].unique())
        selected_merch = st.sidebar.selectbox("👗 Merch Grup Seçin", merch_options)
        
        # Nihai Filtrelenmiş Veri Seti
        cat_df = div_filtered_df[div_filtered_df['Normalized_Merch'] == selected_merch].copy()
        
        # 3. LIFESTYLE YÖNETİMİ
        st.sidebar.divider()
        with st.sidebar.expander("🆕 Lifestyle Tanımla"):
            ls_name = st.text_input("Lifestyle İsmi")
            available_lines = sorted([str(x) for x in cat_df[cols['Line']].dropna().unique()])
            ls_lines = st.multiselect("Paketleri Seç", available_lines)
            
            if st.button("KAYDET"):
                if ls_name and ls_lines:
                    state_key = f"{selected_division}_{selected_merch}"
                    if state_key not in st.session_state['lifestyles']:
                        st.session_state['lifestyles'][state_key] = []
                    st.session_state['lifestyles'][state_key].append({"name": ls_name, "lines": ls_lines})
                    st.success(f"{ls_name} eklendi!")
                    st.rerun()

        # 6. ANA EKRAN
        st.markdown(f"### 🏷️ {selected_division} > {selected_merch} Analiz Paneli")
        
        state_key = f"{selected_division}_{selected_merch}"
        ls_list = st.session_state['lifestyles'].get(state_key, [])
        active_lines = []
        is_filtered = False
        
        if ls_list:
            cols_btn = st.columns(max(len(ls_list) + 1, 6))
            with cols_btn[0]:
                if st.button("TÜMÜ", use_container_width=True, type="primary"):
                    active_lines = []
                    is_filtered = False
            
            for i, ls in enumerate(ls_list):
                if i+1 < len(cols_btn):
                    with cols_btn[i+1]:
                        if st.button(ls['name'], key=f"btn_{i}", use_container_width=True):
                            active_lines = ls['lines']
                            is_filtered = True
        
        # Filtre Uygulama
        display_df = cat_df[cat_df[cols['Line']].astype(str).isin(active_lines)] if is_filtered else cat_df

        # 7. ÖZET METRİKLER
        t_amount = display_df[cols['Amount']].sum()
        t_qty = display_df[cols['Qty']].sum()
        t_stock = display_df[cols['Stock']].sum()
        genel_cover = t_stock / t_qty if t_qty > 0 else (99 if t_stock > 0 else 0)
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='main-card'><span class='metric-label'>TOPLAM CİRO</span><br><span class='metric-value'>{t_amount:,.0f} TL</span></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='main-card'><span class='metric-label'>SATIŞ ADEDİ</span><br><span class='metric-value'>{t_qty:,.0f}</span></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='main-card'><span class='metric-label'>STOK ADEDİ</span><br><span class='metric-value'>{t_stock:,.0f}</span></div>", unsafe_allow_html=True)
        with m4:
            c_color = "#3B82F6" if 6 <= genel_cover <= 9 else ("#EF4444" if genel_cover < 6 else "#F59E0B")
            st.markdown(f"<div class='main-card'><span class='metric-label'>GRUP COVER</span><br><span class='metric-value' style='color:{c_color}'>{genel_cover:.1f}</span></div>", unsafe_allow_html=True)

        # 8. DETAYLI VERİ TABLOSU (DİNAMİK)
        st.markdown("### 📊 Detaylı Analiz")
        
        if is_filtered:
            # Ürün Detay Görünümü (Kısa Kod Bazında)
            detail_analysis = display_df.groupby([cols['Line'], cols['Style']]).agg({
                cols['Amount']: 'sum',
                cols['Qty']: 'sum',
                cols['Stock']: 'sum'
            }).reset_index()
            
            # SyntaxError düzeltilen kısım
            detail_analysis['Cover'] = detail_analysis.apply(
                lambda x: x[cols['Stock']] / x[cols['Qty']] if x[cols['Qty']] > 0 else (99 if x[cols['Stock']] > 0 else 0), 
                axis=1
            ).round(1)
            
            detail_analysis = detail_analysis.sort_values(cols['Amount'], ascending=False)
            
            st.dataframe(
                detail_analysis.rename(columns={
                    cols['Line']: 'Paket / Line',
                    cols['Style']: 'Ürün Kısa Kod',
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
            # Genel Paket Özet Görünümü
            line_analysis = display_df.groupby(cols['Line']).agg({
                cols['Amount']: 'sum',
                cols['Qty']: 'sum',
                cols['Stock']: 'sum'
            }).reset_index()
            
            line_analysis['Cover'] = line_analysis.apply(
                lambda x: x[cols['Stock']] / x[cols['Qty']] if x[cols['Qty']] > 0 else (99 if x[cols['Stock']] > 0 else 0), 
                axis=1
            ).round(1)
            
            line_analysis = line_analysis.sort_values(cols['Amount'], ascending=False)

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
