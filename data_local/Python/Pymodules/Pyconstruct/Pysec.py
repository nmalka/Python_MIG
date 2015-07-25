import base64
import ctypes

def libSo(s):
    s = ctypes.c_char_p(s)
    lib = ctypes.CDLL('/data_local/Python/Pymodules/libsecurity_MIH.so')
    lib.Decrypt.restype = ctypes.c_char_p
    lib.Encrypt.restype = ctypes.c_char_p
    return lib, s
    
def Decrypt(s):
    lib, s = libSo(s)
    return lib.Decrypt(s)

def Encrypt(s):
    lib, s = libSo(s)
    return lib.Encrypt(s)

def Decrypt64(s):
    return base64.b64decode(s)

def Encrypt64(s):
    return base64.b64encode(s)
