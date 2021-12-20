import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import pandas as pd
import uuid

class GreSlayer(QWidget):

    def __init__(self, parent=None):
        super(GreSlayer, self).__init__(parent)
        '''
        Excel File configuration
        '''
        self.file_name= "再要你命3000（完整版）.xlsx"
        self.sheet_name = '3000'
        self.num = 30
        self.df = pd.read_excel(self.file_name, sheet_name=self.sheet_name)
        self.df = self.df.loc[:, ['Word', 'UK Phonetics', 'US Phonetics', 'Paraphrase']]
        self.acc_Prob = 0  # acccumulated probability
        self.acc_True = 0  # acccumulated True
        self.acc_Trials = 0  # acccumulated trials
        self.Mastered_index = []
        self.Unmastered_index = []
        self.population_size = 3000
        self.acc_Trials += 1
        self.word_list = self.df.sample(n=self.num, replace=False)
        self.word_list = self.word_list.reset_index(drop=True)
        self.curr_word = self.word_list.iloc[0, :]
        self.i = 1

        # self.generator = get_random_word()
        '''
        GUI QtWidgets
        '''
        self.b_master = QPushButton("master")
        self.b_showmeaning = QPushButton("show meaning")
        self.b_unmaster = QPushButton("unmaster")
        self.word = QLabel(self.curr_word.loc['Word'])
        self.word.setAlignment(Qt.AlignCenter)
        self.word.setFont(QtGui.QFont('Arial', 50))
        self.pronunciation = QLabel(self.curr_word.loc['US Phonetics'])
        self.pronunciation.setAlignment(Qt.AlignCenter)
        self.pronunciation.setFont(QtGui.QFont("Arial", 20))
        self.meaning = QLabel("")
        self.meaning.setAlignment(Qt.AlignCenter)
        self.meaning.setWordWrap(True)
        self.meaning.setFont(QtGui.QFont('Arial', 50))

        '''
        Layouts
        '''
        layout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.b_master)
        hlayout.addWidget(self.b_showmeaning)
        hlayout.addWidget(self.b_unmaster)
        layout.addWidget(self.word)
        layout.addWidget(self.pronunciation)
        layout.addWidget(self.meaning)
        layout.addLayout(hlayout)
        self.setLayout(layout)

        '''
        map widgets to functions
        '''
        self.b_master.clicked.connect(self.master_perform)
        self.b_showmeaning.clicked.connect(self.show_meaning)
        self.b_unmaster.clicked.connect(self.unmaster_perform)
        self.is_meaning_showed = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Comma:
            self.master_perform()
        elif event.key() == Qt.Key_Period:
            self.show_meaning()
        elif event.key() == Qt.Key_Slash:
            self.unmaster_perform()

    def next_word(self):
        if self.i < self.num - 1:
            if self.i % 10 == 0:
                self.acc_Prob = self.acc_True / self.i
                print("Accumulated probability: %.2f" % self.acc_Prob)
            self.curr_word = self.word_list.iloc[self.i, :]
            self.i = self.i + 1
        else:
            self.perform_save()

    def perform_save(self):
        data_dir_path = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(data_dir_path):
            os.mkdir(data_dir_path)

        vocab_Mastered = self.word_list.iloc[self.Mastered_index].reset_index(drop=True)
        vocab_Unmastered = self.word_list.iloc[self.Unmastered_index].reset_index(drop=True)
        uuid_str = str(uuid.uuid4())
        review_file_name = 'vocab_Unmastered' + '_' + str(round(self.acc_Prob, 2)) + '_' + uuid_str + '.xlsx'
        review_file_name = os.path.join(data_dir_path, review_file_name)
        mastered_file_name = 'vocab_Mastered' + '_' + str(round(self.acc_Prob, 2)) + '_' + uuid_str + '.xlsx'
        mastered_file_name = os.path.join(data_dir_path, mastered_file_name)
        vocab_Mastered.to_excel(mastered_file_name, sheet_name='sheet1', index=False)
        print("successfully saved: " + mastered_file_name)
        vocab_Unmastered.to_excel(review_file_name, sheet_name='sheet1', index=False)
        print("successfully saved: " + review_file_name)
        exit(0)

    def master_perform(self):
        if (self.is_meaning_showed):
            self.acc_True += 1
            self.Mastered_index.append(self.i)
            self.next_word()
            self.meaning.setText("")
            self.word.setText(self.curr_word.loc['Word'])
            self.pronunciation.setText(self.curr_word.loc['US Phonetics'])
            self.is_meaning_showed = not self.is_meaning_showed


    def unmaster_perform(self):
        if (self.is_meaning_showed):
            self.Unmastered_index.append(self.i)
            self.next_word()
            self.meaning.setText("")
            self.word.setText(self.curr_word.loc['Word'])
            self.pronunciation.setText(self.curr_word.loc['US Phonetics'])
            self.is_meaning_showed = not self.is_meaning_showed


    def show_meaning(self):
        if (not self.is_meaning_showed):
            self.meaning.setText(self.curr_word.loc['Paraphrase'])
            self.is_meaning_showed = not self.is_meaning_showed

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # app.setStyleSheet("QLabel{font-size: 18pt;}")
    # Create and show the form
    slayer = GreSlayer()
    slayer.resize(800, 400)
    slayer.show()

    sys.exit(app.exec())
