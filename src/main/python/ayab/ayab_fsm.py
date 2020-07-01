# -*- coding: utf-8 -*-
# This file is part of AYAB.
#
#    AYAB is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    AYAB is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with AYAB.  If not, see <http://www.gnu.org/licenses/>.
#
#    Copyright 2013-2020 Sebastian Oliva, Christian Obersteiner,
#    Andreas Müller, Christian Gerbrandt
#    https://github.com/AllYarnsAreBeautiful/ayab-desktop

# import weakref
import logging

from PyQt5 import QtCore
from PyQt5.QtCore import QState, QObject


class FSM(object):
    """Heirarchical Finite State Machine.

    This replaces `fsyom` and various imperatively-programmed structures
    with a declaratively-programmed, event-driven framework tailored to the UI.
    @author Tom Price
    @date   June 2020
    """
    def __init__(self, parent):
        """Define Hierarchical states for Finite State Machine"""

        # garbage-collector-safe reference to parent
        self.__parent = parent  # weakref.ref(parent)

        # Finite State Machine
        self.machine = QtCore.QStateMachine()

        # Image states
        self.NO_IMAGE = QState(self.machine)
        self.NOT_CONFIGURED = QState(self.machine)
        self.CONFIGURING = QState(self.machine)
        self.KNITTING = QState(self.machine)

        # Set machine states
        self.machine.setInitialState(self.NO_IMAGE)

    def transitions(self):
        """Define transitions between states for Finite State Machine"""

        # Events that trigger state changes
        self.NO_IMAGE.addTransition(self.__parent.signal_image_loaded,
                                    self.NOT_CONFIGURED)
        self.NOT_CONFIGURED.addTransition(self.__parent.ui.knit_button.clicked,
                                          self.CONFIGURING)
        self.CONFIGURING.addTransition(self.__parent.signal_image_loaded,
                                       self.NOT_CONFIGURED)
        self.CONFIGURING.addTransition(self.__parent.signal_image_transformed,
                                       self.NOT_CONFIGURED)
        self.CONFIGURING.addTransition(self.__parent.signal_configure_fail,
                                       self.NOT_CONFIGURED)
        self.CONFIGURING.addTransition(self.__parent.signal_configured,
                                       self.KNITTING)
        self.KNITTING.addTransition(self.__parent.gt.finished,
                                    self.NOT_CONFIGURED)

        # Actions triggered by state changes
        self.NO_IMAGE.entered.connect(
            lambda: logging.debug("Entered state NO_IMAGE"))
        self.NOT_CONFIGURED.entered.connect(
            lambda: logging.debug("Entered state NOT_CONFIGURED"))
        self.CONFIGURING.entered.connect(
            lambda: logging.debug("Entered state CONFIGURING"))
        self.KNITTING.entered.connect(
            lambda: logging.debug("Entered state KNITTING"))

        self.NOT_CONFIGURED.entered.connect(self.__parent.add_image_actions)
        self.NOT_CONFIGURED.entered.connect(self.__parent.reset_progress_bar)
        self.CONFIGURING.entered.connect(self.__parent.plugin.configure)
        self.KNITTING.entered.connect(self.__parent.start_knitting_process)

    def properties(self):
        """Define properties for GUI elements linked to states in Finite State Machine"""

        # Options dock
        self.NO_IMAGE.assignProperty(self.__parent.ui.widget_optionsdock,
                                     "enabled", "False")
        self.NOT_CONFIGURED.assignProperty(self.__parent.ui.widget_optionsdock,
                                           "enabled", "True")
        self.KNITTING.assignProperty(self.__parent.ui.widget_optionsdock,
                                     "enabled", "False")

        # Knit button
        self.NO_IMAGE.assignProperty(self.__parent.ui.knit_button, "enabled",
                                     "False")
        self.NOT_CONFIGURED.assignProperty(self.__parent.ui.knit_button,
                                           "enabled", "True")
        self.KNITTING.assignProperty(self.__parent.ui.knit_button, "enabled",
                                     "False")

        # Cancel button
        self.NO_IMAGE.assignProperty(self.__parent.ui.cancel_button, "enabled",
                                     "False")
        self.NOT_CONFIGURED.assignProperty(self.__parent.ui.cancel_button,
                                           "enabled", "False")
        self.KNITTING.assignProperty(self.__parent.ui.cancel_button, "enabled",
                                     "True")
