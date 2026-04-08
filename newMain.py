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






# Main Entry Point
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# Run entry point if directly run
if __name__ == "__main__": main()