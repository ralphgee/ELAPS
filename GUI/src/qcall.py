#!/usr/bin/env python
from __future__ import division, print_function

import signature
from qdataarg import QDataArg

from PyQt4 import QtCore, QtGui


class QCall(QtGui.QListWidgetItem):
    def __init__(self, gui, callid):
        QtGui.QGroupBox.__init__(self)
        self.Qt_gui = gui
        self.callid = callid
        self.sig = None

        self.UI_init()

    def UI_init(self):
        routines = list(self.Qt_gui.sampler["kernels"])

        # layout
        self.widget = QtGui.QWidget()
        layout = QtGui.QGridLayout()
        self.widget.setLayout(layout)
        layout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)

        # routine
        routine = QtGui.QLineEdit()
        layout.addWidget(routine, 1, 0)
        routine.callid = self.callid
        routine.argid = 0
        routine.setProperty("invalid", True)
        routine.textChanged.connect(self.arg_change)
        completer = QtGui.QCompleter(routines, routine)
        routine.setCompleter(completer)

        # spaces
        layout.setColumnStretch(100, 1)

        self.Qt_remove = QtGui.QToolButton()
        layout.addWidget(self.Qt_remove, 1, 101)
        icon = self.widget.style().standardIcon(
            QtGui.QStyle.SP_DialogCloseButton
        )
        self.Qt_remove.setIcon(icon)
        self.Qt_remove.clicked.connect(self.remove_click)

        # attributes
        self.Qt_args = [routine]
        self.Qt_arglabels = [None]
        self.sig = None

    def update_size(self):
        size = self.widget.sizeHint()
        if self.sig:
            argheight = 0
            layout = self.widget.layout()
            for i, Qarg in enumerate(self.Qt_args):
                argheight = max(argheight, Qarg.sizeHint().height())
            lineheight = self.widget.fontMetrics().lineSpacing()
            margins = layout.contentsMargins()
            top = margins.top()
            bottom = margins.bottom()
            spacing = layout.spacing()
            height = top + lineheight + spacing + argheight + bottom + 4
            size.setHeight(height)
        self.setSizeHint(size)

    def args_init(self):
        call = self.Qt_gui.calls[self.callid]
        self.Qt_args[0].setProperty("invalid", False)
        if isinstance(call, signature.Call):
            self.sig = call.sig
        else:
            minsig = self.Qt_gui.sampler["kernels"][call[0]]
            self.sig = None
            if not self.Qt_gui.nosigwarning_shown:
                self.Qt_gui.UI_alert("No signature found for %r!\n" % call[0] +
                                     "Hover arguments for input syntax.")
                self.Qt_gui.nosigwarning_shown = True
        doc = self.Qt_gui.docs_get(call[0])
        if doc:
            self.Qt_args[0].setToolTip(doc[0][1])
        for argid in range(len(call))[1:]:
            tooltip = ""
            if self.sig:
                argname = self.sig[argid].name
                if doc:
                    tooltip = doc[argid][1]
            else:
                argname = minsig[argid].replace("*", " *")
                if doc:
                    argname += doc[argid][0]
                    tooltip = doc[argid][1]
                if argname in ("int *", "float *", "double *"):
                    if doc:
                        tooltip += "\n\n*Format*:\n" if doc else ""
                    tooltip += ("Scalar:\tvalue\t\te.g. 1, -0.5\n"
                                "Array:\t[#elements]"
                                "\te.g. [10000] for a 100x100 matrix")
            Qarglabel = QtGui.QLabel(argname)
            if tooltip:
                Qarglabel.setToolTip(tooltip)
            self.widget.layout().addWidget(Qarglabel, 0, argid)
            self.Qt_arglabels.append(Qarglabel)
            Qarglabel.setAlignment(QtCore.Qt.AlignCenter)
            if self.sig:
                arg = self.sig[argid]
                if isinstance(arg, signature.Flag):
                    Qarg = QtGui.QComboBox()
                    Qarg.addItems(arg.flags)
                    Qarg.currentIndexChanged.connect(self.arg_change)
                elif isinstance(arg, (signature.Dim, signature.Scalar,
                                      signature.Ld, signature.Inc,
                                      signature.Info)):
                    Qarg = QtGui.QLineEdit()
                    Qarg.textChanged.connect(self.arg_change)
                elif isinstance(arg, signature.Data):
                    Qarg = QDataArg(self)
            else:
                Qarg = QtGui.QLineEdit(" ")
                Qarg.textChanged.connect(self.arg_change)
                if tooltip:
                    Qarg.setToolTip(tooltip)
            if tooltip:
                Qarg.setToolTip(tooltip)
            Qarg.argid = argid
            Qarg.setProperty("invalid", True)
            self.widget.layout().addWidget(Qarg, 1, argid,
                                           QtCore.Qt.AlignCenter)
            self.Qt_args.append(Qarg)
        if self.sig:
            self.showargs_apply()
            self.usevary_apply()

    def args_clear(self):
        self.Qt_args[0].setProperty("invalid", True)
        for Qarg in self.Qt_args[1:]:
            Qarg.deleteLater()
        self.Qt_args = self.Qt_args[:1]
        for Qarglabel in self.Qt_arglabels[1:]:
            Qarglabel.deleteLater()
        self.Qt_arglabels = self.Qt_arglabels[:1]
        self.Qt_args[0].setToolTip("")
        self.update_size()
        self.sig = None

    def showargs_apply(self):
        if not self.sig:
            return
        for argid, arg in enumerate(self.sig):
            for name, classes in (
                ("flags", signature.Flag),
                ("scalars", signature.Scalar),
                ("lds", (signature.Ld, signature.Inc)),
                ("infos", signature.Info)
            ):
                if isinstance(arg, classes):
                    showing = self.Qt_gui.showargs[name]
                    self.Qt_arglabels[argid].setVisible(showing)
                    self.Qt_args[argid].setVisible(showing)

    def usevary_apply(self):
        if not self.sig:
            return
        for Qarg in self.Qt_args:
            if isinstance(Qarg, QDataArg):
                Qarg.usevary_apply()

    def args_set(self, fromargid=None):
        self.Qt_gui.Qt_setting += 1
        call = self.Qt_gui.calls[self.callid]
        # set widgets
        if call[0] not in self.Qt_gui.sampler["kernels"]:
            self.args_clear()
            self.Qt_gui.Qt_setting = False
            return
        if isinstance(call, signature.Call):
            if call.sig != self.sig:
                if len(self.Qt_args) > 1:
                    self.args_clear()
                self.args_init()
        else:
            if len(self.Qt_args) != len(call):
                if len(self.Qt_args) > 1:
                    self.args_clear()
                self.args_init()
        # set values
        for argid, val in enumerate(call):
            Qarg = self.Qt_args[argid]
            Qarg.setProperty("invalid", val is None)
            Qarg.style().unpolish(Qarg)
            Qarg.style().polish(Qarg)
            Qarg.update()
            if Qarg.argid == fromargid:
                continue
            val = "" if val is None else str(val)
            if isinstance(Qarg, QtGui.QLineEdit):
                Qarg.setText(val)
            elif isinstance(Qarg, QtGui.QComboBox):
                Qarg.setCurrentIndex(Qarg.findText(val))
            elif isinstance(Qarg, QDataArg):
                Qarg.set()
        self.update_size()
        self.Qt_gui.Qt_setting -= 1

    def data_viz(self):
        if not self.sig:
            return
        for argid in self.Qt_gui.calls[self.callid].sig.dataargs():
            self.Qt_args[argid].viz()
        self.update_size()

    # event handlers
    def remove_click(self):
        self.Qt_gui.UI_call_remove(self.callid)

    def arg_change(self):
        sender = self.Qt_gui.Qt_app.sender()
        if isinstance(sender, QtGui.QLineEdit):
            # adjust widt no matter where the change came from
            val = str(sender.text())
            if sender.argid != 0:
                width = sender.fontMetrics().width(val)
                width += sender.minimumSizeHint().width()
                height = sender.sizeHint().height()
                sender.setFixedSize(max(height, width), height)
        if self.Qt_gui.Qt_setting:
            return
        if isinstance(sender, QtGui.QComboBox):
            val = str(sender.currentText())
        if not val:
            val = None
        self.Qt_gui.UI_arg_change(self.callid, sender.argid, val)
