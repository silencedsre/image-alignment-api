import base64
from io import BytesIO
import cv2
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify
from scipy.ndimage import interpolation as inter

app = Flask(__name__)

# function to align image horizontally or vertically
def correct_skew(image, delta=1, limit=5):
    def determine_score(arr, angle):
        data = inter.rotate(arr, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2)
        return histogram, score

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    scores = []
    angles = np.arange(-limit, limit + delta, delta)
    for angle in angles:
        histogram, score = determine_score(thresh, angle)
        scores.append(score)

    best_angle = angles[scores.index(max(scores))]

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    aligned_image = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    return aligned_image


# function to save base64 encoded image to a given location (output folder)
def save_image(base64_image_string, filename):
    filename = filename.split(".")[0]
    file_content = base64.b64decode(base64_image_string)

    with open(f"output/aligned_{filename}.jpeg", "wb") as fh:
        fh.write(file_content)


# function to load the file as an image array
def file_to_img_array(file):
    # Read the image via file.stream
    img = Image.open(file.stream)
    img = np.asarray(img)
    r, g, b = cv2.split(img)
    img = cv2.merge([b, g, r])
    return img


# function to convert image array to a base64 encoded image string
def img_array_to_base64_img(img):
    pil_img = Image.fromarray(img)
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")
    base64_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
    return base64_image_string


@app.route("/", methods=["GET"])
def welcome():
    return {
        "welcome": "Welcome to Image Alignment API, Send a Post Request to /align Endpoint"
    }


@app.route("/align", methods=["POST"])
def align_image():
    file = request.files["image"]
    if file.mimetype in ["image/png", "image/jpeg"]:
        img = file_to_img_array(file)
        aligned_image = correct_skew(img)
        base64_image_string = img_array_to_base64_img(aligned_image)

        save_image(base64_image_string, filename=file.filename)
        return jsonify({"img": base64_image_string})
    else:
        return {"error": "Not an image"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
