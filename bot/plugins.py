import inspect
import os
import pkgutil
from typing import List, Tuple, Any, Type, Union, Dict

from bot.base import BotBase


class Plugin(object):

    def on_load(self, bot: BotBase) -> None:
        raise NotImplementedError()

    def name(self) -> str:
        raise NotImplementedError()


class PluginCollection(object):

    def __init__(self, plugin_package: str):
        self._plugin_dict: Dict[str, Plugin] = {}
        self.seen_paths: List[str] = []
        self.plugin_package: str = plugin_package
        self.reload_plugins()

    def reload_plugins(self) -> None:
        self._plugin_dict.clear()
        self.seen_paths = []
        print(f'Looking for plugins under package {self.plugin_package}')
        self.walk_package(self.plugin_package)

    def walk_package(self, package) -> None:
        imported_package: object = __import__(package, fromlist=['blah'])

        plugin_name: str
        is_pkg: bool
        for _, plugin_name, is_pkg in pkgutil.iter_modules(imported_package.__path__, imported_package.__name__ + '.'):
            if not is_pkg:
                plugin_module: object = __import__(plugin_name, fromlist=['blah'])
                cls_members: List[Tuple[str, Type]] = inspect.getmembers(plugin_module, inspect.isclass)
                c: Type
                for (_, c) in cls_members:
                    # Only add classes that are a sub class of Plugin, but NOT Plugin itself
                    if issubclass(c, Plugin) & (c is not Plugin):
                        print(f'Found plugin class: {c.__module__}.{c.__name__}')
                        plugin_instance: Plugin = c()
                        # self.plugins.append(plugin_instance)
                        self._plugin_dict[plugin_instance.name] = plugin_instance

        # Now that we have looked at all the modules in the current package, start looking
        # recursively for additional modules in sub packages
        all_current_paths: List[str] = []
        if isinstance(imported_package.__path__, str):
            all_current_paths.append(imported_package.__path__)
        else:
            all_current_paths.extend([x for x in imported_package.__path__])

        pkg_path: str
        for pkg_path in all_current_paths:
            if pkg_path not in self.seen_paths:
                self.seen_paths.append(pkg_path)

                # Get all subdirectory of the current package path directory
                child_pkgs: List[str] = [p for p in os.listdir(pkg_path) if os.path.isdir(os.path.join(pkg_path, p))]

                # For each subdirectory, apply the walk_package method recursively
                child_pkg: str
                for child_pkg in child_pkgs:
                    self.walk_package(package + '.' + child_pkg)

    def get(self, name: str) -> Plugin:
        return self._plugin_dict[name]

    def __iter__(self):
        return iter(self._plugin_dict.values())

