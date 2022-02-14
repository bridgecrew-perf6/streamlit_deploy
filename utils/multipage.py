import importlib
import os
import sys
import typing
from dataclasses import dataclass

import streamlit as st

PAGE_DIR = "./pages"


def import_page(app_name):
    if not sys.modules.get(f"pages.{app_name}"):
        importlib.import_module(f"pages.{app_name}")
    else:
        importlib.reload(importlib.import_module(f"pages.{app_name}"))


def application_detection():
    """
    Detects if the application is running in a Streamlit app.
    """

    page_path = [page_path for page_path in os.listdir(PAGE_DIR) if not page_path.startswith("__")]
    return page_path


page_path_list = application_detection()


@dataclass
class App:
    name: str
    func: typing.Callable


apps = [App(name=name[:-3], func=import_page) for name in page_path_list]


@dataclass
class MultiApp:
    navbar_name: str = "Navigation"
    navbar_style: str = os.environ.get("NAVBAR_STYLE", "SelectBox")
    horizontal_max_button_size: int = int(os.environ.get("HORIZONTAL_MAX_BUTTON_SIZE", "4"))
    navbar_extra = None
    current_app = apps[0]

    @staticmethod
    def _change_page(app: App) -> None:
        app.func(app.name)

    def _render_navbar(self, sidebar: st.sidebar) -> None:
        global apps
        sidebar.markdown(
            f"""<h1 style="text-align:center;">{self.navbar_name}</h1>""",
            unsafe_allow_html=True,
        )
        sidebar.text("\n")

        possible_styles = ["Button", "SelectBox"]

        if self.navbar_style not in possible_styles:
            sidebar.warning("Invalid Navbar Style - Using Button")
            self.navbar_style = "HorizontalButton"

        if self.navbar_style == "Button":
            app_list = []
            for i, app in enumerate(apps):
                if i % self.horizontal_max_button_size == 0:
                    app_list.append([])
                app_list[-1].append(app)
            for app_group in app_list:
                columns = sidebar.columns(len(app_group))
                for app, column in zip(app_group, columns):
                    if column.button(app.name):
                        self.current_app = app
        else:
            app_names = [app.name for app in apps]
            app_name = sidebar.selectbox("", app_names)
            self.current_app = [app for app in apps if app.name == app_name][0]

        if self.navbar_extra:
            self.navbar_extra.func(sidebar)

        sidebar.write("---")
        self._change_page(self.current_app)

    def run(self):
        self._render_navbar(st.sidebar)


multi_app = MultiApp(horizontal_max_button_size=2)
