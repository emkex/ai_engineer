import pandas as pd
import numpy as np

string_data = pd.Series(["aardvark", np.nan, None, "avocado"])

# example of dropna
cleaned = string_data.dropna()
print(cleaned)

# example of fillna
filled = string_data.fillna(0)
print(filled)

# example of isna
mask = string_data.isna()
print(mask)

# example of ffill
string_data = pd.Series(["aardvark", np.nan, None, "avocado"])
filled_ffill = string_data.fillna(method="ffill")
print(filled_ffill)

df = pd.DataFrame(np.random.standard_normal((7, 3)))
df.iloc[:4, 1] = np.nan
df.iloc[:2, 2] = np.nan

print(df)
# df_purified = df.dropna() # leaves only rows without any NaN values
# print(df_purified)

df_pur_2 = df.dropna(thresh=2) # leaves only columns with at least 2 non-NaN values
print(df_pur_2)

# df_pur_3 = df.dropna(thresh=3) # leaves only columns with at least 3 non-NaN values
# print(df_pur_3)

print(df)
df.loc[:, 1] = df.loc[:, 1].fillna(df[0].max())
print(df)

data = pd.DataFrame({"food": ["bacon", "pulled pork", "bacon","pastrami", "corned beef", "bacon","pastrami", "honey ham", "nova lox"],"ounces": [4, 3, 12, 6, 7.5, 8, 3, 5, 6]})
print(data)

meat_to_animal = {"bacon": "pig","pulled pork": "pig","pastrami": "cow","corned beef": "cow","honey ham": "pig","nova lox": "salmon"}

data['from_animal'] = data['food'].map(meat_to_animal)
print(data)

print(data['ounces'].replace([4, 3], np.nan))
print(data['ounces'].replace({4: np.nan, 3: 0}))
print(data)

data.rename(columns={"food": "type_of_food", "ounces": "weight_in_ounces"}, inplace=True)
print(data)

data = np.random.uniform(size=40)
a = pd.cut(data, 4, precision=2, right=False)
print(a, '\n')
print(a.value_counts(), '\n')

bins = [0, 0.25, 1]
quarters = ['quater', 'rest']
b = pd.cut(data, bins=bins, labels=quarters)
print(b)
# print(pd.value_counts(b))
print(b.value_counts())

# pandas.qcut - quantile-based discretization function

data = pd.DataFrame(np.random.standard_normal((1000, 4)))

col = data[2]
print(col[col.abs() > 3])

print(data[(data.abs() > 3).any(axis=1)]) # if I dont use .any, it will be just a mask for numbers (not axis) with True/False values or NaN

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

print('--------------------------------------------------')

pd_data_qcut = pd.qcut(values, q=bins, labels=labels)
dummies_qcut = pd.get_dummies(data=pd_data_qcut, prefix='Dummi').astype(int)
print(pd_data_qcut.value_counts())
print(dummies_qcut)

bins = pd.Series(pd_data_cut, name='cut_quartiles')
results = pd.Series(values).groupby(bins).agg(['count', 'min', 'max']).reset_index()
print(results)

bins = pd.Series(pd_data_qcut, name='qcut_quartiles')
results = pd.Series(values).groupby(bins).agg(['count', 'min', 'max']).reset_index()
print(results)


