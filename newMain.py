# =======================================================
# This is a project for 문제해결과컴퓨팅사고 SKKU 2026-1
# Team: 지시약과 아이들
# Licence for PySide6 by LGPL #TODO: To be added Later
# =======================================================

# Imports
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Callable
from enum import Enum
import copy
import math

# PySide6 Imports
from PySide6.QtCore import (
    Signal, QEvent,                                         # Signals & Events
    QPointF, QRect,                                         # Geometry & Coordinates
    Qt, QObject, QTimer,                                    # Utilities / Timing / Flags
)
from PySide6.QtGui import (
    QPainter, QPaintEvent, QPen, QPolygonF, QTransform,     # Painting & Drawing
    QColor, QCursor,                                        # Colors & Cursor
    QMouseEvent,                                            # Input Events
)
from PySide6.QtWidgets import (
    # Application
    QApplication, QMainWindow,
    # Containers & Layouts
    QColorDialog, QDialog, QFrame, QGroupBox, QStackedWidget, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget,
    # Input Widgets
    QComboBox, QDoubleSpinBox, QLineEdit, QPushButton, QRadioButton, QSlider, QToolButton,
    # Etc
    QLabel, QAbstractItemView, QTableWidgetItem, QHeaderView, QToolTip
)

# =======================================================
# Memory Management Policy (MMP)
# 1. All Variables Kept Singleton, Passed by Reference
# 2. Exception for Initialization of Internal Variables
# =======================================================
# Type Annotation Policy
# 1. All Non-Widget Class Data Variable Types Annotated
# 2. Return Values Annotated When Not Explicit
# 3. When Explicit, Return Values Optionally Annotated
# =======================================================

# =======================================================
# Abstract Objects: For Calculation and Simulation
# =======================================================

# Chemical: Stores information of a single substance
@dataclass
class Chemical():
    # All chemicals are treated monoprotic including indicators
    name: str
    is_acid: bool
    is_strong: bool
    pK_: float | None = None # pKa or pKb depending on is_acid
    # Only for indicators
    acid_color: QColor | None = None # Acid Color (HIn)
    base_color: QColor | None = None # Base Color (In-)

# PureSolution: Stores solution info (Chemical, Concentration, Volume)
@dataclass
class PureSolution():
    chemical: Chemical
    concentration: float
    volume: float | None = None # This field does not exist for titrants

# ChemicalType: Enum["ACID", "BASE", "INDICATOR"] --> Specific Categorization for this App
class ChemicalType(Enum):
    ACID = "ACID"
    BASE = "BASE"
    INDICATOR = "INDICATOR"

# SimulationConfigData: Configuration Data for Simulation
@dataclass
class SimulationConfigData():
    analyte: PureSolution | None = None
    titrant: PureSolution | None = None
    indicators: List[Chemical] = field(default_factory=list)
    def clear(self): # Reinitialize
        self.analyte = self.titrant = None
        self.indicators.clear()
    
# Simulation: Main Class for Simulation Management, Used To Calculate States
class Simulation:
    def __init__(self):
        # Library of predefined chemicals
        self.predefined_chemical_library: Dict[ChemicalType, Dict[str, Chemical]] = {
            ChemicalType.ACID: {
                # Strong Acids
                "HYDROCHLORIC_ACID": Chemical("HCl (Hydrochloric Acid)", True, True),
                # Weak Acids
                "ACETIC_ACID": Chemical("CH₃COOH (Acetic Acid)", True, False, 4.76)
            },
            ChemicalType.BASE: {
                # Strong Bases
                "SODIUM_HYDROXIDE": Chemical("NaOH (Sodium Hydroxide)", False, True),
                # Weak Bases
                "SODIUM_ACETATE": Chemical("CH₃COONa (Sodium Acetate)", False, False, 9.24)
            },
            ChemicalType.INDICATOR: {
                # All indicators are weak
                "METHYL_ORANGE": Chemical("Methyl Orange", True, False, 3.47, QColor(220, 40, 40), QColor(220, 40, 40)),
                "BROMOTHYMOL_BLUE": Chemical("Bromothymol Blue (BTB)", True, False, 7.0, QColor(240, 220, 0), QColor(240, 220, 0)),
                "PHENOLPHTHALEIN": Chemical("Phenolphthalein", True, False, 9.3, QColor(0, 0, 0), QColor(255, 20, 147))
            },
        }
        # Users will add/edit/delete from this dictionary
        self.custom_chemical_library: Dict[ChemicalType, Dict[str, Chemical]] = {
            ChemicalType.ACID: {},
            ChemicalType.BASE: {},
            ChemicalType.INDICATOR: {},
        }
        self.config_data: SimulationConfigData | None = None
        self.titrant_volume: float = 0.0
    def start(self, config_data: SimulationConfigData):
        self.config_data = config_data
        self.titrant_volume = 0.0
    def end(self):
        self.config_data = None
        self.titrant_volume = 0.0
    def get_max_titrant_volume(self) -> float:
        # Allow twice the volume of equivalence point
        # This function is unsafe, only use when config_data exists
        return self.config_data.analyte.concentration * self.config_data.analyte.volume / self.config_data.titrant.concentration * 2
    def get_mixture_volume(self) -> float: return self.config_data.analyte.volume + self.titrant_volume

# =======================================================
# Manage Chemicals: Manage List of Chemicals Used in App
# TODO: Add Tool tip to elements
# =======================================================

# ColorPickerWidget: Wrapper of Color Selection Dialog for Indicator Color Selection
class ColorPickerWidget(QWidget):
    def __init__(self, button_text: str, initial: QColor | None = None):
        super().__init__()
        # self.setWindowTitle("Custom Color Tool")
        self.selected_color: QColor = QColor("gray") # Default color needed for QColorDialog.getColor
        self.button_text: str = button_text # Used for title of color selection dialog (Acid/Base Color)

        layout = QHBoxLayout(self)
        button_pick = QToolButton()
        button_pick.setText(button_text)
        self.label_pick = QLabel("선택된 색 : 없음")
        self.color_swatch = QLabel()
        self.color_swatch.setFixedSize(15, 15)  # Make it a square
        layout.addWidget(button_pick)
        layout.addWidget(self.label_pick)
        layout.addWidget(self.color_swatch)

        # Load default color if it exists
        if initial:
            self.selected_color = copy.deepcopy(initial) # Dereference for Initialization by MMP-2
            self.label_pick.setText(f"선택된 색 : {initial.name()}")
            self.color_swatch.setStyleSheet(f"background-color: {initial.name()}; border: 1px solid black;") #TODO: Restyle swatch size and QSS
        
        # Signals
        button_pick.clicked.connect(self._choose_color)
    def _choose_color(self):
        color: QColor = QColorDialog.getColor(self.selected_color, self, self.button_text) #TODO: getColor language control is not managed: displays system lanaguage - check needed
        if color.isValid():
            self.selected_color = color
            self.label_pick.setText(f"선택된 색 : {color.name()}")
            self.color_swatch.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;") #TODO: Restyle swatch size and QSS
    def get_selected_color(self) -> QColor | None:
        if self.label_pick.text() == "선택된 색 : 없음": return None # Check manually by string since selected_color is always valid
        return self.selected_color

