from django.shortcuts import redirect, render
import os, shutil
import threading
import requests
import time
from instagrapi import Client

cl = Client()

save_location="downloads"
SESSION_FILE="session.json"

def download_file(url, filename, taken_at):
    if not url:
        print(f"⚠️ Skipping missing URL: {filename}")
        return
    if os.path.exists(filename):
        print(f"⏩ File already exists, skipping: {filename}")
        return
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in response.iter_content(16384):
                f.write(chunk)
        timestamp = time.mktime(taken_at.timetuple())
        os.utime(filename, (timestamp, timestamp))
        print(f"✅ File downloaded: {filename}")
    except Exception as e:
        print(f"❌ Error: {filename}: {e}")
        
def index(request):
    try:
        if os.path.exists(SESSION_FILE):
            cl = Client(SESSION_FILE)
            cl.get_timeline_feed()
    except Exception as e:
        error_message = str(e)
        
    return render(request, "downloader/index.html")


def posts(request):
    if request.method == "POST":
        url = str(request.POST["postURL"])
        try:
            if os.path.exists(SESSION_FILE):
                cl = Client()
                cl.load_settings(SESSION_FILE)
                cl.get_timeline_feed()
            else:
                return render(request, "downloader/index.html")
        except Exception as e:
            error_message = str(e)
            print(error_message)
            return render(request, "downloader/posts.html", {"error": "Invalid Login."})
        
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
                media_pk = cl.media_pk_from_url(url)
                post = cl.media_info(media_pk)
                folder = os.path.join(save_location, post.user.username, "posts")
                os.makedirs(folder, exist_ok=True)
                if post.media_type == 1:
                    filename = os.path.join(folder, f"{post.pk}_{post.taken_at.strftime('%Y%m%d')}.jpg")
                    download_file(post.thumbnail_url, filename, post.taken_at)
                elif post.media_type == 8 and hasattr(post, 'resources'):
                    for i, resource in enumerate(post.resources):
                        ext = "mp4" if resource.video_url else "jpg"
                        url = resource.video_url if ext == "mp4" else resource.thumbnail_url
                        filename = os.path.join(folder, f"{post.pk}_{i+1}_{post.taken_at.strftime('%Y%m%d')}.{ext}")
                        download_file(url, filename, post.taken_at)
                        
            except Exception as e:
                error_message = str(e)
                return render(
                    request,
                    "downloader/posts.html",
                    {"error": f"An error occurred: {error_message}"},
                )

    if os.path.exists(save_location):
        media_files = os.listdir(save_location)
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
        try:
            if os.path.exists(SESSION_FILE):
                cl = Client()
                cl.load_settings(SESSION_FILE)
                cl.get_timeline_feed()
            else:
                return render(request, "downloader/index.html")
        except Exception as e:
            error_message = str(e)
            print(error_message)
            return render(request, "downloader/reels.html", {"error": "Invalid Login."})
        
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
                media_pk = cl.media_pk_from_url(url)
                reel = cl.media_info(media_pk)
                folder = os.path.join(save_location, post.user.username, "reels")
                os.makedirs(folder, exist_ok=True)
                if reel.media_type == 2 and reel.product_type == "clips":
                    filename = os.path.join(folder, f"{reel.pk}_{reel.taken_at.strftime('%Y%m%d')}.mp4")
                    thumb_filename = os.path.join(folder, f"{reel.pk}_{reel.taken_at.strftime('%Y%m%d')}_thumb.jpg")
                    download_file(reel.video_url, filename, reel.taken_at)
                    if reel.thumbnail_url:
                        download_file(reel.thumbnail_url, thumb_filename, reel.taken_at)
                
            except Exception as e:
                error_message = str(e)
                return render(
                    request,
                    "downloader/reels.html",
                    {"error": f"An error occurred: {error_message}"},
                )

    if os.path.exists(save_location):
        media_files = os.listdir(save_location)
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

