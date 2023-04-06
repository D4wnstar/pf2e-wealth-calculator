from pf2e_wealth_calculator.pf2ewc import get_loot_stats, process_loot_file
from pf2e_wealth_calculator.structs import Origins, Money

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QCoreApplication as QCA
from PyQt6 import QtGui
import pandas as pd

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
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))

        self.menu_file = QtW.QMenu(self.menubar)
        self.menu_file.setObjectName(u"menuFile")
        self.menubar.addAction(self.menu_file.menuAction())

        self.menu_edit = QtW.QMenu(self.menubar)
        self.menu_edit.setObjectName(u"menuEdit")        
        self.menubar.addAction(self.menu_edit.menuAction())
        
        self.setMenuBar(self.menubar)
        
        self.statusbar = QtW.QStatusBar(self)
        self.statusbar.setObjectName(u"statusbar")
        
        self.setStatusBar(self.statusbar)

        self.action_open = QtGui.QAction(self)
        self.action_open.setObjectName(u"actionOpen")
        self.menu_file.addAction(self.action_open)

        self.action_save = QtGui.QAction(self)
        self.action_save.setObjectName(u"actionSave")
        self.menu_file.addAction(self.action_save)
        
        self.action_copy = QtGui.QAction(self)
        self.action_copy.setObjectName(u"actionCopy")
        self.menu_edit.addAction(self.action_copy)
        
        self.action_cut = QtGui.QAction(self)
        self.action_cut.setObjectName(u"actionCut")
        self.menu_edit.addAction(self.action_cut)
        
        self.action_paste = QtGui.QAction(self)
        self.action_paste.setObjectName(u"actionPaste")
        self.menu_edit.addAction(self.action_paste)


    def init_fonts(self):
        self.title_font = QtGui.QFont()
        self.title_font.setFamilies([u"Constantia"])
        self.title_font.setPointSize(14)
        self.title_font.setBold(True)
        self.title_font.setUnderline(True)
        self.title_font.setKerning(True)
        self.title_font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferDefault)

        self.subtitle_font = QtGui.QFont()
        self.subtitle_font.setFamilies([u"Constantia"])
        self.subtitle_font.setPointSize(11)


    def init_input_ui(self):
        self.input_label = QtW.QLabel(self.centralwidget)
        self.input_label.setObjectName(u"input_label")
        self.input_label.setGeometry(QtCore.QRect(40, 10, 191, 41))
        self.input_label.setFont(self.title_font)
        self.input_label.setCursor(QtGui.QCursor(Qt.CursorShape.ArrowCursor))
        self.input_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.item_textbox = QtW.QPlainTextEdit(self.centralwidget)
        self.item_textbox.setObjectName(u"item_textbox")
        self.item_textbox.setGeometry(QtCore.QRect(20, 50, 231, 221))

        self.calculate_button = QtW.QPushButton(self.centralwidget)
        self.calculate_button.setObjectName(u"calculate_button")
        self.calculate_button.setGeometry(QtCore.QRect(40, 290, 191, 41))


    def init_random_ui(self):
        self.random_label = QtW.QLabel(self.centralwidget)
        self.random_label.setObjectName(u"random_label")
        self.random_label.setGeometry(QtCore.QRect(40, 360, 191, 41))
        self.random_label.setFont(self.title_font)
        self.random_label.setCursor(QtGui.QCursor(Qt.CursorShape.ArrowCursor))
        self.random_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.randomize_button = QtW.QPushButton(self.centralwidget)
        self.randomize_button.setObjectName(u"randomize_button")
        self.randomize_button.setGeometry(QtCore.QRect(40, 500, 191, 41))

        self.layoutWidget = QtW.QWidget(self.centralwidget)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QtCore.QRect(20, 403, 231, 91))
        
        self.rand_param_grid = QtW.QGridLayout(self.layoutWidget)
        self.rand_param_grid.setObjectName(u"rand_param_grid")
        self.rand_param_grid.setContentsMargins(0, 0, 0, 0)
        
        self.nitems_spinbox = QtW.QSpinBox(self.layoutWidget)
        self.nitems_spinbox.setObjectName(u"nitems_spinbox")
        self.nitems_spinbox.setValue(5)
        self.rand_param_grid.addWidget(self.nitems_spinbox, 0, 1, 1, 1)

        self.lvlrange_label = QtW.QLabel(self.layoutWidget)
        self.lvlrange_label.setObjectName(u"lvlrange_label")
        self.rand_param_grid.addWidget(self.lvlrange_label, 1, 0, 1, 1)

        self.nitems_label = QtW.QLabel(self.layoutWidget)
        self.nitems_label.setObjectName(u"nitems_label")
        self.rand_param_grid.addWidget(self.nitems_label, 0, 0, 1, 1)

        self.minlvl_spinbox = QtW.QSpinBox(self.layoutWidget)
        self.minlvl_spinbox.setObjectName(u"minlvl_spinbox")
        self.rand_param_grid.addWidget(self.minlvl_spinbox, 1, 1, 1, 1)

        self.maxlvl_spinbox = QtW.QSpinBox(self.layoutWidget)
        self.maxlvl_spinbox.setObjectName(u"maxlvl_spinbox")
        self.maxlvl_spinbox.setValue(30)
        self.rand_param_grid.addWidget(self.maxlvl_spinbox, 1, 2, 1, 1)


    def init_output(self):
        self.gridLayoutWidget = QtW.QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QtCore.QRect(290, 20, 491, 521))
        
        self.output_grid = QtW.QGridLayout(self.gridLayoutWidget)
        self.output_grid.setObjectName(u"output_grid")
        self.output_grid.setContentsMargins(0, 0, 0, 0)
        
        self.totalvalue_vbox = QtW.QVBoxLayout()
        self.totalvalue_vbox.setObjectName(u"totalvalue_vbox")
        
        self.totalvalue_label = QtW.QLabel(self.gridLayoutWidget)
        self.totalvalue_label.setObjectName(u"totalvalue_label")
        self.totalvalue_label.setFont(self.title_font)

        self.totalvalue_vbox.addWidget(self.totalvalue_label)

        self.totalcp_label = QtW.QLabel(self.gridLayoutWidget)
        self.totalcp_label.setObjectName(u"totalcp_label")

        self.totalvalue_vbox.addWidget(self.totalcp_label)

        self.totalsp_label = QtW.QLabel(self.gridLayoutWidget)
        self.totalsp_label.setObjectName(u"totalsp_label")

        self.totalvalue_vbox.addWidget(self.totalsp_label)

        self.totalgp_label = QtW.QLabel(self.gridLayoutWidget)
        self.totalgp_label.setObjectName(u"totalgp_label")

        self.totalvalue_vbox.addWidget(self.totalgp_label)

        self.ofwhich_label = QtW.QLabel(self.gridLayoutWidget)
        self.ofwhich_label.setObjectName(u"ofwhich_label")
        self.ofwhich_label.setFont(self.subtitle_font)

        self.totalvalue_vbox.addWidget(self.ofwhich_label)

        self.itemsgp_label = QtW.QLabel(self.gridLayoutWidget)
        self.itemsgp_label.setObjectName(u"itemsgp_label")

        self.totalvalue_vbox.addWidget(self.itemsgp_label)

        self.artobjgp_label = QtW.QLabel(self.gridLayoutWidget)
        self.artobjgp_label.setObjectName(u"artobjgp_label")

        self.totalvalue_vbox.addWidget(self.artobjgp_label)

        self.currencygp_label = QtW.QLabel(self.gridLayoutWidget)
        self.currencygp_label.setObjectName(u"currencygp_label")

        self.totalvalue_vbox.addWidget(self.currencygp_label)

        self.output_grid.addLayout(self.totalvalue_vbox, 0, 0, 1, 1)

        self.breakdown_vbox = QtW.QVBoxLayout()
        self.breakdown_vbox.setObjectName(u"breakdown_vbox")
        self.breakdown_label = QtW.QLabel(self.gridLayoutWidget)
        self.breakdown_label.setObjectName(u"breakdown_label")
        self.breakdown_label.setFont(self.title_font)

        self.breakdown_vbox.addWidget(self.breakdown_label)

        self.levels_vbox = QtW.QVBoxLayout()
        self.levels_vbox.setObjectName(u"levels_vbox")
        self.levels_label = QtW.QLabel(self.gridLayoutWidget)
        self.levels_label.setObjectName(u"levels_label")
        self.levels_label.setFont(self.subtitle_font)

        self.levels_vbox.addWidget(self.levels_label)

        self.levelsexample_label = QtW.QLabel(self.gridLayoutWidget)
        self.levelsexample_label.setObjectName(u"levelsexample_label")

        self.levels_vbox.addWidget(self.levelsexample_label)


        self.breakdown_vbox.addLayout(self.levels_vbox)

        self.categories_vbox = QtW.QVBoxLayout()
        self.categories_vbox.setObjectName(u"categories_vbox")
        self.categories_label = QtW.QLabel(self.gridLayoutWidget)
        self.categories_label.setObjectName(u"categories_label")
        self.categories_label.setFont(self.subtitle_font)

        self.categories_vbox.addWidget(self.categories_label)

        self.catexamples_label = QtW.QLabel(self.gridLayoutWidget)
        self.catexamples_label.setObjectName(u"catexamples_label")

        self.categories_vbox.addWidget(self.catexamples_label)


        self.breakdown_vbox.addLayout(self.categories_vbox)

        self.subcategory_vbox = QtW.QVBoxLayout()
        self.subcategory_vbox.setObjectName(u"subcategory_vbox")
        self.subcategory_label = QtW.QLabel(self.gridLayoutWidget)
        self.subcategory_label.setObjectName(u"subcategory_label")
        self.subcategory_label.setFont(self.subtitle_font)

        self.subcategory_vbox.addWidget(self.subcategory_label)

        self.subcatexample_label = QtW.QLabel(self.gridLayoutWidget)
        self.subcatexample_label.setObjectName(u"subcatexample_label")

        self.subcategory_vbox.addWidget(self.subcatexample_label)


        self.breakdown_vbox.addLayout(self.subcategory_vbox)

        self.rarities_vbox = QtW.QVBoxLayout()
        self.rarities_vbox.setObjectName(u"rarities_vbox")
        self.rarities_label = QtW.QLabel(self.gridLayoutWidget)
        self.rarities_label.setObjectName(u"rarities_label")
        self.rarities_label.setFont(self.subtitle_font)

        self.rarities_vbox.addWidget(self.rarities_label)

        self.rarexample_label = QtW.QLabel(self.gridLayoutWidget)
        self.rarexample_label.setObjectName(u"rarexample_label")

        self.rarities_vbox.addWidget(self.rarexample_label)


        self.breakdown_vbox.addLayout(self.rarities_vbox)


        self.output_grid.addLayout(self.breakdown_vbox, 0, 1, 2, 1)

        self.comparison_vbox = QtW.QVBoxLayout()
        self.comparison_vbox.setObjectName(u"comparison_vbox")
        self.comparison_label = QtW.QLabel(self.gridLayoutWidget)
        self.comparison_label.setObjectName(u"comparison_label")
        self.comparison_label.setFont(self.title_font)

        self.comparison_vbox.addWidget(self.comparison_label)

        self.expected_label = QtW.QLabel(self.gridLayoutWidget)
        self.expected_label.setObjectName(u"expected_label")

        self.comparison_vbox.addWidget(self.expected_label)

        self.difference_label = QtW.QLabel(self.gridLayoutWidget)
        self.difference_label.setObjectName(u"difference_label")

        self.comparison_vbox.addWidget(self.difference_label)

        self.output_grid.addLayout(self.comparison_vbox, 1, 0, 1, 1)


    def init_dividers(self):
        self.hline = QtW.QFrame(self.centralwidget)
        self.hline.setObjectName(u"hline")
        self.hline.setGeometry(QtCore.QRect(7, 340, 261, 20))
        self.hline.setFrameShape(QtW.QFrame.Shape.HLine)
        self.hline.setFrameShadow(QtW.QFrame.Shadow.Sunken)

        self.vline = QtW.QFrame(self.centralwidget)
        self.vline.setObjectName(u"vline")
        self.vline.setGeometry(QtCore.QRect(260, 20, 20, 521))
        self.vline.setFrameShape(QtW.QFrame.Shape.VLine)
        self.vline.setFrameShadow(QtW.QFrame.Shadow.Sunken)


    def retranslate_ui(self):
        self.action_open.setText(QCA.translate("main_window", u"Open", None))
        self.action_save.setText(QCA.translate("main_window", u"Save", None))
        self.action_copy.setText(QCA.translate("main_window", u"Copy", None))
        self.action_cut.setText(QCA.translate("main_window", u"Cut", None))
        self.action_paste.setText(QCA.translate("main_window", u"Paste", None))
        self.input_label.setText(QCA.translate("main_window", u"INPUT", None))
        self.item_textbox.setPlaceholderText(QCA.translate("main_window", u"Add your items here!", None))
        self.random_label.setText(QCA.translate("main_window", u"RANDOM", None))
        self.randomize_button.setText(QCA.translate("main_window", u"Randomize!", None))
        self.totalvalue_label.setText(QCA.translate("main_window", u"TOTAL VALUE", None))
        self.totalcp_label.setText(QCA.translate("main_window", u"0 cp", None))
        self.totalsp_label.setText(QCA.translate("main_window", u"0 sp", None))
        self.totalgp_label.setText(QCA.translate("main_window", u"0 gp", None))
        self.ofwhich_label.setText(QCA.translate("main_window", u"OF WHICH", None))
        self.itemsgp_label.setText(QCA.translate("main_window", u"Items: 0 gp", None))
        self.artobjgp_label.setText(QCA.translate("main_window", u"Art objects: 0 gp", None))
        self.currencygp_label.setText(QCA.translate("main_window", u"Currency: 0 gp", None))
        self.breakdown_label.setText(QCA.translate("main_window", u"BREAKDOWN", None))
        self.levels_label.setText(QCA.translate("main_window", u"LEVELS", None))
        self.levelsexample_label.setText(QCA.translate("main_window", u"...", None))
        self.categories_label.setText(QCA.translate("main_window", u"CATEGORIES", None))
        self.catexamples_label.setText(QCA.translate("main_window", u"...", None))
        self.subcategory_label.setText(QCA.translate("main_window", u"SUBCATEGORIES", None))
        self.subcatexample_label.setText(QCA.translate("main_window", u"...", None))
        self.rarities_label.setText(QCA.translate("main_window", u"RARITIES", None))
        self.rarexample_label.setText(QCA.translate("main_window", u"...", None))
        self.comparison_label.setText(QCA.translate("main_window", u"COMPARISON", None))
        self.expected_label.setText(QCA.translate("main_window", u"Expected: 0 gp", None))
        self.difference_label.setText(QCA.translate("main_window", u"Difference: None", None))
        self.calculate_button.setText(QCA.translate("main_window", u"Calculate!", None))
        self.lvlrange_label.setText(QCA.translate("main_window", u"Level range (min/max):", None))
        self.nitems_label.setText(QCA.translate("main_window", u"Number of items:", None))
        self.menu_file.setTitle(QCA.translate("main_window", u"File", None))
        self.menu_edit.setTitle(QCA.translate("main_window", u"Edit", None))


    def init_ui(self):
        self.centralwidget = QtW.QWidget(self)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setEnabled(True)
        self.setCentralWidget(self.centralwidget)

        self.init_menubar()
        self.init_fonts()
        self.init_input_ui()
        self.init_random_ui()
        self.init_output()
        self.init_dividers()

        self.calculate_button.clicked.connect(self.calculate)
        
        QtW.QWidget.setTabOrder(self.item_textbox, self.calculate_button)
        QtW.QWidget.setTabOrder(self.calculate_button, self.nitems_spinbox)
        QtW.QWidget.setTabOrder(self.nitems_spinbox, self.minlvl_spinbox)
        QtW.QWidget.setTabOrder(self.minlvl_spinbox, self.maxlvl_spinbox)
        QtW.QWidget.setTabOrder(self.maxlvl_spinbox, self.randomize_button)

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

    
    def update_ui(self,
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


def gui_entry_point() -> int:
    app = QtW.QApplication([])
    win = MainWindow()
    win.show()
    return app.exec()