# AddEditChemicalModal: Modal Containing Fields for Individual Chemical Add/Edit
class AddEditChemicalModal(QDialog):
    def __init__(
        self,
        parent: QWidget,
        is_indicator: bool,
        initial: Chemical | None = None, # if exists serves as initial value (edit mode), else (add mode)
        is_acid: bool = True # is_acid field not used when is_indicator == True
    ):
        super().__init__(parent)
        self.is_indicator: bool = is_indicator

        layout = QVBoxLayout(self)
        # Name
        layout_name = QHBoxLayout()
        layout.addLayout(layout_name)
        label_name = QLabel("이름 :")
        self.lineedit_name = QLineEdit()
        layout_name.addWidget(label_name)
        layout_name.addWidget(self.lineedit_name)
        if not is_indicator:
            # Strength
            self.is_acid: bool = is_acid
            layout_strength = QHBoxLayout()
            layout.addLayout(layout_strength)
            label_strength = QLabel("세기 :")
            self.combobox_strength = QComboBox()
            self.combobox_strength.addItem("선택 안함", None)
            self.combobox_strength.addItem("강산" if is_acid else "강염기", True)
            self.combobox_strength.addItem("약산" if is_acid else "약염기", False)
            layout_strength.addWidget(label_strength)
            layout_strength.addWidget(self.combobox_strength)
            self.combobox_strength.currentIndexChanged.connect(self._on_strength_combobox_index_change)
        else:
            # Is Acid or not
            layout_is_acid = QHBoxLayout()
            layout.addLayout(layout_is_acid)
            label_is_acid = QLabel("액성")
            self.combobox_is_acid = QComboBox()
            self.combobox_is_acid.addItem("선택 안함", None)
            self.combobox_is_acid.addItem("산성", True)
            self.combobox_is_acid.addItem("염기성", False)
            layout_is_acid.addWidget(label_is_acid)
            layout_is_acid.addWidget(self.combobox_is_acid)
        # pKa or pKb
        layout_pK_ = QHBoxLayout()
        layout.addLayout(layout_pK_)
        self.label_pK_ = QLabel(
            "pK<sub>a</sub>/pK<sub>b</sub> :" if is_indicator
            else ("pK<sub>a</sub> :" if is_acid else "pK<sub>b</sub> :")
        )
        self.dspin_pK_ = QDoubleSpinBox()
        self.dspin_pK_.setRange(0.00, 14.00)
        self.dspin_pK_.setSingleStep(0.01)
        self.dspin_pK_.setDecimals(2)
        layout_pK_.addWidget(self.label_pK_)
        layout_pK_.addWidget(self.dspin_pK_)
        self.label_pK_.setEnabled(is_indicator)
        self.dspin_pK_.setEnabled(is_indicator)
        # Color selection
        if is_indicator:
            if initial:
                self.select_acid_color = ColorPickerWidget("산성에서의 색 선택", initial.acid_color)
                self.select_base_color = ColorPickerWidget("염기성에서의 색 선택", initial.base_color)
            else:
                self.select_acid_color = ColorPickerWidget("산성에서의 색 선택")
                self.select_base_color = ColorPickerWidget("염기성에서의 색 선택")
            layout.addWidget(self.select_acid_color)
            layout.addWidget(self.select_base_color)
        # Buttons
        layout_buttons = QHBoxLayout()
        layout.addLayout(layout_buttons)
        button_ok = QPushButton("확인")
        button_cancel = QPushButton("취소")
        layout_buttons.addStretch(1)
        layout_buttons.addWidget(button_ok)
        layout_buttons.addWidget(button_cancel)

        # Load initial values if it exists
        if initial:
            # If we are at edit mode
            if not is_indicator:
                self.lineedit_name.setText(initial.name)
                self.lineedit_name.setReadOnly(True) # Cannot edit name
                self.combobox_strength.setCurrentIndex(1 if initial.is_strong else 2)
                if initial.pK_: self.dspin_pK_.setValue(initial.pK_)
            else:
                self.lineedit_name.setText(initial.name)
                self.lineedit_name.setReadOnly(True) # Cannot edit name
                self.combobox_is_acid.setCurrentIndex(1 if initial.is_acid else 2)
                self.dspin_pK_.setValue(initial.pK_)

        # Signals
        button_ok.clicked.connect(self._on_ok_button_click)
        button_cancel.clicked.connect(self.reject)
    def _on_strength_combobox_index_change(self, index: int):
        if index == 2:
            self.label_pK_.setEnabled(True)
            self.dspin_pK_.setEnabled(True)
        else:
            self.label_pK_.setEnabled(False)
            self.dspin_pK_.setEnabled(False)
    def _on_ok_button_click(self):
        if not self.is_indicator:
            current_data: bool | None = self.combobox_strength.currentData()
            if (
                not self.lineedit_name.text() or
                current_data == None or
                (
                    current_data == False and
                    self.dspin_pK_.value() == 0.0
                )
            ):
                # Invalid Input
                #TODO: USER WARNING TO ENTER ALL SELECTIONS
                print("FILL ALL VALUES")
                return
            else: self.accept()
        else:
            current_data: bool | None = self.combobox_is_acid.currentData()
            if (
                not self.lineedit_name.text() or
                current_data == None or
                self.dspin_pK_.value() == 0.0 or
                not self.select_acid_color.get_selected_color() or
                not self.select_base_color.get_selected_color()
            ):
                # Invalid Input
                # TODO: USER WARNING TO ENTER ALL SELECTIONS
                print("FILL ALL VALUES")
                return
            else: self.accept()
    # This is only used for chemical selection (from select button)
    @staticmethod
    def get_chemical(
        parent: QWidget,
        is_acid: bool,
        initial: Chemical | None = None
    ) -> Chemical | None:
        dialog = AddEditChemicalModal(parent, False, initial, is_acid)
        if dialog.exec() == QDialog.Accepted:
            is_strong: bool = dialog.combobox_strength.currentData()
            return Chemical(
                dialog.lineedit_name.text(),
                is_acid,
                is_strong,
                None if is_strong else dialog.dspin_pK_.value()
            )
        else: return None
    # This is only used for chemical selection (from select button)
    @staticmethod
    def get_indicator(
        parent: QWidget,
        initial: Chemical | None = None,
    ) -> Chemical | None:
        dialog = AddEditChemicalModal(parent, True, initial)
        if dialog.exec() == QDialog.Accepted:
            is_acid: bool = dialog.combobox_is_acid.currentData()
            return Chemical(
                dialog.lineedit_name.text(),
                is_acid,
                False,
                dialog.dspin_pK_.value(),
                dialog.select_acid_color.get_selected_color(),
                dialog.select_base_color.get_selected_color()
            )
        else: return None
                
