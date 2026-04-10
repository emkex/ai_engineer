import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import matplotlib.pyplot as plt

# # Пример данных: y = 2 + 3*x + шум (линейная зависимость)
# np.random.seed(42)
# x = np.linspace(0, 10, 50)
# y = 2 + 3 * x + np.random.normal(0, 5, 50)  # Добавляем шум
# data = pd.DataFrame({'x': x, 'y': y})
#
# # 1. Линейная модель: y ~ x (Patsy формула)
# y_patsy, X_patsy = patsy.dmatrices('y ~ x', data=data, return_type='dataframe')
# model_lin = sm.OLS(y_patsy, X_patsy).fit()  # МНК (OLS) через statsmodels
#
# # Коэффициенты
# print("Коэффициенты линейной модели (from statsmodel):")
# print(model_lin.params)  # Intercept ≈2, x≈3 (ожидаемо)
#
# # Метрики
# rss = model_lin.ssr  # RSS = сумма квадратов остатков
# tss = np.sum((y - np.mean(y))**2)  # TSS = общий разброс от среднего
# ess = tss - rss  # ESS = объяснённый разброс
# r2 = model_lin.rsquared  # R² от statsmodels
# print(f"RSS: {rss:.2f}, TSS: {tss:.2f}, ESS: {ess:.2f}, R²: {r2:.4f}")
#
# # График: данные + тренд-линия (МНК)
# plt.scatter(data['x'], data['y'], label='Данные')
# y_pred = model_lin.predict(X_patsy)  # Предсказания
# plt.plot(data['x'], y_pred, color='red', label='МНК тренд (линейный)')
# plt.xlabel('x')
# plt.ylabel('y')
# plt.legend()
# plt.title('Линейная регрессия с МНК')
# plt.show()
#
# # 2. Полиномиальная модель: y ~ x + I(x**2) (не только линейная)
# # I() для математических операций в формуле Patsy
# y_poly, X_poly = patsy.dmatrices('y ~ x + I(x**2)', data=data, return_type='dataframe')
# model_poly = sm.OLS(y_poly, X_poly).fit()  # МНК на полиноме степени 2
#
# # Коэффициенты
# print("Коэффициенты полиномиальной модели (from statsmodel):")
# print(model_poly.params)  # Intercept, x, x²
#
# # Метрики (аналогично)
# rss_poly = model_poly.ssr
# tss_poly = np.sum((y - np.mean(y))**2)  # TSS то же
# ess_poly = tss_poly - rss_poly
# r2_poly = model_poly.rsquared
# print(f"RSS: {rss_poly:.2f}, TSS: {tss_poly:.2f}, ESS: {ess_poly:.2f}, R²: {r2_poly:.4f}")
#
# # График: данные + полиномиальный тренд
# plt.scatter(data['x'], data['y'], label='Данные')
# y_pred_poly = model_poly.predict(X_poly)
# plt.plot(data['x'], y_pred_poly, color='green', label='МНК тренд (полином 2 степени)')
# plt.xlabel('x')
# plt.ylabel('y')
# plt.legend()
# plt.title('Полиномиальная регрессия с МНК')
# plt.show()

# -------------------------------------------

