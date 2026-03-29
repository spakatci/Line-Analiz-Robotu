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

# 3. GELİŞTİRİLMİŞ HATA ÖNLEYİCİ VERİ İŞLEME FONKSİYONU
def process_data(file):
    try:
        # Önce başlık satırını bulmak için ilk 20 satırı oku
        df_preview = pd.read_excel(file, nrows=20, header=None)
        header_row = 0
        found = False
        
        # Kritik kolon anahtar kelimeleri
        keywords = ['line', 'ciro', 'amount', 'stock', 'stok', 'division', 'merch']
        
        for i, row in df_preview.iterrows():
            row_str = " ".join(str(val).lower() for val in row.values)
            if any(key in row_str for key in keywords):
                header_row = i
                found = True
                break
        
        # Tespit edilen satırdan itibaren oku
        df = pd.read_excel(file, header=header_row)
        
        # Kolon Eşleştirme Sözlüğü (Genişletilmiş)
        mapping = {
            'Line': ['Product Line', 'Line', 'Urun Grubu', 'Koleksiyon', 'LINE', 'Ürün Grubu'],
            'Amount': ['Net Amount', 'Ciro', 'Tutar', 'Amount', 'CIRO', 'Net Tutar', 'Satış Tutarı'],
            'Qty': ['Net Quantity', 'Sales Qty', 'Adet', 'Satis', 'ADET', 'Satış Adedi'],
            'Stock': ['Stock', 'Mevcut Stok', 'Quantity', 'Stok', 'STOK', 'Kalan Stok'],
            'Div': ['Sub Division', 'Merch Group', 'Alt Bolum', 'Division', 'BOLUM', 'Bölüm', 'Ana Grup'],
            'Style': ['Style', 'Model', 'Short Code', 'Code', 'STIL', 'Stil'],
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
            st.warning(f"Bazı kolonlar tam eşleşmedi: {missing}. Excel başlıklarınızı kontrol edin.")
            return None, None

        # Veri Temizleme ve Sayısallaştırma
        for k in ['Amount', 'Qty', 'Stock']:
            col_name = final_cols[k]
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)

        # Kategori Normalleştirme (Esnek Eşleştirme)
        def normalize_div(val):
            val = str(val).upper().replace('İ', 'I').replace('Ş', 'S').replace('Ç', 'C').replace('Ö', 'O').replace('Ü', 'U').replace('Ğ', 'G')
            if any(x in val for x in ['WOMAN', 'KADIN', 'BAYAN', 'WD']): return 'WOMAN'
            if any(x in val for x in ['MAN', 'ERKEK', 'BAY', 'MD']): return 'MAN'
            if any(x in val for x in ['GIRL', 'KIZ']): return 'GIRL'
            if any(x in val for x in ['BOY', 'ERKEK COCUK']): return 'BOY'
            return val # Eşleşmezse orijinali döndür (Hata ayıklama için)
        
        df['Normalized_Div'] = df[final_cols['Div']].apply(normalize_div)
        return df, final_cols
    except Exception as e:
        st.error(f"Dosya işlenirken teknik bir hata oluştu: {e}")
        return None, None

# 4. SIDEBAR - YÜKLEME VE YÖNETİM
st.sidebar.markdown("### 📥 Veri Girişi")
uploaded_file = st.sidebar.file_uploader("Excel Dosyası Seçin", type=['xlsx'])