# EditChemicals: Display Predefined/Custom Chemicals and Support Add/Edit/Delete for Latter
class EditChemicals(QWidget):
    chemical_selection_changed = Signal() # Emitted when a chemical is selected
    def __init__(self, simulation_obj: Simulation, chemical_type: ChemicalType):
        super().__init__()
        self.simulation_obj: Simulation = simulation_obj
        self.chemical_type: ChemicalType = chemical_type
        self.selected_chemical: Chemical | None = None

        layout = QVBoxLayout(self)
        type_name: str = (
            "산" if chemical_type == ChemicalType.ACID else (
                "염기" if chemical_type == ChemicalType.BASE else
                "지시약"
            )
        )
        #TODO: For indicators, add a visual way of seeing colors --> QSS
        # Predefined Chemicals
        groupbox_predefined = QGroupBox(f"미리 정의된 {type_name}")
        layout.addWidget(groupbox_predefined)
        layout_predefined = QVBoxLayout(groupbox_predefined)
        self.table_predefined = QTableWidget() #TODO: Change this to list + stacked widgets
        self.table_predefined.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Horizontally fills parent
        layout_predefined.addWidget(self.table_predefined)
        # Select rows instead of cells
        self.table_predefined.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Only select on row
        self.table_predefined.setSelectionMode(QAbstractItemView.SingleSelection)
        # Do not trigger edits, the table is immutable on its own
        self.table_predefined.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_predefined.setCurrentItem(None) # Default No Selection
        # Load data
        if chemical_type != ChemicalType.INDICATOR:
            self.table_predefined.setColumnCount(3)
            self.table_predefined.setHorizontalHeaderLabels(["이름", "세기", "pKa" if chemical_type == ChemicalType.ACID else "pKb"])
            cnt = self.table_predefined.rowCount() # Row count
            values = simulation_obj.predefined_chemical_library[chemical_type].values()
            for chemical in values:
                row_position = cnt
                self._create_row_chemical(self.table_predefined, row_position, chemical)
                cnt += 1
        else:
            self.table_predefined.setColumnCount(5)
            self.table_predefined.setHorizontalHeaderLabels(["이름", "액성", "pKa/pKb", "산성에서의 색", "염기성에서의 색"])
            cnt = self.table_predefined.rowCount() # Row count
            values = simulation_obj.predefined_chemical_library[ChemicalType.INDICATOR].values()
            for chemical in values:
                row_position = cnt
                self._create_row_indicator(self.table_predefined, row_position, chemical)
                cnt += 1
        # Custom Chemicals
        groupbox_custom = QGroupBox(f"사용자 정의 {type_name}")
        layout.addWidget(groupbox_custom)
        layout_custom = QVBoxLayout(groupbox_custom)
        self.table_custom = QTableWidget()
        self.table_custom.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Horizontally fills parent
        layout_custom.addWidget(self.table_custom)
        # Select rows instead of cells
        self.table_custom.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Only select on row
        self.table_custom.setSelectionMode(QAbstractItemView.SingleSelection)
        # Do not trigger edits, the table is immutable on its own
        self.table_custom.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_custom.setCurrentItem(None) # Default No Selection
        # Load data
        if chemical_type != ChemicalType.INDICATOR:
            self.table_custom.setColumnCount(3)
            self.table_custom.setHorizontalHeaderLabels(["이름", "세기", "pKa" if chemical_type == ChemicalType.ACID else "pKb"])
            cnt = self.table_custom.rowCount() # Row count
            values = simulation_obj.custom_chemical_library[chemical_type].values()
            for chemical in values:
                row_position = cnt
                self._create_row_chemical(self.table_custom, row_position, chemical)                        
                cnt += 1
        else:
            self.table_custom.setColumnCount(5)
            self.table_custom.setHorizontalHeaderLabels(["이름", "액성", "pKa/pKb", "산성에서의 색", "염기성에서의 색"])
            cnt = self.table_custom.rowCount() # Row count
            values = simulation_obj.custom_chemical_library[ChemicalType.INDICATOR].values()
            for chemical in values:
                row_position = cnt
                self._create_row_indicator(self.table_custom, row_position, chemical)
                cnt += 1
        # Add / Edit / Delete Buttons
        layout_buttons_custom = QHBoxLayout()
        layout_custom.addLayout(layout_buttons_custom)
        self.button_add = QPushButton("추가")
        self.button_edit = QPushButton("수정")
        self.button_delete = QPushButton("삭제")
        self.button_add.setAutoDefault(False) # Disables any default behavior
        self.button_edit.setAutoDefault(False) # Disables any default behavior
        self.button_delete.setAutoDefault(False) # Disables any default behavior
        layout_buttons_custom.addStretch(1)
        layout_buttons_custom.addWidget(self.button_add)
        layout_buttons_custom.addWidget(self.button_edit)
        layout_buttons_custom.addWidget(self.button_delete)
        self.button_edit.setEnabled(False)
        self.button_delete.setEnabled(False)

        # Signals
        # Open selection modal on handle double click
        self.table_custom.itemDoubleClicked.connect(self._on_item_edit)
        # On button clicks
        self.button_add.clicked.connect(self._on_add_button_click)
        self.button_edit.clicked.connect(self._on_edit_button_click)
        self.button_delete.clicked.connect(self._on_delete_button_click)
        # Allow only one table to be selected at one time
        self.table_predefined.itemClicked.connect(self._on_table_predefined_click)
        self.table_custom.itemClicked.connect(self._on_table_custom_click)
    @staticmethod
    def _create_row_chemical(table: QTableWidget, row: int, chemical: Chemical):
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(chemical.name))
        table.setItem(row, 1, QTableWidgetItem(("강" if chemical.is_strong else "약") + ("산" if chemical.is_acid else "염기")))
        if chemical.pK_: table.setItem(row, 2, QTableWidgetItem(f"{chemical.pK_:.2f}"))
        else: table.setItem(row, 2, QTableWidgetItem(""))
        # Alignment
        table.item(row, 0).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        table.item(row, 1).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        table.item(row, 2).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Add data to first item
        table.item(row, 0).setData(Qt.UserRole, chemical) # Reference Passed Directly by MMP-1
    @staticmethod
    def _create_row_indicator(table: QTableWidget, row: int, indicator: Chemical):
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(indicator.name))
        table.setItem(row, 1, QTableWidgetItem("산" if indicator.is_acid else "염기"))
        table.setItem(row, 2, QTableWidgetItem(f"{indicator.pK_:.2f}"))
        # TODO: Add color indicating --> perhaps by qss
        table.setItem(row, 3, QTableWidgetItem(f"{indicator.acid_color.name()}"))
        table.setItem(row, 4, QTableWidgetItem(f"{indicator.base_color.name()}"))
        # Alignment
        table.item(row, 0).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        table.item(row, 1).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        table.item(row, 2).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        table.item(row, 3).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        table.item(row, 4).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        # Add data to first item
        table.item(row, 0).setData(Qt.UserRole, indicator) # Reference Passed Directly by MMP-1
    @staticmethod
    def _make_key(name: str) -> str: return name.upper().replace(" ", "_")
    def _on_table_predefined_click(self):
        current_row = self.table_predefined.currentRow()
        if current_row != -1:
            # Retrieve data stored in column 0
            self.selected_chemical = self.table_predefined.item(current_row, 0).data(Qt.UserRole)
            self.table_custom.clearSelection()
            self.button_edit.setEnabled(False)
            self.button_delete.setEnabled(False)
            self.chemical_selection_changed.emit()
    def _on_table_custom_click(self):
        current_row = self.table_custom.currentRow()
        if current_row != -1:
            # Retrieve data stored in column 0
            self.selected_chemical = self.table_custom.item(current_row, 0).data(Qt.UserRole)
            self.table_predefined.clearSelection()
            self.button_edit.setEnabled(True)
            self.button_delete.setEnabled(True)
            self.chemical_selection_changed.emit()
    def _on_add_button_click(self):
        if self.chemical_type == ChemicalType.ACID:
            new_acid = AddEditChemicalModal.get_chemical(self, True)
            if not new_acid: return
            else:
                row_position = self.table_custom.rowCount()
                self._create_row_chemical(self.table_custom, row_position, new_acid)
                self.table_custom.selectRow(row_position)
                self._on_table_custom_click()
                # Add to custom library: passed by reference by MMP-1
                self.simulation_obj.custom_chemical_library[ChemicalType.ACID].update({self._make_key(new_acid.name): new_acid})
        elif self.chemical_type == ChemicalType.BASE:
            new_base = AddEditChemicalModal.get_chemical(self, False)
            if not new_base: return
            else:
                row_position = self.table_custom.rowCount()
                self._create_row_chemical(self.table_custom, row_position, new_base)
                self.table_custom.selectRow(row_position)
                self._on_table_custom_click()
                # Add to custom library: passed by reference by MMP-1
                self.simulation_obj.custom_chemical_library[ChemicalType.BASE].update({self._make_key(new_base.name): new_base})
        else:
            # Indicator
            new_indicator = AddEditChemicalModal.get_indicator(self)
            if not new_indicator: return
            else:
                row_position = self.table_custom.rowCount()
                self._create_row_indicator(self.table_custom, row_position, new_indicator)
                self.table_custom.selectRow(row_position)
                self._on_table_custom_click()
                # Add to custom library: passed by reference by MMP-1
                self.simulation_obj.custom_chemical_library[ChemicalType.INDICATOR].update({self._make_key(new_indicator.name): new_indicator})
    def _on_edit_button_click(self):
        # Predefined elements cannot be edited
        if self.table_predefined.currentRow() != -1: return
        row_position = self.table_custom.currentRow()
        # The name of chemical is not-editable
        # Newly made chemicals from edit are discarded, while the original object is edited by MMP-1
        # Custom library and row data reference the current_chemical, so not edit of reference needed
        current_chemical: Chemical = self.table_custom.item(row_position, 0).data(Qt.UserRole)
        if self.chemical_type == ChemicalType.ACID:
            edited_acid = AddEditChemicalModal.get_chemical(self, True, current_chemical)
            if not edited_acid: return
            else:
                current_chemical.is_strong = edited_acid.is_strong
                current_chemical.pK_ = edited_acid.pK_
                self.table_custom.item(row_position, 1).setText(("강" if current_chemical.is_strong else "약") + ("산" if current_chemical.is_acid else "염기"))
                if current_chemical.pK_: self.table_custom.item(row_position, 2).setText(f"{current_chemical.pK_:.2f}")
        elif self.chemical_type == ChemicalType.BASE:
            edited_base = AddEditChemicalModal.get_chemical(self, False, current_chemical)
            if not edited_base: return
            else:
                current_chemical.is_strong = edited_base.is_strong
                current_chemical.pK_ = edited_base.pK_
                self.table_custom.item(row_position, 1).setText(("강" if current_chemical.is_strong else "약") + ("산" if current_chemical.is_acid else "염기"))
                if current_chemical.pK_: self.table_custom.item(row_position, 2).setText(f"{current_chemical.pK_:.2f}")
        else:
            # Indicator
            edited_indicator = AddEditChemicalModal.get_indicator(self, current_chemical)
            if not edited_indicator: return
            else:
                current_chemical.is_acid = edited_indicator.is_acid
                current_chemical.pK_ = edited_indicator.pK_
                # Since not direct memeber of a class the reference for color is changed by MMP-1
                current_chemical.acid_color = edited_indicator.acid_color
                current_chemical.base_color = edited_indicator.base_color
                self.table_custom.item(row_position, 1).setText("산" if current_chemical.is_acid else "염기")
                self.table_custom.item(row_position, 2).setText(f"{current_chemical.pK_:.2f}")
                #TODO: Add color indicating --> perhaps by QSS
                self.table_custom.item(row_position, 3).setText(f"{current_chemical.acid_color.name()}")
                self.table_custom.item(row_position, 4).setText(f"{current_chemical.base_color.name()}")
    def _on_item_edit(self, _: QTableWidgetItem): self._on_edit_button_click()
    def _on_delete_button_click(self):
        # Predefined elements cannot be deleted
        if self.table_predefined.currentRow() != -1: return
        row_position = self.table_custom.currentRow()
        current_chemical: Chemical = self.table_custom.item(row_position, 0).data(Qt.UserRole)
        self.simulation_obj.custom_chemical_library[self.chemical_type].pop(self._make_key(current_chemical.name))
        self.table_custom.removeRow(row_position)
        self.table_custom.clearSelection()
        self.button_edit.setEnabled(False)
        self.button_delete.setEnabled(False)
        # Disable Selection
        self.selected_chemical = None
        self.chemical_selection_changed.emit()