# # Генерация данных: y = 2 + 3*x + 1.5*x2 + шум
# np.random.seed(42)
# n = 50
# x = np.linspace(0, 10, n)
# x2 = np.linspace(-5, 5, n) + np.random.normal(0, 1, n)  # второй регрессор с шумом
# y = 2 + 3 * x + 1.5 * x2 + np.random.normal(0, 5, n)
# data = pd.DataFrame({'x': x, 'x2': x2, 'y': y})
#
# # 1. Множественная линейная модель: y ~ x + x2
# y_lin, X_lin = patsy.dmatrices('y ~ x + x2', data=data, return_type='dataframe')
# model_lin = sm.OLS(y_lin, X_lin).fit()
#
# print("Коэффициенты множественной линейной модели:")
# print(model_lin.params)          # Intercept ≈2, x≈3, x2≈1.5
#
# # Метрики
# rss = model_lin.ssr
# tss = np.sum((y - np.mean(y))**2)
# ess = tss - rss
# r2 = model_lin.rsquared
# print(f"RSS: {rss:.2f}, TSS: {tss:.2f}, ESS: {ess:.2f}, R²: {r2:.4f}")
#
# # График: данные vs предсказания (3D не нужен, просто scatter y vs y_pred)
# plt.scatter(model_lin.fittedvalues, data['y'], label='Данные vs предсказания')
# plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', label='Идеальная линия')
# plt.xlabel('Предсказанные значения ŷ')
# plt.ylabel('Реальные значения y')
# plt.title('Множественная линейная регрессия: y ~ x + x2')
# plt.legend()
# plt.show()
#
# # 2. Полиномиальная модель с двумя переменными: y ~ x + x2 + I(x**2)
# y_poly, X_poly = patsy.dmatrices('y ~ x + x2 + I(x**2)', data=data, return_type='dataframe')
# model_poly = sm.OLS(y_poly, X_poly).fit()
#
# print("Коэффициенты полиномиальной модели:")
# print(model_poly.params)
#
# # Метрики полиномиальной
# rss_poly = model_poly.ssr
# ess_poly = tss - rss_poly  # TSS тот же
# r2_poly = model_poly.rsquared
# print(f"Полином: RSS: {rss_poly:.2f}, ESS: {ess_poly:.2f}, R²: {r2_poly:.4f}")

# --------------------------------------------------------

# # ПРИМЕР С ТРАНСФОРМАЦИЕЙ РЕГРЕССОРОВ
#
# # --- Генерация данных (train set): y = 0.05 + 0.1*x1 + 0.000001*x2 + шум
# # x1 (волатильность): 0-1, x2 (объём торгов): большие числа ~1e6-1e7
# np.random.seed(42)
# n = 50
# x1 = np.random.uniform(0, 1, n)  # Волатильность (малый масштаб)
# x2 = np.random.uniform(1e6, 1e7, n)  # Объём торгов (большой масштаб)
# y = 0.05 + 0.1 * x1 + 0.000001 * x2 + np.random.normal(0, 0.01, n)  # Доходность акции
# train_data = pd.DataFrame({'x1': x1, 'x2': x2, 'y': y})
#
# # --- Модель с трансформациями: y ~ standardize(x1) + center(x2)
# # standardize нормализует x1 (среднее 0, std 1) — помогает, когда масштабы разные (x1 малый, x2 большой)
# # example of standardize: (x - mean) / std ||| 1 2 3 4 5 -> mean=3, std=1.58 -> standardized: [-1.26, -0.63, 0, 0.63, 1.26]
# # center центрирует x2 (среднее 0) — Intercept становится средним y (базовая доходность без влияния x's)
# # example of center: x - mean ||| 10 20 30 40 50 -> mean=30 -> centered: [-20, -10, 0, 10, 20]
# y_train, X_train = patsy.dmatrices('y ~ standardize(x1) + center(x2)', data=train_data, return_type='dataframe')
# model = sm.OLS(y_train, X_train).fit()  # МНК (OLS)
#
# # --- Вывод коэффициентов
# print("Коэффициенты модели (Intercept — базовая доходность, standardize(x1) — эффект нормализованной волатильности, center(x2) — эффект центрированного объёма):")
# print(model.params)
#
# # --- Метрики (RSS — необъяснённый разброс, TSS — общий разброс, ESS — объяснённый, R² — доля объяснённого)
# rss = model.ssr  # Сумма квадратов остатков (необъяснённая часть)
# tss = np.sum((y - np.mean(y))**2)  # Общая сумма квадратов (полный разброс от среднего y)
# ess = tss - rss  # Объяснённая сумма квадратов (часть, которую модель учла)
# r2 = model.rsquared  # R² = ESS/TSS (0-1, чем выше — тем лучше модель объясняет данные)
# print(f"RSS (необъяснённый разброс): {rss:.4f}")
# print(f"TSS (общий разброс): {tss:.4f}")
# print(f"ESS (объяснённый разброс): {ess:.4f}")
# print(f"R² (доля объяснённого): {r2:.4f}")
#
# # --- График: реальные vs предсказанные y (для проверки качества модели)
# y_pred = model.predict(X_train)
# plt.scatter(y_pred, y, label='Данные vs предсказания')
# plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', label='Идеальная линия')
# plt.xlabel('Предсказанные значения ŷ')
# plt.ylabel('Реальные значения y')
# plt.title('Множественная регрессия: y ~ standardize(x1) + center(x2)')
# plt.legend()
# plt.show()
#
# # --- Новые данные (test set): генерируем похожие, но новые
# new_x1 = np.random.uniform(0, 1, 10)
# new_x2 = np.random.uniform(1e6, 1e7, 10)
# new_y = 0.05 + 0.1 * new_x1 + 0.000001 * new_x2 + np.random.normal(0, 0.01, 10)  # Для проверки
# new_data = pd.DataFrame({'x1': new_x1, 'x2': new_x2, 'y': new_y})
#
# # --- Применяем те же трансформации к новым данным (используем design_info от train, чтобы mean/std были из исходных данных — избегаем leakage)
# new_X = patsy.build_design_matrices([X_train.design_info], new_data, NA_action='raise')[0]  # build_design_matrices применяет standardize/center от train
#
# # --- Предсказания на новых данных
# new_y_pred = model.predict(new_X)
#
# print("Предсказанные y для новых данных:")
# print(new_y_pred)
#
# # --- График для новых данных: реальные vs предсказанные
# plt.scatter(new_y_pred, new_y, label='Новые данные vs предсказания')
# plt.plot([new_y.min(), new_y.max()], [new_y.min(), new_y.max()], 'r--', label='Идеальная линия')
# plt.xlabel('Предсказанные значения ŷ (на новых данных)')
# plt.ylabel('Реальные значения y (новые)')
# plt.title('Предсказания на новых данных с трансформациями из train')
# plt.legend()
# plt.show()

