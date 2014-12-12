#!/usr/bin/env python
from __future__ import division, print_function


class Signature(list):
    def __init__(self, *args, **kwargs):
        if "file" in kwargs:
            self.filename = kwargs["file"]
            # read signature from file
            with open(self.filename) as fin:
                sig = eval(fin.read())
            if not isinstance(sig, Signature):
                raise TypeError(self.filename + "did not conatin a Signature")
            # initialize from loaded signature
            list.__init__(self, sig)
            self.complexity = sig.complexity
            return
        # set attributes
        list.__init__(self, args)
        self.complexity = None
        self.filename = None
        if "complexity" in kwargs:
            self.complexity = kwargs["complexity"]

        # infer and compile min and attr
        if no isinstance(self[i], Name):
            self[0] = Name(self[0])
        lambdaargs = ", ".join(arg.name for arg in self)
        for arg in self:
            if hasattr(arg, "minstr") and arg.minstr:
                arg.min = eval("lambda " + lambdaargs + ": " + arg.minstr)
            if arg.attrstr:
                arg.attr = eval("lambda (" + lambdaargs + "): filter(None, (" +
                                arg.attrstr + "))")

    def __str__(self):
        return (self[0].name + "(" +
                ", ".join(arg.name for arg in self[1:]) + ")")

    def __repr__(self):
        return (self.__class__.__name__ + "(" + repr(self[0].name) + ", "
                + ", ".join(map(repr, self[1:])) + ")")

    def __call__(self, *args):
        return Call(self, *args)

    def create_call(self):
        args = tuple(arg.default() for arg in self[1:])
        return self(*args)


class Call(list):
    def __init__(self, sig, *args):
        if not isinstance(sig, Signature):
            raise TypeError("a Signature is requred as first argument")
        if len(args) != len(sig) - 1:
            raise TypeError(sig[0].name + "() takes exactly " +
                            str(len(self) - 1) + " arguments (" +
                            str(len(args)) + " given)")
        list.__init__(self, (sig[0].name,) + args)
        self.__dict__["sig"] = sig

    def __str__(self):
        return self[0] + "(" + ", ".join(map(str, self[1:])) + ")"

    def __repr__(self):
        return (self.__class__.__name__ + "(" + repr(self.sig) + ", " +
                ", ".join(map(repr, self[1:])) + ")")

    def __getattr__(self, name):
        for i, arg in enumerate(self.sig):
            if arg.name == name:
                return self[i]
        raise AttributeError(repr(self.sig[0].name) + " call has no attribute "
                             + repr(name))

    def __setattr__(self, name, value):
        for i, arg in enumerate(self.sig):
            if arg.name == name:
                self[i] = value
                return
        raise AttributeError(repr(self.sig[0].name) + " call has no attribute "
                             + repr(name))

    def copy(self):
        return Call(self.sig, self[1:])

    def complete_once(self):
        l = list(self)
        for i, arg in enumerate(self.sig):
            if self[i] is None and hasattr(arg, "min"):
                try:
                    self[i] = arg.min(*self)
                except TypeError:
                    pass  # probably a None

    def complete(self, overwrite=False):
        if overwrite:
            self.clear_completable()
        calls = []
        while list(self) not in calls:
            calls.append(list(self))
            self.complete_once()

    def clear_completable(self):
        for i, arg in enumerate(self.sig):
            if hasattr(arg, "min"):
                self[i] = None


class Arg():
    def __init__(self, name, attr=None):
        self.name = name
        self.attrstr = attr

    def __repr__(self):
        args = [self.name]
        if self.attrstr:
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"


class Name(Arg):
    def default(self):
        return self.name


class Flag(Arg):
    def __init__(self, name, flags, attr=None):
        Arg.__init__(self, name, attr)
        self.flags = flags

    def __repr__(self):
        args = [self.name, self.flags]
        if self.attrstr:
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"

    def default(self):
        return self.flags[0]


class Side(Flag):
    def __init__(self, name="side", attr=None):
        Flag.__init__(self, name, ["L", "R"], attr)

    def __repr__(self):
        args = []
        if self.name != "side":
            args.append(self.name)
        if self.attrstr:
            if self.name == "side":
                args.append(None)
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"


class Uplo(Flag):
    def __init__(self, name="uplo", attr=None):
        Flag.__init__(self, name, ["L", "U"], attr)

    def __repr__(self):
        args = []
        if self.name != "uplo":
            args.append(self.name)
        if self.attrstr:
            if self.name == "uplo":
                args.append(None)
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"


class Trans(Flag):
    def __init__(self, name="trans", attr=None):
        Flag.__init__(self, name, ["N", "T"], attr)

    def __repr__(self):
        args = []
        if self.name != "trans":
            args.append(self.name)
        if self.attrstr:
            if self.name == "trans":
                args.append(None)
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"


class Diag(Flag):
    def __init__(self, name="diag", attr=None):
        Flag.__init__(self, name, ["N", "U"], attr)

    def __repr__(self):
        args = []
        if self.name != "diag":
            args.append(self.name)
        if self.attrstr:
            if self.name == "diag":
                args.append(None)
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"


class Dim(Arg):
    def __init__(self, name, min=None, attr=None):
        Arg.__init__(self, name, attr)
        self.minstr = min

    def __repr__(self):
        args = [self.name]
        if self.minstr:
            args.append(self.minstr)
        if self.attrstr:
            if not self.minstr:
                args.append(None)
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"

    def default(self):
        if self.minstr is None:
            return 0
        return None


class Scalar(Arg):
    def __init__(self, name="alpha", attr=None):
        Arg.__init__(self, name, attr)

    def __repr__(self):
        args = []
        if self.name != "alpha":
            args.append(self.name)
        if self.attrstr:
            if self.name == "alpha":
                args.append(None)
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"

    def default(self):
        return 1


class iScalar(Scalar):
    pass


class sScalar(Scalar):
    pass


class dScalar(Scalar):
    pass


class cScalar(Scalar):
    def default(self):
        return "1,0"


class zScalar(Scalar):
    def default(self):
        return "1,0"


class Data(Arg):
    def __init__(self, name, min=None, attr=None):
        Arg.__init__(self, name, attr)
        self.minstro = min
        self.minstr = min
        if min:
            self.minstr = "'[' + str(" + min + ") + ']'"

    def __repr__(self):
        args = [self.name]
        if self.minstr:
            args.append(self.minstro)
        if self.attrstr:
            if self.minstr:
                args.append(None)
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"

    def default(self):
        if self.minstr is None:
            return "[1]"
        return None


class iData(Data):
    pass


class sData(Data):
    pass


class dData(Data):
    pass


class cData(Data):
    def __init__(self, name, min=None, attr=None):
        if min:
            min = "2 * (" + min + ")"
        Data.__init__(self, name, min, attr)


class zData(Data):
    def __init__(self, name, min=None, attr=None):
        if min:
            min = "2 * (" + min + ")"
        Data.__init__(self, name, min, attr)


class Ld(Arg):
    def __init__(self, name, min=None, attr=None):
        Arg.__init__(self, name, attr)
        self.minstr = min

    def __repr__(self):
        args = [self.name]
        if self.minstr:
            args.append(self.minstr)
        if self.attrstr:
            if self.minstr:
                args.append(None)
            args.append(self.attrstr)
        args = map(repr, args)
        return self.__class__.__name__ + "(" + ", ".join(args) + ")"

    def default(self):
        if self.minstr is None:
            return "1"
        return None


class Inc(Arg):
    def default(self):
        return "1"

# attr
lower = "lower"
upper = "upper"
symm = "symm"
herm = "herm"
