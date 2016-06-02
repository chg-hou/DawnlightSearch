from __future__ import absolute_import

from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic, QtGui, QtCore
from PyQt5 import QtSql, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QSettings

from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDateTimeEdit
from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import QDialogButtonBox, QListWidget, QListWidgetItem, QFileDialog
from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget
from PyQt5.QtCore import QSettings

HACKED_QT_EDITROLE = QtCore.Qt.UserRole  # qt bug: cannot set different values for display and user roles.
