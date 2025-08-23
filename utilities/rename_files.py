import os
from os import listdir
from os.path import isfile, join

for f in os.listdir("."):

    # print(f)
    f_new = f.replace("'", "_")
    f_new = f_new.replace("｜", "_")
    f_new = f_new.replace("⧸", "_")
    f_new = f_new.replace("Ø", "_")
    f_new = f_new.replace("–", "_")
    f_new = f_new.replace("ę", "_")
    f_new = f_new.replace("?", "_")
    f_new = f_new.replace("？", "_")
    f_new = f_new.replace("＂", "_")
    f_new = f_new.replace("：", "_")
    
    

    if (f != f_new):
        print("renaming from: ", f)
        print("renaming to:   ", f_new)
        os.rename(f, f_new)


