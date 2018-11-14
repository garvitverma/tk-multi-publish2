# Copyright (c) 2018 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import copy
import sgtk
from ..data import PublishData

logger = sgtk.platform.get_logger(__name__)

class PluginSetting(PublishData):
    """
    This class provides an interface to settings defined for a given
    :ref:`publish-api-task`.
    """

    def __init__(self, name, data_type, default_value, description=None):
        """
        This class derives from :ref:`publish-api-data`.  A few special keys
        are set by default and are accessible after initialization. Those keys
        are:

        * ``default_value``: The default value as configured for this setting.
        * ``description``: Any description provided for this setting in the config.
        * ``name``: The display name for this setting.
        * ``type``: The type for this setting (:py:attr:`bool`, :py:attr:`str`, etc).
        * ``value``: The current value of this setting.

        .. note:: There is typically no need to create instances of this class
            manually. Each :ref:`publish-api-task` will expose a dictionary of
            configured ``PluginSettings``.
        """

        super(PluginSetting, self).__init__()

        self.default_value = default_value
        self.description = description
        self.name = name
        self.type = data_type
        self.value = default_value

    @property
    def string_value(self):
        """The setting value as a string."""
        return str(self.value)


def get_plugin_setting(settings_key, context=None, plugin_schema={}, validate=False):
    """
    """
    # the current bundle (the publisher instance)
    app = sgtk.platform.current_bundle()

    # Set the context if not specified
    context = context or app.context

    logger.debug("Finding plugin settings for context: %s" % (context,))

    if context == app.context:
        # if the context matches the bundle, we don't need to do any extra
        # work since the settings are already accessible via our app instance
        app_obj = app
    else:
        # find the matching raw app settings for this context
        context_settings = sgtk.platform.engine.find_app_settings(
            app.engine.name,
            app.name,
            app.sgtk,
            context,
            app.engine.instance_name
        )

        # No settings found, raise an error
        if not context_settings:
            raise TankError("Cannot find settings for %s for context %s" % (app.name, context))

        if len(context_settings) > 1:
            # There's more than one instance of the app for the engine instance, so we'll
            # need to deterministically pick one. We'll pick the one with the same
            # application instance name as the current app instance.
            for settings in context_settings:
                if settings.get("app_instance") == app.instance_name:
                    app_settings = settings
                    break
        else:
            app_settings = context_settings[0]

        if not app_settings:
            raise TankError(
                "Search for %s settings for context %s yielded too "
                "many results (%s), none named '%s'" % (app.name, context,
                ", ".join([s.get("app_instance") for s in context_settings]),
                app.instance_name)
            )

        new_env = app_settings["env_instance"]
        new_eng = app_settings["engine_instance"]
        new_app = app_settings["app_instance"]
        new_settings = app_settings["settings"]
        new_descriptor = new_env.get_app_descriptor(new_eng, new_app)

        # Create a new app instance from the new env / context
        app_obj = sgtk.platform.application.get_application(
                app.engine,
                new_descriptor.get_path(),
                new_descriptor,
                new_settings,
                new_app,
                new_env,
                context)

    # Inject the plugin's schema for proper settings resolution
    schema = copy.deepcopy(app_obj.descriptor.configuration_schema)        
    schema.update(plugin_schema)

    # Resolve the setting value, this also implicitly validates the value
    plugin_setting = sgtk.platform.bundle.resolve_setting_value(
                          app_obj.sgtk,
                          app_obj.engine.name,
                          schema[settings_key],
                          app_obj.settings,
                          settings_key,
                          None,
                          bundle=app_obj,
                          validate=validate
                      )
    if not plugin_setting:
        logger.debug("Could not find setting '%s' for context: %s" % (settings_key, context))

    return plugin_setting