# ManageSelectChemicalsModal: Modal Chat Allows Managing and Selecting Chemicals
class ManageSelectChemicalsModal(QDialog):
    def __init__(
        self,
        parent: QWidget,
        simulation_obj: Simulation,
        enable_select: bool,
        enable_acid: bool,
        enable_base: bool,
        enable_indicator: bool
    ):
        # enable_select: True enables final selection ok, if False, the final Cancel button and selection label is removed
        # enable_acid/base/indicator enables their tabs
        super().__init__(parent)
        self.simulation_obj: Simulation = simulation_obj       
        self.setWindowTitle("물질 선택" if enable_select else "물질 추가/제거")
        self.setModal(True)

        # self.setGeometry --> #TODO: Set position
        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        # TODO: Couldn't find a way to not rotate text
        # self.tab_widget.setTabPosition(QTabWidget.West) # Set tabs to left
        editchemicals_acid = EditChemicals(simulation_obj, ChemicalType.ACID)
        editchemicals_base = EditChemicals(simulation_obj, ChemicalType.BASE)
        editchemicals_indicator = EditChemicals(simulation_obj, ChemicalType.INDICATOR)
        self.tab_widget.addTab(editchemicals_acid, "산")
        self.tab_widget.addTab(editchemicals_base, "염기")
        self.tab_widget.addTab(editchemicals_indicator, "지시약")
        # Enable/Disable tab
        self.tab_widget.setTabEnabled(0, enable_acid)
        self.tab_widget.setTabEnabled(1, enable_base)
        self.tab_widget.setTabEnabled(2, enable_indicator)

        # Selection and OK/Cancel Buttons
        layout_selection_and_buttons = QHBoxLayout()
        layout.addLayout(layout_selection_and_buttons)
        self.label_selected_chemical = QLabel("선택된 물질 : 없음")
        if not enable_select: self.label_selected_chemical.hide() # Show only for selection mode
        self.button_ok = QPushButton("확인")
        self.button_ok.setEnabled(not enable_select) # Initial disablement since no chemical is selected
        button_cancel = QPushButton("취소")
        layout_selection_and_buttons.addStretch(1) # Left shift all contents
        layout_selection_and_buttons.addWidget(self.label_selected_chemical)
        layout_selection_and_buttons.addWidget(self.button_ok)
        layout_selection_and_buttons.addWidget(button_cancel)
        if not enable_select: button_cancel.hide() # Cancel not needed if not selection mode

        # Signals
        editchemicals_acid.chemical_selection_changed.connect(self._on_chemical_select_status_change)
        editchemicals_base.chemical_selection_changed.connect(self._on_chemical_select_status_change)
        editchemicals_indicator.chemical_selection_changed.connect(self._on_chemical_select_status_change)
        self.tab_widget.currentChanged.connect(self._on_current_tab_change)
        self.button_ok.clicked.connect(self.accept)
        button_cancel.clicked.connect(self.reject)
    def _get_selected_chemical(self) -> Chemical | None:
        current_widget: EditChemicals = self.tab_widget.currentWidget()
        return current_widget.selected_chemical
    def _update_ok_button_enabled(self):
        # If there is no selected chemical ok should be disabled
        print(self._get_selected_chemical(), not not self._get_selected_chemical())
        self.button_ok.setEnabled(not not self._get_selected_chemical())
    def _on_chemical_select_status_change(self):
        self.label_selected_chemical.setText(f"선택된 물질 : {"없음" if not self._get_selected_chemical() else self._get_selected_chemical().name}")
        self._update_ok_button_enabled()
    def _on_current_tab_change(self, _: int):
        self._on_chemical_select_status_change()
    @staticmethod
    def manage_chemicals(
        parent: QWidget,
        simulation_obj: Simulation,
        enable_acid: bool,
        enable_base: bool,
        enable_indicator: bool
    ):
        # This is only used to manage chemicals (from menubar)
        dialog = ManageSelectChemicalsModal(parent, simulation_obj, False, enable_acid, enable_base, enable_indicator)
        dialog.exec()
    def get_chemical(
        parent: QWidget,
        simulation_obj: Simulation,
        enable_acid: bool,
        enable_base: bool,
        enable_indicator: bool
    ) -> Chemical | None:
        # This is only used for chemical selection (from select button)
        dialog = ManageSelectChemicalsModal(parent, simulation_obj, True, enable_acid, enable_base, enable_indicator)
        if dialog.exec() == QDialog.Accepted: return dialog._get_selected_chemical()
        else: return None

# =======================================================
# Configuration: Getting Configs for Simulation
# =======================================================

# DynamicIndicatorListEntry: Entry Containing Indicator Info for DynamicIndicatorList 
class DynamicIndicatorListEntry(QWidget):
    # Entries for the list
    def __init__(self, indicator: Chemical, remove_callback: Callable[[DynamicIndicatorListEntry], None]):
        super().__init__()
        self.remove_callback: Callable[[DynamicIndicatorListEntry], None] = remove_callback
        self.indicator: Chemical = indicator # Stores a reference by MMP-1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Set indicator info and X symbol for remove
        label = QLabel(f"{indicator.name}, pK<sub>{"a" if indicator.is_acid else "b"}</sub>={indicator.pK_:.2f}")
        self.button_remove = QToolButton()
        self.button_remove.setText("✕") #TODO: Replace with icon
        self.button_remove.setFixedWidth(30)
        self.button_remove.clicked.connect(lambda: self.remove_callback(self))
        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(self.button_remove)
    def set_read_only(self, read_only: bool): self.button_remove.setEnabled(not read_only)

# DynamicIndicatorList: List Allowing Selection of Indicators up to a Maximum Number
class DynamicIndicatorList(QWidget):
    def __init__(self, simulation_obj: Simulation, MAX_ENTRIES: int):
        super().__init__()
        self.simulation_obj: Simulation = simulation_obj
        self.MAX_ENTRIES: int = MAX_ENTRIES
        self.entries: List[DynamicIndicatorListEntry] = []
        self.indicators: List[Chemical] = []

        self.list_layout = QVBoxLayout(self)
        # Add + button always at bottom
        self.button_plus = QPushButton("+ 지시약 추가하기")
        self.list_layout.addWidget(self.button_plus)
        self.update_plus_visibility()

        # Signals
        self.button_plus.clicked.connect(self.add_entry)
    def add_entry(self):
        if len(self.entries) >= self.MAX_ENTRIES: return
        indicator = ManageSelectChemicalsModal.get_chemical(self, self.simulation_obj, False, False, True)
        if not indicator: return
        # Add indicator to lists
        entry = DynamicIndicatorListEntry(indicator, self.remove_entry)
        self.list_layout.insertWidget(len(self.entries), entry)
        self.entries.append(entry)
        self.update_plus_visibility()
        self.indicators.append(indicator)
    def remove_entry(self, entry_widget: DynamicIndicatorListEntry):
        self.indicators.remove(entry_widget.indicator)
        self.entries.remove(entry_widget)
        entry_widget.setParent(None) # Remove parent
        entry_widget.deleteLater() # Schedule delete
        self.update_plus_visibility()
    # The plus button disappears when max entry is reached
    def update_plus_visibility(self):
        if len(self.entries) < self.MAX_ENTRIES: self.button_plus.show()
        else: self.button_plus.hide()
    def set_read_only(self, read_only: bool):
        for entry in self.entries: entry.set_read_only(read_only)
        self.button_plus.setEnabled(not read_only)

