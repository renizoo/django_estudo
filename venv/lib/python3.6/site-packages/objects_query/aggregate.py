#encoding: UTF-8

from operator import attrgetter
from copy import deepcopy

class AggregationFunction():
    """
    Прародитель всех функций аггрегации
    """

    def __init__(self, field):
        self.field = field

    def add_value(self, obj):
        """
        Метод для добавления значения. Необходимо перекрыть
        :param obj: Объект из которого значение извлекается
        :return:
        """
        raise NotImplementedError()

    def get_result(self):
        """
        Возвращает итоговое значение. Необходимо перекрыть
        Может быть использовано для подсчета значений после накопления данных
        :return:
        """
        raise NotImplementedError()

    @property
    def result(self):
        """
        Результат вычисления
        :return:
        """
        return self.get_result()

class Aggregator():
    """
    Аггрегатор по iterable объектов

    Aggregator(iterable, [field_group_by_1, [field_group_by_2, ..]] [additional_field = AggregateFunction(aggregate_field), ...])
    Результат вычислений iterable of dict

    iterable - iterable объектов
    field_group_by_X - имя аттрибутов по значениям которых будет происходить группировка, эти поля входят в результат
    additional_field - имя поля значением которого будет результат вычислений
    AggregateFunction - аггрегационная функция
    aggregate_field - имя аттрибута по которому будет происходить вычисление значения функции
    """

    def __init__(self, iterator, *args, **kwargs):
        self.iterator = iterator
        self.group_by = args
        self.additional = kwargs
        self._fetched = False
        self.cache = None

    ### magic methods ###

    def __iter__(self):
        self.fetch_all()
        for o in self.cache:
            yield o

    def __len__(self):
        self.fetch_all()
        return len(self.cache)

    ### end of magic methods ###

    def fetch_all(self):
        if not self._fetched:
            data = dict()
            keygen = attrgetter(*self.group_by)
            key_to_tuple = len(self.group_by) == 1
            # calculating values
            for obj in self.iterator:
                key = keygen(obj)
                if key_to_tuple:
                    key = (key,)
                if not key in data:
                    data[key] = deepcopy(self.additional)
                for i in data[key].values():
                    i.add_value(obj)
            # expand values into dict
            self.cache = list()
            for df in data:
                item = dict(zip(self.group_by, df))
                for afn in data[df]:
                    item[afn] = data[df][afn].result
                self.cache.append(item)
        return self.cache

### Functions ###

class Count(AggregationFunction):
    """
    Считает количество нахождений аттрибута
    """

    def __init__(self, field):
        super().__init__(field)
        self.r = 0

    def add_value(self, obj):
        if hasattr(obj, self.field):
            self.r += 1

    def get_result(self):
        return self.r

class Sum(AggregationFunction):
    """
    Считает сумму значений аттрибутов
    """

    def __init__(self, field):
        super().__init__(field)
        self.r = 0

    def add_value(self, obj):
        if hasattr(obj, self.field):
            self.r += getattr(obj, self.field)

    def get_result(self):
        return self.r

class Avg(AggregationFunction):
    """
    Среднее значение аттрибутов
    """

    def __init__(self, field):
        super().__init__(field)
        self.r = 0
        self.c = 0

    def add_value(self, obj):
        if hasattr(obj, self.field):
            self.r += getattr(obj, self.field)
            self.c += 1

    def get_result(self):
        return self.r / self.c

class MinMaxBase(AggregationFunction):
    """
    Базовый класс для все функций использующих сравнение
    """

    def __init__(self, field, start_value = 0):
        super().__init__(field)
        self.r = start_value

    def add_value(self, obj):
        if hasattr(obj, self.field):
            self.r = self.cmp(self.r, getattr(obj, self.field))

    def get_result(self):
        return self.r

    def cmp(self, v1, v2):
        """
        Сама функция сравнения. Должна возвращать значение которое является правильным
        :param v1:
        :param v2:
        :return:
        """
        raise NotImplementedError()

class Max(MinMaxBase):
    """
    Макимальное значение аттрибута
    """

    def cmp(self, v1, v2):
        return max(v1, v2)

class Min(MinMaxBase):
    """
    Минимальное значение аттрибута
    """

    def cmp(self, v1, v2):
        return min(v1, v2)

if __name__ == "__main__":

    class F(): pass

    to = F()
    to.id = 2
    to.type = 1
    to.s = 'aaa1111'
    to.a = '1'

    to1 = F()
    to1.id = 1
    to1.type = 1
    to1.s = 'aaa1'

    a = Aggregator([to, to1], 'type', ct = Max('id'))
    a.fetch_all()
    print(a.__dict__)