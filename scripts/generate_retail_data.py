"""
generate_retail_data.py
Generates synthetic retail data: dimensions and 10M fact sales rows.
Outputs CSV files into the data/raw/ directory relative to project root.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import random
import csv

# -------------------------------------------------------------------
# Path resolution: script is in src/data_generation/
# Go up two levels to reach project root, then to data/raw/
# -------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_DIR = os.path.join(BASE_PROJECT_DIR, "data", "raw")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration
N_SALES = 10_000_000
N_CUSTOMERS = 200_000
N_PRODUCTS = 2_000
N_STORES = 200
N_PROMOTIONS = 100
RANDOM_SEED = 42
CHUNK_SIZE = 500_000

if RANDOM_SEED is not None:
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2026, 5, 26)

# -------------------------------------------------------------------
# Retail dictionaries and configuration maps
# -------------------------------------------------------------------
STORE_CHAINS = {
    'Supermarket': ['FreshMart','CityFood','DailyGrocer','MarketPlace','ValueSave','GoodMart'],
    'Hypermarket': ['MegaMart','SuperSaver','GlobalHyper','BigBox','GiantStore','PriceCutter'],
    'Convenience': ['QuickStop','CornerShop','EasyBuy','OnTheRun','MiniMarket','FastShop'],
    'Department':  ['CityCenter','TheGalleria','TownSquare','UrbanMall','GrandPlaza','MetroStore']
}
STORE_SUFFIXES = ['Center','Plaza','Market','Point','Hub','Square','Mart']

REGION_CITY_MAP = {
    'North':   ['New York','Chicago','Boston','Seattle','Detroit','Minneapolis','Buffalo','Pittsburgh'],
    'South':   ['Houston','Dallas','Miami','Atlanta','Austin','Nashville','Orlando','San Antonio'],
    'East':    ['Philadelphia','Baltimore','Charlotte','Jacksonville','Washington DC','Tampa','Richmond'],
    'West':    ['Los Angeles','San Francisco','Phoenix','San Diego','Portland','Las Vegas','Sacramento'],
    'Central': ['Kansas City','St. Louis','Omaha','Denver','Cleveland','Columbus','Indianapolis','Milwaukee']
}
REGIONS = list(REGION_CITY_MAP.keys())

PROMO_TEMPLATES = {
    'Percentage':    ['Spring Sale','Summer Deal','Winter Discount','Flash Sale','Clearance','Happy Hour','Member Special'],
    'Fixed Amount':  ['Cashback','Save $','Discount Voucher','Price Drop','Instant Save','Coupon Special'],
    'BOGO':          ['Buy 1 Get 1 Free','2 for 1','3 for 2','Multi-buy','Double Up'],
    'Free Shipping': ['Free Delivery','No Shipping Fee','Shipping included','Free Post']
}

PRODUCT_NAMES = {
    'Electronics': ['Smartphone','Laptop','Headphones','Smartwatch','Tablet','Monitor','Speaker','Camera','Console','Router'],
    'Home':        ['Desk','Chair','Lamp','Sofa','Table','Bed','Cabinet','Vacuum','Blender','Toaster'],
    'Sports':      ['Shoes','Tshirt','Backpack','Bike','Ball','Racket','Dumbbells','Mat','Gloves','Helmet'],
    'Kids':        ['Doll','Action Figure','Puzzle','Blocks','Board Game','Plushie','Lego Set','Cart','Book','Costume'],
    'Garden':      ['Lawn Mower','Hedge Trimmer','Hose','Shovel','Rake','Faucet','Seeds','Pot','Fertilizer','Gnome']
}
PRODUCT_ADJECTIVES = ['Pro','Plus','Max','Lite','Ultra','Mini','Elite','Core','Prime','Select','Air','Studio']

BRANDS = {
    'Electronics': ['Sony','Samsung','Apple','Philips','LG','Dell','HP','Asus','Bose','Logitech'],
    'Home':        ['IKEA','Tefal','Bosch','Electrolux','Dyson','Nespresso','Kenwood','Braun','Rowenta','DeLonghi'],
    'Sports':      ['Nike','Adidas','Puma','Reebok','UnderArmour','NewBalance','Asics','Jordan','Mizuno','Salomon'],
    'Kids':        ['LEGO','Fisher-Price','Mattel','Hasbro','Playmobil','Barbie','HotWheels','Nerf','Cocomelon','PawPatrol'],
    'Garden':      ['Husqvarna','Bosch','Black and Decker','Gardena','Makita','Stihl','Fiskars','Wolf','Karcher']
}

FIRST_NAMES_MALE = ['James','John','Robert','Michael','William','David','Richard','Joseph','Thomas','Charles','Daniel','Matthew']
FIRST_NAMES_FEMALE = ['Mary','Patricia','Jennifer','Linda','Elizabeth','Barbara','Susan','Jessica','Sarah','Karen','Lisa','Nancy']
LAST_NAMES = ['Smith','Johnson','Douglas','Williams','Brown','Jones','Garcia','Middle','Davis','Rodriguez','Martinez','Hernandez','Lopez']

GENDERS = ['Male','Female']
EDUCATION = ['High School','Bachelor','Master','PhD']
MARITAL = ['Single','Married','Divorced','Widowed']
CONTACT_PREF = ['Email','SMS','Phone','Mail']
PAYMENT = ['Card','Cash','Bank Transfer','Digital Wallet','PayPal']
CHANNELS = ['Online','In-Store','Mobile App','Phone Order']
STORE_TYPES = ['Supermarket','Hypermarket','Convenience','Department']
RETURN_REASONS = ['Defective','Wrong item','Not as described','Changed mind','Late delivery','Other']
CAT_NAMES = ['Electronics','Home','Sports','Kids','Garden']

CATEGORY_CFG = {
    'Electronics': {'price_lo':250, 'price_hi':600, 'weight_lo':0.3, 'weight_hi':3.0, 'tax_rate':0.21, 'warranty_prob':0.9, 'return_rate_base':0.03},
    'Home':        {'price_lo':80,  'price_hi':200, 'weight_lo':1.0, 'weight_hi':15.0,'tax_rate':0.21, 'warranty_prob':0.5, 'return_rate_base':0.06},
    'Sports':      {'price_lo':40,  'price_hi':150, 'weight_lo':0.2, 'weight_hi':5.0, 'tax_rate':0.21, 'warranty_prob':0.3, 'return_rate_base':0.09},
    'Kids':        {'price_lo':15,  'price_hi':60,  'weight_lo':0.1, 'weight_hi':2.0, 'tax_rate':0.10, 'warranty_prob':0.2, 'return_rate_base':0.15},
    'Garden':      {'price_lo':30,  'price_hi':120, 'weight_lo':0.5, 'weight_hi':12.0,'tax_rate':0.21, 'warranty_prob':0.6, 'return_rate_base':0.07},
}

def clean_df(df, string_default='Unknown', int_default=0, float_default=0.0):
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna(string_default).replace('', string_default).astype(str)
    for col in df.select_dtypes(include=['int64','int32']).columns:
        df[col] = df[col].fillna(int_default).astype(int)
    for col in df.select_dtypes(include=['float64','float32']).columns:
        df[col] = df[col].fillna(float_default)
    return df

def generate_hours_vectorized(channels, store_types):
    n = len(channels)
    hours = np.zeros(n, dtype=np.uint8)

    online_probs = np.array([0.01,0.01,0.01,0.01,0.01,0.01,0.02,0.03,0.04,0.05,0.05,0.05,0.05,0.05,0.06,0.07,0.08,0.09,0.09,0.07,0.05,0.03,0.02,0.01])
    online_probs /= online_probs.sum()

    mobile_probs = np.array([0.01,0.01,0.01,0.01,0.02,0.03,0.05,0.06,0.07,0.08,0.08,0.07,0.07,0.06,0.06,0.06,0.05,0.04,0.03,0.02,0.02,0.01,0.01,0.01])
    mobile_probs /= mobile_probs.sum()

    phone_probs = np.zeros(24)
    phone_probs[9:21] = 1/12
    phone_probs /= phone_probs.sum()

    instore_default_probs = np.zeros(24)
    instore_default_probs[8:21] = 1/13
    instore_default_probs /= instore_default_probs.sum()

    instore_broad_probs = np.zeros(24)
    instore_broad_probs[6:23] = 1/17
    instore_broad_probs /= instore_broad_probs.sum()

    mask_online = (channels == 'Online')
    mask_mobile = (channels == 'Mobile App')
    mask_phone = (channels == 'Phone Order')
    mask_instore = (channels == 'In-Store')

    if mask_online.any():
        hours[mask_online] = np.random.choice(24, size=mask_online.sum(), p=online_probs)
    if mask_mobile.any():
        hours[mask_mobile] = np.random.choice(24, size=mask_mobile.sum(), p=mobile_probs)
    if mask_phone.any():
        hours[mask_phone] = np.random.choice(24, size=mask_phone.sum(), p=phone_probs)
    if mask_instore.any():
        broad_mask = np.isin(store_types[mask_instore], ['Convenience','Hypermarket'])
        broad_idx = np.where(mask_instore)[0][broad_mask]
        default_idx = np.where(mask_instore)[0][~broad_mask]
        if len(broad_idx) > 0:
            hours[broad_idx] = np.random.choice(24, size=len(broad_idx), p=instore_broad_probs)
        if len(default_idx) > 0:
            hours[default_idx] = np.random.choice(24, size=len(default_idx), p=instore_default_probs)

    return np.clip(hours, 0, 23).astype(np.uint8)

# --- Generate dim_store (no dummy row with -1) ---
print("Generating dim_store...")
store_ids = np.arange(1, N_STORES + 1)
store_data = []
unique_names = set()
while len(unique_names) < N_STORES:
    stype = np.random.choice(STORE_TYPES)
    reg = random.choice(REGIONS)
    city = random.choice(REGION_CITY_MAP[reg])
    chain = random.choice(STORE_CHAINS[stype])
    suffix = random.choice(STORE_SUFFIXES)
    name = f"{chain} {city} {suffix}"
    if name not in unique_names:
        unique_names.add(name)
        store_data.append((name, city, stype, reg, chain, suffix))

store_sizem2 = np.where(
    np.array([d[2] for d in store_data]) == 'Hypermarket', np.random.randint(2500, 5000, N_STORES),
    np.where(np.array([d[2] for d in store_data]) == 'Supermarket', np.random.randint(800, 2500, N_STORES),
    np.where(np.array([d[2] for d in store_data]) == 'Department',  np.random.randint(1200, 3500, N_STORES),
                                                      np.random.randint(150, 800, N_STORES)))
)
store_staff = np.clip((store_sizem2 / 45 + np.random.normal(0, 8, N_STORES)).astype(int), 3, 200)
store_parking = np.clip((store_sizem2 / 25 + np.random.normal(0, 15, N_STORES)).astype(int), 0, 500)
store_rating = np.clip(2.0 + (store_staff/200)*0.8 + (store_parking/500)*0.5 + np.random.uniform(0, 1.2, N_STORES), 2.0, 5.0).round(1)

store_df = pd.DataFrame({
    'storeid': store_ids,
    'storename': [d[0] for d in store_data],
    'city': [d[1] for d in store_data],
    'type': [d[2] for d in store_data],
    'staff': store_staff,
    'sizem2': store_sizem2,
    'hascafe': np.random.choice([0,1], N_STORES, p=[0.6,0.4]),
    'openingyear': np.random.randint(1985, 2023, N_STORES),
    'region': [d[3] for d in store_data],
    'renovationyear': np.random.choice([0]+list(range(2010,2024)), N_STORES, p=[0.35]+[0.65/14]*14),
    'parkingspots': store_parking,
    'storerating': store_rating,
    'hasdeliveryservice': np.random.choice([0,1], N_STORES, p=[0.4,0.6]),
    'floornumber': np.random.randint(1, 6, N_STORES),
    'distancetocitycenterkm': np.random.uniform(0.5, 25.0, N_STORES).round(1),
    'annualrentcost': (store_sizem2 * 12 * 1.5).round(2),
    'storesizemultiplier': np.random.lognormal(mean=0.5, sigma=1.2, size=N_STORES).clip(0.1, 10.0).round(4)
})

store_df['renovationyear'] = np.where(
    (store_df['renovationyear'] != 0) & (store_df['renovationyear'] < store_df['openingyear']),
    store_df['openingyear'],
    store_df['renovationyear']
)

store_df.to_csv(f"{OUTPUT_DIR}/dim_store.csv", index=False, encoding='utf-8', quoting=csv.QUOTE_MINIMAL)

# --- Generate dim_product (no dummy row with -1) ---
print("Generating dim_product...")
product_pool = []
product_names_set = set()
while len(product_pool) < N_PRODUCTS * 1.5:
    cat = random.choice(CAT_NAMES)
    brand = random.choice(BRANDS[cat])
    adj = random.choice(PRODUCT_ADJECTIVES)
    noun = random.choice(PRODUCT_NAMES[cat])
    variant = np.random.choice(['','V2','X','Series 5','Mk1','2024','Ltd','Gen3'], p=[0.4,0.1,0.1,0.1,0.1,0.1,0.05,0.05])
    name = f"{brand} {adj} {noun} {variant}".strip()
    if name not in product_names_set:
        product_names_set.add(name)
        product_pool.append((name, cat, brand))

selected_products = product_pool[:N_PRODUCTS]
product_ids = np.arange(1, N_PRODUCTS + 1)
margins = np.zeros(N_PRODUCTS)
margins[:int(N_PRODUCTS*0.05)] = 0.30
margins[int(N_PRODUCTS*0.05):int(N_PRODUCTS*0.10)] = np.random.uniform(0.20, 0.29, int(N_PRODUCTS*0.05))
margins[int(N_PRODUCTS*0.10):int(N_PRODUCTS*0.15)] = 0.15
margins[int(N_PRODUCTS*0.15):int(N_PRODUCTS*0.65)] = np.random.uniform(0.05, 0.10, int(N_PRODUCTS*0.50))
margins[int(N_PRODUCTS*0.65):int(N_PRODUCTS*0.95)] = np.random.uniform(0.00, 0.05, int(N_PRODUCTS*0.30))
margins[int(N_PRODUCTS*0.95):] = np.random.uniform(-0.10, 0.00, N_PRODUCTS - int(N_PRODUCTS*0.95))
np.random.shuffle(margins)

product_unitprice = []
product_unitcost = []
for i, p_info in enumerate(selected_products):
    cfg = CATEGORY_CFG[p_info[1]]
    price = round(np.random.uniform(cfg['price_lo'], cfg['price_hi']) * np.random.uniform(0.9, 1.5), 2)
    margin = margins[i]
    cost = round(price * (1.0 - margin), 2)
    if cost <= 0:
        cost = round(price * 0.75, 2)
        margins[i] = 0.25
    product_unitprice.append(price)
    product_unitcost.append(cost)

product_df = pd.DataFrame({
    'productid': product_ids,
    'name': [p[0] for p in selected_products],
    'category': [p[1] for p in selected_products],
    'brand': [p[2] for p in selected_products],
    'unitcost': product_unitcost,
    'unitprice': product_unitprice,
    'margin_pct': margins.round(4),
    'weight': np.random.uniform(0.1, 15.0, N_PRODUCTS).round(2),
    'color': np.random.choice(['Red','Blue','Green','Black','White','Gray','Silver','Gold'], N_PRODUCTS),
    'material': np.random.choice(['Plastic','Metal','Wood','Glass','Fabric'], N_PRODUCTS),
    'supplierid': np.random.randint(1, 51, N_PRODUCTS),
    'isactive': np.random.choice([0,1], N_PRODUCTS, p=[0.05,0.95]),
    'minstock': np.random.randint(2, 100, N_PRODUCTS),
    'tax_rate': np.array([CATEGORY_CFG[p[1]]['tax_rate'] for p in selected_products]).round(2),
    'haswarranty': np.random.choice([0,1], N_PRODUCTS),
    'ecofriendly': np.random.choice([0,1], N_PRODUCTS),
    'seasonalityfactor': np.random.uniform(0.7, 1.3, N_PRODUCTS).round(2),
    'warrantymonths': np.random.choice([0,12,24,36], N_PRODUCTS),
    'ecoscore': np.random.randint(20, 200, N_PRODUCTS),
    'releaseyear': np.random.randint(2018, 2026, N_PRODUCTS),
    'skucount': np.random.randint(1, 10, N_PRODUCTS),
    'isdiscontinued': np.random.choice([0,1], N_PRODUCTS, p=[0.90,0.10]),
    'productrating': np.clip(1.0 + np.random.normal(3.0, 0.8, N_PRODUCTS), 1.0, 5.0).round(1),
    'stockstatus': np.random.choice(['In Stock','Low Stock','Out of Stock'], N_PRODUCTS, p=[0.80,0.15,0.05])
})
product_df.to_csv(f"{OUTPUT_DIR}/dim_product.csv", index=False, encoding='utf-8', quoting=csv.QUOTE_MINIMAL)

# --- Generate dim_promotion (promoid 0 for No Promotion) ---
print("Generating dim_promotion...")
promo_ids = np.arange(1, N_PROMOTIONS + 1)
promo_types = np.random.choice(['Percentage','Fixed Amount','BOGO','Free Shipping'], N_PROMOTIONS)

promo_start_list = [START_DATE + timedelta(days=int(d)) for d in np.random.randint(0, 900, N_PROMOTIONS)]
promo_end_list = [ps + timedelta(days=int(d)) for ps, d in zip(promo_start_list, np.random.randint(15, 120, N_PROMOTIONS))]
promo_end_list = [min(pe, END_DATE) for pe in promo_end_list]

promo_isactive = np.array([1 if pe >= END_DATE else 0 for pe in promo_end_list])

discount_pct = np.where(promo_types == 'Percentage', np.random.uniform(0.10, 0.45, N_PROMOTIONS).round(4), 0.0)
discount_fixed = np.where(promo_types == 'Fixed Amount', np.random.uniform(5, 50, N_PROMOTIONS).round(2), 0.0)

promo_df = pd.DataFrame({
    'promoid': promo_ids,
    'promoname': [f"Promo {i}" for i in promo_ids],
    'discount_pct': discount_pct,
    'discount_fixed': discount_fixed,
    'type': promo_types,
    'isactive': promo_isactive,
    'minspend': np.random.choice([0,25,50,100], N_PROMOTIONS),
    'channel': np.random.choice(['Online','In-Store','All'], N_PROMOTIONS),
    'budget': np.random.uniform(1000, 50000, N_PROMOTIONS).round(2),
    'startdate': [ps.strftime('%Y-%m-%d') for ps in promo_start_list],
    'enddate': [pe.strftime('%Y-%m-%d') for pe in promo_end_list],
    'targetaudience': np.random.choice(['All','Loyal','New'], N_PROMOTIONS),
    'maxdiscountcap': np.random.uniform(10, 100, N_PROMOTIONS).round(2),
    'isstackable': np.random.choice([0,1], N_PROMOTIONS),
    'redemption_rate': np.random.uniform(0.01, 0.30, N_PROMOTIONS).round(3),
    'coderequired': np.random.choice([0,1], N_PROMOTIONS),
    'promoupliftfactor': np.random.uniform(1.0, 2.0, N_PROMOTIONS).round(3)
})

no_promo = pd.DataFrame([{
    'promoid': 0,
    'promoname': 'No Promotion',
    'discount_pct': 0.0,
    'discount_fixed': 0.0,
    'type': 'None',
    'isactive': 1,
    'minspend': 0,
    'channel': 'All',
    'budget': 0.0,
    'startdate': START_DATE.strftime('%Y-%m-%d'),
    'enddate': END_DATE.strftime('%Y-%m-%d'),
    'targetaudience': 'All',
    'maxdiscountcap': 0.0,
    'isstackable': 0,
    'redemption_rate': 0.0,
    'coderequired': 0,
    'promoupliftfactor': 1.0
}])
promo_df = pd.concat([no_promo, promo_df], ignore_index=True)
promo_df.to_csv(f"{OUTPUT_DIR}/dim_promotion.csv", index=False, encoding='utf-8', quoting=csv.QUOTE_MINIMAL)

# --- Generate dim_customer (no dummy row with -1) ---
print("Generating dim_customer...")
customer_ids = np.arange(1, N_CUSTOMERS + 1)
customer_df = pd.DataFrame({
    'customerid': customer_ids,
    'fullname': [f"Customer {i}" for i in customer_ids],
    'email': [f"customer{i}@example.com" for i in customer_ids],
    'age': np.random.randint(18, 76, N_CUSTOMERS),
    'gender': np.random.choice(GENDERS, N_CUSTOMERS),
    'city': np.random.choice(sum(REGION_CITY_MAP.values(), []), N_CUSTOMERS),
    'tier': np.random.choice(['Bronze','Silver','Gold','Platinum'], N_CUSTOMERS, p=[0.5,0.3,0.15,0.05]),
    'points': np.random.randint(0, 1000, N_CUSTOMERS),
    'isactive': np.random.choice([0,1], N_CUSTOMERS, p=[0.1,0.9]),
    'lang': np.random.choice(['en','de','fr'], N_CUSTOMERS),
    'totalspend': np.random.uniform(10, 5000, N_CUSTOMERS).round(2),
    'regdate': (START_DATE + pd.to_timedelta(np.random.randint(0, 1000, N_CUSTOMERS), unit='D')).strftime('%Y-%m-%d'),
    'annualincome': np.random.uniform(20000, 150000, N_CUSTOMERS).round(2),
    'incomebracket': np.random.choice(['Low','Medium','High'], N_CUSTOMERS),
    'education': np.random.choice(EDUCATION, N_CUSTOMERS),
    'maritalstatus': np.random.choice(MARITAL, N_CUSTOMERS),
    'childrencount': np.random.randint(0, 5, N_CUSTOMERS),
    'loyaltysegment': np.random.choice(['Bronze','Silver','Gold','Platinum'], N_CUSTOMERS),
    'satisfactionscore': np.random.uniform(1.0, 5.0, N_CUSTOMERS).round(1),
    'dayssincelastpurchase': np.random.randint(-1, 365, N_CUSTOMERS),
    'hassubscription': np.random.choice([0,1], N_CUSTOMERS),
    'preferredcontact': np.random.choice(CONTACT_PREF, N_CUSTOMERS),
    'spendmultiplier': np.random.uniform(0.5, 2.5, N_CUSTOMERS).round(3)
})
customer_df.to_csv(f"{OUTPUT_DIR}/dim_customer.csv", index=False, encoding='utf-8', quoting=csv.QUOTE_MINIMAL)

# --- Generate dim_date (no dummy row) ---
print("Generating dim_date...")
dates = pd.date_range(START_DATE, END_DATE, freq='D')
date_df = pd.DataFrame({
    'datekey': dates.strftime("%Y%m%d").astype(int),
    'fulldate': dates.strftime("%Y-%m-%d"),
    'year': dates.year.astype(int),
    'quarternumber': dates.quarter.astype(int),
    'quartername': 'Q' + dates.quarter.astype(str),
    'monthnumber': dates.month.astype(int),
    'monthname': dates.month_name(),
    'weekdaynumber': (dates.dayofweek + 1).astype(int),
    'weekdayname': dates.day_name(),
    'isweekend': (dates.dayofweek >= 5).astype(int),
    'yearmonth': dates.strftime("%Y-%m"),
    'yearmonthnumber': (dates.year * 100 + dates.month).astype(int),
    'yearquarter': dates.year.astype(str) + '-Q' + dates.quarter.astype(str),
    'yearquarternumber': (dates.year * 10 + dates.quarter).astype(int),
    'yearweek': dates.strftime("%Y-W%W"),
    'yearweeknumber': (dates.isocalendar().week.astype(int) + dates.year * 100),
    'isholiday': np.isin(dates.month, [12, 1]).astype(int)
})
date_df.to_csv(f"{OUTPUT_DIR}/dim_date.csv", index=False, encoding='utf-8', quoting=csv.QUOTE_MINIMAL)

# --- Daily net-sales trend ---
print("Generating trend: decline (60k->50k) then flat, then strong rise to 95k at end...")
n_dates = len(dates)
decline_end = int(n_dates * 0.5)
flat_end    = int(n_dates * 0.7)

start_val, decline_val, flat_val, rise_start, final_peak = 60000, 50000, 50000, 50000, 95000

trend = np.zeros(n_dates)
trend[:decline_end]         = np.linspace(start_val, decline_val, decline_end)
trend[decline_end:flat_end] = flat_val
trend[flat_end:]            = np.linspace(rise_start, final_peak, n_dates - flat_end)

window = 7
ma = np.convolve(trend, np.ones(window)/window, mode='same')
ma[:window//2] = trend[:window//2]
ma[-window//2:] = trend[-window//2:]
smooth_trend = ma

drift_rates = np.zeros(n_dates)
for i in range(1, n_dates):
    if smooth_trend[i-1] != 0:
        drift_rates[i] = (smooth_trend[i] - smooth_trend[i-1]) / smooth_trend[i-1]

volatility = 0.02
noise = np.random.normal(0, 1, n_dates)
smoothed_noise = np.convolve(noise, np.ones(3)/3, mode='same')
final_values = np.zeros(n_dates)
final_values[0] = smooth_trend[0]

for i in range(1, n_dates):
    daily_change = drift_rates[i] + volatility * smoothed_noise[i]
    final_values[i] = final_values[i-1] * (1 + daily_change)

daily_net_sales_target = np.maximum(np.round(final_values).astype(int), 1000)

# --- Pre-generate fact table indices ---
print("Pre-generating vectorized indices for 10M-row fact table...")
product_ids_arr = product_df['productid'].values
customer_ids_arr = customer_df['customerid'].values
store_ids_arr = store_df['storeid'].values
promo_ids_arr = promo_df[promo_df['promoid'] > 0]['promoid'].values
datekeys = date_df['datekey'].values

unitprices_dict = product_df.set_index('productid')['unitprice'].to_dict()
taxrates_dict = product_df.set_index('productid')['tax_rate'].to_dict()
weights_dict = product_df.set_index('productid')['weight'].to_dict()

promo_pct_dict = promo_df.set_index('promoid')['discount_pct'].to_dict()
promo_fixed_dict = promo_df.set_index('promoid')['discount_fixed'].to_dict()

store_types_dict = store_df.set_index('storeid')['type'].to_dict()

daily_trans_allocation = np.floor(N_SALES * (daily_net_sales_target / daily_net_sales_target.sum())).astype(int)
diff = N_SALES - daily_trans_allocation.sum()
daily_trans_allocation[0] += diff

all_products = np.random.choice(product_ids_arr, N_SALES)
all_customers = np.random.choice(customer_ids_arr, N_SALES)
all_stores = np.random.choice(store_ids_arr, N_SALES)
all_promo_has = np.random.choice([0, 1], N_SALES, p=[0.70, 0.30])
all_promos_raw = np.random.choice(promo_ids_arr, N_SALES)
all_promos = np.where(all_promo_has == 1, all_promos_raw, 0)

f_path = f"{OUTPUT_DIR}/fact_sales.csv"
if os.path.exists(f_path):
    os.remove(f_path)

pd.DataFrame(columns=[
    'salesid','datekey','productid','customerid','storeid','promoid',
    'qty','unitprice','tax_rate','net','payment','channel',
    'grossvalue','discountamount','taxamount','shipcost','isreturn',
    'shipweight','discountapplied','returnreason','deliverydays','hour'
]).to_csv(f_path, index=False)

sales_id_cursor = 1
current_buffer = []

for day_idx in range(n_dates):
    n_tr = daily_trans_allocation[day_idx]
    if n_tr == 0:
        continue
    datekey = datekeys[day_idx]
    target = daily_net_sales_target[day_idx]

    prod_choices = all_products[sales_id_cursor - 1 : sales_id_cursor - 1 + n_tr]
    cust_choices = all_customers[sales_id_cursor - 1 : sales_id_cursor - 1 + n_tr]
    store_choices = all_stores[sales_id_cursor - 1 : sales_id_cursor - 1 + n_tr]
    promo_choices = all_promos[sales_id_cursor - 1 : sales_id_cursor - 1 + n_tr]

    unit_prices = np.array([unitprices_dict[p] for p in prod_choices])
    tax_rates = np.array([taxrates_dict[p] for p in prod_choices])
    weights = np.array([weights_dict[p] for p in prod_choices])

    disc_pcts = np.array([promo_pct_dict[pr] for pr in promo_choices])
    disc_fixed = np.array([promo_fixed_dict[pr] for pr in promo_choices])

    raw_qty = np.random.poisson(2, n_tr) + 1
    gross_temp = raw_qty * unit_prices
    disc_temp = (gross_temp * disc_pcts) + (raw_qty * disc_fixed)
    disc_temp = np.minimum(disc_temp, gross_temp)
    net_before_tax_temp = gross_temp - disc_temp
    tax_temp = net_before_tax_temp * tax_rates
    net_temp = net_before_tax_temp + tax_temp
    
    total_net = net_temp.sum()
    scale_factor = (target / total_net) if total_net > 0 else 1.0
    
    scaled_qty = np.maximum(np.round(raw_qty * scale_factor).astype(int), 1)
    gross = scaled_qty * unit_prices
    
    disc_amount = (gross * disc_pcts) + (scaled_qty * disc_fixed)
    disc_amount = np.minimum(disc_amount, gross).round(2)
    discountapplied = (disc_amount > 0.00).astype(int)

    net_before_tax = gross - disc_amount
    tax = net_before_tax * tax_rates
    net_sales = net_before_tax + tax

    channel = np.random.choice(CHANNELS, n_tr, p=[0.5, 0.3, 0.15, 0.05])
    payment = np.random.choice(PAYMENT, n_tr)
    is_online = np.isin(channel, ['Online', 'Mobile App'])

    delivery_days = np.zeros(n_tr, dtype=int)
    if is_online.any():
        delivery_days[is_online] = np.random.negative_binomial(2, 0.4, size=is_online.sum()) + 1
    delivery_days = np.clip(delivery_days, 0, 10)

    return_prob = np.where(channel == 'Online', 0.08, np.where(channel == 'Mobile App', 0.07, 0.02))
    is_return = (np.random.random(n_tr) < return_prob).astype(int)

    shipcost = np.where((is_online) & (is_return == 0), (weights * scaled_qty * 0.5).round(2), 0.0)

    return_reason_arr = np.full(n_tr, "No return", dtype=object)
    mask_ret = is_return == 1
    if mask_ret.any():
        return_reason_arr[mask_ret] = np.random.choice(RETURN_REASONS, mask_ret.sum())

    gross = np.where(is_return == 1, -gross, gross)
    net_sales = np.where(is_return == 1, -net_sales, net_sales)
    disc_amount = np.where(is_return == 1, -disc_amount, disc_amount)
    tax = np.where(is_return == 1, -tax, tax)

    store_types_for_rows = np.array([store_types_dict[s] for s in store_choices])
    hour_arr = generate_hours_vectorized(channel, store_types_for_rows)

    batch_df = pd.DataFrame({
        'salesid': np.arange(sales_id_cursor, sales_id_cursor + n_tr),
        'datekey': datekey,
        'productid': prod_choices,
        'customerid': cust_choices,
        'storeid': store_choices,
        'promoid': promo_choices,
        'qty': scaled_qty,
        'unitprice': unit_prices,
        'tax_rate': tax_rates,
        'net': net_sales,
        'payment': payment,
        'channel': channel,
        'grossvalue': gross,
        'discountamount': disc_amount,
        'taxamount': tax,
        'shipcost': shipcost,
        'isreturn': is_return,
        'shipweight': (weights * scaled_qty),
        'discountapplied': discountapplied,
        'returnreason': return_reason_arr,
        'deliverydays': delivery_days,
        'hour': hour_arr
    })

    current_buffer.append(batch_df)
    sales_id_cursor += n_tr

    if sum(len(df) for df in current_buffer) >= CHUNK_SIZE:
        combined_batch = pd.concat(current_buffer)
        combined_batch.to_csv(f_path, mode='a', header=False, index=False, quoting=csv.QUOTE_MINIMAL, float_format='%.2f')
        current_buffer.clear()
        print(f"Progress: {sales_id_cursor-1:,} / {N_SALES:,} rows generated...")

if current_buffer:
    combined_batch = pd.concat(current_buffer)
    combined_batch.to_csv(f_path, mode='a', header=False, index=False, quoting=csv.QUOTE_MINIMAL, float_format='%.2f')

print(f"\nAll files created successfully under {OUTPUT_DIR}.")