# ConfigurationPanel: Panel on Left for Simulation Configuration
class ConfigurationPanel(QWidget):
    is_running_simulation_changed = Signal(bool) # True: start running, False: stop running
    # Panel that contains all configuration data
    def __init__(self, simulation_obj: Simulation):
        super().__init__()
        self.simulation_obj: Simulation = simulation_obj
        self.selected_analyte: Chemical | None = None
        self.selected_titrant: Chemical | None = None
        self.is_simulation_running: bool = False
        self.setFixedWidth(300) #TODO: Fix Width
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10) # Vertical Gap

        # Choose analyte/titrant and their concentration, volume
        groupbox_config = QGroupBox("적정 상황을 선택하세요")
        layout.addWidget(groupbox_config)
        layout_groupbox_config = QVBoxLayout(groupbox_config)
        layout_groupbox_config.setContentsMargins(12, 8, 12, 8)
        layout_groupbox_config.setSpacing(4)

        # Select analyate and display its properties
        layout_analyte_choose = QHBoxLayout()
        label_analyte_tag = QLabel("분석액 :")
        label_analyte_tag.setToolTip("분석액(Analyte): 농도 분석을 할 물질")
        self.label_analyte = QLabel("—") # Displays name #TODO: QSS Value Display
        self.button_analyte_choose = QToolButton()
        self.button_analyte_choose.setText("선택")
        layout_analyte_choose.addWidget(label_analyte_tag)
        layout_analyte_choose.addWidget(self.label_analyte)
        layout_analyte_choose.addWidget(self.button_analyte_choose)
        layout_groupbox_config.addLayout(layout_analyte_choose)

        layout_analyte_info = QHBoxLayout()
        label_analyte_info_tag = QLabel("특징 :") # Displays acid/base, strength, and pKa/b if possible
        label_analyte_info_tag.setToolTip("분석액 액성(산성/염기성), 세기(강/약), 해리상수(pK<sub>a</sub>/pK<sub>b</sub>)")
        self.label_analyte_info = QLabel("—") #TODO: QSS Value Display
        layout_analyte_info.addWidget(label_analyte_info_tag)
        layout_analyte_info.addWidget(self.label_analyte_info)
        layout_groupbox_config.addLayout(layout_analyte_info)

        # Concentration and Volume of Analyte
        layout_analyte_concentration = QHBoxLayout()
        label_analyte_concentration_tag = QLabel("농도 :")
        label_analyte_concentration_tag.setToolTip("분석액 농도(M)")
        self.dspin_analyte_concentration = QDoubleSpinBox()
        self.dspin_analyte_concentration.setRange(0.01, 10.00)
        self.dspin_analyte_concentration.setSingleStep(0.01)
        self.dspin_analyte_concentration.setDecimals(2)
        self.dspin_analyte_concentration.setSuffix(" M")
        self.dspin_analyte_concentration.setValue(1.00) # Default of 1.00M
        layout_analyte_concentration.addWidget(label_analyte_concentration_tag)
        layout_analyte_concentration.addWidget(self.dspin_analyte_concentration)
        layout_groupbox_config.addLayout(layout_analyte_concentration)

        layout_analyte_volume = QHBoxLayout()
        label_analyte_volume_tag = QLabel("부피 :")
        label_analyte_volume_tag.setToolTip("분석액 부피(mL)")
        self.dspin_analyte_volume = QDoubleSpinBox()
        self.dspin_analyte_volume.setRange(10, 500)
        self.dspin_analyte_volume.setDecimals(0)
        self.dspin_analyte_volume.setSingleStep(1)
        self.dspin_analyte_volume.setSuffix(" mL")
        layout_analyte_volume.addWidget(label_analyte_volume_tag)
        layout_analyte_volume.addWidget(self.dspin_analyte_volume)
        layout_groupbox_config.addLayout(layout_analyte_volume)

        # Select titrant and display its properties
        layout_titrant_choose = QHBoxLayout()
        label_titrant_choose = QLabel("적정액 :")
        label_titrant_choose.setToolTip("적정액(Titrant): 농도 분석을 위한 표준용액")
        self.label_titrant = QLabel("—") #TODO: QSS Value Display
        self.button_titrant_choose = QToolButton()
        self.button_titrant_choose.setText("선택") #TODO: Add fixed width
        layout_titrant_choose.addWidget(label_titrant_choose)
        layout_titrant_choose.addWidget(self.label_titrant)
        layout_titrant_choose.addWidget(self.button_titrant_choose)
        layout_groupbox_config.addLayout(layout_titrant_choose)

        layout_titrant_info = QHBoxLayout()
        label_titrant_info_tag = QLabel("특징 :") # Displays acid/base, strength, and pKa/b if possible
        label_titrant_info_tag.setToolTip("적정액 액성(산성/염기성), 세기(강/약), 해리상수(pK<sub>a</sub>/pK<sub>b</sub>)")
        self.label_titrant_info = QLabel("—") #TODO: QSS Value Display
        layout_titrant_info.addWidget(label_titrant_info_tag)
        layout_titrant_info.addWidget(self.label_titrant_info)
        layout_groupbox_config.addLayout(layout_titrant_info)

        # Concentration and Volume of Titrant
        layout_titrant_concentration = QHBoxLayout()
        label_titrant_concentration_tag = QLabel("농도 :")
        label_titrant_concentration_tag.setToolTip("적정액 농도(M)")
        self.dspin_titrant_concentration = QDoubleSpinBox()
        self.dspin_titrant_concentration.setRange(0.01, 10.00)
        self.dspin_titrant_concentration.setSingleStep(0.01)
        self.dspin_titrant_concentration.setDecimals(2)
        self.dspin_titrant_concentration.setSuffix(" M")
        self.dspin_titrant_concentration.setValue(1.00) # Default 1.00M
        layout_titrant_concentration.addWidget(label_titrant_concentration_tag)
        layout_titrant_concentration.addWidget(self.dspin_titrant_concentration)
        layout_groupbox_config.addLayout(layout_titrant_concentration)
        
        # Choose indicator
        groupbox_indicator = QGroupBox("지시약을 선택하세요")
        layout.addWidget(groupbox_indicator)
        layout_groupbox_config = QVBoxLayout(groupbox_indicator)
        layout_groupbox_config.setContentsMargins(12, 8, 12, 8)
        layout_groupbox_config.setSpacing(4)

        self.indicator_list = DynamicIndicatorList(self.simulation_obj, 2)
        layout_groupbox_config.addWidget(self.indicator_list)
        
        # Buttons for clear and submit
        layout_buttons = QHBoxLayout()
        self.button_reset = QPushButton("초기화 ⟲") #TODO: Set readonly when simulation is on
        self.button_reset.setToolTip("모든 선택 사항 초기화")
        self.button_submit = QPushButton("시뮬레이션 시작 →")
        self.button_submit.setToolTip("모든 설정 사항 제출 및 시뮬레이션 시작")
        layout_buttons.addWidget(self.button_reset)
        layout_buttons.addWidget(self.button_submit)
        layout.addLayout(layout_buttons)
        #TODO: Add spacing and size
        layout.addStretch(1) # All elements above do not expand vertically
        
        # Signals
        self.button_analyte_choose.clicked.connect(self._on_analyte_choose_button_click)
        self.button_titrant_choose.clicked.connect(self._on_titrant_choose_button_click)
        #TODO: self.button_reset.clicked.connect()
        self.button_submit.clicked.connect(self._on_submit_button_click)
    def get_config_data(self) -> SimulationConfigData | None:
        if (
            not self.selected_analyte or
            not self.selected_titrant or
            not self.indicator_list.indicators
        ):
            return None
        return SimulationConfigData(
            PureSolution(
                self.selected_analyte,
                self.dspin_analyte_concentration.value(),
                self.dspin_analyte_volume.value()
            ),
            PureSolution(
                self.selected_titrant,
                self.dspin_titrant_concentration.value()
            ),
            self.indicator_list.indicators
        )
    def _on_analyte_choose_button_click(self):
        enable_acid = enable_base = True
        if self.selected_titrant:
            # Disable the selection of chemical type the other side already chose
            if self.selected_titrant.is_acid: enable_acid = False
            else: enable_base = False
        self.selected_analyte = ManageSelectChemicalsModal.get_chemical(self, self.simulation_obj, enable_acid, enable_base, False)
        # If no chemical is selected return
        if not self.selected_analyte: return
        # Display properties of selection
        self.label_analyte.setText(self.selected_analyte.name)
        if self.selected_analyte.is_acid:
            if self.selected_analyte.is_strong: self.label_analyte_info.setText("강산")
            else: self.label_analyte_info.setText(f"약산(pK<sub>a</sub>={self.selected_analyte.pK_})")
        else:
            if self.selected_analyte.is_strong: self.label_analyte_info.setText("강염기")
            else: self.label_analyte_info.setText(f"약염기(pK<sub>b</sub>={self.selected_analyte.pK_})")
    def _on_titrant_choose_button_click(self):
        enable_acid = enable_base = True
        if self.selected_analyte:
            # Disable the selection of chemical type the other side already chose
            if self.selected_analyte.is_acid: enable_acid = False
            else: enable_base = False
        self.selected_titrant = ManageSelectChemicalsModal.get_chemical(self, self.simulation_obj, enable_acid, enable_base, False)
        # If no chemical is selected return
        if not self.selected_titrant: return
        # Display properties of selection
        self.label_titrant.setText(self.selected_titrant.name)
        if self.selected_titrant.is_acid:
            if self.selected_titrant.is_strong: self.label_titrant_info.setText("강산")
            else: self.label_titrant_info.setText(f"약산(pK<sub>a</sub>={self.selected_titrant.pK_})")
        else:
            if self.selected_titrant.is_strong: self.label_titrant_info.setText("강염기")
            else: self.label_titrant_info.setText(f"약염기(pK<sub>b</sub>={self.selected_titrant.pK_})")
    def _set_readonly_and_change_submit_button(self, is_started: bool):
        # If is_started == True, readOnly=True, else readOnly=False with text changing
        self.button_analyte_choose.setEnabled(not is_started)
        self.button_titrant_choose.setEnabled(not is_started)
        self.dspin_analyte_concentration.setReadOnly(is_started)
        self.dspin_titrant_concentration.setReadOnly(is_started)
        self.dspin_analyte_volume.setReadOnly(is_started)
        self.indicator_list.set_read_only(is_started)
        self.button_reset.setEnabled(not is_started)
        self.button_submit.setText("시뮬레이션 시작 →" if not is_started else "시뮬레이션 종료")
        self.button_submit.setToolTip("모든 설정 사항 제출 및 시뮬레이션 시작" if not is_started else "시뮬레이션 종료")
    def _on_submit_button_click(self):
        # VERY IMPORTANT: Entry Point to Simulation
        if self.is_simulation_running:
            self.is_simulation_running = False
            self._set_readonly_and_change_submit_button(False)
            self.simulation_obj.end()
            self.is_running_simulation_changed.emit(False)
        else:
            config_data = self.get_config_data()
            if not config_data:
                #TODO: ADD USER WARNING
                print("Invalid Simulation Config")
                return
            self.is_simulation_running = True
            self._set_readonly_and_change_submit_button(True)
            self.simulation_obj.start(config_data)
            self.is_running_simulation_changed.emit(True)
   
