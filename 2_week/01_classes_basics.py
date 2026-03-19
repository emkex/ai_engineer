# ═══════════════════════════════════════════════════════════════
# ТЕМА 1: Классы, __init__, self, методы
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   class — чертёж объекта. __init__ — конструктор, вызывается при создании.
#   self — ссылка на текущий экземпляр объекта (обязательный первый параметр).
#
#   Типы методов:
#   - instance method: принимает self, работает с данными экземпляра
#   - @classmethod: принимает cls, работает с классом (фабричные методы)
#   - @staticmethod: не принимает self/cls, вспомогательная логика
#

# Describe @classmethod and @staticmethod with examples:
#   @classmethod — метод, который работает с классом, а не с конкретным экземпляром. Обычно используется для создания альтернативных конструкторов или для доступа к классовым атрибутам.
#   @staticmethod — метод, который не зависит ни от экземпляра, ни от класса. Обычно используется для вспомогательных функций, которые логически связаны с классом, но не требуют доступа к его данным.

# то есть, классовый метод - это метод, который работает с классом, а не с конкретным экземпляром. Он принимает cls в качестве первого параметра и может использовать его для доступа к атрибутам класса или для создания новых экземпляров.
# cls - ссылка на сам класс, аналог self для экземпляра

# статический метод - это метод, который не зависит ни от экземпляра, ни от класса. Он не принимает self или cls в качестве параметров и обычно используется для вспомогательных функций, которые логически связаны с классом, но не требуют доступа к его данным.

# ───────────────────────────────────────────────────────────────
# ПРИМЕР: Класс Molecule (молекула)
# ───────────────────────────────────────────────────────────────

import random


class Molecule:
    """Молекула химического соединения."""

    count = 0  # классовый атрибут — общий для всех экземпляров

    def __init__(self, name: str, formula: str, mass: float) -> None:
        self.name = name          # название соединения
        self.formula = formula    # химическая формула
        self.mass = mass          # молярная масса (г/моль)
        Molecule.count += 1       # увеличиваем счётчик при создании

    def describe(self) -> str:
        """Возвращает описание молекулы."""
        return f"{self.name} ({self.formula}), M = {self.mass} г/моль"

    @classmethod
    def get_count(cls) -> int:
        """Сколько молекул создано."""
        return cls.count

    @staticmethod
    def is_organic(formula: str) -> bool:
        """Органическая ли молекула (содержит углерод C)."""
        return "C" in formula


# Демонстрация
water = Molecule("Вода", "H2O", 18.015)
caffeine = Molecule("Кофеин", "C8H10N4O2", 194.19)
glucose = Molecule("Глюкоза", "C6H12O6", 180.16)

print(water.describe())
print(caffeine.describe())
print(f"Создано молекул: {Molecule.get_count()}") # через класс
print(f"Кофеин — органика? {Molecule.is_organic(caffeine.formula)}") # через класс передаём формулу, но не экземпляр (можно было просто текстом "C8H10N4O2")
print(f"Вода — органика? {Molecule.is_organic(water.formula)}")


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 1: Класс Asset
# ───────────────────────────────────────────────────────────────
# Создай класс Asset (финансовый инструмент):
#
# Атрибуты экземпляра:
#   - ticker: str         — тикер/символ (AAPL, BTC, GOLD, SPY)
#   - name: str           — полное название
#   - price: float        — текущая цена в USD
#   - asset_type: str     — тип: "equity", "bond", "commodity", "crypto"
#
# Классовый атрибут:
#   - count: int = 0      — счётчик созданных инструментов
#
# Методы:
#   - describe() -> str   — "AAPL | Apple Inc. | $182.50 | equity"
#   - @staticmethod is_risky(asset_type: str) -> bool
#       True если "crypto" или "commodity"
#   - @classmethod get_count(cls) -> int
#
# Пример использования:
#   a = Asset("AAPL", "Apple Inc.", 182.50, "equity")
#   print(a.describe())
#   # → AAPL | Apple Inc. | $182.50 | equity
#   print(Asset.is_risky("crypto"))  # → True
#   print(Asset.is_risky("bond"))    # → False