if uploaded_file:
    df, cols = process_data(uploaded_file)
    
    if df is not None:
        # Mevcut kategorileri tespit et
        existing_cats = df['Normalized_Div'].unique()
        
        # Merch Grup Seçimi
        standard_cats = ["WOMAN", "MAN", "GIRL", "BOY"]
        # Eğer standartlar dışı bir kategori varsa listeye ekle
        final_category_options = [c for c in standard_cats if c in existing_cats] + [c for c in existing_cats if c not in standard_cats]
        
        if not final_category_options:
            st.error("Excel dosyasında kategori sütunu (Division) boş görünüyor.")
            st.stop()

        selected_cat = st.sidebar.selectbox("Analiz Edilecek Grubu Seçin", final_category_options)
        
        cat_df = df[df['Normalized_Div'] == selected_cat].copy()
        
        if cat_df.empty:
            st.warning(f"Seçilen grupta ({selected_cat}) veri bulunamadı. Lütfen Excel'deki kategori isimlerini kontrol edin.")
            with st.expander("Sistem Tarafından Okunan Kategoriler"):
                st.write(existing_cats)
        else:
            # Lifestyle Yönetimi
            st.sidebar.divider()
            with st.sidebar.expander("🆕 Yeni Lifestyle Tanımla"):
                ls_name = st.text_input("Lifestyle Adı (Örn: Casual)")
                ls_lines = st.multiselect("Paketleri Seç", sorted(cat_df[cols['Line']].unique()))
                if st.button("KAYDET"):
                    if ls_name and ls_lines:
                        if selected_cat not in st.session_state['lifestyles']:
                            st.session_state['lifestyles'][selected_cat] = []
                        st.session_state['lifestyles'][selected_cat].append({"name": ls_name, "lines": ls_lines})
                        st.success(f"{ls_name} Kaydedildi!")
                        st.rerun()

            # 5. ANA PANEL - LIFESTYLE BUTONLARI
            st.markdown(f"### 🏷️ {selected_cat} Lifestyle Seçimi")
            ls_options = st.session_state['lifestyles'].get(selected_cat, [])
            
            btn_cols = st.columns(max(len(ls_options) + 1, 5))
            active_lines = []
            
            with btn_cols[0]:
                if st.button("TÜMÜ", use_container_width=True, type="primary"): 
                    active_lines = []
            
            for i, ls in enumerate(ls_options):
                if i+1 < len(btn_cols):
                    with btn_cols[i+1]:
                        if st.button(ls['name'], use_container_width=True):
                            active_lines = ls['lines']

            # Filtreleme
            display_df = cat_df[cat_df[cols['Line']].isin(active_lines)] if active_lines else cat_df

            # 6. ÜST METRİKLER
            total_s = display_df[cols['Amount']].sum()
            total_q = display_df[cols['Qty']].sum()
            line_count = len(display_df[cols['Line']].unique())
            
            m1, m2, m3 = st.columns(3)
            with m1: st.markdown(f"<div class='main-card'><p style='font-size:10px; font-weight:900; color:#94A3B8;'>TOPLAM CIRO</p><h2>{total_s:,.0f} TL</h2></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='main-card'><p style='font-size:10px; font-weight:900; color:#94A3B8;'>TOPLAM ADET</p><h2>{total_q:,.0f}</h2></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='main-card'><p style='font-size:10px; font-weight:900; color:#94A3B8;'>PAKET SAYISI</p><h2>{line_count}</h2></div>", unsafe_allow_html=True)

            # 7. TOP 5 SIRALAMA
            line_sum = display_df.groupby(cols['Line']).agg({cols['Amount']: 'sum', cols['Qty']: 'sum', cols['Stock']: 'sum'}).reset_index()
            # Cover Hesabı
            line_sum['Cover'] = (line_sum[cols['Stock']] / line_sum[cols['Qty']]).replace([np.inf, -np.inf], 99).round(1)
            line_sum = line_sum.sort_values(cols['Amount'], ascending=False)

            st.markdown("### 🏆 En İyi Performans Gösteren 5 Paket")
            t_cols = st.columns(5)
            for idx, (i, row) in enumerate(line_sum.head(5).iterrows()):
                cv = row['Cover']
                # Renk Skalası
                color = "#EF4444" if cv < 6 else "#2563EB" if cv <= 8 else "#F59E0B"
                with t_cols[idx]:
                    st.markdown(f"""
                    <div style='background:white; padding:20px; border-radius:24px; border-bottom:4px solid {color}; box-shadow:0 4px 6px rgba(0,0,0,0.02);'>
                        <p style='font-size:10px; font-weight:900; color:#64748B; margin-bottom:5px;'>#{idx+1} {str(row[cols['Line']])[:12]}</p>
                        <h4 style='margin:0;'>{row[cols['Amount']]:,.0f} TL</h4>
                        <p style='font-size:12px; font-weight:900; color:{color}; margin-top:10px;'>COVER: {cv}</p>
                    </div>
                    """, unsafe_allow_html=True)

            # 8. ANA TABLO
            st.markdown("### 📊 Detaylı Analiz Tablosu")
            st.dataframe(
                line_sum.rename(columns={cols['Line']: 'Paket', cols['Amount']: 'Ciro', cols['Qty']: 'Satış', cols['Stock']: 'Stok'}),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ciro": st.column_config.NumberColumn(format="%d TL"),
                    "Cover": st.column_config.NumberColumn(format="%.1f")
                }
            )

else:
    st.markdown("""
        <div style='text-align:center; padding:100px;'>
            <h1 style='color:#CBD5E1; font-size:80px;'>📊</h1>
            <h2 style='color:#475569;'>Hoş Geldiniz</h2>
            <p style='color:#94A3B8; max-width:500px; margin: 0 auto;'>Analiz yapmak istediğiniz Excel dosyasını sol taraftaki menüden yükleyin. Uygulama başlıkları otomatik olarak tanıyacaktır.</p>
        </div>
    """, unsafe_allow_html=True)