# -----------------------------------------------------

# --- Генерация train данных: y = 0.05 + 0.1*x1 + 0.000001*x2 + шум
# x1 (волатильность): 0-1 (малый масштаб), x2 (объём торгов): 1e6-1e7 (большой масштаб)
np.random.seed(42)
n = 50
x1 = np.random.uniform(0, 1, n)  # Волатильность
x2 = np.random.uniform(1e6, 1e7, n)  # Объём торгов
y = 0.05 + 0.1 * x1 + 0.000001 * x2 + np.random.normal(0, 0.01, n)  # Доходность акции
train_data = pd.DataFrame({'x1': x1, 'x2': x2, 'y': y})

# --- Модель без трансформаций: y ~ x1 + x2 (для сравнения, коэффициенты для исходных переменных)
y_orig, X_orig = patsy.dmatrices('y ~ x1 + x2', data=train_data, return_type='dataframe')
print(y_orig, X_orig)
model_orig = sm.OLS(y_orig, X_orig).fit()  # МНК на исходных данных

print("Коэффициенты модели без трансформаций (для исходных x1/x2):")
print(model_orig.params)  # Intercept ≈0.05, x1≈0.1, x2≈0.000001 (ожидаемо, но x2 доминирует по масштабу)

# --- Метрики для модели без трансформаций
rss_orig = model_orig.ssr  # Сумма квадратов остатков (необъяснённый разброс)
tss = np.sum((y - np.mean(y))**2)  # Общая сумма квадратов (полный разброс от среднего y; то же для всех моделей)
ess_orig = tss - rss_orig  # Объяснённая сумма квадратов
r2_orig = model_orig.rsquared  # R² = ESS/TSS
print(f"Без трансформаций: RSS: {rss_orig:.4f}, TSS: {tss:.4f}, ESS: {ess_orig:.4f}, R²: {r2_orig:.4f}")

# --- Модель с трансформациями: y ~ standardize(x1) + center(x2) (коэффициенты для трансформированных x)
y_trans, X_trans = patsy.dmatrices('y ~ standardize(x1) + center(x2)', data=train_data, return_type='dataframe')
model_trans = sm.OLS(y_trans, X_trans).fit()  # МНК на трансформированных данных

print("\nКоэффициенты модели с трансформациями (для standardize(x1)/center(x2)):")
print(model_trans.params)  # Intercept ≈ mean(y), standardize(x1) — эффект на 1 std x1, center(x2) — эффект на 1 единицу x2 (не меняет β)

