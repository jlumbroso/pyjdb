# pyjdb
Python interface with Java debugger through JDB.

## Example

Let's assume that we have this Java file, `IterPower.java`:
```java
public class IterPower {
    public static void main(String[] args) {
        // ... parse arguments ...
        System.out.println(iterPower(base, exp));
    }

    public static int iterPower(int base, int exp) {
        int result = 1;
        while (exp > 0) {
            result *= base;
            exp -= 1;
        }
        return result;
    }
}
```
which has been compiled with debugging information, `javac -g IterPower.java`. The following is a Python snippet:
```python
import pyjdb
import itertools

p = pyjdb.JdbProcess("IterPower")
p.spawn("10 4")

variables = {}

while True:
    
    # Try to make an additional step and retrieve local variables
    result = None
    try:
        p.step()
        result = p.locals()
    except pyjdb.EOF:
        break
    if result is None:
        continue

    # Store the values of each variable
    (args, locs) = result
    for (var, val) in itertools.chain(args.items(), locs.items()):
        variables[var] = variables.get(var, list())
        variables[var].append(val)

variables_unique_values = {
    var: set(vals) for (var, vals) in variables.items()
}

print(variables_unique_values)
```
The snippet will output a trace of the variable values of this program through its execution:
```json
{"args": {"instance of java.lang.String[0] (id=495)"},
 "base": {10},
 "exp": {0, 1, 2, 3, 4},
 "result": {1, 10, 100, 1000, 10000}}
```

## Inspiration

This project was inspired by a [talk by Elena Glassman](https://youtu.be/Pt-DMk1YRJ4) in which she shows how to cluster [different implementations of the same solution](http://eglassman.github.io/mit-phd-thesis/thesis-slides.html#/10) according to the trace of the internal variables. Her work, which includes [OverCode](http://eglassman.github.io/overcode/) and [foobaz](https://www.youtube.com/watch?v=4X94_2XEsrE), focuses on Python programs. At my home institution, we use Java in our introductory classes. The initial goal of this project was to apply Dr. Glassman's techniques to Java assignments.

## Related projects

There were several ambitious projects related to bringing a Java debugger to Python. These projects highlight how complex an undertaking it is to implement the actual JDWP protocol. This is why in this project, our approach has been to piggy-back on `jdb` so as to not need to reimplement protocol-level functionality.

- [csuter/pyjdb](https://github.com/csuter/pyjdb) (abandonned): A Python implementation of the JDWP specifications.

- [soulseekah/pyjdb](https://github.com/soulseekah/pyjdb) (abandonned): A `jdb` replacement with more user-friendly features.