class Asset:
    
    count = 0

    def __init__(self, ticker, name, price, asset_type):
        self.ticker = ticker
        self.name = name
        self.price = price
        self.asset_type = asset_type
        
        Asset.count += 1
    
    def describe(self) -> str:
        return f"{self.ticker} | {self.name} | ${self.price:.2f} | {self.asset_type}"
    
    @staticmethod
    def is_high_risky(asset_type) -> bool:
        return asset_type in ["crypto"]
    
    @classmethod
    def get_count(cls) -> int:
        return cls.count

a = Asset("AAPL", "Apple Inc.", 182.50, "equity")
print(Asset.count)
print(a.describe())
print(Asset.is_high_risky(a.asset_type))
print(Asset.is_high_risky('crypto'))

# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 2: Класс Portfolio
# ───────────────────────────────────────────────────────────────
# Создай класс Portfolio (инвестиционный портфель):
#
# Атрибуты:
#   - owner: str          — имя владельца
#   - cash: float         — свободный кэш в USD (начальный капитал)
#   - _positions: dict    — {ticker: {"shares": float, "avg_price": float}}
#   - _history: list[str] — история операций
#
# Методы:
#   - buy(ticker: str, shares: float, price: float) -> bool
#       Покупка: списывает cash, добавляет позицию. False если недостаточно средств.
#   - sell(ticker: str, shares: float, price: float) -> bool
#       Продажа: зачисляет cash, убирает позицию. False если нет столько акций.
#   - get_history() -> list[str]   — список операций
#   - __str__() -> str  — "Портфель Иванов И.И.: cash=$1500.00, позиций=3"
#
# Важно: при нехватке средств/акций — напечатать предупреждение,
#         вернуть False, не изменять состояние.

class Portfolio:
    
    def __init__(self, owner, cash):
        self.owner = owner
        self.cash = cash
        self._positions = {}
        self._history = []
    
    def buy(self, ticker, shares, price) -> bool:
        cost = shares * price
        if cost > self.cash:
            print(f"Недостаточно средств для покупки {shares} акций {ticker} по ${price:.2f} (нужно ${cost:.2f}, есть ${self.cash:.2f})")
            return False
        
        self.cash -= cost
        if ticker in self._positions:
            pos = self._positions[ticker]
            total_shares = pos["shares"] + shares
            pos["avg_price"] = (pos["avg_price"] * pos["shares"] + cost) / total_shares
            pos["shares"] = total_shares
        else:
            self._positions[ticker] = {"shares": shares, "avg_price": price}
        
        self._history.append(f"Куплено {shares} акций {ticker} по ${price:.2f}")
        return True
    
    def sell(self, ticker, shares, price) -> bool:
        if ticker not in self._positions or self._positions[ticker]["shares"] < shares:
            print(f"Недостаточно акций {ticker} для продажи {shares} (есть {self._positions.get(ticker, {}).get('shares', 0)})")
            return False
        
        revenue = shares * price
        self.cash += revenue
        pos = self._positions[ticker]
        pos["shares"] -= shares
        if pos["shares"] == 0:
            del self._positions[ticker]
        
        self._history.append(f"Продано {shares} акций {ticker} по ${price:.2f}")
        return True
    
    def get_history(self):
        return self._history
    
    def __str__(self):
        return f"Портфель {self.owner}: cash=${self.cash:.2f}, позиций={len(self._positions)}"
    
# Демонстрация
portfolio = Portfolio("Иванов И.И.", 10000)
print(portfolio)
portfolio.buy("AAPL", 10, 150)  # $1500
portfolio.buy("GOOG", 5, 2000)   # $10000 -# недостаточно средств
portfolio.buy("TSLA", 2, 800)    
print(portfolio)
portfolio.sell("AAPL", 5, 160)   # +$800
portfolio.sell("GOOG", 1, 2100)   # +$2100
portfolio.sell("TSLA", 1, 850)    
print(portfolio)
print("История операций:")
print(portfolio.get_history())
