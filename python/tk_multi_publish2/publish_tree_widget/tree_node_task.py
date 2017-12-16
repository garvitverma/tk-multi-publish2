# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import sgtk
from sgtk.platform.qt import QtCore, QtGui
from .tree_node_base import TreeNodeBase
from .custom_widget_task import CustomTreeWidgetTask

logger = sgtk.platform.get_logger(__name__)


class TreeNodeTask(TreeNodeBase):
    """
    Tree item for a publish task
    """

    def __init__(self, task, parent):
        """
        :param task: Task instance
        :param parent: The parent QWidget for this control
        """
        self._task = task

        super(TreeNodeTask, self).__init__(parent)

        # tasks cannot be dragged or dropped on
        self.setFlags(self.flags() | QtCore.Qt.ItemIsSelectable)

        # set up defaults based on task settings
        self.update()

    def update(self):
        """
        Pull the widget's state from the associated task
        """
        state = QtCore.Qt.Checked if self._task.checked else QtCore.Qt.Unchecked
        self.setData(0, self.CHECKBOX_ROLE, state)
        self._embedded_widget.set_checkbox_value(state)
        self._embedded_widget.ui.checkbox.setEnabled(self._task.enabled)

    def __repr__(self):
        return "<TreeNodeTask %s>" % str(self)

    def __str__(self):
        return self._task.plugin.name

    def _create_widget(self, parent):
        """
        Create the widget that is used to visualise the node
        """
        # create an item widget and associate it with this QTreeWidgetItem
        widget = CustomTreeWidgetTask(self, parent)
        widget.set_header(self._task.plugin.name)
        widget.set_icon(self._task.plugin.icon)
        widget.set_checkbox_value(self.data(0, self.CHECKBOX_ROLE))
        return widget

    def set_check_state(self, state, apply_to_all_plugins=False):
        """
        Called by child item when checkbox was ticked
        """
        if apply_to_all_plugins:
            # do it for all of the items
            self.treeWidget().set_check_state_for_all_plugins(self._task.plugin, state)
        else:
            # set just this one
            super(TreeNodeTask, self).set_check_state(state)

    @property
    def task(self):
        """
        Associated task instance
        """
        return self._task

    def get_publish_instance(self):
        """
        Returns the low level item or task instance
        that this object represents

        :returns: task or item instance
        """
        return self.task

    def create_summary(self):
        """
        Creates summary of actions

        :returns: List of strings
        """
        if self.enabled:
            return [self._task.plugin.name]
        else:
            return []

    def validate(self, standalone):
        """
        Perform validation
        """
        if not self.enabled:
            # nothing to do!
            return True

        try:
            status = self._task.validate()
        except Exception, e:
            self._set_status_upwards(
                self._embedded_widget.VALIDATION_ERROR,
                str(e)
            )
            status = False
        else:
            if status:
                if standalone:
                    self._embedded_widget.set_status(
                        self._embedded_widget.VALIDATION_STANDALONE)
                else:
                    self._embedded_widget.set_status(
                        self._embedded_widget.VALIDATION)
            else:
                self._set_status_upwards(
                    self._embedded_widget.VALIDATION_ERROR,
                    "Unknown validation error"
                )
        return status

    def publish(self):
        """
        Perform publish
        """
        if not self.enabled:
            # nothing to do!
            return True

        try:
            self._task.publish()
        except Exception, e:
            self._set_status_upwards(
                self._embedded_widget.PUBLISH_ERROR,
                str(e)
            )
            raise
        else:
            self._embedded_widget.set_status(self._embedded_widget.PUBLISH)
        return True

    def finalize(self):
        """
        Perform finalize
        """
        if not self.enabled:
            # nothing to do!
            return True

        try:
            self._task.finalize()
        except Exception, e:
            self._set_status_upwards(
                self._embedded_widget.FINALIZE_ERROR,
                str(e)
            )
            raise
        else:
            self._embedded_widget.set_status(self._embedded_widget.FINALIZE)
        return True
