# ═══════════════════════════════════════════════════════════════
# ТЕМА 2: Инкапсуляция и @property
# ═══════════════════════════════════════════════════════════════
#
# ТЕОРИЯ:
#   Инкапсуляция — скрываем детали реализации, предоставляем интерфейс.
#
#   Соглашения по именованию:
#   - name      — публичный атрибут (доступен всем)
#   - _name     — защищённый (соглашение: "внутри класса/наследников")
#   - __name    — приватный (name mangling → _ClassName__name)
#
#   @property — питоничный способ геттеров и сеттеров:
#   @property        def field(self) -> T: ...  # геттер
#   @field.setter    def field(self, v: T): ...  # сеттер с валидацией
#   @field.deleter   def field(self): ...         # удаление
#

# геттер и сеттеры используются обычно для непубличных атрибутов?
# Ответ: не обязательно, @property может быть и для публичного атрибута, если нужно контролировать доступ или вычислять значение на лету.
# Но часто @property применяется именно для "защищённых" или "приватных" атрибутов, чтобы скрыть детали реализации и обеспечить валидацию при установке значения.
# 
# в чем конктретный смысл "защищённого" атрибута, если он всё равно доступен извне?
# Ответ: "защищённый" атрибут (с одним подчеркинием) — это соглашение между разработчиками, что этот атрибут предназначен для внутреннего использования и не должен использоваться напрямую извне. Это не техническое ограничение, а договорённость. Такой атрибут может быть доступен извне, но его использование считается плохой практикой, так как это может привести к непредвиденным последствиям, если внешний код начнет изменять внутреннее состояние объекта. Поэтому важно уважать эти соглашения и не использовать "защищённые" атрибуты напрямую.
# 
# Но если без @property, то разве изменится логика?
# Ответ: без @property, если мы просто используем публичные атрибуты, то мы не сможем контролировать доступ к ним и выполнять валидацию при их изменении. Например, если у нас есть атрибут price, и мы хотим убедиться, что он всегда положительный, то без @property мы не сможем гарантировать это, так как кто-то может напрямую установить price = -100. С @property мы можем создать сеттер, который будет проверять значение перед его установкой и выбрасывать исключение, если оно некорректное. Таким образом, @property позволяет нам инкапсулировать логику доступа к атрибутам и обеспечивать целостность данных. 
# ───────────────────────────────────────────────────────────────
# ПРИМЕР: Класс ChromatographyColumn (хроматографическая колонка)
# ───────────────────────────────────────────────────────────────


class ChromatographyColumn:
    """Хроматографическая колонка."""

    def __init__(self, length_mm: float, diameter_mm: float, stationary_phase: str) -> None:
        self._length_mm = length_mm          # защищённый — только для чтения снаружи
        self._diameter_mm = diameter_mm      # защищённый
        self.__stationary_phase = stationary_phase  # приватный — только через метод

    @property
    def length(self) -> float:
        """Длина колонки в мм."""
        return self._length_mm

    @length.setter
    def length(self, value: float) -> None:
        if value <= 0:
            raise ValueError(f"Длина должна быть > 0, получено: {value}")
        self._length_mm = value

    @property
    def diameter(self) -> float:
        return self._diameter_mm

    @property
    def stationary_phase(self) -> str:
        """Неподвижная фаза (только чтение)."""
        return self.__stationary_phase

    @property
    def volume_ml(self) -> float:
        """Вычисляемое свойство: объём колонки в мл."""
        import math
        r = self._diameter_mm / 2
        return round(math.pi * r**2 * self._length_mm / 1000, 3)

    def __repr__(self) -> str:
        return (f"ChromatographyColumn(length={self._length_mm}мм, "
                f"diameter={self._diameter_mm}мм, phase='{self.__stationary_phase}')")


# Демонстрация
col = ChromatographyColumn(250, 4.6, "C18")
print(col)
print(f"Объём: {col.volume_ml} мл")
print(f"Фаза: {col.stationary_phase}")

col.length = 150  # через сеттер
print(f"Новая длина: {col.length} мм")

# Попытка отрицательной длины:
try:
    col.length = -10
except ValueError as e:
    print(f"Ошибка: {e}")

