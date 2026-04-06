'''
    This is a project for 문제해결과컴퓨팅사고 SKKU 2026-1 by team 지시약과 아이들
    Licence for PySide6 by LGPL --> To be added Later
'''
import sys
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QApplication, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QGroupBox, QRadioButton, QFrame, QComboBox, QDoubleSpinBox, QToolButton, QLineEdit,
                               QTabWidget, QColorDialog)

# Simple Class for Acids and Bases
class Chemical():
    def __init__(self, name: str, is_acid: bool, is_strong: bool, k_val: float | None = None, acid_color: QColor | None = None, base_color: QColor | None = None):
        self.name = name
        self.is_acid = is_acid
        self.is_strong = is_strong
        self.k_val = k_val # K value at 25 degrees, specified only when is_strong == False
        self.acid_color = acid_color
        self.base_color = base_color
    WATER_COLOR = QColor(230, 240, 255)
class PureSolution():
    def __init__(self, chemical: Chemical, concentration: float, volume: float | None = None):
        self.chemical = chemical
        self.concentration = concentration
        self.volume = volume # Volume can be optional

# Chemical Library
chemical_library = {
    "ACID": {
        # Strong Acids
        "HYDROCHLORIC_ACID": Chemical("HCl (Hydrochloric Acid)", True, True),
        # Weak Acids
        "ACETIC_ACID": Chemical("CH₃COOH (Acetic Acid)", True, False, 1.8e-5)
    },
    "BASE": {
        # Strong Bases
        "SODIUM_HYDROXIDE": Chemical("NaOH (Sodium Hydroxide)", False, True),
        # Weak Bases
        "SODIUM_ACETATE": Chemical("CH₃COONa (Sodium Acetate)", False, False, 5.6e-10)
    },
    "INDICATOR": {
        # Indicators of non-monoprotic features should be handled later on
        # All indicators are treated as monoprotic
        "METHYL_ORANGE": Chemical("Methyl Orange", True, False, 3.4e-4, QColor(220, 40, 40), QColor(220, 40, 40)),
        "BROMOTHYMOL_BLUE": Chemical("Bromothymol Blue (BTB)", True, False, 8e-8, QColor(240, 220, 0), QColor(240, 220, 0)),
        "PHENOLPHTHALEIN": Chemical("Phenolphthalein", True, False, 4e-10, Chemical.WATER_COLOR, QColor(255, 20, 147))
    }
}

# Start Screen
class StartScreen(QWidget):
    request_next_page = Signal()
    def __init__(self):
        super().__init__()

        # Create main headline and button for continue
        headline = QLabel("Welcome to Acid-Base Titration Simulator")
        button_continue = QPushButton("Get Started")
        # button_continue.setIcon()
        button_continue.clicked.connect(lambda: self.request_next_page.emit())
        
        layout = QVBoxLayout()
        layout.addWidget(headline)
        layout.addWidget(button_continue)
        self.setLayout(layout)

