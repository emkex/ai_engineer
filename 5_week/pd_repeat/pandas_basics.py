import numpy as np
import pandas as pd

obj = pd.Series([4, 7, -5, 3], index=["d", "b", "a", "c"])
print(obj)

print(obj[["c", "a", "d"]]) # Reordering based on index labels

print(obj*2) # Original Series remains unchanged

data = {"state": ["Ohio", "Ohio", "Ohio", "Nevada", "Nevada", "Nevada"],
"year": [2000, 2001, 2002, 2001, 2002, 2003],
"pop": [1.5, 1.7, 3.6, 2.4, 2.9, 3.2]}

frame = pd.DataFrame(data)

frame = pd.DataFrame(data, columns=['year', 'state', 'pop', 'debt'])
frame['debt'] = np.arange(6)

frame['debt'] = pd.Series([1.2, 2, 3.3], index=[0, 2, 4])
print(frame) # Missing values are filled with NaN

# append

idx1 = pd.Index([1, 2, 3])
idx2 = pd.Index([4, 5, 6])
idx3 = idx1.append(idx2)
print(idx3)  # Output: Int64Index([1, 2, 3, 4, 5, 6], dtype='int64')

# difference
idx4 = pd.Index([1, 2, 3, 4, 5])
idx5 = pd.Index([4, 5])
idx6 = idx4.difference(idx5)
print(idx6)  # Output: Int64Index([1, 2, 3], dtype='int64')

# intersection
idx7 = pd.Index([1, 2, 3, 4])
idx8 = pd.Index([3, 4, 5, 6])
idx9 = idx7.intersection(idx8)
print(idx9)  # Output: Int64Index([3, 4], dtype='int64')

# delete

idx10 = pd.Index([1, 2, 3, 4, 5])
idx11 = idx10.delete(2)  # Delete element at index 2
print(idx11)  # Output: Int64Index([1, 2, 4, 5], dtype='int64')

obj3 = pd.Series(["blue", "purple", "yellow"], index=[0, 2, 4])

# ffil = interpolate missing values forward

obj3 = obj3.reindex(index=np.arange(6), method="ffill") # other args are columns,
print(obj3)

data = pd.DataFrame(np.arange(16).reshape((4, 4)),index=["Ohio", "Colorado", "Utah", "New York"],columns=["one", "two", "three", "four"])

data.drop(index=["Colorado", "Ohio"]) # drop rows | just a copy, original remains unchanged

data.drop(columns=["one", "three"]) # drop columns | just a copy, original remains unchanged
print(data)

obj = pd.Series(np.arange(4., 8.), index=["a", "b", "c", "d"])

print(obj.loc[["b", "a", "d"]]) # choose by index labels in any order, but not by position like 0 1 2 ...

print(obj.iloc[[0, 1, 2]]) # choose by position like 0 1 2 ...

data = pd.DataFrame(np.arange(16).reshape((4, 4)), index=["Ohio", "Colorado", "Utah", "New York"], columns=["one", "two", "three", "four"])

print(data[data['two'] > 6]) # filter rows based on column value
print(data[:2]) # first two rows
print(data[data < 2])

a = data.loc['Colorado', ['two', 'three']] # select by label
b = data.iloc[2, [3, 0, 1]] # select by position
c = data.loc[:"Utah", "two"] # slice rows up to 'Utah' and select 'two' column

print(a,b,c)

# loc or iloc [row selection , column selection]

df1 = pd.DataFrame(np.arange(12.).reshape((3, 4)), columns=list("abcd"))
df2 = pd.DataFrame(np.arange(20.).reshape((4, 5)), columns=list("abcde"))

print(df1,'\n',df2)

print(df1 + df2) # alignment based on row and column labels
print(df1.add(df2, fill_value=0)) # fill missing values with 0 before operation

# Functions like numpy

def f1(x):
    return x.max() - x.min()

data = pd.DataFrame(np.random.randn(5, 4), columns=list("ABCD"))
print(data)

for_each_column = data.apply(f1) # apply to each column or row by specifying axis
print(for_each_column)

print(data)
for_each_line = data.apply(f1, axis=1) # or axis='columns'
print(for_each_line)

def f2(x):
    return pd.Series([x.min(), x.max()], index=['min', 'max'])

print(data.apply(f2))

def f3(x):
    if x > 0:
        return 100
    else:
        return -100

print(data.map(f3)) # element-wise operation

aa = data.sort_values('D') # sort by column D
bb = data.sort_values(['B', 'C']) # sort by columns B and C

print(aa)
print(bb)

# rankings
ranked = data.rank() # rank values in each column
print(ranked)

ranked = data.rank(ascending=False) # rank values in descending order
print(ranked)

# ------------------------------------------------------------------------------

np.random.seed(0)

# Create a date index and tickers
dates = pd.date_range('2016-10-13', '2016-10-21')  # includes 2016-10-17..2016-10-21
tickers = ["AAPL", "GOOG", "IBM", "MSFT"]

# Simulate a simple random-walk price series for each ticker
start_prices = np.array([115.0, 770.0, 135.0, 55.0])
daily_returns = np.random.normal(loc=0.0, scale=0.01, size=(len(dates), len(tickers)))
prices = (1 + daily_returns).cumprod(axis=0) * start_prices

price = pd.DataFrame(prices, index=dates, columns=tickers)
print("price:\n", price.head(), "\n")

# Percent change (returns)
returns = price.pct_change()
print("returns.tail():\n", returns.tail(), "\n")

# Correlation and covariance between MSFT and IBM
msft_ibm_corr = returns["MSFT"].corr(returns["IBM"])
msft_ibm_cov = returns["MSFT"].cov(returns["IBM"])
print(f"MSFT-IBM correlation: {msft_ibm_corr}")
print(f"MSFT-IBM covariance: {msft_ibm_cov}\n")

# Full correlation and covariance matrices
print("Correlation matrix:\n", returns.corr(), "\n")
print("Covariance matrix:\n", returns.cov())
