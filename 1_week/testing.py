print('Hello, World!')

print(input('What is your name? '))

mydict = {'слива':5, 'папайя':6, 'лук':56, 'маракуйя':78, 'ежевика':45}

# sortting using lambda func

sort_my_dict = dict(sorted(mydict.items(), key=lambda item: len(item[0])))

print(sort_my_dict)

# mapping using lambda func

mylist = [1, 2, 3, 4, 5]
squared_list = list(map(lambda x: x**2, mylist))
print(squared_list) # map works as follows: it takes a function and an iterable, applies the function to each item in the iterable, and returns a map object (which is an iterator). In this case, we are using a lambda function to square each element in the list `mylist`. The result is then converted to a list using the `list()` function.

# filtering using lambda func

mylist = [1, 2, 3, 4, 5]
even_numbers = list(filter(lambda x: x % 2 == 0, mylist))
print(even_numbers) # filter works similarly to map, but instead of applying a function to

lst = ['ролл', 'яблоко', 'книга', 'шар', 'ноутбук']

with_a = list(filter(lambda x: 'а' in x, lst))
print(with_a) # This code filters the list `lst` to include only those items that contain the letter 'а'.

