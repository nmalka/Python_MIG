import sys
import types
ignore_types = [types.MethodType, 
          types.ModuleType, 
          types.InstanceType, 
          types.MethodType, 
          types.FunctionType, 
          types.ClassType, 
          types.BuiltinFunctionType,
          types.BuiltinMethodType,]

def tb_frame_locals(DEBUG=False):
    ret = ''
    tb = sys.exc_info()[2]
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    ret =  "Locals by frame, innermost last\n"
    for frame in stack:
        ret += "\nFrame %s in %s at line %s\n" % (frame.f_code.co_name,
                                             frame.f_code.co_filename,
                                             frame.f_lineno)
        for key, value in frame.f_locals.items():
            if not DEBUG and type(value) in ignore_types:
                continue
            ret += "\n\t%20s = " % key
            try:               
                ret += '%s\n' %  repr(value)
            except:
                if DEBUG:
                    ret += "<ERROR WHILE PRINTING VALUE: %s, %s>\n" % (sys.exc_info()[0], sys.exc_info()[1])
                else:
                    ret += "<ERROR WHILE PRINTING VALUE>\n"
    return ret + '\t%s\n' % ('-'* 20)


