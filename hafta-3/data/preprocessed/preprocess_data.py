import pandas as pd
import os

def tr_upper_series(col):
    """Pandas Series içindeki küçük 'i' ve 'ı' harflerini bozmadan büyütür"""
    return col.astype(str).str.replace('i', 'İ').str.replace('ı', 'I').str.upper()

def normalize_tr_to_ascii(text):
    """İsimleri İngilizce karakterlere dönüştürerek köklerini bulmak için"""
    if pd.isna(text): return text
    text = str(text).upper()
    for k, v in {'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'}.items():
        text = text.replace(k, v)
    return text

def turkish_score(text):
    """İçindeki Türkçe karakter sayısını bulur"""
    tr_chars = set('ÇĞİÖŞÜ')
    return sum(1 for char in str(text) if char in tr_chars)

def clean_series(series):
    """Sayı içeren, 1 harfli olan veya geçersiz (nan) verileri acımadan temizler"""
    series = series.astype(str).str.strip()
    series = series[series.str.len() > 1] # Tek harfleri uçur (A, B, C...)
    series = series[~series.str.contains(r'\d', na=False)] # Sayıları uçur
    invalid = ['nan', 'none', 'null', '']
    series = series[~series.str.lower().isin(invalid)]
    return series

def tr_lower(col):
    """En son ekrana yazdırırken Türkçe küçük harfe çevirmek için"""
    return col.str.replace('I', 'ı').str.replace('İ', 'i').str.lower()

# 1. DOSYALARI OKUMA (Kvtoraman HARİÇ)
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(script_dir, '..', 'raw')

dfs = {
    'female': pd.read_csv(os.path.join(base_dir, 'turkishnames', 'female_name_tally'), sep=r'\s+', header=None, names=['name', 'count']),
    'male': pd.read_csv(os.path.join(base_dir, 'turkishnames', 'male_name_tally'), sep=r'\s+', header=None, names=['name', 'count']),
    'tr_erkek': pd.read_csv(os.path.join(base_dir, 'tr_isim_erkek.txt'), sep=',', header=None, names=['name', 'count']),
    'emrekgn': pd.read_csv(os.path.join(base_dir, 'emrekgn.txt'), header=None, names=['name'])
}
dfs['emrekgn']['count'] = 0 # Count'u olmayanlara 0 ekliyoruz

# 2. TEMİZLEME VE BÜYÜTME İŞLEMLERİ
for name, df in dfs.items():
    df['name'] = clean_series(df['name'])
    df.dropna(subset=['name'], inplace=True)
    df['name'] = tr_upper_series(df['name'])

# Güvenilir Referans Listemiz (KVTORAMAN HARİÇ, sadece EMREKGN)
whitelist_names = set(dfs['emrekgn']['name'])

# 3. TOPLAM COUNT HESAPLAMA
variant_counts = {}
for name, df in dfs.items():
    if 'count' in df.columns and name != 'emrekgn':
        for _, row in df.iterrows():
            variant_counts[row['name']] = variant_counts.get(row['name'], 0) + row['count']

all_unique_names = set(list(variant_counts.keys()) + list(whitelist_names))

# 4. İSİMLERİ AYNI KÖKTE BİRLEŞTİRME
base_to_variants = {}
for name in all_unique_names:
    base = normalize_tr_to_ascii(name)
    if base not in base_to_variants: base_to_variants[base] = []
    base_to_variants[base].append(name)

# 5. KUSURSUZ MANTIK: En Doğru Formu Seçme
best_variant_map = {}
for base, variants in base_to_variants.items():
    variants_in_wl = [v for v in variants if v in whitelist_names]
    
    if variants_in_wl:
        best_variant = max(variants_in_wl, key=lambda v: (turkish_score(v), variant_counts.get(v, 0)))
    else:
        best_variant = max(variants, key=lambda v: variant_counts.get(v, 0))
        
    for variant in variants:
        best_variant_map[variant] = best_variant

# 6. TÜM DATAFRAME'LERDEKİ İSİMLERİ GÜNCEL FORMLA DEĞİŞTİR
for name, df in dfs.items():
    df['name'] = df['name'].map(best_variant_map)
    dfs[name] = df.groupby('name', as_index=False)['count'].sum()

# 7. LİMİTLERE GÖRE FİLTRELEME
dfs['female'] = dfs['female'][dfs['female']["count"] >= 1305]
dfs['male'] = dfs['male'][dfs['male']["count"] >= 490]
# Not: Eğer tr_erkek için de minimum bir limit (örn: >= 5) koymak istersen buraya satır ekleyebilirsin.

# 8. KÜÇÜK HARFE ÇEVİRME VE BİRLEŞTİRME
all_names = pd.concat([df['name'] for df in dfs.values()], ignore_index=True)
final_names = all_names.dropna().drop_duplicates()
final_names = tr_lower(final_names).sort_values().reset_index(drop=True)

# 9. DOSYAYA KAYDETME
save_path = os.path.join(script_dir, 'turkish_names_final.txt')
final_names.to_csv(save_path, index=False, header=False, encoding='utf-8')

print(f"✅ 'kvtoraman' HARİÇ tutularak oluşturulan saf veri seti kaydedildi!")
print(f"👉 Dosya Yolu: {save_path}")
print(f"📊 Toplam Benzersiz İsim Sayısı: {len(final_names)}")
