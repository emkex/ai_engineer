import pandas as pd
import numpy as np

'''
Работа с категориальными данными (pandas.Categorical) — для повторяющихся значений: экономит память (строки → коды + словарь), ускоряет groupby, merge, sort.
Алгоритм:
Создать: pd.Categorical(values) или series.astype('category') или pd.Categorical.from_codes(codes, categories).
Просмотр: cat.array.categories (список категорий), cat.array.codes (коды).
Модификация (на копии): cat.set_categories(new_cats) — изменить словарь; cat.remove_unused_categories() — убрать неиспользуемые; cat.rename_categories(new_names) — переименовать.
Биннинг: pd.cut(data, bins, labels) — по фиксированным границам; pd.qcut(data, q, labels) — по квантилям (равные группы).
One-hot: pd.get_dummies(data, prefix='prefix', dtype=int) — для ML, превращает категории в 0/1 столбцы.
Аггрегация: series.groupby(categorical).agg(['mean', 'std']) — статистика по группам.
'''

# Operations for handling missing data | categorical variables to dummy/indicator variables (matrix)
# Unitary code for categorical methods
# example of get_dummies
df = pd.DataFrame({"key": ["b", "b", "a", "c", "a", "b"],
                   "data1": range(6)})
print(df)

dummies = pd.get_dummies(df['key'], prefix='key').astype(int)
print(dummies)

df_with_dummies = df[['data1']].join(dummies)
print(df_with_dummies)

# one more example
np.random.seed(12345)
values = np.random.uniform(size=1000)

bins = [0, 0.25, 0.5, 0.75, 1.0]
labels = ['Q1', 'Q2', 'Q3', 'Q4']

pd_data_cut = pd.cut(values, bins=bins, labels=labels)
dummies_cut = pd.get_dummies(data=pd_data_cut, prefix='Dummi').astype(int)
print(pd_data_cut.value_counts())
print(dummies_cut)

pd_data_qcut = pd.qcut(values, q=bins, labels=labels)
dummies_qcut = pd.get_dummies(data=pd_data_qcut, prefix='Dummi').astype(int)
print(pd_data_qcut.value_counts())
print(dummies_qcut)

# ------------------ Categorical data ------------------
values = pd.Series([0, 1, 0, 0] * 2) # order | how to store info
dim = pd.Series(['apple', 'orange']) # data | how to represent info
print(values)
print(dim)

# data (or dataframe) TAKE order
a = dim.take(values)
print(a) # initial object | how to represent initial info

# example

fruits = ['apple', 'orange', 'apple', 'apple'] * 2
N = len(fruits)
rng = np.random.default_rng(12345)

df = pd.DataFrame({
    'fruit': fruits,
    'basket_id': np.arange(N),
    'count': rng.integers(3, 15, size=N),
    'weight': rng.uniform(0, 4, size=N)
},
    columns=['basket_id', 'fruit', 'count', 'weight'])

fruit_cat_data = df['fruit'].astype('category')

print(fruit_cat_data)
print(fruit_cat_data.array.categories)
print(fruit_cat_data.array.codes)

print('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm\n')
print(fruit_cat_data.cat.categories)
print(fruit_cat_data.cat.codes)

actual_categories = ['apple', 'orange', 'banana']
fruit_cat_data_2 = fruit_cat_data.cat.set_categories(actual_categories)
print(fruit_cat_data_2)
print(fruit_cat_data.value_counts())
print(fruit_cat_data_2.value_counts())

cat_s3 = fruit_cat_data_2[fruit_cat_data_2.isin(['apple', 'orange'])] # same as fruit_cat_data_2[(fruit_cat_data_2 == 'apple') | (fruit_cat_data_2 == 'orange')]
print(cat_s3.cat.remove_unused_categories()) # work with copy | original remains unchanged
print(cat_s3.cat.rename_categories(['banana', 'kiwi', 'grape'])) # work with copy | original remains unchanged
print(cat_s3) # proof that original remains unchanged
print('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm\n')

categories = ['foo', 'bar', 'baz']
codes = [0, 1, 2, 0, 0, 1]

my_cats_2 = pd.Categorical.from_codes(codes, categories)
print(my_cats_2)

rng = np.random.default_rng(seed=12345)
draws = rng.standard_normal(1000)

bins = pd.qcut(draws, 4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
print(bins)

print(bins.codes)

bins = pd.Series(bins, name='quartile')
print(bins)

results = pd.Series(draws).groupby(bins).agg(['count', 'min', 'max']).reset_index() # .agg is a function to apply multiple aggregation functions | .reset_index() to turn index 'quartiles' into a column
print(results)

# so from 2 series (what to distribute - draws - and by which groups - .groupby(bins)) we created a dataframe with statistics based on quartiles