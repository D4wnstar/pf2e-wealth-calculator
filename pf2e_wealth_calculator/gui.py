from pf2e_wealth_calculator.pf2ewc import get_loot_stats, process_loot_file
from pf2e_wealth_calculator.structs import Origins, Money
from pf2e_wealth_calculator.dataframes import tbl

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QCoreApplication as QCA
from PyQt6 import QtGui

import io


class MainWindow(QtW.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setGeometry(200, 100, 800, 600)
        self.setObjectName("main_window")
        self.setWindowTitle("PF2e Wealth Calculator")
        self.init_ui()

    def init_menubar(self):
        self.menubar = QtW.QMenuBar(self)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))

        self.menu_file = QtW.QMenu(self.menubar)
        self.menu_file.setObjectName("menuFile")
        self.menubar.addAction(self.menu_file.menuAction())

        self.menu_edit = QtW.QMenu(self.menubar)
        self.menu_edit.setObjectName("menuEdit")
        self.menubar.addAction(self.menu_edit.menuAction())

        self.setMenuBar(self.menubar)

        self.statusbar = QtW.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")

        self.setStatusBar(self.statusbar)

        self.action_open = QtGui.QAction(self)
        self.action_open.setObjectName("actionOpen")
        self.menu_file.addAction(self.action_open)

        self.action_save = QtGui.QAction(self)
        self.action_save.setObjectName("actionSave")
        self.menu_file.addAction(self.action_save)

        self.action_copy = QtGui.QAction(self)
        self.action_copy.setObjectName("actionCopy")
        self.menu_edit.addAction(self.action_copy)

        self.action_cut = QtGui.QAction(self)
        self.action_cut.setObjectName("actionCut")
        self.menu_edit.addAction(self.action_cut)

        self.action_paste = QtGui.QAction(self)
        self.action_paste.setObjectName("actionPaste")
        self.menu_edit.addAction(self.action_paste)

    def init_fonts(self):
        self.title_font = QtGui.QFont()
        self.title_font.setFamilies(["Constantia"])
        self.title_font.setPointSize(14)
        self.title_font.setBold(True)
        self.title_font.setUnderline(True)
        self.title_font.setKerning(True)
        self.title_font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferDefault)

        self.subtitle_font = QtGui.QFont()
        self.subtitle_font.setFamilies(["Constantia"])
        self.subtitle_font.setPointSize(11)

    def init_input_ui(self):
        self.input_label = QtW.QLabel(self.centralwidget)
        self.input_label.setObjectName("input_label")
        self.input_label.setGeometry(QtCore.QRect(20, 10, 231, 31))
        self.input_label.setFont(self.title_font)
        self.input_label.setCursor(QtGui.QCursor(Qt.CursorShape.ArrowCursor))
        self.input_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.item_textbox = QtW.QPlainTextEdit(self.centralwidget)
        self.item_textbox.setObjectName("item_textbox")
        self.item_textbox.setGeometry(QtCore.QRect(20, 50, 231, 221))

        self.calculate_button = QtW.QPushButton(self.centralwidget)
        self.calculate_button.setObjectName("calculate_button")
        self.calculate_button.setGeometry(QtCore.QRect(40, 290, 191, 41))

    def init_random_ui(self):
        self.random_label = QtW.QLabel(self.centralwidget)
        self.random_label.setObjectName("random_label")
        self.random_label.setGeometry(QtCore.QRect(40, 360, 191, 41))
        self.random_label.setFont(self.title_font)
        self.random_label.setCursor(QtGui.QCursor(Qt.CursorShape.ArrowCursor))
        self.random_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.randomize_button = QtW.QPushButton(self.centralwidget)
        self.randomize_button.setObjectName("randomize_button")
        self.randomize_button.setGeometry(QtCore.QRect(40, 500, 191, 41))

        self.layoutWidget = QtW.QWidget(self.centralwidget)
        self.layoutWidget.setObjectName("layoutWidget")
        self.layoutWidget.setGeometry(QtCore.QRect(20, 403, 231, 91))

        self.rand_param_grid = QtW.QGridLayout(self.layoutWidget)
        self.rand_param_grid.setObjectName("rand_param_grid")
        self.rand_param_grid.setContentsMargins(0, 0, 0, 0)

        self.nitems_spinbox = QtW.QSpinBox(self.layoutWidget)
        self.nitems_spinbox.setObjectName("nitems_spinbox")
        self.nitems_spinbox.setValue(5)
        self.rand_param_grid.addWidget(self.nitems_spinbox, 0, 1, 1, 1)

        self.lvlrange_label = QtW.QLabel(self.layoutWidget)
        self.lvlrange_label.setObjectName("lvlrange_label")
        self.rand_param_grid.addWidget(self.lvlrange_label, 1, 0, 1, 1)

        self.nitems_label = QtW.QLabel(self.layoutWidget)
        self.nitems_label.setObjectName("nitems_label")
        self.rand_param_grid.addWidget(self.nitems_label, 0, 0, 1, 1)

        self.minlvl_spinbox = QtW.QSpinBox(self.layoutWidget)
        self.minlvl_spinbox.setObjectName("minlvl_spinbox")
        self.rand_param_grid.addWidget(self.minlvl_spinbox, 1, 1, 1, 1)

        self.maxlvl_spinbox = QtW.QSpinBox(self.layoutWidget)
        self.maxlvl_spinbox.setObjectName("maxlvl_spinbox")
        self.maxlvl_spinbox.setValue(30)
        self.rand_param_grid.addWidget(self.maxlvl_spinbox, 1, 2, 1, 1)

    def init_total_value(self):
        self.totalvalue_label = QtW.QLabel(self.centralwidget)
        self.totalvalue_label.setObjectName("totalvalue_label")
        self.totalvalue_label.setFont(self.title_font)
        self.totalvalue_label.setGeometry(290, 10, 181, 31)

        self.totalvalue_widget = QtW.QWidget(self.centralwidget)
        self.totalvalue_widget.setGeometry(291, 51, 181, 281)

        self.totalvalue_vbox = QtW.QVBoxLayout(self.totalvalue_widget)
        self.totalvalue_vbox.setObjectName("totalvalue_vbox")
        self.totalvalue_vbox.setContentsMargins(0, 0, 0, 0)

        self.totalcp_label = QtW.QLabel(self.centralwidget)
        self.totalcp_label.setObjectName("totalcp_label")
        self.totalvalue_vbox.addWidget(self.totalcp_label)

        self.totalsp_label = QtW.QLabel(self.centralwidget)
        self.totalsp_label.setObjectName("totalsp_label")
        self.totalvalue_vbox.addWidget(self.totalsp_label)

        self.totalgp_label = QtW.QLabel(self.centralwidget)
        self.totalgp_label.setObjectName("totalgp_label")
        self.totalvalue_vbox.addWidget(self.totalgp_label)

        self.ofwhich_label = QtW.QLabel(self.centralwidget)
        self.ofwhich_label.setObjectName("ofwhich_label")
        self.ofwhich_label.setFont(self.subtitle_font)
        self.totalvalue_vbox.addWidget(self.ofwhich_label)

        self.itemsgp_label = QtW.QLabel(self.centralwidget)
        self.itemsgp_label.setObjectName("itemsgp_label")
        self.totalvalue_vbox.addWidget(self.itemsgp_label)

        self.artobjgp_label = QtW.QLabel(self.centralwidget)
        self.artobjgp_label.setObjectName("artobjgp_label")
        self.totalvalue_vbox.addWidget(self.artobjgp_label)

        self.currencygp_label = QtW.QLabel(self.centralwidget)
        self.currencygp_label.setObjectName("currencygp_label")
        self.totalvalue_vbox.addWidget(self.currencygp_label)

    def init_comparison(self):
        self.comparison_label = QtW.QLabel(self.centralwidget)
        self.comparison_label.setObjectName("comparison_label")
        self.comparison_label.setFont(self.title_font)
        self.comparison_label.setGeometry(290, 360, 179, 42)

        self.comparison_widget = QtW.QWidget(self.centralwidget)
        self.comparison_widget.setGeometry(291, 404, 181, 141)

        self.comparison_grid = QtW.QGridLayout(self.comparison_widget)
        self.comparison_grid.setObjectName("comparison_vbox")
        self.comparison_grid.setContentsMargins(0, 0, 0, 0)

        self.minlvlcmp_label = QtW.QLabel(self.centralwidget)
        self.comparison_grid.addWidget(self.minlvlcmp_label, 0, 0, 1, 1)

        self.maxlvlcmp_label = QtW.QLabel(self.centralwidget)
        self.comparison_grid.addWidget(self.maxlvlcmp_label, 0, 1, 1, 1)

        self.minlvlcmp_spinbox = QtW.QSpinBox(self.centralwidget)
        self.comparison_grid.addWidget(self.minlvlcmp_spinbox, 1, 0, 1, 1)

        self.maxlvlcmp_spinbox = QtW.QSpinBox(self.centralwidget)
        self.comparison_grid.addWidget(self.maxlvlcmp_spinbox, 1, 1, 1, 1)

        self.expected_label = QtW.QLabel(self.centralwidget)
        self.expected_label.setObjectName("expected_label")
        self.comparison_grid.addWidget(self.expected_label, 2, 0, 1, 2)

        self.difference_label = QtW.QLabel(self.centralwidget)
        self.difference_label.setObjectName("difference_label")
        self.comparison_grid.addWidget(self.difference_label, 3, 0, 1, 2)

    def init_breakdown(self):
        self.breakdown_label = QtW.QLabel(self.centralwidget)
        self.breakdown_label.setObjectName("breakdown_label")
        self.breakdown_label.setFont(self.title_font)
        self.breakdown_label.setGeometry(530, 10, 241, 31)

        self.breakdown_widget = QtW.QWidget(self.centralwidget)
        self.breakdown_widget.setGeometry(530, 52, 241, 491)

        self.breakdown_vbox = QtW.QVBoxLayout(self.breakdown_widget)
        self.breakdown_vbox.setObjectName("breakdown_vbox")
        self.breakdown_vbox.setContentsMargins(0, 0, 0, 0)

        self.levels_vbox = QtW.QVBoxLayout()
        self.levels_vbox.setObjectName("levels_vbox")

        self.levels_label = QtW.QLabel(self.breakdown_widget)
        self.levels_label.setObjectName("levels_label")
        self.levels_label.setFont(self.subtitle_font)
        self.levels_vbox.addWidget(self.levels_label)

        self.levelsexample_label = QtW.QLabel(self.breakdown_widget)
        self.levelsexample_label.setObjectName("levelsexample_label")
        self.levels_vbox.addWidget(self.levelsexample_label)

        self.breakdown_vbox.addLayout(self.levels_vbox)

        self.categories_vbox = QtW.QVBoxLayout()
        self.categories_vbox.setObjectName("categories_vbox")

        self.categories_label = QtW.QLabel(self.breakdown_widget)
        self.categories_label.setObjectName("categories_label")
        self.categories_label.setFont(self.subtitle_font)
        self.categories_vbox.addWidget(self.categories_label)

        self.catexamples_label = QtW.QLabel(self.breakdown_widget)
        self.catexamples_label.setObjectName("catexamples_label")
        self.categories_vbox.addWidget(self.catexamples_label)

        self.breakdown_vbox.addLayout(self.categories_vbox)

        self.subcategories_vbox = QtW.QVBoxLayout()
        self.subcategories_vbox.setObjectName("subcategories_vbox")

        self.subcategories_label = QtW.QLabel(self.breakdown_widget)
        self.subcategories_label.setObjectName("subcategories_label")
        self.subcategories_label.setFont(self.subtitle_font)
        self.subcategories_vbox.addWidget(self.subcategories_label)

        self.subcatexample_label = QtW.QLabel(self.breakdown_widget)
        self.subcatexample_label.setObjectName("subcatexample_label")
        self.subcategories_vbox.addWidget(self.subcatexample_label)

        self.breakdown_vbox.addLayout(self.subcategories_vbox)

        self.rarities_vbox = QtW.QVBoxLayout()
        self.rarities_vbox.setObjectName("rarities_vbox")

        self.rarities_label = QtW.QLabel(self.breakdown_widget)
        self.rarities_label.setObjectName("rarities_label")
        self.rarities_label.setFont(self.subtitle_font)
        self.rarities_vbox.addWidget(self.rarities_label)

        self.rarexample_label = QtW.QLabel(self.breakdown_widget)
        self.rarexample_label.setObjectName("rarexample_label")
        self.rarities_vbox.addWidget(self.rarexample_label)

        self.breakdown_vbox.addLayout(self.rarities_vbox)

    def init_dividers(self):
        self.hline = QtW.QFrame(self.centralwidget)
        self.hline.setObjectName("hline")
        self.hline.setGeometry(QtCore.QRect(7, 340, 491, 20))
        self.hline.setFrameShape(QtW.QFrame.Shape.HLine)
        self.hline.setFrameShadow(QtW.QFrame.Shadow.Sunken)

        self.vline_left = QtW.QFrame(self.centralwidget)
        self.vline_left.setObjectName("vline_left")
        self.vline_left.setGeometry(QtCore.QRect(260, 20, 20, 521))
        self.vline_left.setFrameShape(QtW.QFrame.Shape.VLine)
        self.vline_left.setFrameShadow(QtW.QFrame.Shadow.Sunken)

        self.vline_right = QtW.QFrame(self.centralwidget)
        self.vline_right.setObjectName("vline_right")
        self.vline_right.setGeometry(QtCore.QRect(490, 20, 20, 521))
        self.vline_right.setFrameShape(QtW.QFrame.Shape.VLine)
        self.vline_right.setFrameShadow(QtW.QFrame.Shadow.Sunken)

    def retranslate_ui(self):
        self.action_open.setText(QCA.translate("main_window", "Open", None))
        self.action_save.setText(QCA.translate("main_window", "Save", None))
        self.action_copy.setText(QCA.translate("main_window", "Copy", None))
        self.action_cut.setText(QCA.translate("main_window", "Cut", None))
        self.action_paste.setText(QCA.translate("main_window", "Paste", None))
        self.input_label.setText(QCA.translate("main_window", "INPUT", None))
        self.item_textbox.setPlaceholderText(
            QCA.translate("main_window", "Add your items here!", None)
        )
        self.random_label.setText(QCA.translate("main_window", "RANDOM", None))
        self.randomize_button.setText(QCA.translate("main_window", "Randomize!", None))
        self.totalvalue_label.setText(QCA.translate("main_window", "TOTAL VALUE", None))
        self.totalcp_label.setText(QCA.translate("main_window", "0 cp", None))
        self.totalsp_label.setText(QCA.translate("main_window", "0 sp", None))
        self.totalgp_label.setText(QCA.translate("main_window", "0 gp", None))
        self.ofwhich_label.setText(QCA.translate("main_window", "OF WHICH", None))
        self.itemsgp_label.setText(QCA.translate("main_window", "Items: 0 gp", None))
        self.artobjgp_label.setText(
            QCA.translate("main_window", "Art objects: 0 gp", None)
        )
        self.currencygp_label.setText(
            QCA.translate("main_window", "Currency: 0 gp", None)
        )
        self.breakdown_label.setText(QCA.translate("main_window", "BREAKDOWN", None))
        self.levels_label.setText(QCA.translate("main_window", "LEVELS", None))
        self.levelsexample_label.setText(QCA.translate("main_window", "...", None))
        self.categories_label.setText(QCA.translate("main_window", "CATEGORIES", None))
        self.catexamples_label.setText(QCA.translate("main_window", "...", None))
        self.subcategories_label.setText(
            QCA.translate("main_window", "SUBCATEGORIES", None)
        )
        self.subcatexample_label.setText(QCA.translate("main_window", "...", None))
        self.rarities_label.setText(QCA.translate("main_window", "RARITIES", None))
        self.rarexample_label.setText(QCA.translate("main_window", "...", None))
        self.comparison_label.setText(QCA.translate("main_window", "COMPARISON", None))
        self.minlvlcmp_label.setText(
            QCA.translate("main_window", "Minimum level:", None)
        )
        self.maxlvlcmp_label.setText(
            QCA.translate("main_window", "Maximum level:", None)
        )
        self.expected_label.setText(
            QCA.translate("main_window", "Expected: 0 gp", None)
        )
        self.difference_label.setText(
            QCA.translate("main_window", "Difference: None", None)
        )
        self.calculate_button.setText(QCA.translate("main_window", "Calculate!", None))
        self.lvlrange_label.setText(
            QCA.translate("main_window", "Level range (min/max):", None)
        )
        self.nitems_label.setText(
            QCA.translate("main_window", "Number of items:", None)
        )
        self.menu_file.setTitle(QCA.translate("main_window", "File", None))
        self.menu_edit.setTitle(QCA.translate("main_window", "Edit", None))

    def init_ui(self):
        self.centralwidget = QtW.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setEnabled(True)
        self.setCentralWidget(self.centralwidget)

        self.init_menubar()
        self.init_fonts()
        self.init_input_ui()
        self.init_random_ui()
        self.init_total_value()
        self.init_comparison()
        self.init_breakdown()
        self.init_dividers()

        self.calculate_button.clicked.connect(self.calculate)

        QtW.QWidget.setTabOrder(self.item_textbox, self.calculate_button)
        QtW.QWidget.setTabOrder(self.calculate_button, self.nitems_spinbox)
        QtW.QWidget.setTabOrder(self.nitems_spinbox, self.minlvl_spinbox)
        QtW.QWidget.setTabOrder(self.minlvl_spinbox, self.maxlvl_spinbox)
        QtW.QWidget.setTabOrder(self.maxlvl_spinbox, self.randomize_button)
        QtW.QWidget.setTabOrder(self.randomize_button, self.minlvlcmp_spinbox)
        QtW.QWidget.setTabOrder(self.minlvlcmp_spinbox, self.maxlvlcmp_spinbox)

        self.retranslate_ui()

    def calculate(self):
        """Calculate the stats for the loot in the text box and update the UI accordingly"""
        input_text = self.item_textbox.toPlainText()

        money = {
            Origins.ITEM: Money(origin=Origins.ITEM),
            Origins.ART_OBJECT: Money(origin=Origins.ART_OBJECT),
            Origins.CURRENCY: Money(origin=Origins.CURRENCY),
        }
        levels: dict[str, int] = {}
        categories: dict[str, int] = {}
        subcategories: dict[str, int] = {}
        rarities: dict[str, int] = {}

        loot = process_loot_file(io.StringIO(input_text))
        get_loot_stats(loot, money, levels, categories, subcategories, rarities)

        for origin in money.keys():
            money[origin].gp += money[origin].cp // 100
            money[origin].gp += money[origin].sp // 10
            money[origin].cp %= 100
            money[origin].sp %= 10

        def get_total(money_list):
            res = Money(origin=Origins.TOTAL, check_origin=False)
            for item in money_list:
                res += item
            return res

        money[Origins.TOTAL] = get_total(money.values())

        self.update_ui(money, levels, categories, subcategories, rarities)

    def update_ui(
        self,
        money: dict[Origins, Money],
        levels: dict[str, int],
        categories: dict[str, int],
        subcategories: dict[str, int],
        rarities: dict[str, int],
    ):
        self.totalcp_label.setText(f"{money[Origins.TOTAL].cp} cp")
        self.totalsp_label.setText(f"{money[Origins.TOTAL].sp} sp")
        self.totalgp_label.setText(f"{money[Origins.TOTAL].gp} gp")

        self.itemsgp_label.setText(f"Items: {money[Origins.ITEM].gp} gp")
        self.artobjgp_label.setText(f"Art objects: {money[Origins.ART_OBJECT].gp} gp")
        self.currencygp_label.setText(f"Currency: {money[Origins.CURRENCY].gp} gp")

        min_level = self.minlvlcmp_spinbox.value()
        max_level = self.maxlvlcmp_spinbox.value()
        total_value = tbl["Total Value"][min_level - 1 : max_level].sum()

        self.expected_label.setText(f"Expected: {total_value} gp")

        if total_value - money[Origins.TOTAL].gp < 0:
            self.difference_label.setText(
                f"Difference: {abs(total_value - money[Origins.TOTAL].gp)} gp too much"
            )
        elif total_value - money[Origins.TOTAL].gp > 0:
            self.difference_label.setText(
                f"Difference: {abs(total_value - money[Origins.TOTAL].gp)} gp too little"
            )
        else:
            self.difference_label.setText(f"Difference: None")

        self.remove_previous_labels()

        for lvl, amount in levels.items():
            self.temp_label = QtW.QLabel(self.breakdown_widget)
            self.temp_label.setObjectName(f"level{lvl}_label")
            self.temp_label.setText(f"Level {lvl}: {amount}")
            self.levels_vbox.addWidget(self.temp_label)

        for cat, amount in categories.items():
            self.temp_label = QtW.QLabel(self.breakdown_widget)
            self.temp_label.setObjectName(f"{cat}_label")
            self.temp_label.setText(f"{cat.capitalize()}: {amount}")
            self.categories_vbox.addWidget(self.temp_label)

        for subcat, amount in subcategories.items():
            self.temp_label = QtW.QLabel(self.breakdown_widget)
            self.temp_label.setObjectName(f"{subcat}_label")
            self.temp_label.setText(f"{subcat.capitalize()}: {amount}")
            self.subcategories_vbox.addWidget(self.temp_label)

        for rar, amount in rarities.items():
            self.temp_label = QtW.QLabel(self.breakdown_widget)
            self.temp_label.setObjectName(f"{rar}_label")
            self.temp_label.setText(f"{rar.capitalize()}: {amount}")
            self.rarities_vbox.addWidget(self.temp_label)

    def remove_previous_labels(self):
        for vbox in (
            self.levels_vbox,
            self.categories_vbox,
            self.subcategories_vbox,
            self.rarities_vbox,
        ):
            labels = (vbox.itemAt(i) for i in range(vbox.count()))
            for label in labels:
                widget = label.widget()
                if all(
                    widget.objectName() != name
                    for name in (
                        "levels_label",
                        "categories_label",
                        "subcategories_label",
                        "rarities_label",
                    )
                ):
                    widget.deleteLater()


def gui_entry_point() -> int:
    app = QtW.QApplication([])
    win = MainWindow()
    win.show()
    return app.exec()