# Configuration Screen
class ConfigurationScreen(QWidget):
    class ConfigData():
        def __init__(self, analyte: PureSolution, titrant: PureSolution, indicator: Chemical):
            self.analyte = analyte
            self.titrant = titrant
            self.indicator = indicator
    request_next_page = Signal(ConfigData)
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        tabs = QTabWidget()
        # Analyte and Titrant Configruation
        tab_analyte_titrant = QWidget()
        layout_analyte_titrant = QHBoxLayout()

        self.config_analyte = self.SolutionConfigWidget(True, True)
        toolbutton_swap = QToolButton()
        toolbutton_swap.setText("Swap") # Change this later on to setIcon
        self.config_titrant = self.SolutionConfigWidget(False, False)
        toolbutton_swap.clicked.connect(self.__swap_acid_base)

        layout_analyte_titrant.addWidget(self.config_analyte)
        layout_analyte_titrant.addWidget(toolbutton_swap)
        layout_analyte_titrant.addWidget(self.config_titrant)
        tab_analyte_titrant.setLayout(layout_analyte_titrant)

        # Indicator Configuration
        self.config_indicator = self.IndicatorConfigWidget()

        layout_buttons = QHBoxLayout()
        button_clear = QPushButton("Reset")
        button_finish = QPushButton("Finish")
        layout_buttons.addWidget(button_clear)
        layout_buttons.addWidget(button_finish)

        button_finish.clicked.connect(self.__submit_config)

        tabs.addTab(tab_analyte_titrant, "Analyte && Titrant")
        tabs.addTab(self.config_indicator, "Indicator")
        layout.addWidget(tabs)
        layout.addLayout(layout_buttons)
        self.setLayout(layout)

    def __swap_acid_base(self):
        self.config_analyte.switch_acid_base()
        self.config_titrant.switch_acid_base()
    def __submit_config(self):
        analyte = self.config_analyte.get_solution()
        titrant = self.config_titrant.get_solution()
        indicator = self.config_indicator.get_chemical()
        if not analyte or not titrant or not indicator:
            print("ERROR: There exist empty sections in the Form")
            # TODO Need to add user warning message
            return
        self.request_next_page.emit(self.ConfigData(analyte, titrant, indicator))
        

    class SolutionConfigWidget(QGroupBox):
        def __init__(self, is_analyte: bool, is_acid: bool):
            super().__init__()
            self.setTitle("Analyte" if is_analyte else "Titrate")
            self.is_acid = is_acid
            self.is_analyte = is_analyte
            layout = QVBoxLayout()

            current_type = "Acid" if self.is_acid else "Base"
            self.label_type = QLabel(f"Type: {current_type}")

            # Selection Between Predefined and Custom
            self.radio_predefined = QRadioButton(f"Select from Predefined {current_type}s")
            frame_predefined = QFrame()
            layout_predefined = QVBoxLayout()
            self.combo_predefined = QComboBox()
            self.__configure_combo_predefined()
            layout_predefined.addWidget(self.combo_predefined)
            frame_predefined.setLayout(layout_predefined)
            
            self.radio_custom = QRadioButton(f"Custom {current_type}")
            frame_custom = QFrame()
            layout_custom = QVBoxLayout()
            # Custom Name
            layout_custom_name = QHBoxLayout()
            label_custom_name = QLabel("Name :")
            self.lineedit_custom_name = QLineEdit()
            layout_custom_name.addWidget(label_custom_name)
            layout_custom_name.addWidget(self.lineedit_custom_name)
            # Strength
            layout_custom_strength = QHBoxLayout()
            label_custom_strength = QLabel("Strength :")
            self.combo_custom_strength = QComboBox()
            self.combo_custom_strength.addItem("Select...", None)
            self.combo_custom_strength.addItem("Strong", True)
            self.combo_custom_strength.addItem("Weak", False)
            self.combo_custom_strength.setCurrentIndex(0)
            self.combo_custom_strength.currentTextChanged.connect(self.__custom_strength_changed)
            layout_custom_strength.addWidget(label_custom_strength)
            layout_custom_strength.addWidget(self.combo_custom_strength)
            # Dissociation Constant
            layout_custom_k_val = QHBoxLayout()
            self.label_custom_k_val = QLabel("K<sub>a</sub> at 25℃ :" if self.is_acid else "K<sub>b</sub> at 25℃ :")
            self.lineedit_custom_k_val = QLineEdit()
            self.lineedit_custom_k_val.setPlaceholderText("e.g., 1.2e-7") # TODO: Need manual checking validity for each input
            self.label_custom_k_val.setEnabled(False)
            self.lineedit_custom_k_val.setEnabled(False)
            layout_custom_k_val.addWidget(self.label_custom_k_val)
            layout_custom_k_val.addWidget(self.lineedit_custom_k_val)

            layout_custom.addLayout(layout_custom_name)
            layout_custom.addLayout(layout_custom_strength)
            layout_custom.addLayout(layout_custom_k_val)
            frame_custom.setLayout(layout_custom)

            # Enabling and Disabling based on toggling
            self.radio_predefined.toggled.connect(frame_predefined.setEnabled)
            self.radio_custom.toggled.connect(frame_custom.setEnabled)
            frame_predefined.setEnabled(False)
            frame_custom.setEnabled(False)
            self.radio_predefined.setChecked(True)
            
            layout_concentration = QHBoxLayout()
            label_concentration = QLabel("Concentration :")
            self.dspin_concentration = QDoubleSpinBox()
            self.dspin_concentration.setMinimum(0.0)
            self.dspin_concentration.setValue(1.0)
            self.dspin_concentration.setSingleStep(0.1)
            label_concentration_unit = QLabel("M (mol/L)")
            layout_concentration.addWidget(label_concentration)
            layout_concentration.addWidget(self.dspin_concentration)
            layout_concentration.addWidget(label_concentration_unit)

            layout.addWidget(self.label_type)
            layout.addWidget(self.radio_predefined)
            layout.addWidget(frame_predefined)
            layout.addWidget(self.radio_custom)
            layout.addWidget(frame_custom)
            layout.addLayout(layout_concentration)

            if is_analyte:
                layout_volume = QHBoxLayout()
                label_volume = QLabel("Volume :")
                self.dspin_volume = QDoubleSpinBox()
                self.dspin_volume.setRange(0.0, 10000.0)
                self.dspin_volume.setValue(100.0)
                self.dspin_volume.setSingleStep(1)
                self.dspin_volume.setDecimals(1)
                label_volume_unit = QLabel("mL")
                layout_volume.addWidget(label_volume)
                layout_volume.addWidget(self.dspin_volume)
                layout_volume.addWidget(label_volume_unit)
                
                layout.addLayout(layout_volume)
            
            self.setLayout(layout)
        def switch_acid_base(self):
            self.is_acid = not self.is_acid
            current_type = "Acid" if self.is_acid else "Base"
            self.label_type.setText(f"Type: {current_type}")
            self.radio_predefined.setText(f"Select from Predefined {current_type}s")
            self.__configure_combo_predefined()
            self.radio_custom.setText(f"Custom {current_type}")
            self.label_custom_k_val.setText("K<sub>a</sub> at 25℃ :" if self.is_acid else "K<sub>b</sub> at 25℃ :")
        def __configure_combo_predefined(self):
            self.combo_predefined.clear()
            self.combo_predefined.addItem("Select...", None)
            first_key = "ACID" if self.is_acid else "BASE"
            for key in chemical_library[first_key]:
                self.combo_predefined.addItem(chemical_library[first_key][key].name, key)
            self.combo_predefined.setCurrentIndex(0)
        def __custom_strength_changed(self, text: str):
            if text == "Strong":
                self.label_custom_k_val.setEnabled(False)
                self.lineedit_custom_k_val.setEnabled(False)
            elif text == "Weak":
                self.label_custom_k_val.setEnabled(True)
                self.lineedit_custom_k_val.setEnabled(True)
        def __check_valid(self) -> bool:
            if self.radio_predefined.isChecked():
                if not self.combo_predefined.currentData(): return False
            elif self.radio_custom.isChecked():
                if (
                    not self.lineedit_custom_name.text() or
                    (self.combo_custom_strength.currentData() == None) or
                    (not self.combo_custom_strength.currentData() and not self.lineedit_custom_k_val.text())
                ): return False
            else: return False
            return True
        def get_solution(self) -> PureSolution | None:
            # Check validity
            if not self.__check_valid():
                print("ERROR: Need to fill out all configurations for solution to proceed")
                # TODO: Add here a user error message
                return None
            if self.radio_predefined.isChecked():
                chem = chemical_library["ACID" if self.is_acid else "BASE"][self.combo_predefined.currentData()]
                return PureSolution(
                    Chemical(chem.name, self.is_acid, chem.is_strong, chem.k_val),
                    self.dspin_concentration.value(),
                    self.dspin_volume.value() if self.is_analyte else None
                )
            else: return PureSolution(
                Chemical(
                    self.lineedit_custom_name,
                    self.is_acid,
                    self.combo_custom_strength.currentData(),
                    None if self.combo_custom_strength.currentData() else float(self.lineedit_custom_k_val.text())
                ),
                self.dspin_concentration.value(),
                self.dspin_volume.value() if self.is_analyte else None
            )
    class IndicatorConfigWidget(QWidget):
        def __init__(self):
            super().__init__()
            # self.setTitle("Configure Indicator")
            layout = QVBoxLayout()
            # Selection Between Predefined and Custom
            self.radio_predefined = QRadioButton("Select from Predefined Indicators")
            frame_predefined = QFrame()
            layout_predefined = QVBoxLayout()
            self.combo_predefined = QComboBox()
            self.__configure_combo_predefined()
            layout_predefined.addWidget(self.combo_predefined)
            frame_predefined.setLayout(layout_predefined)
            
            radio_custom = QRadioButton("Custom Indicator")
            frame_custom = QFrame()
            layout_custom = QVBoxLayout()
            # Custom Name
            layout_custom_name = QHBoxLayout()
            label_custom_name = QLabel("Name :")
            self.lineedit_custom_name = QLineEdit()
            layout_custom_name.addWidget(label_custom_name)
            layout_custom_name.addWidget(self.lineedit_custom_name)
            # Type
            layout_custom_type = QHBoxLayout()
            label_custom_type = QLabel("Type :")
            self.combo_custom_type = QComboBox()
            self.combo_custom_type.addItem("Select...", None)
            self.combo_custom_type.addItem("Acid", True)
            self.combo_custom_type.addItem("Base", False)
            self.combo_custom_type.setCurrentIndex(0)
            layout_custom_type.addWidget(label_custom_type)
            layout_custom_type.addWidget(self.combo_custom_type)
            # Dissociation Constant
            layout_custom_k_val = QHBoxLayout()
            label_custom_k_val = QLabel("K<sub>a</sub> or K<sub>b</sub> at 25℃ :")
            self.lineedit_custom_k_val = QLineEdit()
            self.lineedit_custom_k_val.setPlaceholderText("e.g., 1.2e-7") # Need manual checking validity for each input
            layout_custom_k_val.addWidget(label_custom_k_val)
            layout_custom_k_val.addWidget(self.lineedit_custom_k_val)
            # Select Acid/Base Color
            self.select_acid_color = self.ColorPickerWidget("Select Acid Color")
            self.select_base_color = self.ColorPickerWidget("Select Base Color")

            layout_custom.addLayout(layout_custom_name)
            layout_custom.addLayout(layout_custom_type)
            layout_custom.addLayout(layout_custom_k_val)
            layout_custom.addWidget(self.select_acid_color)
            layout_custom.addWidget(self.select_base_color)
            frame_custom.setLayout(layout_custom)

            # Enabling and Disabling based on toggling
            self.radio_predefined.toggled.connect(frame_predefined.setEnabled)
            radio_custom.toggled.connect(frame_custom.setEnabled)
            frame_predefined.setEnabled(False)
            frame_custom.setEnabled(False)
            self.radio_predefined.setChecked(True)

            layout.addWidget(self.radio_predefined)
            layout.addWidget(frame_predefined)
            layout.addWidget(radio_custom)
            layout.addWidget(frame_custom)
            
            self.setLayout(layout)
        def __configure_combo_predefined(self):
            self.combo_predefined.clear()
            self.combo_predefined.addItem("Select...", None)
            for key in chemical_library["INDICATOR"]:
                self.combo_predefined.addItem(chemical_library["INDICATOR"][key].name, key)
            self.combo_predefined.setCurrentIndex(0)
        def get_chemical(self) -> Chemical | None:
            if self.radio_predefined.isChecked():
                data = self.combo_predefined.currentData()
                if not data: return None
                indic = chemical_library["INDICATOR"][data]
                return Chemical(indic.name, indic.is_acid, indic.is_strong, indic.k_val, indic.acid_color, indic.base_color)
            else:
                name = self.lineedit_custom_name.text()
                is_acid = self.combo_custom_type.currentData()
                acid_color = self.select_acid_color.get_color()
                k_val = self.lineedit_custom_k_val.text()
                base_color = self.select_base_color.get_color()
                if not name or not is_acid or not k_val or not acid_color or not base_color: return None
                return Chemical(name, is_acid, False, float(k_val), acid_color, base_color)
        class ColorPickerWidget(QWidget):
            def __init__(self, btn_text: str):
                super().__init__()
                # self.setWindowTitle("Custom Color Tool")
                self.selected_color = QColor("gray") # Default
                self.btn_text = btn_text
                layout = QHBoxLayout()
                
                self.btn_pick = QToolButton()
                self.btn_pick.setText(btn_text)
                self.btn_pick.clicked.connect(self.choose_color)
                self.label = QLabel("No color selected yet")
                self.color_swatch = QLabel()
                self.color_swatch.setFixedSize(15, 15)  # Make it a square

                layout.addWidget(self.btn_pick)
                layout.addWidget(self.label)
                layout.addWidget(self.color_swatch)
                self.setLayout(layout)
            def choose_color(self):
                color = QColorDialog.getColor(self.selected_color, self, self.btn_text)
                if color.isValid():
                    self.selected_color = color
                    self.label.setText(f"Selected : {color.name()}")
                    self.color_swatch.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            def get_color(self) -> QColor | None:
                if self.label.text() == "No color selected yet": return None
                return QColor(self.selected_color.red(), self.selected_color.green(), self.selected_color.blue())
 
# Simulation Screen
class SimulationScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.config_data = None
    def reload_page(self, config_data: ConfigurationScreen.ConfigData):
        if not config_data: return
        # Reload page based on self.config_data

# Main Window for App
class MainWindow(QWidget):
    def __init__(self):
        # Init parameters
        super().__init__()
        self.setWindowTitle("Acid-Base Titration Simulator")
        # self.resize()

        # Create stacked widget and screens
        self.stacked_widget = QStackedWidget() # Consider adding transition animation
        start_screen = StartScreen()
        start_screen.request_next_page.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        configuration_screen = ConfigurationScreen()
        configuration_screen.request_next_page.connect(self.__to_simulation_page)
        self.simulation_screen = SimulationScreen()

        # Add screens to stacked widget
        self.stacked_widget.addWidget(start_screen)
        self.stacked_widget.addWidget(configuration_screen)
        self.stacked_widget.addWidget(self.simulation_screen)

        # Add stacked widget to main window
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)
    def __to_simulation_page(self, config_data: ConfigurationScreen.ConfigData):
        self.simulation_screen.reload_page(config_data)
        self.stacked_widget.setCurrentIndex(2)

# Main Entry Point
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# Run entry point if directly run
if __name__ == "__main__": main()