def download_posts_in_background(cl, username, save_location):
    try:
        user_id = cl.user_info_by_username_v1(username).pk
        posts = cl.user_medias(user_id, amount=0)
        posts = [p for p in posts if p.media_type == 1 or (p.media_type == 8 and hasattr(p, 'resources'))]
        folder = os.path.join(save_location, username, "posts")
        os.makedirs(folder, exist_ok=True)
        
        for post in posts:
            try:
                if post.media_type == 1:
                    filename = os.path.join(folder, f"{post.pk}_{post.taken_at.strftime('%Y%m%d')}.jpg")
                    download_file(post.thumbnail_url, filename, post.taken_at)
                elif post.media_type == 8 and hasattr(post, 'resources'):
                    for i, resource in enumerate(post.resources):
                        ext = "mp4" if resource.video_url else "jpg"
                        url = resource.video_url if ext == "mp4" else resource.thumbnail_url
                        filename = os.path.join(folder, f"{post.pk}_{i+1}_{post.taken_at.strftime('%Y%m%d')}.{ext}")
                        download_file(url, filename, post.taken_at)
                        
            except Exception as e:
                print(f"Error processing post {post.pk}: {e}")
        
        stories = cl.user_stories(user_id)
        folder = os.path.join(save_location, username, "stories")
        os.makedirs(folder, exist_ok=True)
        for index, story in enumerate(stories, 1):
            ext = "mp4" if story.video_url else "jpg"
            filename = os.path.join(folder, f"{story.pk}.{ext}")
            cl.story_download(story.pk, filename, folder)
            
        
        highlights = cl.user_highlights(user_id)
        folder = os.path.join(save_location, username, "highlights")
        os.makedirs(folder, exist_ok=True)
        
        for index, highlight in enumerate(highlights, 1):
            highlight_info = cl.highlight_info(highlight.pk)
            for i, item in enumerate(highlight_info.items, 1):
                url = str(item.thumbnail_url if item.media_type == 1 else item.video_url)
                ext = "jpg" if item.media_type == 1 else "mp4"
                filename = os.path.join(folder, f"{item.pk}_{item.taken_at.strftime('%Y%m%d')}.{ext}")
                download_file(url, filename, item.taken_at)
                
                thumb_filename = os.path.join(folder, f"{item.pk}_{item.taken_at.strftime('%Y%m%d')}_thumb.jpg")
                if item.thumbnail_url and item.media_type != 1:
                    download_file(item.thumbnail_url, thumb_filename, item.taken_at)

    except Exception as e:
        print(f"Background download failed: {e}")

def allposts(request):
    if request.method == "POST":
        username = str(request.POST["postURL"])
        try:
            if os.path.exists(SESSION_FILE):
                cl = Client()
                cl.load_settings(SESSION_FILE)
                cl.get_timeline_feed()
            else:
                return render(request, "downloader/index.html")
        except Exception as e:
            error_message = str(e)
            print(error_message)
            return render(request, "downloader/allposts.html", {"error": "Invalid Login."})

        if username != "":
            try:
                
                thread = threading.Thread(
                            target=download_posts_in_background,
                            args=(cl, username, save_location),
                            daemon=True  # Optional: make it a daemon thread
                        )
                thread.start()

                # Return a response immediately to the user
                return render(
                    request,
                    "downloader/allposts.html",
                    {
                        "message": "Download started in background."
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

def download_reels_in_background(cl, username, save_location):
    try:
        user_id = cl.user_info_by_username_v1(username).pk
        reels = cl.user_clips(user_id, amount=0)
        folder = os.path.join(save_location, username, "reels")
        os.makedirs(folder, exist_ok=True)
        
        for reel in reels:
            try:
                filename = os.path.join(folder, f"{reel.pk}_{reel.taken_at.strftime('%Y%m%d')}.mp4")
                thumb_filename = os.path.join(folder, f"{reel.pk}_{reel.taken_at.strftime('%Y%m%d')}_thumb.jpg")
                download_file(reel.video_url, filename, reel.taken_at)
                if reel.thumbnail_url:
                    download_file(reel.thumbnail_url, thumb_filename, reel.taken_at)
            except Exception as e:
                print(f"Error processing reel {reel.pk}: {e}")
    except Exception as e:
        print(f"Background download failed: {e}")

def allreels(request):
    if request.method == "POST":
        username = str(request.POST["postURL"])
        try:
            if os.path.exists(SESSION_FILE):
                cl = Client()
                cl.load_settings(SESSION_FILE)
                cl.get_timeline_feed()
            else:
                return render(request, "downloader/index.html")
        except Exception as e:
            error_message = str(e)
            print(error_message)
            return render(request, "downloader/allreels.html", {"error": "Invalid Login."})
        
        if username != "":
            try:
                
                thread = threading.Thread(
                            target=download_reels_in_background,
                            args=(cl, username, save_location),
                            daemon=True  # Optional: make it a daemon thread
                        )
                thread.start()
                
                # Return a response immediately to the user
                return render(
                    request,
                    "downloader/allreels.html",
                    {
                        "message": "Download started in background."
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
        
        try:
            if os.path.exists(SESSION_FILE):
                cl.load_settings(SESSION_FILE)
                cl.get_timeline_feed()
                print("Logged In with Session")
            
            else:
                if username != "" and password != "":
                    logged_in = cl.login(username, password)
                    cl.dump_settings(SESSION_FILE)
                    cl.get_timeline_feed()
                    if logged_in == True:
                        print(username + " Logged In")
                    else:
                        return render(
                            request,
                            "downloader/index.html",
                            {"error": "Login Failed."},
                        )
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