# --- Метрики для модели с трансформациями (метрики те же, что без, т.к. трансформации линейные и не меняют fit)
rss_trans = model_trans.ssr
ess_trans = tss - rss_trans
r2_trans = model_trans.rsquared
print(f"С трансформациями: RSS: {rss_trans:.4f}, ESS: {ess_trans:.4f}, R²: {r2_trans:.4f} (метрики совпадают с моделью без трансформаций)")

# --- Пересчёт коэффициентов к исходным переменным (из трансформированной модели)
mean_x1 = train_data['x1'].mean()
std_x1 = train_data['x1'].std()
mean_x2 = train_data['x2'].mean()

beta_x1_orig = model_trans.params['standardize(x1)'] / std_x1  # β для исходного x1
beta_x2_orig = model_trans.params['center(x2)']  # β для x2 не меняется (center только сдвигает)
intercept_orig = model_trans.params['Intercept'] - beta_x1_orig * mean_x1 - beta_x2_orig * mean_x2  # Пересчёт Intercept

print("\nПересчитанные коэффициенты для исходных переменных (из модели с трансформациями):")
print(f"Intercept: {intercept_orig:.4f}, x1: {beta_x1_orig:.4f}, x2: {beta_x2_orig:.10f} (совпадают с моделью без трансформаций)")

# --- График: реальные vs предсказанные y для модели без трансформаций
y_pred_orig = model_orig.predict(X_orig)
plt.scatter(y_pred_orig, y, label='Данные vs предсказания (без трансформаций)')
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', label='Идеальная линия')
plt.xlabel('Предсказанные ŷ')
plt.ylabel('Реальные y')
plt.title('Модель без трансформаций: y ~ x1 + x2')
plt.legend()
plt.show()

# --- График: реальные vs предсказанные y для модели с трансформациями (предсказания те же)
y_pred_trans = model_trans.predict(X_trans)
plt.scatter(y_pred_trans, y, label='Данные vs предсказания (с трансформациями)')
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', label='Идеальная линия')
plt.xlabel('Предсказанные ŷ')
plt.ylabel('Реальные y')
plt.title('Модель с трансформациями: y ~ standardize(x1) + center(x2)')
plt.legend()
plt.show()

# --- Новые данные (test set): генерируем похожие
new_n = 10
new_x1 = np.random.uniform(0, 1, new_n)
new_x2 = np.random.uniform(1e6, 1e7, new_n)
new_y = 0.05 + 0.1 * new_x1 + 0.000001 * new_x2 + np.random.normal(0, 0.01, new_n)
new_data = pd.DataFrame({'x1': new_x1, 'x2': new_x2, 'y': new_y})

# --- Предсказания на новых данных без трансформаций (для сравнения)
new_X_orig = patsy.dmatrices('y ~ x1 + x2', data=new_data, return_type='dataframe')[1]
new_y_pred_orig = model_orig.predict(new_X_orig)

# --- Предсказания на новых данных с трансформациями (используя design_info от train для mean/std)
new_X_trans = patsy.build_design_matrices([X_trans.design_info], new_data, NA_action='raise')[0]
new_y_pred_trans = model_trans.predict(new_X_trans)

print("\nПредсказанные y для новых данных (без трансформаций):")
print(new_y_pred_orig)
print("Предсказанные y для новых данных (с трансформациями, пересчитано под исходные):")
print(new_y_pred_trans)  # Совпадают с без трансформаций

# --- График для новых данных без трансформаций: реальные vs предсказанные
plt.scatter(new_y_pred_orig, new_y, label='Новые данные vs предсказания (без трансформаций)')
plt.plot([new_y.min(), new_y.max()], [new_y.min(), new_y.max()], 'r--', label='Идеальная линия')
plt.xlabel('Предсказанные ŷ')
plt.ylabel('Реальные y (новые)')
plt.title('Предсказания на новых данных без трансформаций')
plt.legend()
plt.show()

# --- График для новых данных с трансформациями: реальные vs предсказанные
plt.scatter(new_y_pred_trans, new_y, label='Новые данные vs предсказания (с трансформациями)')
plt.plot([new_y.min(), new_y.max()], [new_y.min(), new_y.max()], 'r--', label='Идеальная линия')
plt.xlabel('Предсказанные ŷ')
plt.ylabel('Реальные y (новые)')
plt.title('Предсказания на новых данных с трансформациями из train')
plt.legend()
plt.show()