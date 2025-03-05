from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from mainapp.helpers import is_bookid_invalid, is_rating_invalid, get_rated_bookids
import BookRecSystem.settings as settings
from mainapp.models import UserRating, SaveForLater
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import requests

"""
    Production File Path :  staticfiles_storage.url(file)
    Developement File Path : settings.STATICFILES_DIRS[0] + 'app/.../file'
"""
book_path = os.path.join(settings.STATICFILES_DIRS[0] + "/mainapp/dataset/books.csv")
user_ratings_path = os.path.join(
    settings.STATICFILES_DIRS[0] + "/mainapp/csv/userratings.csv"
)


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


def search(request):
    """
    AJAX request for search bar functionality
    """
    if request.method == "POST" and is_ajax(request=request):
        query = request.POST.get("bookName", None)
        if not query:
            return JsonResponse({"success": False}, status=200)
        df_book = pd.read_csv(book_path)
        top5_result = df_book[
            df_book["original_title"].str.contains(query, regex=False, case=False)
        ][:5]
        top5_result = json.dumps(top5_result.to_dict("records"))
        print(top5_result)

        return JsonResponse({"success": True, "top5_result": top5_result}, status=200)


def book_summary(request):
    """
    AJAX request for book summary
    """
    if request.method == "POST" and is_ajax(request=request):
        bookid = request.POST.get("bookid", None)
        if is_bookid_invalid(bookid):
            return JsonResponse({"success": False}, status=200)
        
        try:
            URL = "https://www.goodreads.com/book/show/" + bookid
            page = requests.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")
            
            # Look for description in different possible elements
            description = soup.find(class_="TruncatedContent__text")
            if not description:
                description = soup.find(class_="DetailsLayoutRightParagraph__widthConstrained")
            if not description:
                description = soup.find(id="description")
                
            if not description:
                return JsonResponse({"success": False}, status=200)
                
            summary = description.get_text().strip()
            # Limit to reasonable length while keeping complete sentences
            if len(summary) > 500:
                summary = ". ".join(summary.split(". ")[:3]) + "..."
                
            return JsonResponse({"success": True, "booksummary": summary}, status=200)
            
        except Exception as e:
            print(f"Error fetching summary: {str(e)}")
            return JsonResponse({"success": False}, status=200)


def get_book_details(request):
    """
    AJAX request for book details
    """
    if request.method == "POST" and is_ajax(request=request):
        bookid = request.POST.get("bookid", None)
        if is_bookid_invalid(bookid):
            return JsonResponse({"success": False}, status=200)

        df_book = pd.read_csv(book_path)
        book_details = df_book[df_book["book_id"] == int(bookid)]
        if not len(book_details):
            return JsonResponse({"success": False}, status=200)

        book_details = json.dumps(book_details.to_dict("records"))
        return JsonResponse({"success": True, "book_details": book_details}, status=200)


@login_required
def user_rate_book(request):
    """
    AJAX request when user rates book
    """
    if request.method == "POST" and is_ajax(request=request):
        bookid = request.POST.get("bookid", None)
        bookrating = request.POST.get("bookrating", None)
        if is_bookid_invalid(bookid) or is_rating_invalid(bookrating):
            return JsonResponse({"success": False}, status=200)

        # Using Inbuilt Model
        query = UserRating.objects.filter(user=request.user).filter(bookid=bookid)
        if not query:
            # Create Rating
            UserRating.objects.create(
                user=request.user, bookid=bookid, bookrating=bookrating
            )
        else:
            # Update Rating
            rating_object = query[0]
            rating_object.bookrating = bookrating
            rating_object.save()
        return JsonResponse({"success": True}, status=200)


def save_book(request):
    """AJAX request when user saves book"""
    if request.method == "POST" and is_ajax(request=request):
        bookid = request.POST.get("bookid", None)
        user_ratings = list(UserRating.objects.filter(user=request.user))
        rated_books = set(get_rated_bookids(user_ratings))
        if is_bookid_invalid(bookid) or bookid in rated_books:
            return JsonResponse({"success": False}, status=200)

        SaveForLater.objects.create(user=request.user, bookid=bookid)
        return JsonResponse({"success": True}, status=200)


def remove_saved_book(request):
    """AJAX request when user removes book"""
    if request.method == "POST" and is_ajax(request=request):
        bookid = request.POST.get("bookid", None)
        if is_bookid_invalid(bookid):
            return JsonResponse({"success": False}, status=200)

        saved_book = SaveForLater.objects.filter(user=request.user, bookid=bookid)
        saved_book.delete()
        return JsonResponse({"success": True}, status=200)
