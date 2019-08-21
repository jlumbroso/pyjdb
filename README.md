# pyjdb
Python interface with Java debugger through JDB.

## Example

## Inspiration

This project was inspired by a [talk by Elena Glassman](https://youtu.be/Pt-DMk1YRJ4) in which she shows how to cluster [different implementations of the same solution](http://eglassman.github.io/mit-phd-thesis/thesis-slides.html#/10) according to the trace of the internal variables. Her work, which includes [OverCode](http://eglassman.github.io/overcode/) and [foobaz](https://www.youtube.com/watch?v=4X94_2XEsrE), focuses on Python programs. At my home institution, we use Java in our introductory classes. The initial goal of this project was to apply Dr. Glassman's techniques to Java assignments.

## Related projects

There were several ambitious projects related to bringing a Java debugger to Python. These projects highlight how complex an undertaking it is to implement the actual JDWP protocol. This is why in this project, our approach has been to piggy-back on `jdb` so as to not need to reimplement protocol-level functionality.

- [csuter/pyjdb](https://github.com/csuter/pyjdb) (abandonned): A Python implementation of the JDWP specifications.

- [soulseekah/pyjdb](https://github.com/soulseekah/pyjdb) (abandonned): A `jdb` replacement with more user-friendly features.