# =======================================================
# Titrant Volume: Autotitration and User-Control
# =======================================================

# TitrantVolumeManager: Synchronizes Auotitration Start/Stop and User Control over Titrnat Volume
class TitrantVolumeManager(QObject):
    # Widgets should first set internal variables then emit the signal
    is_user_moving_slider_changed = Signal() # When user moving slider state changes
    is_autotitration_on_changed = Signal() # When autotitration state changes
    current_volume_changed = Signal() # Emits when volume is changed
    timer_timeout = Signal() # called when timer timeouted
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.is_autotitration_on: bool = False
        self.is_user_moving_slider: bool = False
        # Timer for Autotitration
        self.timer = QTimer(parent)
        # Signals
        self.timer.timeout.connect(self.timer_timeout.emit)
    def start_simulation(self):
        self.is_autotitration_on = False
        self.is_user_moving_slider = False
    def end_simulation(self):
        self.timer.stop()

# =======================================================
# Experiment Visuals: Visualization of Experiment
# =======================================================

# TitrationModelFactory: Creates 2D Model for Visuals
class TitrationModelFactory():
    POINTS_CONICAL_FLASK: List[QPointF] = [
        QPointF(0.5, 2.1), # 0
        QPointF(0.5, 1.6), # 1
        QPointF(0.0, 0.0), # 2
        QPointF(1.4, 0.0), # 3
        QPointF(0.9, 1.6), # 4
        QPointF(0.9, 2.1), # 5
    ]
    POINTS_BURETTE: List[QPointF] = [
        QPointF(0.52, 7.00), # 0
        QPointF(0.52, 3.00), # 1
        QPointF(0.60, 2.90), # 2
        QPointF(0.60, 2.68), # 3
        QPointF(0.50, 2.68), # 4
        QPointF(0.50, 2.46), # 5
        QPointF(0.60, 2.46), # 6
        QPointF(0.60, 2.24), # 7
        QPointF(0.70, 1.74), # 8
        QPointF(0.80, 2.24), # 9
        QPointF(0.80, 2.46), # 10
        QPointF(0.90, 2.46), # 11
        QPointF(0.90, 2.68), # 12
        QPointF(0.80, 2.68), # 13
        QPointF(0.80, 2.90), # 14
        QPointF(0.88, 3.00), # 15
        QPointF(0.88, 7.00), # 16
    ]
    POINTS_RED_SCREW: List[QPointF] = [
        QPointF(0.35, 2.72), # 0
        QPointF(0.35, 2.42), # 1
        QPointF(0.50, 2.42), # 2
        QPointF(0.50, 2.72), # 3
    ]
    POINTS_STOPCOCK_RELEASE: List[QPointF] = [
        QPointF(0.90, 2.63), # 0
        QPointF(0.90, 2.51), # 1
        QPointF(0.98, 2.51), # 2
        QPointF(1.06, 2.37), # 3
        QPointF(1.22, 2.37), # 4
        QPointF(1.22, 2.77), # 5
        QPointF(1.06, 2.77), # 6
        QPointF(0.98, 2.63), # 7
    ]
    POINTS_STOPCOCK_HOLD: List[QPointF] = [
        QPointF(0.90, 2.63), # 0
        QPointF(0.90, 2.51), # 1
        QPointF(1.22, 2.51), # 2
        QPointF(1.22, 2.63), # 3
    ] 

    def __init__(self):
        self._transform = QTransform()
        self._transform.scale(1 / 7.0, -1 / 7.0) # second
        self._transform.translate(-0.7, -3.5) # first
        self._points_conical_flask: List[QPointF] = [ self._transform.map(p) for p in self.POINTS_CONICAL_FLASK ]
        self._points_burette: List[QPointF] = [ self._transform.map(p) for p in self.POINTS_BURETTE ]
        self._points_red_screw: List[QPointF] = [ self._transform.map(p) for p in self.POINTS_RED_SCREW ]
        self._points_stopcock_release: List[QPointF] = [ self._transform.map(p) for p in self.POINTS_STOPCOCK_RELEASE ]
        self._points_stopcock_hold: List[QPointF] = [ self._transform.map(p) for p in self.POINTS_STOPCOCK_HOLD ]
    def conical_flask(self) -> QPolygonF: return QPolygonF(self._points_conical_flask)
    def burette(self) -> QPolygonF: return QPolygonF(self._points_burette)
    def red_screw(self) -> QPolygonF: return QPolygonF(self._points_red_screw)
    def stopcock(self, is_released: bool):
        if is_released: return QPolygonF(self._points_stopcock_release)
        else: return QPolygonF(self._points_stopcock_hold)
    def _fluid_conical_flask_by_height(self, ratio_height: float) -> QPolygonF:
        # 0 <= ratio < 1 as to how much the flask is filled regarding height
        return QPolygonF([
            self._points_conical_flask[1] * ratio_height + self._points_conical_flask[2] * (1 - ratio_height),
            self._points_conical_flask[2],
            self._points_conical_flask[3],
            self._points_conical_flask[4] * ratio_height + self._points_conical_flask[3] * (1 - ratio_height),
        ])
    def fluid_conical_flask(self, ratio_volume: float) -> QPolygonF:
        # Ratio = Max Volume / Current Volume --> When ratio == 1, height is 80%
        # Diameters from the slice of conical flask: only ratios are used
        upper: float = self.POINTS_CONICAL_FLASK[5].x() - self.POINTS_CONICAL_FLASK[0].x()
        lower: float = self.POINTS_CONICAL_FLASK[3].x() - self.POINTS_CONICAL_FLASK[2].x()
        max_fill: float = (4 * upper + lower) / 5 # 80% from bottom
        current_fill: float = math.cbrt(lower * lower * lower * (1 - ratio_volume) + max_fill * max_fill * max_fill * ratio_volume)
        ratio_height = (lower - current_fill) / (lower - upper)
        return self._fluid_conical_flask_by_height(ratio_height)
    def _fluid_burette_by_height(self, ratio_height: float, is_released: bool) -> QPolygonF:
        # 0 <= ratio < 1 as to how much the burette is filled regarding height
        if not is_released: return QPolygonF([
            self._points_burette[0] * ratio_height + self._points_burette[1] * (1 - ratio_height),
            self._points_burette[1],
            self._points_burette[2],
            self._points_burette[3],
            self._points_burette[13],
            self._points_burette[14],
            self._points_burette[15],
            self._points_burette[16] * ratio_height + self._points_burette[15] * (1 - ratio_height),
        ])
        else: return QPolygonF([
            self._points_burette[0] * ratio_height + self._points_burette[1] * (1 - ratio_height),
            self._points_burette[1],
            self._points_burette[2],
            self._points_burette[3],
            QPointF((0.68 - 0.7) / 7, self._points_burette[3].y()),
            self._points_burette[8],
            QPointF((0.72 - 0.7) / 7, self._points_burette[13].y()),
            self._points_burette[13],
            self._points_burette[14],
            self._points_burette[15],
            self._points_burette[16] * ratio_height + self._points_burette[15] * (1 - ratio_height),
        ])
    def fluid_burette(self, ratio_volume: float, is_released: bool) -> QPolygonF:
        # Starts with 80% full and ends at 5%
        return self._fluid_burette_by_height(ratio_volume * (0.8 - 0.05) + 0.05, is_released)

