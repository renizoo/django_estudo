#encoding: UTF-8

class Dict2ObjRef():
    """
    Объект использует обернутый словарь. RW режим. . Не рекурсивно.
    """

    def __init__(self, d):
        object.__setattr__(self, 'proxy_dict', d)

    def __getattr__(self, name):
        try:
            return self.proxy_dict[name]
        except:
            raise AttributeError

    def __contains__(self, item):
        return item in self.proxy_dict

    def __setattr__(self, name, value):
        self.proxy_dict[name] = value

class Dict2ObjRO():
    """
    Объект копирует в себя словарь. RO режим. Не рекурсивно.
    """

    def __init__(self, d):
        self.__dict__.update(d)

def dict2obj(iterable, wrap_class = Dict2ObjRef):
    """
    Итератор оборачивает dict из iterable классом wrap_class
    :param iterable: iterable of dicts
    :param wrap_class: class of wrapping
    :return:
    """
    for i in iterable:
        yield wrap_class(i)

if __name__ == "__main__":

    d = {'e': 1, 'k': 'aaaa'}
    o = Dict2ObjRef(d)
    print(o.__dict__)
    print(o.e, o.k)
    o.e = 'test1'
    print(o.e, o.k)
    print(d)
