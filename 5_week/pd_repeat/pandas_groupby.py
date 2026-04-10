import pandas as pd
import numpy as np

df = pd.DataFrame({"key1": ["a", "a", None, "b", "b", "a", None],
                   "key2": pd.Series([1, 2, 1, 2, 1, None, 1], dtype="Int64"),
                   "data1": np.random.standard_normal(7),
                   "data2": np.random.standard_normal(7)})

# to find average of data3 sorted by key1 and key2

grouped = df.groupby(['key1', 'key2'])['data2'].mean()
print(grouped)

# through each group
for name, group in df.groupby(['key1', 'key2']):
    print(f"Group: {name}")
    print(group)

dict = {name: group for name, group in df.groupby(['key1', 'key2'])}
print(dict['a', 2])

# group by columns by dictionary mapping

people = pd.DataFrame(np.random.standard_normal((5, 5)),
                      columns=["a", "b", "c", "d", "e"],
                      index=["Joe", "Steve", "Wanda", "Jill", "Trey"])

people.iloc[2:3, [1,2]] = np.nan  # introduce NaN values

mapping = {"a": "red", "b": "red", "c": "blue", "d": "blue", "e": "red", 'f': 'orange'} # f is not in people columns but...

by_column = people.groupby(mapping, axis=1) # or axis='columns'
print(by_column.sum())

# --------------------------------------------------------------------

# group by OWN function

grouped = df.groupby('key1') # group by key1 column
print(grouped)

def max_minus_min(argument):
    return argument.max() - argument.min()

aggregated_data = grouped.agg(max_minus_min)
print(aggregated_data)

# --------------------------------------------------------------------

tips = pd.read_csv('tips.csv')
tips['tip_pct'] = tips['tip'] / (tips['total_bill'] - tips['tip'])

grouped = tips.groupby(['day', 'smoker'], as_index=False) # separate by day and smoker status | as_index=False to keep group keys as columns, not index
print(grouped['tip_pct'].mean()) # average tip percentage by day and smoker status

grouped_pct = grouped['tip_pct']
print(grouped_pct.agg(['mean', 'std', max_minus_min]))

# several functions at once for multiple columns
functions = ['count', 'mean', 'max']
result = grouped[['tip_pct', 'total_bill']].agg(functions)
print(result)

# different functions for different columns
grouped.agg({"tip" : ["min", "max", "mean", "std"], "size" : "sum"})

# --------------------------------------------------------------------

# sep by cuts and qcuts

frame = pd.DataFrame({"data1": np.random.standard_normal(1000),
                      "data2": np.random.standard_normal(1000)})

quartiles = pd.cut(frame['data1'], 4) # sep data1 into 4 equal-width bins (DATA 111111, NO 2)

grouped = frame.groupby(quartiles)
print(grouped.agg(['count', 'min', 'max']))

quartiles_q = pd.qcut(frame['data2'], 4) # sep data1 into 4 equal-width bins (DATA 111111, NO 2)

grouped_q = frame.groupby(quartiles_q)
print(grouped_q.agg(['count', 'min', 'max']))

# вопрос: если при группировке groupby не указан столбец, то все идет по индексу? ответ: да, по индексу

# --------------------------------------------------------------------

# example of групповое взвешенное среднее и корреляция (SEPARATE - APPLY - COMBINE)

df = pd.DataFrame({'category': ['a', 'a', 'a', 'b', 'b', 'b'],
                   'data': np.random.standard_normal(6),
                   'weights': np.random.uniform(size=6)})

print(df)

def weighted_mean(group):
    group_weighted_avg = np.average(group['data'], weights=group['weights'])
    return group_weighted_avg

grouped = df.groupby('category') # SEPARATE

print(grouped.apply(weighted_mean)) # APPLY

# --------------------------------------------------------------------

# groupby and not apply but transform

df = pd.DataFrame({'key': ['a', 'b', 'c'] * 4,
                   'value': np.arange(12.)})

print(df)

g = df.groupby('key')['value']
print(g)

def get_mean(group):
    return group.mean()

g.transform(get_mean) # get series of means for each element in the group grouped by 'key'
g.transform('mean')
