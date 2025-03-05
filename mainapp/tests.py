from django.urls import reverse, resolve
from django.test import TestCase, Client 
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from mainapp import views
from django.contrib.auth.models import User
from mainapp.models import UserRating, SaveForLater
from mainapp.helpers import most_common_genre_recommendations
import pandas as pd
import os
import random
import math
import BookRecSystem.settings as settings


class HomeTests(TestCase):
    """
    Index View Test Case
    """

    def setUp(self):
        self.client = Client()  # Add explicit client initialization
        self.url = reverse("index")

    def test_home_view_status_code(self):
        """
        Index View Status Code
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_url_resolves_home_view(self):
        """
        Root URL Status Code
        """
        view = resolve("/")
        self.assertEqual(view.func, views.index)


class GenreTestCase(TestCase):
    """
    Genre View Test Case
    """

    def setUp(self):
        self.genres = [
            "art",
            "biography",
            "business",
            "Christian",
            "Comics",
            "Contemporary",
            "Cookbooks",
            "Crime",
            "Fantasy",
            "Fiction",
            "History",
            "Horror",
            "Manga",
            "Memoir",
            "Mystery",
            "Nonfiction",
            "Paranormal",
            "Philosophy",
            "Poetry",
            "Psychology",
            "Religion",
            "Science",
            "Suspense",
            "Spirituality",
            "Sports",
            "Thriller",
            "Travel",
            "Classics",
        ]

    def test_genre_status_code(self):
        """
        All Genre Tests
        """
        for genre in self.genres:
            url = reverse("genre_books", kwargs={"genre": genre})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)


class ExploreTestCase(TestCase):
    """
    Explore View Test Case
    """

    def setUp(self):
        self.url = reverse("explore_books")

    def test_explore_status_code(self):
        """
        Explore View Status Code
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class BaseTest(TestCase):
    """Base Test Class with common setup"""
    def setUp(self):
        self.client = Client(HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

class AjaxBaseTest(TestCase):
    """Base class for AJAX tests"""
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123'
        )
        # Set AJAX headers
        self.ajax_headers = {
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
            'content_type': 'application/json'
        }

class SearchAjaxTest(AjaxBaseTest):
    def setUp(self):
        super().setUp()
        self.url = reverse('search_ajax')

    @patch('mainapp.views_ajax.pd.read_csv')
    def test_search(self, mock_read_csv):
        # Mock DataFrame
        mock_df = MagicMock()
        mock_df.__getitem__.return_value.str.contains.return_value = True
        mock_df.iloc.__getitem__.return_value = {'book_id': 1}
        mock_read_csv.return_value = mock_df

        response = self.client.post(
            self.url, 
            {'bookName': 'test book'},
            **self.ajax_headers
        )
        self.assertEqual(response.status_code, 200)

class BookDetailsTest(AjaxBaseTest):
    def setUp(self):
        super().setUp()
        self.url = reverse('book_details')

    def test_book_details(self):
        response = self.client.post(
            self.url,
            {'bookid': '1'},
            **self.ajax_headers
        )
        self.assertEqual(response.status_code, 200)

