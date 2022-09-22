# pysproto
A simple python implement of sproto.

# Description
The sproto of skynet is built in lua & C on linux platform, which is not protable on Windows and godot engine. So I use python to build a protable prototype, and I will translate it to gdscript in future.
This project completed the interpreter and encoder of simple types (integer, string), which is enough for the skynet's offical example. Complex types will be implemented in the future.

# How to use
Clone skynet project [skynet](https://github.com/cloudwu/skynet) to your server and run the example as:
```shell
./skynet examples/config
```
Set the value of `TARGET_SERVER` & `TARGET_PORT` variables to your target server's ip and port in the `test.py`, and run as:
```shell
python test.py
```

# TODO
decoder & interpreter of arrays
decoder & interpreter of custom types