# ExperimentVisuals: Paints Experiment
class ExperimentVisuals(QWidget):
    # Colors used
    GLASS_COLOR = QColor(230, 230, 230, 40)
    TITRANT_COLOR = QColor(100, 180, 255, 150)
    WATER_COLOR = QColor(220, 230, 240, 80)
    REDSCREW_COLOR = QColor(220, 70, 70, 255)

    # Only created once simulation starts, and destroyed when over
    def __init__(self, simulation_obj: Simulation, titrant_volume_manager: TitrantVolumeManager, indicator_index: int):
        # TODO: Set Minimal Width
        super().__init__()
        self.is_released: bool = False
        self.simulation_obj: Simulation = simulation_obj
        self.titrant_volume_manager: TitrantVolumeManager = titrant_volume_manager
        self._hovering: bool = False # Prevent spawning tooltips constantly
        self.indicator_index: int = indicator_index

        self.model_factory = TitrationModelFactory()
        # Get references in order to handle mouse event
        self.painted_stopcock: QPolygonF = None
        self.setMouseTracking(True)
        
        # Signals
        self.titrant_volume_manager.is_autotitration_on_changed.connect(self._on_autotitration_on_change)
        self.titrant_volume_manager.is_user_moving_slider_changed.connect(self._on_user_moving_slider_change)
        self.titrant_volume_manager.current_volume_changed.connect(self._on_current_volume_change)
    def paintEvent(self, _: QPaintEvent):
        max_titrant_volume: float = self.simulation_obj.get_max_titrant_volume()
        current_titrant_volume: float = self.simulation_obj.titrant_volume
        analyte_volume: float = self.simulation_obj.config_data.analyte.volume
        # TODO: Render Text about  pH, indicator name
        painter = QPainter(self)
        # Float coordinates look smooth
        painter.setRenderHint(QPainter.Antialiasing)
        # Background White
        rect = self.rect()
        painter.fillRect(rect, Qt.white)
        # transform that scales and then moves (0, 0) to the center of widget
        transform = QTransform()
        w = rect.width()
        h = rect.height()
        transform.translate(w / 2, h / 2) # second
        transform.scale(h * 0.9, h * 0.9) # first
        # Draw
        # Info Rect #TODO: Set font, size, color etc properties
        rect_info = QRect(10, 10, w, 40)
        # painter.fillRect(rect_info, Qt.red)
        painter.drawText(rect_info, Qt.AlignLeft, f"{self.simulation_obj.config_data.indicators[self.indicator_index].name}\npH : 4.4")
        # Burette
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(self.GLASS_COLOR)
        painter.drawPolygon(transform.map(self.model_factory.burette()))
        # Burette Fluid
        painter.setPen(QPen(Qt.black, 0.5))
        painter.setBrush(self.TITRANT_COLOR)
        painter.drawPolygon(transform.map(self.model_factory.fluid_burette((max_titrant_volume - current_titrant_volume) / max_titrant_volume, self.is_released)))
        # Conical Flask
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(self.GLASS_COLOR)
        painter.drawPolygon(transform.map(self.model_factory.conical_flask()))
        # Conical Flask Fluid
        painter.setPen(QPen(Qt.black, 0.5))
        painter.setBrush(self.WATER_COLOR)
        painter.drawPolygon(transform.map(self.model_factory.fluid_conical_flask((analyte_volume + current_titrant_volume) / (analyte_volume + max_titrant_volume))))
        # Red Screw
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(self.REDSCREW_COLOR)
        painter.drawPolygon(transform.map(self.model_factory.red_screw()))
        # Stopcock
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(self.GLASS_COLOR)
        self.painted_stopcock = transform.map(self.model_factory.stopcock(self.is_released))
        painter.drawPolygon(self.painted_stopcock)
        painter.end()
    def mouseMoveEvent(self, event: QMouseEvent):
        # When mouse hovers above stopcock, change mouse shape to make it seem the stopcock is pressable
        if not self.painted_stopcock: return
        inside: bool = self.painted_stopcock.containsPoint(event.position(), Qt.WindingFill)
        if inside and not self._hovering:
            # Show tooltip
            QToolTip.showText(event.globalPosition().toPoint(), f"클릭하여 자동적정 {"시작" if not self.is_released else "종료"}", self)
            self._hovering = True
            # Make the stopcock look clickable
            self.setCursor(QCursor(Qt.PointingHandCursor))
        elif not inside and self._hovering:
            QToolTip.hideText()
            self._hovering = False
            self.setCursor(QCursor(Qt.ArrowCursor))
    def mousePressEvent(self, event: QMouseEvent):
        # If this is triggered, it is guaranteed that user is not moving slider
        if not self.painted_stopcock: return
        if self.painted_stopcock.containsPoint(event.position(), Qt.WindingFill):
            # Stopcock clicked --> Autotitration on/off
            self.titrant_volume_manager.is_autotitration_on = not self.is_released # If it was previously released, autotitration turns off
            self.titrant_volume_manager.is_autotitration_on_changed.emit()
    def _on_autotitration_on_change(self):
        self.is_released = self.titrant_volume_manager.is_autotitration_on
        self.update()
    def _on_user_moving_slider_change(self):
        if self.titrant_volume_manager.is_autotitration_on: return
        # Change release state only if autotitration is off, and how is determined by whether user moves slider
        self.is_released = self.titrant_volume_manager.is_user_moving_slider
        self.update()
    def _on_current_volume_change(self):
        # TODO: Add Volume to Height Transform
        # Volume is automatically handles withing paintEvent
        self.update()

# Simulation Panel: Shows up to 2 Visuals of Experiment
class SimulationPanel(QWidget):
    def __init__(self, simulation_obj: Simulation, titrant_volume_manager: TitrantVolumeManager):
        super().__init__()
        self.simulation_obj: Simulation = simulation_obj
        self.titrant_volume_manager: TitrantVolumeManager = titrant_volume_manager
        
        self.layout_main = QHBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
    def _clear_layout(self):
        # This layout should only contain widgets and stretches
        while self.layout_main.count():
            item = self.layout_main.takeAt(0) # Remove item from layout
            widget = item.widget()
            if widget: widget.deleteLater()  # Ensure that the widget is deleted
    def start_simulation(self):
        for i in range(len(self.simulation_obj.config_data.indicators)): self.layout_main.addWidget(
            ExperimentVisuals(self.simulation_obj, self.titrant_volume_manager, i)
        )
    def end_simulation(self): self._clear_layout()

# =======================================================
# Calculation Display: pH Graph, Calculation
# =======================================================

class CalculationsPanel(QTabWidget):
    def __init__(self):
        super().__init__()


# =======================================================
# Slider: Control Widget of Titrant Volume
# =======================================================

# SliderTicks: Ticks Indicating Progression of Slider
class SliderTicks(QWidget):
    def __init__(self):
        # Ticks for the slider --> variable
        super().__init__()    
        self.setFixedHeight(20) # Set fixed height
        self.layout_main = QHBoxLayout(self)
        self.layout_main.setContentsMargins(2, 0, 2, 0) #TODO: Reconsider making this 0, 0, 0, 0
        self.layout_main.setSpacing(0)
    def clear(self):
        # This layout should only contain widgets and stretches
        while self.layout_main.count():
            item = self.layout_main.takeAt(0) # Remove item from layout
            widget = item.widget()
            if widget: widget.deleteLater()  # Ensure that the widget is deleted
    def set_scale(self, max_val: float, split_number: int): # split number is number of intervals
        self.clear()
        self.layout_main.addWidget(QLabel("0.00mL"))
        # Create N + 1 equally spaced numbers from 0 to max_val except 0
        tick_numbers = [i * max_val / split_number for i in range(1, split_number + 1)]
        for num in tick_numbers:
            self.layout_main.addStretch(1) # This creates spaces in between
            self.layout_main.addWidget(QLabel(f"{num:.2f}mL"))
        # Automatically updates

