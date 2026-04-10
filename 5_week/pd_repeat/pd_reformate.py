import pandas as pd
import numpy as np

data = pd.Series(np.random.uniform(size=9), index=[["a", "a", "a", "b", "b", "c", "c", "d", "d"], [1, 2, 3, 1, 3, 1, 2, 2, 3]])

print(data)

data.unstack()
print(data.unstack())
print((data.unstack()).stack())

# ---------------------------------------------------------------

df1 = pd.DataFrame({"key": ["b", "b", "a", "c", "a", "a", "b"], "data1": pd.Series(range(7), dtype="Int64")})
df2 = pd.DataFrame({"key": ["a", "b", "d"], "data2": pd.Series(range(3), dtype="Int64")})

merged = pd.merge(df1, df2, on='key') # join df2 to df1 by argument 'on'
print(merged)

merged_outer = pd.merge(df1, df2, how='outer', on='key') # outer join, with different keys
print(merged_outer)

# if df2 contains multiple matches for the same key values in df1, the result will be the cartesian product of the matches
df3 = pd.DataFrame({"key": ["a", "b", "b", 'd'], "data2": pd.Series(range(4), dtype="Int64")})
merged_multiple = pd.merge(df1, df3, on='key')
print(merged_multiple)

df1 = pd.DataFrame(np.arange(6).reshape(3, 2), index=["a", "b", "c"],
columns=["one", "two"])
df2 = pd.DataFrame(5 + np.arange(4).reshape(2, 2), index=["a", "c"],
columns=["three", "four"])

print(df1.join([df2], how='outer')) # join df2 to df1 by index

print(pd.concat([df1, df2], axis=0)) # concatenate along rows
print(pd.concat([df1, df2], axis=1)) # concatenate along columns (by index)

df1 = pd.DataFrame(np.random.standard_normal((3, 4)),
columns=["a", "b", "c", "d"])
df2 = pd.DataFrame(np.random.standard_normal((2, 3)),
columns=["b", "d", "a"])

print(df1,'\n',df2)

print(pd.concat([df1, df2])) # concatenate and ignore index, sort columns
print(pd.concat([df1, df2], ignore_index=True)) # concatenate and ignore index, sort columns
print(pd.concat([df1, df2], keys=['one', 'two'])) # concatenate and name dfs' indices

# Forms, rotations | pivot, melt

wide_data = pd.read_csv('macrodata.csv')
print(wide_data.head())

periods = pd.PeriodIndex(year=wide_data.pop("year"),quarter=wide_data.pop("quarter"),name="date")
wide_data.index = periods.to_timestamp("D")
print(wide_data.head())

wide_data.columns.name = "item"
print(wide_data)

long_data_from_wide = wide_data.stack().reset_index().rename(columns={0:"value"}) # from wide to long | WITHOUT melt
print(long_data_from_wide)

wide_data_from_long = long_data_from_wide.pivot(index='date', columns='item', values='value') # from long to wide | WITH pivot
print(wide_data_from_long)

wide_data_from_long = wide_data_from_long.reset_index()
long_data_from_wide = pd.melt(frame=wide_data_from_long, id_vars='date')
print(long_data_from_wide)





