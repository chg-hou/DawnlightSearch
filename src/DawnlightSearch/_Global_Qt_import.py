from __future__ import absolute_import


from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtCore import pyqtSlot, QSettings, QUrl, QDateTime, QTranslator, QCoreApplication, QLocale

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDateTimeEdit
from PyQt5.QtWidgets import QDialogButtonBox, QListWidget, QListWidgetItem, QFileDialog
from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget

from PyQt5.QtGui import QDesktopServices

HACKED_QT_EDITROLE = QtCore.Qt.UserRole  # qt bug: cannot set different values for display and user roles.
