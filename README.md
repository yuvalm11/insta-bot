# Insta-bot

Check out my photos on Instagram before you start reading!

![medium-filled-instagram](medium/filled/instagram.svg) [@everyday__ppl](https://www.instagram.com/everyday__ppl/)

As a hobbyist photographer, I enjoy taking pictures in my free time and I wanted to start sharing them on Instagram. The process of selecting photos, editing posts, and uploading them to Instagram is a bit tedious, so I decided to automate it.

I used the [Instagram Graph API](https://developers.facebook.com/docs/instagram-api), some Python libraries, and a GitHub Actions workflow to automate the process.

I now can simply dump all my photos in a folder and let the workflow take care of the rest.

## Workflow

The workflow is triggered daily, selects a random image from the `images_to_upload` folder, fixes the EXIF orientation, creates a caption, and uploads it to Instagram. The image is then moved to the `uploaded_images` folder with a timestamp of the upload in the filename.

## Setup

1. Create a new Instagram Business account and connect it to your Facebook page -- this is necessary to use the Instagram Graph API and might feel a little tedious, but it's a one-time thing.

2. create a new repository for the public repo and set it up as a GitHub Pages site. This will be used to temporarily host the images that are uploaded to Instagram.

4. Create a private repo for the bot and add the following files:

- `main.py` - the main script that selects a random image, fixes the EXIF orientation, creates a caption, and uploads it to Instagram.
- `images_to_upload` - a folder that contains the images to upload.
- `uploaded_images` - a folder that contains the images that have been uploaded to Instagram.
- `.github/workflows/graph_api_daily.yml` - the GitHub Actions workflow.

5. Store the access token and business ID as github secrets.

6. Edit the workflow file to point to your own repos and secrets.