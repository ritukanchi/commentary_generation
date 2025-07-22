import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

load_dotenv("../../.env")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

result = cloudinary.uploader.upload("../dataset/frames/frametest/frame_0.jpg")
print("Uploaded URL:", result["secure_url"])

# testing of API 