class BookSummaryTestCase(TestCase):
    """
    Book Summary View Test Case
    """

    def setUp(self):
        self.url = reverse("summary_ajax")
        self.inputs = ["random_text", 1e10, ""]

    def test_book_summary_view_status_code(self):
        """
        AJAX Test request with valid and invalid Book Id
        """
        for ele in self.inputs:
            response = self.client.post(
                self.url, data={"bookid": ele}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("false", response.content.decode("utf-8"))


class BookDetailsTestCase(BaseTest):
    """AJAX Book Details Test Case"""
    def setUp(self):
        super().setUp()
        self.url = reverse('book_details')
        
    def test_book_details(self):
        """Test book details retrieval"""
        response = self.client.post(
            self.url,
            data={'bookid': '1'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)


class UserRateBookTest(AjaxBaseTest):
    def setUp(self):
        super().setUp()
        self.url = reverse('user_rate_book')
        self.client.login(username='testuser', password='test123')

    def test_rate_book(self):
        response = self.client.post(
            self.url,
            {
                'bookid': '1',
                'bookrating': '4'
            },
            **self.ajax_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            UserRating.objects.filter(
                user=self.user,
                bookid='1',
                bookrating='4'
            ).exists()
        )


class MostCommonGenreTestCase(TestCase):
    """
    Test most common genre books when recommendations are short
    """

    def setUp(self):
        self.SEED = 42
        self.df_book = pd.read_csv(
            os.path.join(settings.STATICFILES_DIRS[0] + "/mainapp/dataset/books.csv")
        )

    def test_genre_driver(self):
        test_cases = [
            (10, 5, 1),
            (10, 5, 2),
            (10, 5, 3),
            (10, 5, 4),
            (10, 5, 5),
            (10, 6, 1),
            (10, 6, 1),
            (10, 6, 2),
            (10, 6, 3),
            (10, 6, 4),
            (10, 7, 1),
            (10, 7, 2),
            (10, 7, 3),
            (10, 8, 1),
            (10, 8, 2),
            (10, 9, 1),
            (10, 10, 0),
        ]
        for tnum, already_slice, bestbookids_slice in test_cases:
            all_books, n2 = self.template(tnum, already_slice, bestbookids_slice)
            genre_recomm_bookids = most_common_genre_recommendations(all_books, n2)
            if n2:
                genre_recomm_bookids = most_common_genre_recommendations(all_books, n2)
                self.assertEqual(len(genre_recomm_bookids), n2)

    def template(self, tnum, already_slice, bestbookids_slice):
        """
        Generates `tnum` random bookids, divides the bookids into 3 input variables of the function `most_common_genre_recommendations`
        The variables store,
        already_rated - books rated by user
        best_bookids - books recommended consisting of top 6 bookids from embedding_bookids and top 3 from tfidf recommendations
        best_bookids_tfidf - `n1` books taken from remaining tfidf recommendations
        """
        random.seed(self.SEED)
        books = random.sample(self.df_book.book_id.to_list(), tnum)
        already_rated = books[:already_slice]
        best_bookids = books[already_slice : already_slice + bestbookids_slice]
        n1 = math.ceil((9 - len(best_bookids)) / 2)
        n2 = math.floor((9 - len(best_bookids)) / 2)
        best_bookids_tfidf = books[tnum - n1 + 1 :]
        all_books = best_bookids + already_rated + best_bookids_tfidf
        return all_books, n2


class RatedBooksTestCase(TestCase):
    """Already Read Books View Test Case"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="test_user", email="qwe@gmail.com"
        )
        self.user.set_password("foopassword")
        self.user.save()
        self.url = reverse("read_books")

    def test_redirect_if_not_rated(self):
        """Test If The read_books Redirects
        Accordingly When No Book Is Rated
        """
        self.client.login(username="test_user", password="foopassword")
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("index"))
        self.client.logout()

    def test_read_book_status_code(self):
        """Test The Status Code Of read_books
        When Book Has Been Rated
        """
        self.userRating = UserRating.objects.create(
            user=self.user, bookid="2", bookrating="4"
        )
        self.userRating.save()
        self.client.login(username="test_user", password="foopassword")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()


class AddBooksTestCase(TestCase):
    """Saved For Later Books View Test Case"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="test_user", email="qwe@gmail.com"
        )
        self.user.set_password("foopassword")
        self.user.save()
        self.book = pd.read_csv(
            os.path.join(settings.STATICFILES_DIRS[0] + "/mainapp/dataset/books.csv")
        )
        self.bookid = self.book.iloc[0]["book_id"]

    def test_save_book_status(self):
        """Test the status code of save_book
        When a book is Saved
        """
        book_id = self.bookid
        self.client.login(username="test_user", password="foopassword")

        response = self.client.post(
            reverse("save_book"),
            data={"bookid": book_id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("true", response.content.decode("utf-8"))
        self.client.logout()

    def test_after_remove(self):
        """Test the status code of
        remove_saved_book When a book is removed
        """
        book_id = self.bookid
        self.client.login(username="test_user", password="foopassword")

        response = self.client.post(
            reverse("remove_saved_book"),
            data={"bookid": book_id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("true", response.content.decode("utf-8"))
        self.client.logout()

    def test_redirect_if_not_saved(self):
        """Test If The to_read Redirects
        Accordingly When No Book Is Saved
        """
        self.client.login(username="test_user", password="foopassword")
        response = self.client.get(reverse("to_read"))
        self.assertRedirects(response, reverse("index"))
        self.client.logout()

    def test_to_read_status_if_saved(self):
        """Test the status code of to_read
        When a book is Saved
        """
        self.client.login(username="test_user", password="foopassword")
        self.saveLater = SaveForLater.objects.create(user=self.user, bookid="2")
        self.saveLater.save()
        response = self.client.get(reverse("to_read"))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