# SliderCard: Main Card Containing Slider and ETC.
class SliderCard(QFrame):
    SLIDER_VALUE_TO_VOLUME = 1000 # Slider Unit / mL
    TIMEOUT_INTERVAL = 50 # 50ms
    # A slider and additional elemnts that control titrant volume
    def __init__(self, simulation_obj: Simulation, titrant_volume_manager: TitrantVolumeManager):
        super().__init__()
        self.simulation_obj: Simulation = simulation_obj
        self.titrant_volume_manager: TitrantVolumeManager = titrant_volume_manager

        self.setEnabled(False)
        self.setToolTip("적정 상황 및 지시약을 먼저 설정하세요")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        layout_header = QHBoxLayout()
        layout.addLayout(layout_header)
        # Start button and speed control for autotitriation
        layout_autotitration = QHBoxLayout()
        self.button_start = QToolButton()
        self.button_start.setText("▶") # '⏹' for stop
        self.button_start.setFixedWidth(30)
        label_speed_tag = QLabel("속도 :")
        self.dspin_speed = QDoubleSpinBox()
        self.dspin_speed.setRange(0.1, 10.0)
        self.dspin_speed.setSingleStep(0.1)
        self.dspin_speed.setDecimals(1)
        self.dspin_speed.setSuffix(" mL/s")
        layout_autotitration.addWidget(self.button_start)
        layout_autotitration.addWidget(label_speed_tag)
        layout_autotitration.addWidget(self.dspin_speed)
        # Volume Marking
        self.label_titrant_volume = QLabel("0.00mL") #TODO: QSS Value Display
        layout_header.addLayout(layout_autotitration)
        layout_header.addStretch(1)
        layout_header.addWidget(self.label_titrant_volume)
        
        # Slider
        self.slider_titrant_volume = QSlider(Qt.Horizontal)
        layout.addWidget(self.slider_titrant_volume)
        # Slider Ticks
        self.slider_ticks = SliderTicks()
        # TODO: Add ticks once activated
        layout.addWidget(self.slider_ticks)

        # Signals
        self.slider_titrant_volume.sliderPressed.connect(self._on_slider_press_by_user)
        self.slider_titrant_volume.sliderReleased.connect(self._on_slider_release_by_user)
        self.slider_titrant_volume.valueChanged.connect(self._on_slider_value_change)
        self.button_start.clicked.connect(self._on_start_button_click) # Autotitration

        self.titrant_volume_manager.is_user_moving_slider_changed.connect(self._on_user_moving_slider_change)
        self.titrant_volume_manager.is_autotitration_on_changed.connect(self._on_autotitration_on_change)
        self.titrant_volume_manager.timer_timeout.connect(self._on_timer_timeout)
        self.titrant_volume_manager.current_volume_changed.connect(self._on_current_volume_change)
    def get_autotitration_speed(self) -> float: return self.dspin_speed.value()
    def start_simulation(self):
        self.setEnabled(True)
        max_volume = self.simulation_obj.get_max_titrant_volume()
        self.slider_titrant_volume.setMaximum(max_volume * self.SLIDER_VALUE_TO_VOLUME)
        self.slider_ticks.set_scale(max_volume, 5) # Set ticks
    def end_simulation(self):
        self.setEnabled(False)
        # self.label_titrant_volume.setText("0.00mL")
        self.slider_titrant_volume.setValue(0)
        self.slider_ticks.clear() # Clear ticks
    # Emitting signals
    def _on_slider_press_by_user(self):
        self.titrant_volume_manager.is_user_moving_slider = True
        self.titrant_volume_manager.is_user_moving_slider_changed.emit()
    def _on_slider_release_by_user(self):
        self.titrant_volume_manager.is_user_moving_slider = False
        self.titrant_volume_manager.is_user_moving_slider_changed.emit()
    def _on_slider_value_change(self, new_val: int):
        self.simulation_obj.titrant_volume = new_val / self.SLIDER_VALUE_TO_VOLUME
        self.titrant_volume_manager.current_volume_changed.emit()
    def _on_start_button_click(self):
        self.titrant_volume_manager.is_autotitration_on = not self.titrant_volume_manager.is_autotitration_on
        self.titrant_volume_manager.is_autotitration_on_changed.emit()
    # Connecting slots
    def _on_user_moving_slider_change(self):
        if self.titrant_volume_manager.is_autotitration_on:
            if self.titrant_volume_manager.is_user_moving_slider:
                # Stop timer
                self.titrant_volume_manager.timer.stop()
            else:
                # Start timer
                self.titrant_volume_manager.timer.start(self.TIMEOUT_INTERVAL)
    def _on_autotitration_on_change(self):
        if self.titrant_volume_manager.is_autotitration_on:
            # If current volume is maximum reset volume
            if self.simulation_obj.titrant_volume * self.SLIDER_VALUE_TO_VOLUME == self.slider_titrant_volume.maximum():
                self.simulation_obj.titrant_volume = 0.0
                self.slider_titrant_volume.setValue(0)
                self.titrant_volume_manager.current_volume_changed.emit()
            self.button_start.setText("■")
            self.titrant_volume_manager.timer.start(self.TIMEOUT_INTERVAL)
        else:
            self.button_start.setText("▶")
            self.titrant_volume_manager.timer.stop()
    def _on_current_volume_change(self):
        self.label_titrant_volume.setText(f"{self.simulation_obj.titrant_volume:.2f}mL")
    def _on_timer_timeout(self):
        current_volume = self.simulation_obj.titrant_volume
        if current_volume * self.SLIDER_VALUE_TO_VOLUME == self.slider_titrant_volume.maximum():
            # Reached end
            self.titrant_volume_manager.is_autotitration_on = False
            self.titrant_volume_manager.is_autotitration_on_changed.emit()
        else:
            self.slider_titrant_volume.setValue(
                (current_volume + self.get_autotitration_speed() * self.TIMEOUT_INTERVAL / 1000) *
                self.SLIDER_VALUE_TO_VOLUME
            ) # This calls current_volume_changed automatically

# =======================================================
# Main Window and Entry Point of Application
# =======================================================

# MainWindow: Main Window Widget of App
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("중화적정 시뮬레이션 프로그램")
        #TODO: self.resize: decide later on

        # Setup simulation
        self.simulation_obj: Simulation = Simulation() # This object's reference gets passed on to children

        # Setup titrant volume manager
        self.titrant_volume_manager = TitrantVolumeManager(self)

        # Build ui framework
        self._build_ui_framework()
    def _build_ui_framework(self):
        # Build Menu Bar
        # TODO: Add actino implementations
        menubar = self.menuBar()
        # File Menu
        file_menu = menubar.addMenu("파일")
        action_quit = file_menu.addAction("종료하기") # Quit program
        action_quit.setShortcut("Ctrl+Q") # Quit
        action_quit.triggered.connect(self.close)
        # Edit Menu
        edit_menu = menubar.addMenu("편집")
        action_reset = edit_menu.addAction("설정 초기화") # Reset all configurations
        action_reset.setShortcut("Ctrl+R") # Reset
        # Window Menu
        window_menu = menubar.addMenu("창")
        action_add_delete_chemicals = window_menu.addAction("물질 추가/제거") # Add edit delete chemicals
        action_add_delete_chemicals.setShortcut("Ctrl+M") # Manage
        action_show_theoretical_background = window_menu.addAction("이론적 배경") # Show theoretical background
        action_show_theoretical_background.setShortcut("Ctrl+T") # Theoretical
        # Help Menu
        help_menu = menubar.addMenu("도움말")
        action_about = help_menu.addAction("프로그램 정보")

        # Build Central Widget
        central = QWidget()
        # Main Layout
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)
        layout.setContentsMargins(15, 10, 15, 10) # Set inner padding of layout
        layout.setSpacing(10) # Set vertical gap for all inner widgets
        # Title
        label_title = QLabel("중화적정 시뮬레이션")
        label_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_title)

        # Layout for Main Row
        layout_main_row = QHBoxLayout()
        layout_main_row.setSpacing(12) # Horizontal Gap
        # Slider card that controls simulation
        self.slider_card = SliderCard(self.simulation_obj, self.titrant_volume_manager)
        # Add to main layout
        layout.addLayout(layout_main_row, stretch=1) # Only the main row expands vertically
        layout.addWidget(self.slider_card, stretch=0)
        
        # Add widgets to main row
        config_panel = ConfigurationPanel(self.simulation_obj)
        self.simulation_panel = SimulationPanel(self.simulation_obj, self.titrant_volume_manager)
        self.calculations_panel = CalculationsPanel()
        layout_main_row.addWidget(config_panel)
        layout_main_row.addWidget(self.simulation_panel, stretch=3)
        layout_main_row.addWidget(self.calculations_panel, stretch=2) #TODO: Modify value
        
        # Signals
        # TODO: Consider moving simulation start/stop button to simulation panel
        config_panel.is_running_simulation_changed.connect(self._on_running_simulation_change)
    def _on_running_simulation_change(self, is_started: bool):
        # Activation/Deactivation of components
        if is_started: self.start_simulation()
        else: self.end_simulation()
    def start_simulation(self):
        self.titrant_volume_manager.start_simulation()
        # Activate all components as simulation has started
        self.simulation_panel.start_simulation()
        # Activate and configure slider card
        self.slider_card.start_simulation()
    def end_simulation(self):
        self.titrant_volume_manager.end_simulation()
        self.simulation_panel.end_simulation()
        self.slider_card.end_simulation()


# Main Entry Point
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# Run entry point if directly run
if __name__ == "__main__": main()