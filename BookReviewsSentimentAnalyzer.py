"""-------------------------------------------
Package Name: BookReviewsSentimentAnalyzer
Author: Hussain Ali Khan
Version: 1.0.1
Last Modified: 12/02/2018
-------------------------------------------
"""

import sys
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QMessageBox, QDesktopWidget
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer
import goodreads_api_client as gr
from PyQt5 import QtWidgets, QtGui
import requests
from requests import HTTPError
from bs4 import BeautifulSoup
import re
import pandas as pd


class BookProfiler(QMainWindow):
    def __init__(self):
        super(BookProfiler, self).__init__()
        loadUi('book.ui', self)
        qt_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())
        self.search_btn.clicked.connect(self.search_book)
        self.export_to_csv_btn.clicked.connect(self.export)
        self.search_txt.setText("")
        self.client = gr.Client(developer_key='NqaQK91zheH4ofJYuTmpA')
        self.search_tbl.resizeRowsToContents()
        self.search_tbl.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.label_default_style = 'color: red; font-size: 16px; background-color: none; text-align: justify;'
        self.book_data = {}
        self.book_review_data = {}
        self.clear_fields()

    @pyqtSlot()
    def search_book(self):

        self.clear_fields()

        book_isbn = self.search_txt.text()

        if book_isbn != "":

            if (len(book_isbn) == 10 or len(book_isbn) == 13) and book_isbn.isnumeric():
                try:
                    book = self.get_book(book_isbn)

                    keys_wanted = ['id', 'title', 'isbn', 'isbn13', 'num_pages', 'authors', 'format',
                                   'edition_information',
                                   'publisher', 'publication_day', 'publication_month', 'publication_year',
                                   'description']

                    reduced_book = {k: v for k, v in book.items() if k in keys_wanted}

                    book_id = ""

                    if reduced_book["id"] is not None:
                        book_id = reduced_book["id"]

                    authors = "N/A"

                    if len(reduced_book["authors"]["author"]) > 0:
                        try:
                            authors = reduced_book["authors"]["author"]["name"]
                        except TypeError:
                            author_names = []
                            for author in reduced_book["authors"]["author"]:
                                if author is not None:
                                    author_names.append(author["name"])
                            authors = ', '.join(author_names)

                    date_published = "N/A"

                    if reduced_book["publication_day"] is not None:
                        if reduced_book["publication_month"] is not None:
                            if reduced_book["publication_year"] is not None:
                                date_published = reduced_book["publication_day"] + "/" + reduced_book[
                                    "publication_month"] + "/" + \
                                                 reduced_book["publication_year"]
                    elif reduced_book["publication_month"] is not None:
                        if reduced_book["publication_year"] is not None:
                            date_published = reduced_book["publication_month"] + "/" + reduced_book["publication_year"]

                    isbn = "N/A"

                    if reduced_book["isbn"] is not None:
                        isbn = reduced_book["isbn"]

                    reviews = self.get_reviews(isbn)

                    self.book_review_data = reviews

                    isbn13 = "N/A"

                    if reduced_book["isbn13"] is not None:
                        isbn13 = reduced_book["isbn13"]

                    edition = "N/A"

                    if reduced_book["edition_information"] is not None:
                        edition = reduced_book["edition_information"]

                    book_format = "N/A"

                    if reduced_book["format"] is not None:
                        book_format = reduced_book["format"]

                    publisher = "N/A"

                    if reduced_book["publisher"] is not None:
                        publisher = reduced_book["publisher"]

                    pages = "N/A"

                    if reduced_book["num_pages"] is not None:
                        pages = reduced_book["num_pages"]

                    title = "N/A"

                    if reduced_book["title"] is not None:
                        title = reduced_book["title"]

                    description = "N/A"

                    if reduced_book["description"] is not None:
                        description = reduced_book["description"]

                    book_info = {
                        "isbn": isbn,
                        "isbn13": isbn13,
                        "title": title,
                        "authors": authors,
                        "pages": pages,
                        "date_published": date_published,
                        "edition": edition,
                        "format": book_format,
                        "publisher": publisher,
                        "description": description
                    }

                    self.book_data = book_info

                    self.show_information(book_info, reviews)

                except HTTPError:
                    print("ISBN isn't Valid")
                    self.show_message("ISBN Not Found On Goodreads.com", "Error! ISBN Not Found!!")

            else:
                self.show_message("Please Enter A Valid ISBN Number", "Error! Invalid ISBN Entered!!")

        else:
            self.show_message("Please Enter ISBN Number To Search", "Error! Empty ISBN")

    def get_book(self, isbn):
        book = self.client.Book.show_by_isbn(str(isbn))
        return book

    def clear_fields(self):
        self.book_isbn.setText("")
        self.book_isbn13.setText("")
        self.book_title.setText("")
        self.book_authors.setText("")
        self.book_pages.setText("")
        self.book_date_published.setText("")
        self.book_edition.setText("")
        self.book_format.setText("")
        self.book_publisher.setText("")
        self.book_description.setText("")
        self.search_tbl.setRowCount(0)

    def get_reviews(self, isbn):

        key = "NqaQK91zheH4ofJYuTmpA"

        endpoint = "https://www.goodreads.com/api/reviews_widget_iframe?did=" + key +\
                   "&amp;format=html&amp;isbn=" + isbn + \
                   "&amp;links=660&amp;review_back=fff&amp;stars=000&amp;text=000"

        r = requests.get(url=endpoint)

        soup = BeautifulSoup(r.content, "html.parser")

        reviews = soup.find_all('div', attrs={"itemprop": "reviews"})

        review_by = []
        review_rating = []
        review_text = []

        for review in reviews:

            reviewer = review.find("span", attrs={"class": "gr_review_by"})

            if reviewer is not None:
                reviewer = reviewer.a
                if reviewer is not None:
                    review_by.append(reviewer.text)
            else:
                review_by.append("N/A")

            rating = review.find("span", attrs={"class": "gr_rating"})

            if rating is not None:
                review_rating.append(self.get_rating(rating.text))
            else:
                review_rating.append("N/A")

            rev = review.find("div", attrs={"class": "gr_review_text"})

            if rev is not None:
                review_text.append(self.clean_text(rev.text))
            else:
                review_text.append("N/A")

        revs = {"reviewer": review_by, "rating": review_rating, "review": review_text}
        return revs

    def show_information(self, book_info, reviews):

        if reviews is not None:
            reviewers = reviews["reviewer"]
            ratings = reviews["rating"]
            reviews_text = reviews["review"]

            for rev in range(len(reviewers)):
                pos = self.search_tbl.rowCount()
                self.search_tbl.insertRow(pos)
                self.search_tbl.setItem(pos, 0, QtWidgets.QTableWidgetItem(reviewers[rev]))
                self.search_tbl.setItem(pos, 1, QtWidgets.QTableWidgetItem(str(ratings[rev])+"/5"))
                self.search_tbl.setItem(pos, 2, QtWidgets.QTableWidgetItem(reviews_text[rev]))
                self.search_tbl.resizeColumnsToContents()

        self.book_isbn.setText(book_info["isbn"])
        self.book_isbn.setStyleSheet(self.label_default_style)
        self.book_isbn13.setText(book_info["isbn13"])
        self.book_isbn13.setStyleSheet(self.label_default_style)
        self.book_title.setText(book_info["title"])
        self.book_title.setStyleSheet(self.label_default_style)
        self.book_authors.setText(book_info["authors"])
        self.book_authors.setStyleSheet(self.label_default_style)
        self.book_pages.setText(book_info["pages"])
        self.book_pages.setStyleSheet(self.label_default_style)
        self.book_date_published.setText(book_info["date_published"])
        self.book_date_published.setStyleSheet(self.label_default_style)
        self.book_edition.setText(book_info["edition"])
        self.book_edition.setStyleSheet(self.label_default_style)
        self.book_format.setText(book_info["format"])
        self.book_format.setStyleSheet(self.label_default_style)
        self.book_publisher.setText(book_info["publisher"])
        self.book_publisher.setStyleSheet(self.label_default_style)
        self.book_description.setText(book_info["description"])
        self.book_description.setStyleSheet(self.label_default_style)

    def show_message(self, message, title):
        choice = QMessageBox.question(self, title, message, QMessageBox.Ok)
        if choice == QMessageBox.Ok:
            print("OK")
        else:
            pass

    def clean_text(self, review):
        review = review.replace("\n", "")
        review = review.replace("...", " ")
        review = review.replace("more", " ")
        review = re.sub('\s+', ' ', review).strip()
        return review

    def get_rating(self, stars):
        rating_scale = {"★★★★★": 5, "★★★★☆": 4, "★★★☆☆": 3, "★★☆☆☆": 2, "★☆☆☆☆": 1}
        return rating_scale[stars]

    @pyqtSlot()
    def export(self):
        self.export_as_csv()

    def export_as_csv(self):
        book_df = pd.DataFrame(self.book_data, index=[0])
        book_df.to_csv("Books/"+self.book_data["isbn"]+"_details.csv")
        review_df = pd.DataFrame(self.book_review_data)
        review_df.to_csv("Reviews/"+self.book_data["isbn"]+"_reviews.csv")
        self.show_message("Exported Book And Review Details To CSV", "Data Exported!!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookProfiler()
    window.show()
    sys.exit(app.exec_())
