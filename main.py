'''
    This is a project for 문제해결과컴퓨팅사고 SKKU 2026-1 by team 지시약과 아이들
    Licence for PySide6 by LGPL --> To be added Later
'''
import sys
from PySide6.QtCore import Signal, QRect, Qt, QPointF, QTimer, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QPaintEvent, QPolygonF, QTransform, QMouseEvent, QCursor
from PySide6.QtWidgets import (QApplication, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QGroupBox, QRadioButton, QFrame, QComboBox, QDoubleSpinBox, QToolButton, QLineEdit,
                               QTabWidget, QColorDialog, QSlider)


# Simple Class for Acids and Bases
class Chemical():
    def __init__(self, name: str, is_acid: bool, is_strong: bool, k_val: float | None = None, acid_color: QColor | None = None, base_color: QColor | None = None):
        self.name = name
        self.is_acid = is_acid
        self.is_strong = is_strong
        self.k_val = k_val # K value at 25 degrees, specified only when is_strong == False
        self.acid_color = acid_color
        self.base_color = base_color
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
        "PHENOLPHTHALEIN": Chemical("Phenolphthalein", True, False, 4e-10, QColor(0, 0, 0), QColor(255, 20, 147))
    }
}



#  TODO: Add default sizes to windows
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
# TODO: Add Clear Functionality
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
    TIMEOUT_INTERVAL = 50 # milliseconds
    request_configuration_page = Signal()
    def __init__(self):
        super().__init__()
        self.reloaded = False
        # Create main elements
        layout = QVBoxLayout()
        self.utility_bar = self.UtilityBar()
        self.experiment_visuals = self.ExperimentVisuals()
        self.utility_bar.hide()
        self.experiment_visuals.hide()
        layout.addWidget(self.utility_bar, 0)
        layout.addWidget(self.experiment_visuals, 1)
        self.setLayout(layout)
        # Configuraiton Panel on New Window | self added as parent to add dependency
        self.configuration_panel = self.ConfigurationPanel(self)
        # Disable X button
        self.configuration_panel.setWindowFlags(
            Qt.Window |
            Qt.WindowTitleHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint
        )
        # Calculation Panel on New Window | self added as parent to add dependency
        self.calculation_panel = self.CalculationPanel(self)
        # Disable X button
        self.calculation_panel.setWindowFlags(
            Qt.Window |
            Qt.WindowTitleHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint
        )

        # Value Definition & Initialization
        self.is_user_moving_slider = False
        self.is_autotitration_on = False
        self.current_volume = 0.0
        self.autotitration_speed = 0.5

        # Handle Signals
        self.configuration_panel.slider_start_moving_by_user.connect(self.__on_slider_start_move_by_user)
        self.configuration_panel.volume_changed.connect(self.__on_volume_change)
        self.configuration_panel.autotitration_start_stop_changed.connect(self.__on_autotitration_start_stop_change)
        self.configuration_panel.autotitration_speed_changed.connect(self.__on_autotitration_speed_change)
        self.experiment_visuals.release_hold_changed.connect(self.__on_release_hold_change)

        self.utility_bar.reconfigure_clicked.connect(self.__on_reconfigure_click)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.__on_timer_timeout)
    def __on_slider_start_move_by_user(self, start_move: bool):
        self.is_user_moving_slider = start_move
        # Send signal to experiment visuals to change stopcock if autotitration off
        if not self.is_autotitration_on:
            self.experiment_visuals.release_or_hold(start_move)
        # Stop timer from firing or restart if autotitration is on
        if self.is_autotitration_on:
            if start_move: self.timer.stop()
            else: self.timer.start(self.TIMEOUT_INTERVAL)
    def __turn_autotitration_on_off(self, turn_on: bool):
        if turn_on:
            self.is_autotitration_on = True
            # Turn autotitration on in config panel --> change button text to stop autotitration and enable speed features
            self.configuration_panel.change_widgets_for_autotitration_on_off(True)
            # Change experiment visuals to stopcock release
            self.experiment_visuals.release_or_hold(True)
            # Start timer
            self.timer.start(self.TIMEOUT_INTERVAL)
        else:
            self.is_autotitration_on = False
            # Turn autotitration off in config panel --> change button tesxt to start autotitrationi and disable speed features
            self.configuration_panel.change_widgets_for_autotitration_on_off(False)
            # Change experiment visuals to stopcock hold
            self.experiment_visuals.release_or_hold(False)
            # Stop timer
            self.timer.stop()
    def __on_autotitration_start_stop_change(self):
        if not self.is_autotitration_on: self.__turn_autotitration_on_off(True)
        else: self.__turn_autotitration_on_off(False)
    def __on_autotitration_speed_change(self, speed: float): self.autotitration_speed = speed
    def __on_release_hold_change(self, is_released: bool):
        if not is_released: self.__turn_autotitration_on_off(True)
        else: self.__turn_autotitration_on_off(False)
    def __on_timer_timeout(self):
        # Set value of the slider
        if self.current_volume == self.configuration_panel.slider_titration.maximum():
            # Reset to 0
            self.configuration_panel.slider_titration.setValue(0)
            # Reached maximum, stop autotitration
            self.__turn_autotitration_on_off(False)
            return
        # Multiply by 100 to match implementation
        self.configuration_panel.slider_titration.setValue((self.current_volume + self.autotitration_speed * (self.TIMEOUT_INTERVAL / 1000)) * 100)
    def __on_volume_change(self, volume: float):
        # Change current value based on current speed
        self.current_volume = volume
        # Change info volume of config panel
        self.configuration_panel.change_info_volume(volume)
        # Rerender water level of experiment visuals
    def reload_page(self, config_data: ConfigurationScreen.ConfigData, main_geometry: QRect):
        if not config_data: return
        # Block double reload
        if self.reloaded: return
        else: self.reloaded = True
        # Show and configure widgets in main window
        # self.utility_bar.show()
        self.experiment_visuals.show()
        # Set window right on the left of the original window
        self.configuration_panel.config(config_data)
        self.configuration_panel.move(main_geometry.x() - self.configuration_panel.frameGeometry().x() - 5, main_geometry.y())
        self.configuration_panel.show()
        # Set window right next to the original window
        self.calculation_panel.move(main_geometry.x() + main_geometry.width() + 5, main_geometry.y())
        self.calculation_panel.show()

        # Control Variables Initialization
        self.is_user_moving_slider = False
        self.is_autotitration_on = False
        self.current_volume = 0.0
        self.autotitration_speed = 0.5
    def clear_page(self):
        # Block clear before reloading
        if not self.reloaded: return
        else: self.reload = False
        self.configuration_panel.hide()
        self.calculation_panel.hide()
        self.utility_bar.hide()
        self.experiment_visuals.hide()
    def __on_reconfigure_click(self):
        self.clear_page()
        self.request_configuration_page.emit()
    class UtilityBar(QWidget):
        reconfigure_clicked = Signal()
        def __init__(self):
            super().__init__()
            layout = QHBoxLayout()
            button_reconfigure = QPushButton("Reconfigure")
            button_theoretical_background = QPushButton("Theoretical Background")
            layout.addWidget(button_reconfigure)
            layout.addWidget(button_theoretical_background)
            self.setLayout(layout)
            button_reconfigure.clicked.connect(lambda: self.reconfigure_clicked.emit())

    class ExperimentVisuals(QWidget):
        # Colors used
        # BURETTE_COLOR = QColor(200, 200, 200, 40)
        GLASS_COLOR = QColor(230, 230, 230, 40)
        # FLASK_COLOR = QColor(180, 190, 200, 50)
        TITRANT_COLOR = QColor(100, 180, 255, 150)
        WATER_COLOR = QColor(220, 230, 240, 80)
        REDSCREW_COLOR = QColor(220, 70, 70, 255)

        # Signals
        release_hold_changed = Signal(bool) # bool value = is currently released --> will change to the opposite side
        def __init__(self):
            super().__init__()
            self.is_released = False
            self.titration_model = self.TitrationModel()
            self.painted_stop_cock_release = None
            self.painted_stop_cock_hold = None
            self.setMouseTracking(True)
        def paintEvent(self, event: QPaintEvent):
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
            # Burette
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(self.GLASS_COLOR)
            painter.drawPolygon(transform.map(self.titration_model.burette))
            # Burette Titrant
            painter.setPen(QPen(Qt.black, 0.5))
            painter.setBrush(self.TITRANT_COLOR)
            painter.drawPolygon(transform.map(self.titration_model.burette.titrant_edge(0.7, self.is_released)))
            # Conical Flask
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(self.GLASS_COLOR)
            painter.drawPolygon(transform.map(self.titration_model.conical_flask))
            # Conical Flask Water
            painter.setPen(QPen(Qt.black, 0.5))
            painter.setBrush(self.WATER_COLOR)
            painter.drawPolygon(transform.map(self.titration_model.conical_flask.water_edge(0.3)))
            # Red Screw
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(self.REDSCREW_COLOR)
            painter.drawPolygon(transform.map(self.titration_model.red_screw))
            # Stopcock
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(self.GLASS_COLOR)
            self.painted_stop_cock_release = transform.map(self.titration_model.stop_cock_release)
            self.painted_stop_cock_hold = transform.map(self.titration_model.stop_cock_hold)
            painter.drawPolygon(
                self.painted_stop_cock_release
                if self.is_released else self.painted_stop_cock_hold
            )
            painter.end()
        def mouseMoveEvent(self, event: QMouseEvent):
            # When mouse hovers above stopcock, change mouse shape to make it seem the stopcock is pressable
            if not self.painted_stop_cock_release or not self.painted_stop_cock_hold: return
            if (
                (self.is_released and self.painted_stop_cock_release.containsPoint(event.position(), Qt.WindingFill)) or
                (not self.is_released and self.painted_stop_cock_hold.containsPoint(event.position(), Qt.WindingFill))
            ):
                # Make the stopcock look clickable
                self.setCursor(QCursor(Qt.PointingHandCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
        def mousePressEvent(self, event: QMouseEvent):
            if not self.painted_stop_cock_release or not self.painted_stop_cock_hold: return
            if not self.is_released and self.painted_stop_cock_hold.containsPoint(event.position(), Qt.WindingFill):
                # Hold --> Release
                self.release_hold_changed.emit(False)
            elif self.is_released and self.painted_stop_cock_release.containsPoint(event.position(), Qt.WindingFill):
                # Release --> Hold
                self.release_hold_changed.emit(True)
        def release_or_hold(self, release: bool):
            if release:
                if self.is_released: return
                self.is_released = True
                self.update()
            else:
                if not self.is_released: return
                self.is_released = False
                self.update()

        class TitrationModel():
            def __init__(self):
                transform = QTransform()
                transform.scale(1 / 7.0, -1 / 7.0) # second
                transform.translate(-0.7, -3.5) # first               
                self.conical_flask = self.ConicalFlask(transform)
                self.burette = self.Burette(transform)
                self.red_screw = self.RedScrew(transform)
                self.stop_cock_release = self.StopCock(True, transform)
                self.stop_cock_hold = self.StopCock(False, transform)
            class ConicalFlask(QPolygonF):
                def __init__(self, transform: QTransform):
                    self.transform = transform
                    self.points = [
                        QPointF(0.5, 2.1), # 0
                        QPointF(0.5, 1.6), # 1
                        QPointF(0.0, 0.0), # 2
                        QPointF(1.4, 0.0), # 3
                        QPointF(0.9, 1.6), # 4
                        QPointF(0.9, 2.1), # 5
                    ]
                    super().__init__([transform.map(p) for p in self.points])
                def water_edge(self, ratio: float) -> QPolygonF:
                    # 0 <= ratio < 1 as to how much the flask is filled regarding height
                    return QPolygonF([
                        self.transform.map(p) for p in
                        [
                            self.points[1] * ratio + self.points[2] * (1 - ratio),
                            self.points[2],
                            self.points[3],
                            self.points[4] * ratio + self.points[3] * (1 - ratio),
                        ]
                    ])
            class Burette(QPolygonF):
                def __init__(self, transform: QTransform):
                    self.transform = transform
                    self.points = [
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
                    super().__init__([transform.map(p) for p in self.points])
                def titrant_edge(self, ratio: float, is_released: bool) -> QPolygonF:
                    # 0 <= ratio < 1 as to how much the burette is filled regarding height
                    if not is_released:
                        return QPolygonF([
                            self.transform.map(p) for p in
                            [
                                self.points[0] * ratio + self.points[1] * (1 - ratio),
                                self.points[1],
                                self.points[2],
                                self.points[3],
                                self.points[13],
                                self.points[14],
                                self.points[15],
                                self.points[16] * ratio + self.points[15] * (1 - ratio),
                            ]
                        ])
                    else:
                        return QPolygonF([
                            self.transform.map(p) for p in
                            [
                                self.points[0] * ratio + self.points[1] * (1 - ratio),
                                self.points[1],
                                self.points[2],
                                self.points[3],
                                QPointF(0.68, self.points[3].y()),
                                self.points[8],
                                QPointF(0.72, self.points[13].y()),
                                self.points[13],
                                self.points[14],
                                self.points[15],
                                self.points[16] * ratio + self.points[15] * (1 - ratio),
                            ]
                        ])
            class RedScrew(QPolygonF):
                def __init__(self, transform: QTransform):
                    points = [
                        QPointF(0.35, 2.72), # 0
                        QPointF(0.35, 2.42), # 1
                        QPointF(0.50, 2.42), # 2
                        QPointF(0.50, 2.72), # 3
                    ] # 2.57
                    super().__init__([transform.map(p) for p in points])
            class StopCock(QPolygonF):
                def __init__(self, is_released: bool, transform: QTransform):
                    if is_released:
                        points = [
                            QPointF(0.90, 2.63), # 0
                            QPointF(0.90, 2.51), # 1
                            QPointF(0.98, 2.51), # 2
                            QPointF(1.06, 2.37), # 3
                            QPointF(1.22, 2.37), # 4
                            QPointF(1.22, 2.77), # 5
                            QPointF(1.06, 2.77), # 6
                            QPointF(0.98, 2.63), # 7
                        ] # 2.57
                        super().__init__([transform.map(p) for p in points])
                    else:
                        points = [
                            QPointF(0.90, 2.63), # 0
                            QPointF(0.90, 2.51), # 1
                            QPointF(1.22, 2.51), # 2
                            QPointF(1.22, 2.63), # 3
                        ] # 2.57
                        super().__init__([transform.map(p) for p in points])    
    class ConfigurationPanel(QWidget):
        # Signals
        slider_start_moving_by_user = Signal(bool) # start moving: True, stop moving: false
        volume_changed = Signal(float) # Emitted everytime slider value changes
        autotitration_start_stop_changed = Signal() # state should be tracked in main class
        autotitration_speed_changed = Signal(float) # speed change of autotitration
        
        def __init__(self, parent: QWidget):
            super().__init__(parent)
            self.setWindowTitle("Configuration Panel")
            layout = QVBoxLayout()
            self.simulation_configs = QLabel()

            # Horizontal Line
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)

            # Slider
            info_slider = QLabel("<h2>Drag Slider or CLick Stopcock</h2>")
            self.slider_titration = QSlider(Qt.Horizontal)
            # Volume Applied --> same as slider value
            self.info_volume = QLabel(f"Applied Titrant Volume : 0.00mL")
            layout_autotitration = QHBoxLayout()
            # Auto Titration Button
            self.button_autotitration = QToolButton()
            self.button_autotitration.setText("Start Autotitration")
            # Speed section: disabled and enabled depending on autotitration
            self.info_speed = QLabel("Speed :")
            self.dspin_speed = self.NoTypingSpinBox()
            self.dspin_speed.setMinimum(0.0)
            self.dspin_speed.setValue(0.5)
            self.dspin_speed.setSingleStep(0.1)
            self.info_speed_unit = QLabel("mL/s")

            layout_autotitration.addWidget(self.button_autotitration)
            layout_autotitration.addWidget(self.info_speed)
            layout_autotitration.addWidget(self.dspin_speed)
            layout_autotitration.addWidget(self.info_speed_unit)

            layout.addWidget(self.simulation_configs)
            layout.addWidget(line)
            layout.addWidget(info_slider)
            layout.addWidget(self.slider_titration)
            layout.addWidget(self.info_volume)
            layout.addLayout(layout_autotitration)
            self.setLayout(layout)

            # Signals
            self.slider_titration.sliderPressed.connect(lambda: self.slider_start_moving_by_user.emit(True))
            self.slider_titration.sliderReleased.connect(lambda: self.slider_start_moving_by_user.emit(False))
            self.slider_titration.valueChanged.connect(lambda value: self.volume_changed.emit(value / 100))
            self.button_autotitration.clicked.connect(lambda: self.autotitration_start_stop_changed.emit())
            self.dspin_speed.valueChanged.connect(self.autotitration_speed_changed.emit)
        def change_info_volume(self, volume: float):
            # Change text of added volume label
            self.info_volume.setText(f"Applied Titrant Volume : {volume:.2f}mL")
        def change_widgets_for_autotitration_on_off(self, turn_on: bool):
            if turn_on: self.button_autotitration.setText("Stop Autotitration")
            else: self.button_autotitration.setText("Start Autotitration")
        def config(self, config_data: ConfigurationScreen.ConfigData):
            # Set configuration text
            self.simulation_configs.setText(f"""
                <h1>Simulation Configurations</h1>
                <h2>Analyte</h2>
                {config_data.analyte.chemical.name}<br>
                {"Acid" if config_data.analyte.chemical.is_acid else "Base"} ({
                    "Strong" if config_data.analyte.chemical.is_strong else (
                        ("K<sub>a</sub>" if config_data.analyte.chemical.is_acid else "K<sub>b</sub>") +
                        f"={config_data.analyte.chemical.k_val:.2e}"
                    )
                })<br>
                {config_data.analyte.concentration}M<br>
                {config_data.analyte.volume}mL
                <h2>Titrant</h2>
                {config_data.titrant.chemical.name}<br>
                {"Acid" if config_data.titrant.chemical.is_acid else "Base"} ({
                    "Strong" if config_data.titrant.chemical.is_strong else (
                        ("K<sub>a</sub>" if config_data.titrant.chemical.is_acid else "K<sub>b</sub>") +
                        f"={config_data.titrant.chemical.k_val:.2e}"
                    )
                })<br>
                {config_data.titrant.concentration}M
                <h2>Indicator</h2>
                {config_data.indicator.name}
            """)
            # Set slider properties
            self.slider_titration.setMinimum(0)
            self.slider_titration.setMaximum(10000) # 100 times the real value
            self.slider_titration.setValue(0)
        class NoTypingSpinBox(QDoubleSpinBox):
            # Double spinbox that doesn't typing only arrows
            def event(self, event):
                if event.type() == QEvent.KeyPress:
                    return True  # Block all typing
                return super().event(event)
    class CalculationPanel(QTabWidget):
        def __init__(self, parent: QWidget):
            super().__init__(parent)
            self.setWindowTitle("Calculation Panel")
            self.pH_graph = QLabel("<h1>pH Graph</h1>")
            self.label_simulator = QLabel("<h1>Simulator Calculations</h1>")
            self.label_theoretical = QLabel("<h1>Theoretical Calculations</h1>")
            self.addTab(self.pH_graph, "pH Graph")
            self.addTab(self.label_simulator, "Simulator")
            self.addTab(self.label_theoretical, "Theoretical")

# Main Window for App
class MainWindow(QWidget):
    def __init__(self):
        # Init parameters
        super().__init__()
        self.setWindowTitle("Acid-Base Titration Simulator")
        # self.resize()

        # Create stacked widget and screens
        self.stacked_widget = QStackedWidget() # Consider adding transition animation
        # start_screen = StartScreen()
        # start_screen.request_next_page.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        configuration_screen = ConfigurationScreen()
        configuration_screen.request_next_page.connect(self.__to_simulation_page)
        self.simulation_screen = SimulationScreen()
        self.simulation_screen.request_configuration_page.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        # Add screens to stacked widget
        # self.stacked_widget.addWidget(start_screen)
        self.stacked_widget.addWidget(configuration_screen)
        self.stacked_widget.addWidget(self.simulation_screen)

        # Add stacked widget to main window
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)
    def __to_simulation_page(self, config_data: ConfigurationScreen.ConfigData):
        self.simulation_screen.reload_page(config_data, self.frameGeometry())
        self.stacked_widget.setCurrentIndex(1)

# Main Entry Point
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# Run entry point if directly run
if __name__ == "__main__": main()