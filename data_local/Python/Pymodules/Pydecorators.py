
##################################
#   By: Itzik Ben Itzhak         #
#   Mail: itzik.b.i@gmail.com    #
#   Date: 15/06/09               #
#   ModuleNmae: Pydecorators.py  #
##################################

def decorator(test):
    def _decorator(f):
        def _decorator(user):
            if test == 'acb':
                print "im", test
                f(user)
            else:
                print 'Im not'
        return _decorator
    return _decorator

def mountCheck(lvm):
    def _mountCheck(f):
        def __mountCheck(*args, **kwargs):
            print lvm
            f(*args, **kwargs)
        return __mountCheck
    return _mountCheck
