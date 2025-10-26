import os, random, shutil, requests, sys, time
import PIL.Image, PIL.ImageOps
from PIL.ExifTags import TAGS
from datetime import datetime
from urllib.parse import quote

ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_BUSINESS_ID")
PUBLIC_BASE_URL = os.getenv("PUBLIC_IMAGE_BASE_URL")

root_folder = "./images_to_upload"
dest_folder = "./uploaded_images"


def get_file_creation_time(path):
    stat_info = os.stat(path)
    if hasattr(stat_info, "st_birthtime"):
        return datetime.fromtimestamp(stat_info.st_birthtime)
    return datetime.fromtimestamp(stat_info.st_mtime)


def get_image_taken_time(path):
    img = PIL.Image.open(path)
    exif_data = img._getexif()

    if not exif_data:
        print("NO EXIF DATA")
        return get_file_creation_time(path)

    for tag_id, value in exif_data.items():
        tag = TAGS.get(tag_id, tag_id)
        if tag in ("DateTimeOriginal", "DateTime"):
            return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")

    print("NO EXIF DATE FIELD")
    return get_file_creation_time(path)


def prepare_image():
    """Select a random image, fix orientation, and record metadata for publishing."""
    images = []
    for subdir, _, files in os.walk(root_folder):
        images += [
            os.path.join(subdir, f)
            for f in files
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

    if not images:
        raise Exception("No images found to upload.")

    random_image = random.choice(images)
    chosen_subdir, file_name = random_image.split("/")[2:]

    # build caption
    time_taken = get_image_taken_time(random_image)
    formatted_date = time_taken.strftime("%A, %B %d, %Y")
    caption = f"{chosen_subdir} // {formatted_date}"

    # fix EXIF orientation
    img = PIL.Image.open(random_image)
    img = PIL.ImageOps.exif_transpose(img)
    img.save(random_image)

    # clean up file name
    safe_subdir = chosen_subdir.replace(" ", "_")
    filename, ext = os.path.splitext(file_name)
    now = datetime.now().strftime("%d-%m-%Y_%H-%M")
    safe_filename = f"{filename}_UPLOADED_AT_{now}{ext}".replace(" ", "_")

    rel_path = f"{safe_subdir}/{safe_filename}"

    # save metadata for publish step
    with open("upload_meta.txt", "w") as f:
        f.write(f"{random_image}|{rel_path}|{caption}")

    print("Prepared for upload:", random_image)
    return random_image


def publish_image():
    """Upload image to Instagram and archive it only after successful publish."""
    with open("upload_meta.txt") as f:
        original_path, rel_path, caption = f.read().strip().split("|", 2)

    public_url = f"{PUBLIC_BASE_URL}/{quote(rel_path)}"

    # wait for github pages to be live
    for i in range(6):
        r = requests.head(public_url)
        if r.status_code == 200:
            break
        print("Waiting for GitHub Pages URL to be live...")
        time.sleep(5)
    else:
        raise Exception(f"File not live on GitHub Pages: {public_url}")

    # instagram media api
    # create media container
    media_endpoint = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    params = {"image_url": public_url, "caption": caption, "access_token": ACCESS_TOKEN}
    res = requests.post(media_endpoint, params=params).json()
    container_id = res.get("id")
    if not container_id:
        raise Exception("Failed to create media container: " + str(res))

    print(f"Media container created: {container_id}")
    time.sleep(3)

    # wait for media container
    status_endpoint = f"https://graph.facebook.com/v21.0/{container_id}"
    for i in range(10):
        status_res = requests.get(
            status_endpoint,
            params={"fields": "status_code", "access_token": ACCESS_TOKEN},
        ).json()
        status = status_res.get("status_code")
        print(f"[Check {i+1}] Media status: {status}")
        if status == "FINISHED":
            print("Media processing finished, ready to publish.")
            break
        elif status == "ERROR":
            raise Exception("Media processing failed: " + str(status_res))
        time.sleep(5)
    else:
        raise Exception("Media not ready after waiting: " + str(status_res))

    # publish
    publish_endpoint = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    params = {"creation_id": container_id, "access_token": ACCESS_TOKEN}
    res = requests.post(publish_endpoint, params=params).json()

    if "id" in res:
        print("✅ Publish successful:", res)

        # move file to archive
        safe_subdir, safe_filename = rel_path.split("/", 1)
        final_dest = os.path.join(dest_folder, safe_subdir)
        os.makedirs(final_dest, exist_ok=True)
        final_path = os.path.join(final_dest, safe_filename)
        shutil.move(original_path, final_path)
        print(f"Moved to archive: {final_path}")

    else:
        raise Exception("❌ Failed to publish: " + str(res))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    if mode == "prepare":
        prepare_image()
    elif mode == "publish":
        publish_image()
