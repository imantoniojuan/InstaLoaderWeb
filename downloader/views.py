from django.shortcuts import redirect, render
import instaloader, os, shutil
import threading
from instaloader import Instaloader, Profile

# os.path.exists("temp")


# Create your views here.


def index(request):
    try:
        L = instaloader.Instaloader()
        username = L.test_login()
        request.session['username'] = username
    except Exception as e:
        error_message = str(e)
        
    return render(request, "downloader/index.html")


def posts(request):
    if request.method == "POST":
        url = str(request.POST["postURL"])
        if url != "":
            if url.startswith("https://www.instagram.com/") and url.endswith("/"):
                shortcode = url.split("/")[-2]
                print(f"{shortcode=}")
            elif url.startswith("https://www.instagram.com/"):
                shortcode = url.split("/")[-1]
                print(f"{shortcode=}")
            else:
                return render(
                    request, "downloader/posts.html", {"error": "Invalid URL."}
                )
        if shortcode != "":
            try:
                L = instaloader.Instaloader()
                loginUsername = request.session.get('username')
                if loginUsername:
                    L.load_session_from_file(loginUsername)
                L.save_metadata = False
                L.download_video_thumbnails = False
                L.post_metadata_txt_pattern = ""

                print("FINDING POST")
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                print("FOUND")

                # Clearing temp folder before downloading
                if os.path.exists("temp"):
                    shutil.rmtree("temp")
                    print("DELETED OLD TEMP FILES")
                print("CLEANED")

                L.download_post(post, target="temp")
            except Exception as e:
                error_message = str(e)
                return render(
                    request,
                    "downloader/posts.html",
                    {"error": f"An error occurred: {error_message}"},
                )

    if os.path.exists("temp"):
        media_files = os.listdir("temp")
        images = [
            f
            for f in media_files
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]
        videos = [
            f
            for f in media_files
            if f.lower().endswith((".mp4", ".avi", ".mov", ".wmv"))
        ]
        return render(
            request,
            "downloader/posts.html",
            {"data": True, "images": images, "videos": videos},
        )

    return render(request, "downloader/posts.html")


def reels(request):
    if request.method == "POST":
        url = str(request.POST["postURL"])
        if url != "":
            if url.startswith("https://www.instagram.com/") and url.endswith("/"):
                shortcode = url.split("/")[-2]
                print(f"{shortcode=}")
            elif url.startswith("https://www.instagram.com/"):
                shortcode = url.split("/")[-1]
                print(f"{shortcode=}")
            else:
                return render(
                    request, "downloader/posts.html", {"error": "Invalid URL."}
                )
        if shortcode != "":
            try:
                L = instaloader.Instaloader()
                loginUsername = request.session.get('username')
                if loginUsername:
                    L.load_session_from_file(loginUsername)
                L.save_metadata = False
                L.download_video_thumbnails = False
                L.post_metadata_txt_pattern = ""

                print("FINDING POST")
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                print("FOUND")

                # Clearing temp folder before downloading
                if os.path.exists("temp"):
                    shutil.rmtree("temp")
                    print("DELETED OLD TEMP FILES")
                print("CLEANED")

                L.download_post(post, target="temp")
            except Exception as e:
                error_message = str(e)
                return render(
                    request,
                    "downloader/reels.html",
                    {"error": f"An error occurred: {error_message}"},
                )

    if os.path.exists("temp"):
        media_files = os.listdir("temp")
        images = [
            f
            for f in media_files
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]
        videos = [
            f
            for f in media_files
            if f.lower().endswith((".mp4", ".avi", ".mov", ".wmv"))
        ]
        return render(
            request,
            "downloader/reels.html",
            {"data": True, "images": images, "videos": videos},
        )

    return render(request, "downloader/reels.html")

def download_posts_in_background(username, loginUsername):
    try:

        L = instaloader.Instaloader()
        if loginUsername:
            L.load_session_from_file(loginUsername)
        L.save_metadata = False
        L.download_video_thumbnails = False
        L.post_metadata_txt_pattern = ""

        L.dirname_pattern = f"/download/{username}"
        L.download_profile(username)
        print("Download Completed.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def download_reels_in_background(username, loginUsername):
    try:
        print("Download Starting.")
        if not username:
            raise ValueError("Username is required.")
        
        L = instaloader.Instaloader()
        if loginUsername:
            L.load_session_from_file(loginUsername)
        L.save_metadata = False
        L.download_video_thumbnails = False
        L.post_metadata_txt_pattern = ""
        
        L.dirname_pattern = f"/download/{username}"
        profile = Profile.from_username(L.context, username)
        L.download_reels(profile)
        print("Download Completed.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def allposts(request):
    if request.method == "POST":
        username = str(request.POST["postURL"])
        loginUsername = request.session.get('username')

        if username != "":
            try:
                # Start the download in a new thread
                download_thread = threading.Thread(
                    target=download_posts_in_background, args=(username,loginUsername,)
                )
                download_thread.start()

                # Return a response immediately to the user
                return render(
                    request,
                    "downloader/allposts.html",
                    {
                        "message": "Download started! This may take a while, Please do not close this window."
                    },
                )
            except Exception as e:
                error_message = str(e)
                return render(
                    request,
                    "downloader/allposts.html",
                    {"error": f"An error occurred: {error_message}"},
                )
    
    return render(request, "downloader/allposts.html")

def allreels(request):
    if request.method == "POST":
        username = str(request.POST["postURL"])
        loginUsername = request.session.get('username')
        
        if username != "":
            try:
                # Start the download in a new thread
                download_thread = threading.Thread(
                    target=download_reels_in_background, args=(username,loginUsername,)
                )
                download_thread.start()
                
                # Return a response immediately to the user
                return render(
                    request,
                    "downloader/allreels.html",
                    {
                        "message": "Download started! This may take a while, Please do not close this window."
                    },
                )
            except Exception as e:
                error_message = str(e)
                return render(
                    request,
                    "downloader/allreels.html",
                    {"error": f"An error occurred: {error_message}"},
                )
    
    return render(request, "downloader/allreels.html")

def login(request):
    if request.method == "POST":
        username = str(request.POST["username"])
        password = str(request.POST["password"])
        
        if username != "":
            try:
                L = instaloader.Instaloader()
                L.close()
                L.login(username, password)
                L.save_session_to_file()
                request.session['username'] = username
                
                # Return a response immediately to the user
                return render(
                    request,
                    "downloader/index.html",
                    {
                        "message": "Logged in."
                    },
                )
            except Exception as e:
                error_message = str(e)
                return render(
                    request,
                    "downloader/index.html",
                    {"error": f"An error occurred: {error_message}"},
                )
    
    return render(request, "downloader/index.html")