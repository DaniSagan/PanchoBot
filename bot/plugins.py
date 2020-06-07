import inspect
import os
import pkgutil
from typing import List

from bot.base import BotBase


class Plugin(object):
    plugins = []

    def on_load(self, bot: BotBase) -> None:
        raise NotImplementedError()

    def name(self) -> str:
        raise NotImplementedError()


class PluginCollection(object):

    def __init__(self, plugin_package):
        self._plugin_dict = {}
        self.plugin_package = plugin_package
        self.reload_plugins()

    def reload_plugins(self) -> None:
        # self.plugins = []
        self._plugin_dict.clear()
        self.seen_paths = []
        print()
        print('Looking for plugins under package {0}'.format(self.plugin_package))
        self.walk_package(self.plugin_package)

    def walk_package(self, package):
        imported_package = __import__(package, fromlist=['blah'])

        for _, pluginname, ispkg in pkgutil.iter_modules(imported_package.__path__, imported_package.__name__ + '.'):
            if not ispkg:
                plugin_module = __import__(pluginname, fromlist=['blah'])
                clsmembers = inspect.getmembers(plugin_module, inspect.isclass)  # type: List[type]
                for (_, c) in clsmembers:
                    # Only add classes that are a sub class of Plugin, but NOT Plugin itself
                    if issubclass(c, Plugin) & (c is not Plugin):
                        print('Found plugin class: {m}.{n}'.format(m=c.__module__, n=c.__name__))
                        plugin_instance = c()  # type: Plugin
                        # self.plugins.append(plugin_instance)
                        self._plugin_dict[plugin_instance.name] = plugin_instance

        # Now that we have looked at all the modules in the current package, start looking
        # recursively for additional modules in sub packages
        all_current_paths = []
        if isinstance(imported_package.__path__, str):
            all_current_paths.append(imported_package.__path__)
        else:
            all_current_paths.extend([x for x in imported_package.__path__])

        for pkg_path in all_current_paths:
            if pkg_path not in self.seen_paths:
                self.seen_paths.append(pkg_path)

                # Get all subdirectory of the current package path directory
                child_pkgs = [p for p in os.listdir(pkg_path) if os.path.isdir(os.path.join(pkg_path, p))]

                # For each subdirectory, apply the walk_package method recursively
                for child_pkg in child_pkgs:
                    self.walk_package(package + '.' + child_pkg)

    def get(self, name: str) -> Plugin:
        return self._plugin_dict[name]

    def __iter__(self):
        return iter(self._plugin_dict.values())

