# ═══════════════════════════════════════════════════════════════
# ТЕМА 5: Dunder (магические) методы
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   Dunder (double underscore) методы — специальные методы Python.
#   Позволяют классам работать как встроенные типы.
#
#   Строки:
#   __str__(self)    → str(obj), print(obj)      — для пользователя
#   __repr__(self)   → repr(obj), в консоли      — для разработчика (отладка)
#
#   Контейнер:
#   __len__(self)          → len(obj)
#   __getitem__(self, key) → obj[key]
#   __setitem__(self, key, val) → obj[key] = val
#   __contains__(self, item)    → item in obj
#   __iter__(self)         → for x in obj
#
#   Операторы:
#   __add__(self, other)   → obj + other
#   __sub__(self, other)   → obj - other
#   __mul__(self, other)   → obj * other
#   __eq__(self, other)    → obj == other
#   __lt__(self, other)    → obj < other
#   __hash__(self)         → hash(obj), нужен если определён __eq__
#
#   Вызов как функция:
#   __call__(self, ...)    → obj(...)
#
#   Контекстный менеджер:
#   __enter__(self)        → with obj as x:
#   __exit__(self, exc_type, exc_val, exc_tb)
#
# ───────────────────────────────────────────────────────────────
# ПРИМЕР 1: Vector2D — математические операторы
# ───────────────────────────────────────────────────────────────


class Vector2D:
    """Двумерный вектор с перегрузкой операторов."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Vector2D({self.x}, {self.y})"

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __add__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2D":
        """Умножение на скаляр: v * 3"""
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector2D":
        """Умножение с обратным порядком: 3 * v"""
        return self.__mul__(scalar)

    def __abs__(self) -> float:
        """Модуль вектора: abs(v)"""
        return (self.x**2 + self.y**2) ** 0.5

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2D):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def dot(self, other: "Vector2D") -> float:
        """Скалярное произведение."""
        return self.x * other.x + self.y * other.y


v1 = Vector2D(3, 4)
v2 = Vector2D(1, 2)

print(f"v1 = {v1}")
print(f"repr: {repr(v1)}")
print(f"v1 + v2 = {v1 + v2}")
print(f"v1 - v2 = {v1 - v2}")
print(f"v1 * 2 = {v1 * 2}")
print(f"3 * v1 = {3 * v1}")
print(f"|v1| = {abs(v1)}")
print(f"v1 == v2: {v1 == v2}")
print(f"v1 == Vector2D(3, 4): {v1 == Vector2D(3, 4)}")

# Можно хранить в set благодаря __hash__
vectors = {v1, v2, Vector2D(3, 4)}
print(f"Уникальных векторов: {len(vectors)}")


# ───────────────────────────────────────────────────────────────
# ПРИМЕР 2: PeakCollection — контейнер
# ───────────────────────────────────────────────────────────────

class PeakCollection:
    """Коллекция хроматографических пиков."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._peaks: list[float] = []

    def add(self, peak: float) -> None:
        if peak > 0:
            self._peaks.append(peak)

    def __len__(self) -> int:
        return len(self._peaks)

    def __getitem__(self, index: int) -> float:
        return self._peaks[index]

    def __contains__(self, value: float) -> bool:
        return value in self._peaks

    def __iter__(self):
        return iter(self._peaks)

    def __repr__(self) -> str:
        return f"PeakCollection('{self.name}', peaks={self._peaks})"

    def __add__(self, other: "PeakCollection") -> "PeakCollection":
        """Объединение двух коллекций."""
        merged = PeakCollection(f"{self.name}+{other.name}")
        merged._peaks = self._peaks + other._peaks
        return merged


pc = PeakCollection("Образец А")
for p in [12.5, 87.3, 34.1, 65.0, 22.8]:
    pc.add(p)

print(f"\nКоллекция: {repr(pc)}")
print(f"Длина: {len(pc)}")
print(f"Первый пик: {pc[0]}")
print(f"87.3 в коллекции? {87.3 in pc}")
print(f"Все пики > 30: {[p for p in pc if p > 30]}")

pc2 = PeakCollection("Образец Б")
pc2.add(45.0)
pc2.add(19.1)
merged = pc + pc2
print(f"Объединено: {repr(merged)}")


# ───────────────────────────────────────────────────────────────
# ПРИМЕР 3: контекстный менеджер
# ───────────────────────────────────────────────────────────────

