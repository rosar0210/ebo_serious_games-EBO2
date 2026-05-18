# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainUI.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QPushButton,
    QSizePolicy, QTextEdit, QWidget)

class Ui_guiDlg(object):
    def setupUi(self, guiDlg):
        if not guiDlg.objectName():
            guiDlg.setObjectName(u"guiDlg")
        guiDlg.resize(755, 445)
        self.textEdit_2 = QTextEdit(guiDlg)
        self.textEdit_2.setObjectName(u"textEdit_2")
        self.textEdit_2.setGeometry(QRect(40, 50, 661, 221))
        self.textEdit_2.setAutoFillBackground(True)
        self.textEdit_2.setStyleSheet(u"background-color: transparent;")
        self.textEdit_2.setFrameShape(QFrame.NoFrame)
        self.textEdit_2.setFrameShadow(QFrame.Sunken)
        self.textEdit_2.setReadOnly(True)
        self.story_button = QPushButton(guiDlg)
        self.story_button.setObjectName(u"story_button")
        self.story_button.setGeometry(QRect(20, 140, 211, 121))
        self.pasapalabra_button = QPushButton(guiDlg)
        self.pasapalabra_button.setObjectName(u"pasapalabra_button")
        self.pasapalabra_button.setGeometry(QRect(520, 140, 211, 121))
        self.simon_button = QPushButton(guiDlg)
        self.simon_button.setObjectName(u"simon_button")
        self.simon_button.setGeometry(QRect(270, 140, 211, 121))
        self.label = QLabel(guiDlg)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 280, 171, 161))
        self.label.setPixmap(QPixmap(u"logo_euro.png"))
        self.label.setScaledContents(True)
        self.label_2 = QLabel(guiDlg)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(460, 290, 291, 151))
        self.label_2.setPixmap(QPixmap(u"robolab.png"))

        self.retranslateUi(guiDlg)

        QMetaObject.connectSlotsByName(guiDlg)
    # setupUi

    def retranslateUi(self, guiDlg):
        guiDlg.setWindowTitle(QCoreApplication.translate("guiDlg", u"app_juegos", None))
        self.textEdit_2.setHtml(QCoreApplication.translate("guiDlg", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Ubuntu'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:26pt; font-weight:600;\">Selecciona el juego</span></p></body></html>", None))
        self.story_button.setText(QCoreApplication.translate("guiDlg", u"STORY Y CONVERSACI\u00d3N", None))
        self.pasapalabra_button.setText(QCoreApplication.translate("guiDlg", u"PASAPALABRA", None))
        self.simon_button.setText(QCoreApplication.translate("guiDlg", u"SIMON SAYS", None))
        self.label.setText("")
        self.label_2.setText("")
    # retranslateUi

