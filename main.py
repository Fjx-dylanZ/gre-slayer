import sys
from PyQt5.QtWidgets import QApplication, QAction, QDialog, QSpinBox, QProgressBar, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QGridLayout, QMessageBox, QMainWindow, QLCDNumber, QComboBox, QDialogButtonBox, QWidget, QFileDialog, QPlainTextEdit
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, uic
from PyQt5.QtGui import QIcon, QFont
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import subprocess

'''

TODO LIST
- Daily Goal
DONE Handle exception in time machine mode when no previous data is available
DONE Handle exception on saving when not initalized
DONE Handle exception when entering time machine mode when already in time machine mode
DONE custom data file directory
DONE customizability of fonts
- AutoSave
DONE Review Mode
DONE New Words Only Mode
DONE Undo Redo
- Custom review mode + count
- App Packing

'''
class GreSlayer(QMainWindow):
    def getFilePath(self, fileName):
        # File Directory
        self.file_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(self.file_dir, fileName)

    def first_time_check(self):
        try:
            with open(self.getFilePath('.slayerData'), 'r') as f:
                slayerJSON = json.loads(f.readline())
                self.file_path = slayerJSON['file_path']
                if self.version != slayerJSON['version']:
                    raise Exception('Version Mismatch')

                self.wordFontSize = slayerJSON['wordFontSize']
                self.phonFontSize = slayerJSON['phonFontSize']
                self.engMFontSize = slayerJSON['engMFontSize']
                self.cnMFontSize = slayerJSON['cnMFontSize']
                self.annotFontSize = slayerJSON['annotFontSize']
                self.wordFont = slayerJSON['wordFont']
                self.phonFont = slayerJSON['phonFont']
                self.engMFont = slayerJSON['engMFont']
                self.cnMFont = slayerJSON['cnMFont']
                self.annotFont = slayerJSON['annotFont']
                self.update_fonts()
                
                saved_date = slayerJSON['today_date']
                saved_consolidated = int(slayerJSON['today_consolidated'])
                if saved_date == datetime.today().strftime('%Y-%m-%d'):
                    self.today_consolidated = saved_consolidated
                    self.update_objective_label()
        except:
            self.first_time = True
            self.fileDirectorySelect()
            self.versionUpdate()

    def __init__(self):
        super(GreSlayer, self).__init__()

        ''' 
        UI MAPPING
        '''
        #Load the UI file
        uic.loadUi(self.getFilePath('data/greSlayer.ui'), self)
        # Set windown title
        self.setWindowTitle('GRE Slayer')
        #Define widgets
        ## Labels
        self.label_word = self.findChild(QLabel, 'word_label')
        self.label_phonetic = self.findChild(QLabel, 'phonetic_label')
        self.label_engMeaning = self.findChild(QLabel, 'engMean_label')
        self.label_cnMeaning = self.findChild(QLabel, 'cnMean_label')
        self.label_annot = self.findChild(QLabel, 'annot_label')

        ## Buttons
        self.masterButton = self.findChild(QPushButton, 'masterButton')
        self.unmasterButton = self.findChild(QPushButton, 'unmasterButton')
        self.meaningButton = self.findChild(QPushButton, 'meaningButton')
        self.annotButton = self.findChild(QPushButton, 'annotButton')

        ## Annotation Text Edit
        self.annotText = self.findChild(QPlainTextEdit, 'annot_plainTextEdit')

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
        self.annotFontSize = 19
        self.wordFont = '.AppleSystemUIFont'
        self.phonFont = '.AppleSystemUIFont'
        self.engMFont = '.AppleSystemUIFont'
        self.cnMFont = '.AppleSystemUIFont'
        self.annotFont = '.AppleSystemUIFont'


        # Map widgets to functions
        self.masterButton.clicked.connect(self.masterWord)
        self.unmasterButton.clicked.connect(self.unmasterWord)
        self.meaningButton.clicked.connect(self.showMeaning)
        self.annotButton.clicked.connect(self.annotate)
        self.actionSave.triggered.connect(self.perform_save_df)
        self.actionTime_Machine.triggered.connect(self.timeMachinePrompt)
        self.actionEye_Sore.triggered.connect(self.preferencesPage)
        self.actionFile_Directory.triggered.connect(self.fileDirectorySelect)
        self.actionMeaning.triggered.connect(self.meaningToggle)
        self.actionAnnotate.triggered.connect(self.annotToggle)
        self.actionDictionary.triggered.connect(self.dictLookUp)
        self.actionReview_Mode.triggered.connect(self.reviewMode)
        self.actionNew_Words_Only.triggered.connect(self.newWordsOnlyMode)
        '''
        INITIALIZATION
        '''
        self.version = '0.0.5'
        self.dataFeatures = ['Word', 'US Phonetics', 'Paraphrase (English)', 'Paraphrase (w/ POS)', 'Paraphrase', 'Total Correct', 'Total Incorrect', 'Total Memorized', 'Annotation']
        self.today_date = datetime.now().strftime("%Y-%m-%d")
        self.today_goal = 200
        self.today_consolidated = 0 # the number of words that previously were not memorized but are now

        self.today_correct_total = 0
        self.today_incorrect_total = 0
        self.lcd_correct.display(0)
        self.lcd_incorrect.display(0)
        self.mode = 'Default'
        self.timeMachine_timeStamp = None;
        self.file_path = None # file path of the data file
        self.initialized = False 
        self.first_time = True # first time using the program
        self.wordOnly = False # if true, only show words, no meaning, annotation
        
        # hide annotation text edit layout
        self.annotText.setVisible(False)
        self.annotButton.setVisible(False)
        #self.label_annot.setVisible(False)

        # check if the data file (".slayerData") integrity is intact
        self.first_time_check()

        self.fresh_initialize()
        # show the window
        self.show()
    
    def read_data(self):
        self.df = self.df = pd.read_excel(self.file_path).dropna(axis = 0, subset = ['Word'])
        self.df[['Word', 'Paraphrase', 'Paraphrase (w/ POS)', 'Paraphrase (English)', 'US Phonetics']] = self.df[['Word', 'Paraphrase', 'Paraphrase (w/ POS)', 'Paraphrase (English)', 'US Phonetics']].astype(str)

    def fresh_initialize(self):
        # Initialize data
        self.read_data()

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
        self.label_annot.setText('')
        self.label_engMeaning.setText('')
        self.label_cnMeaning.setText('')
        ## Buttons
        self.masterButton.setEnabled(False)
        self.unmasterButton.setEnabled(False)

    def hideShow_LCD(self, switch: bool):
        if switch:
            self.lcd_today.show()
            self.lcd_correct.show()
            self.lcd_incorrect.show()
        else:
            self.lcd_today.hide()
            self.lcd_correct.hide()
            self.lcd_incorrect.hide()

    def update_initilized(self, mode):
        self.initialized = True
        if mode == 'Default':
            self.mode = 'Default'
            self.sample_df = self.df.sample(n=self.numToday)

            #turn on lcd
            self.hideShow_LCD(True)


        elif mode == "Time Machine":
            self.mode = 'Time Machine'
            self.sample_df = self.df[self.dataFeatures + [self.timeMachine_timeStamp]].loc[lambda x: x[self.timeMachine_timeStamp] == False]
            self.sample_df = self.sample_df.sample(n=len(self.sample_df))
            self.numToday = len(self.sample_df)
            # tunr off lcd
            self.hideShow_LCD(False)

        elif mode == "Review":
            self.mode = 'Review'
            self.sample_df = self.df.query("`Total Memorized` > 0")
            self.sample_df = self.sample_df.sample(n=len(self.sample_df))
            self.numToday = len(self.sample_df)
            # tunr off lcd
            self.hideShow_LCD(False)
        
        elif mode == "Review New":
            self.mode = 'Review New'
            self.sample_df = self.df.query("`Total Correct` == 0")
            self.sample_df = self.sample_df.sample(n=len(self.sample_df))
            self.numToday = len(self.sample_df)
            # tunr off lcd
            self.hideShow_LCD(False)
        
        elif mode == "New Words Only":
            self.mode = 'New Words Only'
            self.sample_df = self.df.query("`Total Memorized` == 0")
            self.sample_df = self.sample_df.sample(n=len(self.sample_df))
            self.numToday = len(self.sample_df)
            # tunr on lcd
            self.hideShow_LCD(True)
        
        self.progressBar.setMaximum(self.numToday)
        '''
        update word, phonetic label, lcd_total for the first time
        '''
        self.label_word.setText(self.sample_df.iloc[self.i]['Word'])
        self.label_phonetic.setText(self.sample_df.iloc[self.i]['US Phonetics'])
        self.lcd_overall.display(round(self.sample_df.iloc[self.i]['Total Correct']/self.sample_df.iloc[self.i]['Total Memorized'], 2))
    
    def annotate(self):
        if not self.initialized: return
        if self.annotText.toPlainText() == '': return
        annotate_text = self.annotText.toPlainText()
        self.df.loc[self.sample_df.iloc[self.i].name, 'Annotation'] = annotate_text
        self.label_annot.setText(annotate_text)
        self.label_annot.setVisible(True)
        self.annotText.clear()
        #set focus elsewhere
        self.label_word.setFocus()


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
        self.label_annot.setText('')
        self.label_annot.setVisible(False)
        # update lcd number
        if self.mode == 'Default' or self.mode == 'New Words Only':
            self.lcd_today.display(round(self.today_correct_total/(self.today_correct_total+self.today_incorrect_total), 2))

        # show last word on label_lastWord
        self.label_lastWord.setText(f"{self.sample_df.iloc[self.i]['Word']}: {self.sample_df.iloc[self.i]['Paraphrase']}")

        if (self.i % 15 == 0) and (self.i != 0):
            self.perform_save_df()

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
        self.label_word.setFocus() # necessary if annotation mode is on
    
    def update_objective_label(self):
        self.label_objective.setText(f"Today's Objective: {self.today_consolidated}/200")

    def masterWord(self):
        '''update df stats'''
        self.masterButton.setFocus()
        if self.clicked_word:
            self.df.loc[self.sample_df.iloc[self.i].name, self.time_stamp] = True
            self.df.loc[self.sample_df.iloc[self.i].name, 'Total Correct'] += 1
            if self.mode == 'Default' or self.mode == "New Words Only":
                self.today_correct_total += 1
                self.lcd_correct.display(self.today_correct_total)
            
            if self.df.loc[self.sample_df.iloc[self.i].name, 'Total Incorrect'] > (self.df.loc[self.sample_df.iloc[self.i].name, 'Total Correct'] - 1):
                self.today_consolidated += 1
                self.update_objective_label()
            self.next_word()
        
    def unmasterWord(self):
        '''update df stats'''
        self.unmasterButton.setFocus()
        if self.clicked_word:
            #if self.actionAnnotate.isChecked():
            #    self.annotText.setEnabled(False) # hacky, change later
            self.df.loc[self.sample_df.iloc[self.i].name, self.time_stamp] = False
            self.df.loc[self.sample_df.iloc[self.i].name, 'Total Incorrect'] += 1
            if self.mode == 'Default' or self.mode == "New Words Only":
                self.today_incorrect_total += 1
                self.lcd_incorrect.display(self.today_incorrect_total)
            self.next_word()

    def showMeaning(self):
        #print(self.df.info())
        self.label_word.setFocus()
        if not self.initialized:
            self.settingPrompt()
        else:
            '''
            Retrieve the meaning of the word and update the labels
            '''
            if not self.wordOnly:
                annotation = self.df.loc[self.sample_df.iloc[self.i].name, 'Annotation']
                self.label_annot.setVisible(not pd.isnull(annotation))
                self.label_engMeaning.setText(self.sample_df.iloc[self.i]['Paraphrase (English)'])
                self.label_cnMeaning.setText(self.sample_df.iloc[self.i]['Paraphrase (w/ POS)'])
                self.label_annot.setText((lambda _: _ if not pd.isnull(_) else '')(annotation))

            self.clicked_word = True
            self.masterButton.setEnabled(True)
            self.unmasterButton.setEnabled(True)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.changeFocus()
        if e.key() == Qt.Key_Comma:
            self.masterButton.click()
        if e.key() == Qt.Key_Period:
            self.meaningButton.click()
        if e.key() == Qt.Key_Slash:
            self.unmasterButton.click()
        if e.key() == Qt.Key_Semicolon:
            self.actionMeaning.setChecked(not self.actionMeaning.isChecked())
            self.meaningToggle()
        if e.key() == Qt.Key_Return:
            if self.actionAnnotate.isChecked():
                print('annotate')
                self.annotText.setFocus()
        # back slash
        if e.key() == Qt.Key_Backslash:
            self.undo()

    def undo(self):
        if not self.initialized: return
        if self.i == 0: return
        self.masterButton.setEnabled(False)
        self.unmasterButton.setEnabled(False)
        self.i -= 1
        self.progressBar.setValue(self.progressBar.value() - 1)
        self.label_word.setText(self.sample_df.iloc[self.i]['Word'])
        self.label_phonetic.setText(self.sample_df.iloc[self.i]['US Phonetics'])
        self.label_engMeaning.setText('')
        self.label_cnMeaning.setText('')
        self.label_annot.setText('')

        if self.df.loc[self.sample_df.iloc[self.i].name, self.time_stamp] == True:
            self.df.loc[self.sample_df.iloc[self.i].name, self.time_stamp] = np.nan
            self.df.loc[self.sample_df.iloc[self.i].name, 'Total Correct'] -= 1
            if self.mode == 'Default' or self.mode == "New Words Only":
                self.today_correct_total -= 1
                self.lcd_correct.display(self.today_correct_total)
            # update objective label
            if self.df.loc[self.sample_df.iloc[self.i].name, 'Total Incorrect'] > (self.df.loc[self.sample_df.iloc[self.i].name, 'Total Correct'] - 1):
                self.today_consolidated -= 1
                self.update_objective_label()
        elif self.df.loc[self.sample_df.iloc[self.i].name, self.time_stamp] == False:
            self.df.loc[self.sample_df.iloc[self.i].name, self.time_stamp] = np.nan
            self.df.loc[self.sample_df.iloc[self.i].name, 'Total Incorrect'] -= 1
            if self.mode == 'Default' or self.mode == "New Words Only":
                self.today_incorrect_total -= 1
                self.lcd_incorrect.display(self.today_incorrect_total)
        else:
            raise ValueError('Undo error')
        self.df.loc[self.sample_df.iloc[self.i].name, 'Total Memorized'] -= 1
        #if not self.integrityCheck():
        #    raise ValueError('Undo error')
    def integrityCheck(self):
        defiled = (self.df.loc[:, 'Total Correct'].astype(int) + self.df.loc[:, 'Total Incorrect'].astype(int) != self.df.loc[:, 'Total Memorized'].astype(int)).any()
        if defiled:
            print('Integrity check failed')
            return False
        return True
        

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
            self.df.to_excel(self.file_path, index=False)
            self.outputConfig()
        else:
            # Warning
            reply = QMessageBox.question(self, 'Message',
                "You have not initialized the program. Do you want to save your progress anyway?", QMessageBox.Yes |
                QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.df.to_excel(self.file_path, index=False)

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

    def annotToggle(self):
        if not self.initialized:
            self.actionAnnotate.setChecked(False)
            return
        self.annotButton.setEnabled(self.actionAnnotate.isChecked())
        self.annotButton.setVisible(self.actionAnnotate.isChecked())
        self.annotText.setEnabled(self.actionAnnotate.isChecked())
        self.annotText.setVisible(self.actionAnnotate.isChecked())
        if self.actionAnnotate.isChecked():
            self.annotText.setFocus()
        else:
            self.label_word.setFocus()

    def settingPrompt(self): # ask user to select the number of words to memorize
        prompt = SettingPrompt(self)
        prompt.exec_()
    
    def reviewMode(self):
        if self.initialized:
            QMessageBox.critical(self, 'Warning', 'You need to finish the current task in order to enter Time Machine mode', QMessageBox.Ok)
            return
        # Ask user to choose A or B
        reply = QMessageBox.question(self, 'Message', 'Yes - Review all words\nNo - Review the words you have not got right yet', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            num = len(self.df.query("`Total Memorized` > 0"))
            if num == 0:
                QMessageBox.critical(self, 'Warning', 'No words have been memorized yet', QMessageBox.Ok)
                return
            self.update_initilized('Review')
        elif reply == QMessageBox.No:
            num = len(self.df.query("`Total Correct` == 0"))
            QMessageBox.information(self, 'Message', 'You will review {} new words'.format(num), QMessageBox.Ok)
            if num == 0:
                QMessageBox.critical(self, 'Warning', 'No new words have been memorized yet', QMessageBox.Ok)
                return
            self.update_initilized('Review New')
        else:
            return
    
    def newWordsOnlyMode(self):
        if not self.initialized:
            num = len(self.df.query("`Total Memorized` == 0"))
            if num == 0:
                QMessageBox.information(self, 'Message',
                    "You have memorized all words! Hooray!")
                return
            # confitm to start
            reply = QMessageBox.question(self, 'Message',
                "You will be reviewing " + str(num) + " words. Are you sure to start?", QMessageBox.Yes |
                QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.update_initilized("New Words Only")
            else:
                return
        else:
            # Warning
            QMessageBox.critical(self, 'Warning', 'You need to finish the current task in order to enter Time Machine mode', QMessageBox.Ok)

    def timeMachinePrompt(self):
        if not self.initialized:
            if len(set(self.df.columns) - set(self.dataFeatures)) == 0:
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
                self.outputConfig()
            else:
                QMessageBox.critical(self, 'Warning', 'Please select a valid file!', QMessageBox.Ok)
                sys.exit()

        else:
            QMessageBox.critical(self, 'Warning', 'You need to finish the current task in order to change the file path', QMessageBox.Ok)
    
    def versionUpdate(self):
        temp_df = pd.read_excel(self.file_path).dropna(axis = 0, subset = ['Word'])
        columns = temp_df.columns
        if 'Annotation' not in columns:
            temp_df.insert(0, 'Annotation', [None for _ in range(0, len(temp_df))])
        temp_df.to_excel(self.file_path, index=False)
    def dictLookUp(self):
        if not self.initialized:
            return
        word = self.sample_df.iloc[self.i]['Word']
        subprocess.Popen(['open', 'dict://'+word])
    def changeFocus(self):
        self.label_word.setFocus()
    
    def outputConfig(self):
        with open(self.getFilePath('.slayerData'), 'w') as f:
            f.write(json.dumps({
                "version": self.version, 
                "file_path": self.file_path, 
                "wordFontSize": self.wordFontSize, 
                "phonFontSize": self.phonFontSize, 
                "engMFontSize": self.engMFontSize,
                "cnMFontSize": self.cnMFontSize, 
                "annotFontSize": self.annotFontSize,
                "wordFont": self.wordFont,
                "phonFont": self.phonFont,
                "engMFont": self.engMFont,
                "cnMFont": self.cnMFont,
                "annotFont": self.annotFont,
                "today_date": self.today_date,
                "today_consolidated": self.today_consolidated
                })
                ) 

    def update_fonts(self):
        self.label_word.setFont(QFont(self.wordFont, self.wordFontSize))
        self.label_phonetic.setFont(QFont(self.phonFont, self.phonFontSize))
        self.label_engMeaning.setFont(QFont(self.engMFont, self.engMFontSize))
        self.label_cnMeaning.setFont(QFont(self.cnMFont, self.cnMFontSize))
        self.label_annot.setFont(QFont(self.annotFont, self.annotFontSize))

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
        self.annotSize_spin.setValue(self.parent.annotFontSize)
        # initialize font combobox
        self.word_fontComboBox.setCurrentFont(QFont(self.parent.wordFont, self.parent.wordFontSize))
        self.pho_fontComboBox.setCurrentFont(QFont(self.parent.phonFont, self.parent.phonFontSize))
        self.eng_fontComboBox.setCurrentFont(QFont(self.parent.engMFont, self.parent.engMFontSize))
        self.cn_fontComboBox.setCurrentFont(QFont(self.parent.cnMFont, self.parent.cnMFontSize))
        self.annot_fontComboBox.setCurrentFont(QFont(self.parent.annotFont, self.parent.annotFontSize))

        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.close)
        self.show()

    def on_accept(self):
        self.parent.wordFontSize = self.wordSize_spin.value()
        self.parent.phonFontSize = self.phoSize_spin.value()
        self.parent.engMFontSize = self.engSize_spin.value()
        self.parent.cnMFontSize = self.cnSize_spin.value()
        self.parent.annotFontSize = self.annotSize_spin.value()

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
        
        if self.annot_checkBox.isChecked():
            self.parent.annotFont = ".AppleSystemUIFont"
        else:
            self.parent.annotFont = self.annot_fontComboBox.currentFont().toString().split(',')[0]

        self.parent.update_fonts()
        self.close()

    
    

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
        self.all_timeStamps = list(set(object.df.columns) - set(object.dataFeatures))
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