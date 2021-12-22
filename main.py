import sys
from PyQt5.QtWidgets import QApplication, QAction, QDialog, QSpinBox, QProgressBar, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QGridLayout, QMessageBox, QMainWindow, QLCDNumber, QComboBox, QDialogButtonBox, QWidget, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, uic
from PyQt5.QtGui import QIcon, QFont
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pandas.core.indexes.api import all_indexes_same

'''

TODO LIST
DONE Handle exception in time machine mode when no previous data is available
DONE Handle exception on saving when not initalized
DONE Handle exception when entering time machine mode when already in time machine mode
DONE custom data file directory
DONE customizability of fonts
- AutoSave
- Review Mode
- New Words Only Mode
- App Packing

'''
class GreSlayer(QMainWindow):
    def getFilePath(self, fileName):
        # File Directory
        self.file_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(self.file_dir, fileName)

    def __init__(self):
        super(GreSlayer, self).__init__()

        ''' 
        UI MAPPING
        '''
        #Load the UI file
        uic.loadUi(self.getFilePath('data/greSlayer.ui'), self)

        #Define widgets
        ## Labels
        self.label_word = self.findChild(QLabel, 'word_label')
        self.label_phonetic = self.findChild(QLabel, 'phonetic_label')
        self.label_engMeaning = self.findChild(QLabel, 'engMean_label')
        self.label_cnMeaning = self.findChild(QLabel, 'cnMean_label')

        ## Buttons
        self.masterButton = self.findChild(QPushButton, 'masterButton')
        self.unmasterButton = self.findChild(QPushButton, 'unmasterButton')
        self.meaningButton = self.findChild(QPushButton, 'meaningButton')

        ## Progress bar
        self.progressBar = self.findChild(QProgressBar, 'progressBar')
        
        ## LCD Number
        self.lcd_overall = self.findChild(QLCDNumber, 'lcd_overall')
        self.lcd_today = self.findChild(QLCDNumber, 'lcd_thisTrial')
        self.lcd_correct = self.findChild(QLCDNumber, 'lcd_correct')
        self.lcd_incorrect = self.findChild(QLCDNumber, 'lcd_incorrect')

        ## UI Size
        self.wordFontSize = 36
        self.phonFontSize = 13
        self.engMFontSize = 18
        self.cnMFontSize = 18
        self.wordFont = '.AppleSystemUIFont'
        self.phonFont = '.AppleSystemUIFont'
        self.engMFont = '.AppleSystemUIFont'
        self.cnMFont = '.AppleSystemUIFont'


        # Map widgets to functions
        self.masterButton.clicked.connect(self.masterWord)
        self.unmasterButton.clicked.connect(self.unmasterWord)
        self.meaningButton.clicked.connect(self.showMeaning)
        self.actionSave.triggered.connect(self.perform_save_df)
        self.actionTime_Machine.triggered.connect(self.timeMachinePrompt)
        self.actionEye_Sore.triggered.connect(self.preferencesPage)
        self.actionFile_Directory.triggered.connect(self.fileDirectorySelect)
        self.actionMeaning.triggered.connect(self.meaningToggle)
        '''
        INITIALIZATION
        '''
        self.today_correct_total = 0
        self.today_incorrect_total = 0
        self.lcd_correct.display(0)
        self.lcd_incorrect.display(0)
        self.mode = 'Default'
        self.timeMachine_timeStamp = None;
        self.file_path = None
        self.initialized = False
        self.first_time = True
        self.wordOnly = False
        

        # check if the data file (".slayerData") exists
        if os.path.isfile(self.getFilePath('.slayerData')):
            self.first_time = False
            with open(self.getFilePath('.slayerData'), 'r') as f:
                self.file_path = f.readline()
        else:
            print(self.getFilePath('.slayerData'))
            self.first_time = True
            self.fileDirectorySelect()

        self.fresh_initialize()
        # show the window
        self.show()

    def fresh_initialize(self):
        # Initialize data
        self.df = pd.read_excel(self.file_path).dropna(axis = 0, subset = ['Word'])
        
        self.totalNum = len(self.df)
        self.initialized = False
        self.numToday = 0
        self.i = 0 # index of the current word
        self.lcd_overall.display(0.00)
        self.lcd_today.display(0.00)
        self.sample_df = pd.DataFrame()
        self.clicked_word = False # if clicked the meaning button, then set this to True
        self.time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.small_save_helper = False # if the user has already saved the df, then set this to True
        # Initialize widgets
        ## Progress bar
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setMinimum(0)
        ## Labels
        self.label_word.setText('')
        self.label_phonetic.setText('')
        self.label_engMeaning.setText('')
        self.label_cnMeaning.setText('')
        ## Buttons
        self.masterButton.setEnabled(False)
        self.unmasterButton.setEnabled(False)


    def update_initilized(self, mode):
        self.initialized = True
        if mode == 'Default':
            self.mode = 'Default'
            self.sample_df = self.df.sample(n=self.numToday)

            #turn on lcd
            self.lcd_today.show()
            self.lcd_correct.show()
            self.lcd_incorrect.show()

        elif mode == "Time Machine":
            self.mode = 'Time Machine'
            self.sample_df = self.df[['Word', 'US Phonetics', 'Paraphrase (English)', 'Paraphrase (w/ POS)',
             'Paraphrase', 'Total Correct', 'Total Incorrect', 'Total Memorized',
              self.timeMachine_timeStamp]].loc[lambda x: x[self.timeMachine_timeStamp] == False]
            self.sample_df = self.sample_df.sample(n=len(self.sample_df))
            self.numToday = len(self.sample_df)

            # tunr off lcd
            self.lcd_today.hide()
            self.lcd_correct.hide()
            self.lcd_incorrect.hide()
        
        self.progressBar.setMaximum(self.numToday)
        '''
        update word, phonetic label, lcd_total for the first time
        '''
        self.label_word.setText(self.sample_df.iloc[self.i]['Word'])
        self.label_phonetic.setText(self.sample_df.iloc[self.i]['US Phonetics'])
        self.lcd_overall.display(round(self.sample_df.iloc[self.i]['Total Correct']/self.sample_df.iloc[self.i]['Total Memorized'], 2))

    def next_word(self):
        # update df first
        self.df.loc[self.sample_df.iloc[self.i].name, 'Total Memorized'] += 1

        
        self.clicked_word = False
        # disable master/unmaster button
        self.masterButton.setEnabled(False)
        self.unmasterButton.setEnabled(False)
        # remove meaning on screen
        self.label_engMeaning.setText('')
        self.label_cnMeaning.setText('')
        # update lcd number
        if self.mode == 'Default':
            self.lcd_today.display(round(self.today_correct_total/(self.today_correct_total+self.today_incorrect_total), 2))

        # subsequent update, based on new word
        self.i += 1
        # update progress bar
        self.progressBar.setValue(self.progressBar.value() + 1)

        if self.i >= self.numToday:
            self.perform_save_df()
            reply_box = QMessageBox.question(self, 'Message',
                "Your Progress has been saved! You have finished today's words. Do you want to start a new day?", QMessageBox.Yes |
                QMessageBox.No, QMessageBox.No)
            if reply_box == QMessageBox.Yes:
                self.fresh_initialize()
            else:
                self.small_save_helper = True
                self.close()
            return
        # update word, phonetic label
        self.label_word.setText(self.sample_df.iloc[self.i]['Word'])
        self.label_phonetic.setText(self.sample_df.iloc[self.i]['US Phonetics'])
        # update lcd number, total ratio
        self.lcd_overall.display(round(self.sample_df.iloc[self.i]['Total Correct']/self.sample_df.iloc[self.i]['Total Memorized'], 2))
    
    def masterWord(self):
        '''update df stats'''
        self.df.loc[self.sample_df.iloc[self.i].name, self.time_stamp] = True
        self.df.loc[self.sample_df.iloc[self.i].name, 'Total Correct'] += 1
        if self.mode == 'Default':
            self.today_correct_total += 1
            self.lcd_correct.display(self.today_correct_total)
        self.next_word()
        
    def unmasterWord(self):
        '''update df stats'''
        self.df.loc[self.sample_df.iloc[self.i].name, self.time_stamp] = False
        self.df.loc[self.sample_df.iloc[self.i].name, 'Total Incorrect'] += 1
        if self.mode == 'Default':
            self.today_incorrect_total += 1
            self.lcd_incorrect.display(self.today_incorrect_total)
        self.next_word()

    def showMeaning(self):
        if not self.initialized:
            self.settingPrompt()
        else:
            '''
            Retrieve the meaning of the word and update the labels
            '''
            if not self.wordOnly:
                self.label_engMeaning.setText(self.sample_df.iloc[self.i]['Paraphrase (English)'])
                self.label_cnMeaning.setText(self.sample_df.iloc[self.i]['Paraphrase (w/ POS)'])
            self.clicked_word = True
            self.masterButton.setEnabled(True)
            self.unmasterButton.setEnabled(True)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        if e.key() == Qt.Key_Comma:
            self.masterWord()
        if e.key() == Qt.Key_Period:
            self.showMeaning()
        if e.key() == Qt.Key_Slash:
            self.unmasterWord()
        if e.key() == Qt.Key_Semicolon:
            self.actionMeaning.setChecked(not self.actionMeaning.isChecked())
            self.meaningToggle()
    
    def closeEvent(self, event):
        if (self.initialized) and (self.i > 0): # handle some special cases
            reply = QMessageBox.question(self, 'Message',
                "Are you sure to quit?", QMessageBox.Yes |
                QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if (not self.small_save_helper): # the user has not saved the df, then confirm to save
                    save_reply = QMessageBox.question(self, 'Message',
                        "Do you want to save your progress?", QMessageBox.Yes |
                        QMessageBox.No, QMessageBox.No)
                    if save_reply == QMessageBox.Yes:
                        self.perform_save_df()
                event.accept()
            else:
                if self.small_save_helper: # the user
                    self.fresh_initialize()
                event.ignore()

    def perform_save_df(self):
        if self.initialized:
            self.df.to_excel(self.getFilePath('data/3000CN_ENG.xlsx'), index=False)
        else:
            # Warning
            reply = QMessageBox.question(self, 'Message',
                "You have not initialized the program. Do you want to save your progress anyway?", QMessageBox.Yes |
                QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.df.to_excel(self.getFilePath('data/3000CN_ENG.xlsx'), index=False)

    def meaningToggle(self):
        if self.actionMeaning.isChecked():
            self.wordOnly = False
            if self.initialized:
                self.label_engMeaning.setText(self.sample_df.iloc[self.i]['Paraphrase (English)'])
                self.label_cnMeaning.setText(self.sample_df.iloc[self.i]['Paraphrase (w/ POS)'])
        else:
            self.wordOnly = True
            self.label_engMeaning.setText('')
            self.label_cnMeaning.setText('')

    def settingPrompt(self): # ask user to select the number of words to memorize
        prompt = SettingPrompt(self)
        prompt.exec_()
    
    def timeMachinePrompt(self):
        if not self.initialized:
            if len(set(self.df.columns) - set(['Word', 'US Phonetics', 'Paraphrase (English)', 'Paraphrase (w/ POS)', 'Paraphrase', 'Total Correct', 'Total Incorrect', 'Total Memorized'])) == 0:
                QMessageBox.critical(self, 'Warning', 'No time stamp found!', QMessageBox.Ok)
            else:
                prompt = TimeMachine(self)
                prompt.exec_()
        else:
            # Warning
            QMessageBox.critical(self, 'Warning', 'You need to finish the current task in order to enter Time Machine mode', QMessageBox.Ok)

    def preferencesPage(self):
        prompt = Preferences(self)
        prompt.exec_()
    
    def fileDirectorySelect(self):
        if not self.initialized:

            if self.first_time:
                QMessageBox.information(self, 'Message', 'Please select the directory of your GRE Vcoab first!', QMessageBox.Ok)

            file_path = QFileDialog.getOpenFileName(self, 'Open File', './', 'Excel Files (*.xlsx)')[0]
            if file_path != '':
                self.file_path = file_path
                #update .slayerData file
                with open(self.getFilePath('.slayerData'), 'w') as f:
                    f.write(file_path)
            else:
                QMessageBox.critical(self, 'Warning', 'Please select a valid file!', QMessageBox.Ok)
                sys.exit()

        else:
            QMessageBox.critical(self, 'Warning', 'You need to finish the current task in order to change the file path', QMessageBox.Ok)

class Preferences(QDialog):
    def __init__(self, parent):
        super(Preferences, self).__init__(parent)
        self.parent = parent
        uic.loadUi(self.parent.getFilePath('data/preferences.ui'), self)
        # initialize spinbox value
        self.wordSize_spin.setValue(self.parent.wordFontSize)
        self.phoSize_spin.setValue(self.parent.phonFontSize)
        self.engSize_spin.setValue(self.parent.engMFontSize)
        self.cnSize_spin.setValue(self.parent.cnMFontSize)
        # initialize font combobox
        self.word_fontComboBox.setCurrentFont(QFont(self.parent.wordFont, self.parent.wordFontSize))
        self.pho_fontComboBox.setCurrentFont(QFont(self.parent.phonFont, self.parent.phonFontSize))
        self.eng_fontComboBox.setCurrentFont(QFont(self.parent.engMFont, self.parent.engMFontSize))
        self.cn_fontComboBox.setCurrentFont(QFont(self.parent.cnMFont, self.parent.cnMFontSize))

        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.close)
        self.show()

    def on_accept(self):
        self.parent.wordFontSize = self.wordSize_spin.value()
        self.parent.phonFontSize = self.phoSize_spin.value()
        self.parent.engMFontSize = self.engSize_spin.value()
        self.parent.cnMFontSize = self.cnSize_spin.value()

        # functionalize later
        if self.word_checkBox.isChecked():
            self.parent.wordFont = ".AppleSystemUIFont"
        else:
            self.parent.wordFont = self.word_fontComboBox.currentFont().toString().split(',')[0]
        
        if self.pho_checkBox.isChecked():
            self.parent.phonFont = ".AppleSystemUIFont"
        else:
            self.parent.phonFont = self.pho_fontComboBox.currentFont().toString().split(',')[0]
        
        if self.eng_checkBox.isChecked():
            self.parent.engMFont = ".AppleSystemUIFont"
        else:
            self.parent.engMFont = self.eng_fontComboBox.currentFont().toString().split(',')[0]

        if self.cn_checkBox.isChecked():
            self.parent.cnMFont = ".AppleSystemUIFont"
        else:
            self.parent.cnMFont = self.cn_fontComboBox.currentFont().toString().split(',')[0]
        
        self.update_fonts()
        self.close()
    
    def update_fonts(self):
        self.parent.label_word.setFont(QFont(self.parent.wordFont, self.parent.wordFontSize))
        self.parent.label_phonetic.setFont(QFont(self.parent.phonFont, self.parent.phonFontSize))
        self.parent.label_engMeaning.setFont(QFont(self.parent.engMFont, self.parent.engMFontSize))
        self.parent.label_cnMeaning.setFont(QFont(self.parent.cnMFont, self.parent.cnMFontSize))

    
        

class SettingPrompt(QDialog):
    def __init__(self, object):
        super(SettingPrompt, self).__init__()
        uic.loadUi(object.getFilePath('data/prompt.ui'), self)
        # initalize data
        self.number = 0
        # Define widgets
        self.prompt_label = self.findChild(QLabel, 'prompt_label')
        self.confirmButton = self.findChild(QPushButton, 'confirmButton')
        self.spinBox = self.findChild(QSpinBox, 'spinBox')
        
        # inilialize widgets
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(object.totalNum)
        self.prompt_label.setText(f'Please set the number of words you want to master(max={object.totalNum}):')
        # Map widgets to functions
        self.confirmButton.clicked.connect(lambda: self.onConfirmBtmClicked(object))

        self.show()
    
    def onConfirmBtmClicked(self, object):
        self.number = self.spinBox.value()
        object.numToday = self.number
        object.update_initilized("Default")
        self.close()
        
class TimeMachine(QDialog):
    def __init__(self, object):
        super(TimeMachine, self).__init__()
        uic.loadUi(object.getFilePath('data/timeMachine.ui'), self)
        # initalize data
        self.time_stamp = None
        ## get the time stamp
        self.all_timeStamps = list(set(object.df.columns) - set(['Word', 'US Phonetics', 'Paraphrase (English)', 'Paraphrase (w/ POS)', 'Paraphrase', 'Total Correct', 'Total Incorrect', 'Total Memorized']))
        self.all_timeStamps = sorted(self.all_timeStamps, key=lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'), reverse=True)
  
        ## iterate through the time stamps and get the number of correct and incorrect
        self.informative_timeStamps = {}
        for time_stamp in self.all_timeStamps:
            if len(object.df[object.df[time_stamp] == False]) > 0:
                self.informative_timeStamps[time_stamp] = {
                    'Correct': len(object.df[object.df[time_stamp] == True]),
                    'Incorrect': len(object.df[object.df[time_stamp] == False])
                    }
        ## update time stamps
        self.all_timeStamps = []
        for time_stamp, value in self.informative_timeStamps.items():
            self.all_timeStamps.append(time_stamp + '(Correct: ' + str(value['Correct']) + ', Incorrect: ' + str(value['Incorrect']) + ')')

        # Define widgets
        self.label_timeMachine = self.findChild(QLabel, 'label_timeMachine')
        self.comboBox_timeMachine = self.findChild(QComboBox, 'comboBox_timeMachine')
        self.buttonBox_timeMachine = self.findChild(QDialogButtonBox, 'buttonBox_timeMachine')

        # initalize widgets
        self.label_timeMachine.setText(f'Please select the time you want to go back to:')
        self.comboBox_timeMachine.addItems(self.all_timeStamps)

        # Map widgets to functions
        self.buttonBox_timeMachine.accepted.connect(lambda: self.onConfirmBtmClicked(object))
        self.buttonBox_timeMachine.rejected.connect(self.close)

        self.show()

    def onConfirmBtmClicked(self, object):
        self.time_stamp = self.comboBox_timeMachine.currentText()
        self.time_stamp = self.time_stamp.split('(')[0]
        object.timeMachine_timeStamp = self.time_stamp
        object.update_initilized("Time Machine")
        self.close()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GreSlayer()
    window.show()
    sys.exit(app.exec_())