class InstrumentSession:
    """Сессия работы с прибором — контекстный менеджер."""

    def __init__(self, instrument_name: str) -> None:
        self.instrument_name = instrument_name

    def __enter__(self) -> "InstrumentSession":
        print(f"[{self.instrument_name}] Открываем соединение...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        print(f"[{self.instrument_name}] Закрываем соединение.")
        if exc_type:
            print(f"  Ошибка в сессии: {exc_val}")
        return False  # не подавляем исключения

    def run_sample(self, sample_id: str) -> float:
        import random
        result = round(random.uniform(1.0, 100.0), 2)
        print(f"  Образец {sample_id}: {result} mAU")
        return result


print("\n─── Контекстный менеджер ───")
with InstrumentSession("HPLC-1") as session:
    session.run_sample("S001")
    session.run_sample("S002")


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 1: Класс Matrix (2×2)
# ───────────────────────────────────────────────────────────────
# Создай класс Matrix для матриц 2×2:
#   __init__(self, data: list[list[float]])  — data это [[a,b],[c,d]]
#   __repr__  — красивый вывод матрицы
#   __add__   — сложение матриц
#   __mul__   — матричное умножение (не поэлементное!)
#   __eq__    — сравнение
#   __getitem__(self, key: tuple) → matrix[0, 1] (строка, столбец)
#
# Пример:
#   m1 = Matrix([[1, 2], [3, 4]])
#   m2 = Matrix([[5, 6], [7, 8]])
#   print(m1 + m2)    # [[6, 8], [10, 12]]
#   print(m1 * m2)    # [[19, 22], [43, 50]]
#   print(m1[0, 1])   # 2

class Matrix:
    """Матрица 2×2 с перегрузкой операторов."""

    def __init__(self, data: list[list[float]]) -> None:
        self.data = data  # [[a, b], [c, d]]

    def __repr__(self) -> str:
        a, b = self.data[0]
        c, d = self.data[1]
        return f"[[{a}, {b}], [{c}, {d}]]"

    def __add__(self, other: "Matrix") -> "Matrix":
        if isinstance(other, Matrix):
            return Matrix([
                [self.data[i][j] + other.data[i][j] for j in range(2)]
                for i in range(2)
            ])
        return NotImplemented

    def __mul__(self, other: "Matrix") -> "Matrix":
        if isinstance(other, Matrix):
            a, b = self.data[0]
            c, d = self.data[1]
            e, f = other.data[0]
            g, h = other.data[1]
            return Matrix([
                [a*e + b*g, a*f + b*h],
                [c*e + d*g, c*f + d*h],
            ])
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        return self.data == other.data

    def __getitem__(self, key: tuple) -> float:
        row, col = key
        return self.data[row][col]

#example
m1 = Matrix([[1, 2], [3, 4]])
m2 = Matrix([[5, 6], [7, 8]])
print(m1 + m2)    # [[6, 8], [10, 12]]
print(m1 * m2)    # [[19, 22], [43, 50]]
print(m1[0, 1])   # 2   

# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 2: Класс PriceHistory (контейнер временного ряда)
# ───────────────────────────────────────────────────────────────
# Создай класс PriceHistory (история цен инструмента):
#   __init__(self, ticker: str, prices: list[float] = None)
#
#   __repr__  — "PriceHistory('AAPL', n=252, last=182.50)"
#   __len__   — количество значений
#   __getitem__(self, key)  — поддержка индекса И среза:
#       history[0], history[-1], history[-5:]  (возвращает список для среза)
#   __iter__  — итерация по ценам
#   __contains__(self, price: float) -> bool  — price in history
#   __add__(self, other: "PriceHistory") -> "PriceHistory"
#       — объединение двух историй (для merge данных)
#
#   Метод returns() -> list[float]
#       — дневная доходность: [(p[i]-p[i-1])/p[i-1] for i in range(1, n)]
#   Метод max_drawdown() -> float
#       — максимальная просадка (peak - trough) / peak
#
# Пример:
#   h = PriceHistory("AAPL", [100, 110, 105, 120, 115])
#   print(len(h))        # 5
#   print(h[-2:])        # [120, 115]
#   print(h.returns())   # [0.1, -0.045, 0.143, -0.042]

# >>> ПИШИ ЗДЕСЬ <<<


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 3: Итератор PriceLadder
# ───────────────────────────────────────────────────────────────
# Создай класс PriceLadder(high: float, low: float, step: float):
#   — итерирует уровни цен от high вниз до low с заданным шагом
#   __iter__(self) → self
#   __next__(self) → следующий уровень
#   При исчерпании → raise StopIteration
#
# Должен работать в for-цикле:
#   for level in PriceLadder(100.0, 95.0, 1.0):
#       print(level)   # 100.0, 99.0, 98.0, 97.0, 96.0, 95.0
#
# Применение: перебор ценовых уровней поддержки/сопротивления.

# >>> ПИШИ ЗДЕСЬ <<<
