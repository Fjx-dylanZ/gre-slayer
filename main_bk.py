import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import pandas as pd

import uuid


def get_random_word(file_name="再要你命3000（完整版）.xlsx",
                    sheet_name='3000',
                    num=200,
                    save_option=True):
    df = pd.read_excel(file_name, sheet_name=sheet_name)
    df = df.loc[:, ['Word', 'UK Phonetics', 'US Phonetics', 'Paraphrase']]

    if num == 'NULL':
        num = df.shape[0]
    # Normal Approximation
    acc_Prob = 0  # acccumulated probability
    acc_True = 0  # acccumulated True
    acc_Trials = 0  # acccumulated trials
    Mastered_index = []
    Unmastered_index = []
    population_size = 3000
    acc_Trials += 1
    word_list = df.sample(n=num, replace=False)
    word_list = word_list.reset_index(drop=True)
    for i in range(num):
        acc_Trials += 1
        word = word_list.iloc[i, :]
        # print("word: {}, phonetic: {}".format(word.loc['Word'], word.loc['US Phonetics']))
        yield word.loc['Word']
        yield word.loc['US Phonetics']
        yield word.loc['Paraphrase']

        acc_Prob = acc_True / acc_Trials
        # print("================{}/{}=================".format(i+1, num))

        if acc_Trials % 10 == 0:
            print("Accumulated probability: %.2f" % acc_Prob)
            print(acc_Prob * population_size)

    if save_option == False:
        return
    vocab_Mastered = word_list.iloc[Mastered_index].reset_index(drop=True)
    vocab_Unmastered = word_list.iloc[Unmastered_index].reset_index(drop=True)
    uuid_str = str(uuid.uuid4())
    review_file_name = 'vocab_Unmastered' + '_' + str(round(acc_Prob, 2)) + '_' + uuid_str + '.xlsx'
    mastered_file_name = 'vocab_Mastered' + '_' + str(round(acc_Prob, 2)) + '_' + uuid_str + '.xlsx'
    vocab_Mastered.to_excel(mastered_file_name, sheet_name='sheet1', index=False)
    print("successfully saved: " + mastered_file_name)
    vocab_Unmastered.to_excel(review_file_name, sheet_name='sheet1', index=False)
    print("successfully saved: " + review_file_name)
    return vocab_Mastered, vocab_Unmastered, review_file_name




class GreSlayer(QWidget):

    def __init__(self, parent=None):
        super(GreSlayer, self).__init__(parent)
        '''
        Excel File configuration
        '''
        self.file_name= "再要你命3000（完整版）.xlsx"
        self.sheet_name = '3000'
        self.num = 200
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
        self.word = QLabel(next(self.generator))
        self.word.setAlignment(Qt.AlignCenter)
        self.word.setFont(QtGui.QFont('Arial', 50))
        self.pronunciation = QLabel(next(self.generator))
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
        self.b_master.clicked.connect(self.next_word)
        self.b_showmeaning.clicked.connect(self.show_meaning)
        self.b_unmaster.clicked.connect(self.next_word)
        self.is_meaning_showed = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Comma:
            self.next_word()
        elif event.key() == Qt.Key_Period:
            self.show_meaning()
        elif event.key() == Qt.Key_Slash:
            self.next_word()
    def next_word(self):
        if self.i < self.num:
            self.curr_word = self.word_list.iloc[self.i, :]
            self.i = self.i + 1
        else:
            self.perform_save()

    def perform_save(self):
        vocab_Mastered = self.word_list.iloc[self.Mastered_index].reset_index(drop=True)
        vocab_Unmastered = self.word_list.iloc[self.Unmastered_index].reset_index(drop=True)
        uuid_str = str(uuid.uuid4())
        review_file_name = 'vocab_Unmastered' + '_' + str(round(self.acc_Prob, 2)) + '_' + uuid_str + '.xlsx'
        mastered_file_name = 'vocab_Mastered' + '_' + str(round(self.acc_Prob, 2)) + '_' + uuid_str + '.xlsx'
        vocab_Mastered.to_excel(mastered_file_name, sheet_name='sheet1', index=False)
        print("successfully saved: " + mastered_file_name)
        vocab_Unmastered.to_excel(review_file_name, sheet_name='sheet1', index=False)
        print("successfully saved: " + review_file_name)
        exit(0)

    def master_perform(self):
        if (self.is_meaning_showed):
            self.meaning.setText("")
            self.word.setText(self.curr_word.loc['Word'])
            self.pronunciation.setText(self.curr_word.loc['US Phonetics'])
            self.is_meaning_showed = not self.is_meaning_showed
    def unmaster_perform(self):
        if (self.is_meaning_showed):
            self.next_word(
            self.meaning.setText("")
            self.word.setText(self.curr_word.loc['Word'])
            self.pronunciation.setText(self.curr_word.loc['US Phonetics'])
            self.is_meaning_showed = not self.is_meaning_showed

    def next_word(self):
        if (self.is_meaning_showed):
            self.meaning.setText("")
            self.word.setText(next(self.generator))
            self.pronunciation.setText(next(self.generator))
            self.is_meaning_showed = not self.is_meaning_showed

    def show_meaning(self):
        if (not self.is_meaning_showed):
            self.meaning.setText(next(self.generator))
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
