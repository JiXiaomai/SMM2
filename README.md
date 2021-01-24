# SMM2
Python library for manipulating Super Mario Maker 2 save files.

# Installation
From the Command Prompt: ```pip install https://github.com/MarioPossamato/SMM2/archive/main.zip```

# SMM2 Memory Modding Tools
Most of the code in this script was created by [Treeki](https://github.com/Treeki/) for [CylindricalEarth](https://github.com/Treeki/CylindricalEarth), mainly [pynoexs.py](https://github.com/Treeki/CylindricalEarth/blob/master/pynoexs.py) and [debug_tools.py](https://github.com/Treeki/CylindricalEarth/blob/master/debug_tools.py).  This tool allows users to peek and poke specific pre-designated addresses in Super Mario Maker 2's memory, such as timer and sprite count.

# Library Usage
```py
>>> from SMM2 import encryption
>>> from SMM2 import course
>>> 
>>> data = open("course_data_000.bcd", "rb").read()
>>> 
>>> Course = encryption.Course()
>>> Course.load(data)
>>> Course.decrypt()
>>> 
>>> open("course_data_000.bcd", "wb").write(Course.data)
```

# Who gets credit for this?
Thanks to:
* [Treeki](https://github.com/Treeki/) For creating [CylindricalEarth](https://github.com/Treeki/CylindricalEarth);
* [Kinnay](https://github.com/Kinnay/) For helping me get encryption working;
* [0Liam](https://github.com/0Liam/) For his documentation of save files;
* [RedDuckss](https://github.com/RedDuckss/) For creating [partrick](https://github.com/RedDuckss/partrick);
* [Tarnadas](https://github.com/Tarnadas/) For help with the save.dat file format;
* [Simontime](https://github.com/simontime/) For creating [SMM2CourseDecryptor](https://github.com/simontime/SMM2CourseDecryptor).

Also, I don't know who created [cstool.exe](https://github.com/MarioPossamato/SMM2/blob/main/SMM2/cstool.exe) and [kstool.exe](https://github.com/MarioPossamato/SMM2/blob/main/SMM2/kstool.exe) originally, but they come packaged with [Matthew Bell's](https://github.com/mdbell/) Noexes repository, so all credit goes to the original creator(s).  They're just here because I'm planning on doing something with them in the future.
