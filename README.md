# auto_profiler
[![](https://static.pepy.tech/badge/auto_profiler?style=flat-square)](https://www.pepy.tech/projects/auto_profiler)

This Software presents a real-time timer designed for profiling Python functions or code snippets within the Jupyter environment. The timer integrates seamlessly with Jupyter widgets, providing an interactive and extendable tree-based visualization of profiling results.

Key features of the proposed timer include the ability to filter out external library profiling, allowing users to focus solely on their own code. Additionally, the timer incorporates a threshold-based filter to exclude functions with very short execution times, enabling users to concentrate on more significant performance concerns.

Furthermore, the timer supports variable depth analysis, facilitating the identification of time-consuming functions within nested call hierarchies. It also handles loop or multiple function calls, providing comprehensive profiling capabilities for iterative or repetitive code structures. Moreover, recursive function calls are appropriately handled, ensuring accurate and insightful profiling results.

To optimize efficiency, users have the option to globally disable the timer by setting Profiler.GlobalDisable to True, thereby saving valuable execution time when profiling is not required.

Overall, this real-time timer with interactive Jupyter widgets and an extendable tree-based interface empowers users to effectively profile Python functions or code snippets, filter results based on specific criteria, and gain deeper insights into their code's performance characteristics.

## Features
- Filtering external libraries profiling.
- Filtering very short time functions-> threshold
- Allow depth: you can easily find the time consuming function
- Allow loop or multiple function call
- Allow recursive function call
- Disable it globaly by Profiler.GlobalDisable=True to save time :)
## Installation

Release version:

```bash
$ pip install auto_profiler
```

Development version:

```bash
$ pip install -e git+https://github.com/modaresimr/auto_profiler.git#egg=auto_profiler
```

Install in Jupyter

```bash
$ pip install ipytree
$ jupyter nbextension enable --py --sys-prefix ipytree
```



## Quick start

[Jupyter Notebook](example.ipynb)
### Auto profiling
More commonly, chances are that we want to measure the execution time of an entry function and all its subfunctions. In this case, it's too tedious to do it manually, and we can leverage `Profiler` to inject all the timing points for us automatically:

```python
import time # line number 1
import random

from auto_profiler import Profiler, Tree

def f1():
    mysleep(.6+random.random())

def mysleep(t):
    time.sleep(t)

def fact(i):
    f1()
    if(i==1):
        return 1
    return i*fact(i-1)



def main():
    for i in range(5):
        f1()

    fact(3)

with Profiler():
    main()

```

#### Example Output
##### In Jupyter (realtime view)
![example.gif](https://raw.githubusercontent.com/modaresimr/auto_profiler/master/example.gif)
```

Time   [Hits * PerHit] Function name [Called from] [function location]
-----------------------------------------------------------------------
8.974s [1 * 8.974]  main  [auto-profiler/profiler.py:267]  [/test/t2.py:30]
├── 5.954s [5 * 1.191]  f1  [/test/t2.py:34]  [/test/t2.py:14]
│   └── 5.954s [5 * 1.191]  mysleep  [/test/t2.py:15]  [/test/t2.py:17]
│       └── 5.954s [5 * 1.191]  <time.sleep>
|
|
|   # The rest is for the example recursive function call fact
└── 3.020s [1 * 3.020]  fact  [/test/t2.py:36]  [/test/t2.py:20]
    ├── 0.849s [1 * 0.849]  f1  [/test/t2.py:21]  [/test/t2.py:14]
    │   └── 0.849s [1 * 0.849]  mysleep  [/test/t2.py:15]  [/test/t2.py:17]
    │       └── 0.849s [1 * 0.849]  <time.sleep>
    └── 2.171s [1 * 2.171]  fact  [/test/t2.py:24]  [/test/t2.py:20]
        ├── 1.552s [1 * 1.552]  f1  [/test/t2.py:21]  [/test/t2.py:14]
        │   └── 1.552s [1 * 1.552]  mysleep  [/test/t2.py:15]  [/test/t2.py:17]
        └── 0.619s [1 * 0.619]  fact  [/test/t2.py:24]  [/test/t2.py:20]
            └── 0.619s [1 * 0.619]  f1  [/test/t2.py:21]  [/test/t2.py:14]
```

### Manual profiling

Sometimes, we only want to measure the execution time of partial snippets or a few functions, then we can inject all timing points into our code manually by leveraging `Timer`:

```python

# manual_example.py

import time

from auto_profiler import Timer, Tree


def main():
    t = Timer('sleep1', parent_name='main').start()
    time.sleep(1)
    t.stop()

    t = Timer('sleep2', parent_name='main').start()
    time.sleep(1.5)
    t.stop()

    print(Tree(Timer.root))


if __name__ == '__main__':
    main()
```

Run the example code:

```bash
$ python manual_example.py
```

and it will show you the profiling result:

```
2.503s  main
├── 1.001s  sleep1
└── 1.501s  sleep2

```

## advanced setup


```
def show(p):
    print('Time   [Hits * PerHit] Function name [Called from] [Function Location]\n'+\
          '-----------------------------------------------------------------------')
    print(Tree(p.root, threshold=0.5))
    
@Profiler(depth=4, on_disable=show)
def main():
    for i in range(5):
        f1()

    fact(3)

```

## Supported frameworks

While you can do profiling on normal Python code, as a web developer, chances are that you will usually do profiling on web service code.

Currently supported web frameworks:

- [Flask](http://flask.pocoo.org/)


## Examples

For profiling web service code (involving web requests), check out [examples](examples).


## License

[MIT](http://opensource.org/licenses/MIT)
