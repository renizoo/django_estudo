#encoding: UTF-8

import re
from operator import attrgetter

class FilterObjects():
    """
    Idea based by django.
    
    Служебный класс для исполнения логики критериев. Может быть наследован для 
    изменения логики.
    """

    conditional = True
    """
    Первоначальное значение условий
    """
    conditional_on_error = False
    """
    Значение критерия если такого аттрибута не найдено
    """
    separator = '__'
    """
    Разделитель между именем поля и функции сравнения
    """

    def __init__(self, *args, **kwargs):
        f = kwargs.pop('__func_prepare', self.__prepare_where)
        self.where = f(**kwargs)
        
    def __prepare_where(self, **kwargs):
        def __split(s, v):
            n, sep, f = s.partition(self.separator)
            return n, f, v
        return [__split(k,kwargs[k]) for k in kwargs]
    
    def run_func(self, obj, attr_name, func_name, arg):        
        try:
            attr = getattr(obj, attr_name)
        except AttributeError:
            return self.conditional_on_error
        func = getattr(self, 'func_{}'.format(func_name if func_name else 'default'))
        return func(attr, arg)
    
    def evaluate(self, obj):
        """
        Вычисление истинности критериев
        """
        r = self.conditional
        for w in self.where:
            r = self._cmp(r, self.run_func(obj, *w))
        return r
    
    def _cmp(self, v1, v2):
        """
        Функция объединения критериев. Может быть перекрыта для изменения логики.
        """
        return v1 and v2
    
    ##### functions #####
    
    def func_default(self, v1, v2):
        if v2 is None:
            return v1 is None
        return v1 == v2
    
    def func_in(self, v1, v2):
        return v1 in v2
    
    def func_gt(self, v1, v2):
        return v1 > v2

    def func_gte(self, v1, v2):
        return v1 >= v2

    def func_lt(self, v1, v2):
        return v1 < v2

    def func_lte(self, v1, v2):
        return v1 <= v2

    def func_ne(self, v1, v2):
        if v2 is None:
            return not v1 is None
        return v1 != v2
    
    def func_startswith(self, v1, v2):
        return v1.startswith(v2)

    def func_endswith(self, v1, v2):
        return v1.endswith(v2)
    
    def func_regex(self, v1, v2):
        return bool(re.match(v2, v1))

class Q():
    """
    Idea based by django Q
    Encapsulate filters as objects that can then be combined logically (using
    `&` ,`~` and `|`).
    
    Constructor:
        Q([Q(..)][, fieldname__operation=condition,...][, __filter_class=Q.filter_class])
        
    Usage:
        fo = Q(...)
        for i in filter(fo.evaluate, iterator_of_objects_for_filtering):
            ...
    """
    # Connection types
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'
    
    default = AND
    
    conditional = True
    """
    Первоначальное значение условий
    """
    filter_class = FilterObjects
    """
    Класс вычисления критериев. Может быть изменен в потомках, для смены поведения
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.chain = list()
        if args:
            for o in args:
                self.chain.append((o, self.default))
        self._filter_class = kwargs.pop('__filter_class', self.filter_class)
        self.__e = self._filter_class(**kwargs)
        
    ### magic methods ###
    
    def __or__(self, other):
        self.chain.append((other, self.OR))
        return self

    def __and__(self, other):
        self.chain.append((other, self.AND))
        return self

    def __invert__(self):
        q = type(self)()
        return q.__not(self)
    
    def __not(self, other):
        self.chain.append((other, self.NOT))
        return self
    
    ### end magic methods ###

    def evaluate(self, obj):
        """
        Вычисление истинности критериев.
        Например: функция может использоваться как функция для filter для итератора
        см. QuerySet.filter
        """
        r = self.conditional
        if self.__e:
            r = self.__e.evaluate(obj)
        for o, c in self.chain:
            if c == self.AND:
                r = r and o.evaluate(obj)
            if c == self.OR:
                r = r or o.evaluate(obj)
            if c == self.NOT:
                r = r and not o.evaluate(obj)
        return r
    
class QuerySet():
    """
    Idea based by django QuerySet
    QuerySet для любого iterable из объектов
    """
    
    default_q = Q
    """
    Класс исполнения логики фильтра
    """
    
    def __init__(self, iterator, *args, **kwargs):
        self.iterator = iterator
        self._fetched = False
        self.cache = None
        
    def fetch_all(self):
        """
        Загрузить в кеш все объекты удовлетворяющие условиям
        """
        if not self._fetched:
            self.cache = [o for o in self.iterator]
            self._fetched = True
        return self.cache

    ### magic methods ###

    def __iter__(self):
        if self._fetched:
            for o in self.cache:
                yield o
        else:
            for o in self.iterator:
                yield o
                
    def __len__(self):
        self.fetch_all()
        return len(self.cache)

    ### end of magic methods ###
                
    def filter(self, *args, **kwargs):
        """
        Возвращается новый QuerySet с настроенным заданным фильтром.
        Новый QuerySet ничего о фильтре не знает.
        :param args:
        :param kwargs:
        :return: QuerySet
        """
        return type(self)(filter(self.default_q(*args, **kwargs).evaluate, self))
    
    def exclude(self, *args, **kwargs):
        """
        Тоже самое что и filter, только общее условие отрицается
        """
        return self.filter(~self.default_q(*args, **kwargs))
    
    def count(self):
        """
        :return: Количество записей
        """
        return len(self)

    def sort(self, *args, **kwargs):
        """
        Сортировка массива данных. При вызове этой функции данные преварительно кешируются.
        :param args: имена аттрибутов объектов по которым производится сортировка
        :param kwargs: reverse=(False (default)|True)
        :return: QuerySet с новыми сортированными данными
        """
        if 'key' in kwargs:
            del kwargs['key']
        return type(self)(sorted(self, key = attrgetter(*args), **kwargs))

if __name__ == "__main__":
    
    class F(): pass
    
    #init_default_logger()
    
    to = F()
    to.id = 2
    to.type = 1
    to.s = 'aaa1111'

    to1 = F()
    to1.id = 1
    to1.type = 3
    to1.s = 'aaa1'

    e = Q(Q(Q(id=3) | Q(id=1)) & ~Q(type=2))
    print(e.evaluate(to))

    e = Q(s__regex = '^aaa\d+')
    print(e.evaluate(to))
    
    q = QuerySet([to, to1])
    qq = q.filter(s__regex = '^aaa\d+')
    qqq = qq.filter(Q(Q(id=3) | Q(id=1)) & ~Q(type=2))
    qqqq = q.exclude(id=2)
    for i in q:
        print(i.__dict__)
    