# name mangling — приватный атрибут всё равно доступен, но неявно:
print(col._ChromatographyColumn__stationary_phase)  # не делай так в реальном коде!


# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 1: Класс Price
# ───────────────────────────────────────────────────────────────
# Создай класс Price (цена финансового инструмента):
#
# Внутреннее хранение: __usd: float (всегда в USD, нельзя < 0)
#
# @property usd -> float      — цена в долларах (только чтение)
# @property rub -> float      — в рублях (курс: 1 USD = 91.5 RUB, только чтение)
# @property eur -> float      — в евро (курс: 1 USD = 0.92 EUR, только чтение)
#
# @usd.setter — устанавливает цену в USD,
#               проверяет: цена не может быть отрицательной (ValueError)
#
# @classmethod from_rub(cls, rub: float) -> "Price"
#   — альтернативный конструктор: создаёт Price из рублёвой цены
#
# Пример:
#   p = Price(usd=100.0)
#   print(p.rub)    # → 9150.0
#   print(p.eur)    # → 92.0
#   p2 = Price.from_rub(4575.0)
#   print(p2.usd)   # → 50.0

class Price:

    usd_rub = 91.5 # static field
    usd_eur = 0.92

    def __init__(self, usd):
        self._usd = usd

    @property # getter
    def usd(self) -> float:
        return self._usd
    
    @usd.setter # setter
    def usd(self, value: float):
        if value < 0:
            raise ValueError(f"Цена не может быть отрицательной, получено: {value}")
        self._usd = value
    
    @property
    def rub(self) -> float:
        return self.usd * self.usd_rub
    
    @property
    def eur(self) -> float:
        return self.usd * self.usd_eur
    
    @classmethod
    def from_rub(cls, rub: float) -> "Price":
        usd = rub / cls.usd_rub
        return cls(usd) # создаём экземпляр через конструктор __init__

p = Price(usd=100.0)
print(p.rub)    # → 9150.0
print(p.eur)    # → 92.0
p2 = Price.from_rub(4575.0)
print(p2.usd)   # → 50.0

Price.usd_rub = 100.0 # меняем курс для всех экземпляров
print(p.rub)    # → 10000.0

# проверка. то есть я верно понимаю, что в целом ожно устанавливать любые атрибуты и тд для объектов класса, НО
# если я хочу задавать точную логику атрибутам, то геттер даст мне просто значение, а сеттер - позволит его заменить, НО ТАМ ВОЗМОЖНО ВНУТРЕННЕЕ УСЛОВИЕ, которое без сеттера не сделать.

# прошу простой пример, где без сеттера вообще никак не обойтись.

class BankAccount:
    def __init__(self, balance: float):
        self._balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, amount: float):
        if amount < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = amount

account = BankAccount(100.0)
print(account.balance)  # → 100.0
account.balance = 150.0  # Устанавливаем новый баланс
print(account.balance)  # → 150.0
try:
    account.balance = -50.0  # Попытка установить отрицательный баланс
except ValueError as e:
    print(f"Ошибка: {e}")

# а если бы не было @balance.setter, то что?
# Если бы не было @balance.setter, то мы не смогли бы контролировать установку значения balance. Мы могли бы напрямую установить account._balance = -50.0, что нарушило бы логику нашего класса и позволило бы иметь некорректное состояние объекта. С сеттером мы можем гарантировать, что баланс всегда будет положительным, а без него мы теряем эту гарантию.

# ───────────────────────────────────────────────────────────────
# ЗАДАЧА 2: Класс APICredential
# ───────────────────────────────────────────────────────────────
# Создай класс APICredential (учётные данные для финансового API):
#
# Атрибуты:
#   - service: str        — публичное поле ("alphavantage", "polygon", ...)
#   - _base_url: str      — защищённое поле (можно читать, не рекомендуется менять)
#   - __api_key: str      — приватный ключ (только через @property)
#
# @property api_key -> str  — возвращает замаскированный ключ:
#   первые 4 символа + "***" + последние 4 символа
#   пример: "sk-ant-api03-abcXYZ1234" → "sk-a***1234"
#
# @api_key.setter — устанавливает ключ, минимальная длина 10 символов
#
# Метод info() -> str — "alphavantage @ https://..." (api_key НЕ выводить!)

# >>> ПИШИ ЗДЕСЬ <<<
