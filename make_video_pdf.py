import asyncio
import os
import subprocess
import sys
from contextlib import closing

import boto3
import edge_tts
import fitz  # PyMuPDF
from botocore.exceptions import BotoCoreError, ClientError

AUX_FOLDER = './aux_files/'
VIDEOS_FOLDER = './videos/'

# Create a client using the credentials and region defined in the [adminuser]
# section of the AWS credentials file (~/.aws/credentials).


polly = boto3.client('polly', region_name='eu-west-3', aws_access_key_id='',
                     aws_secret_access_key='')


def extract_text_and_images(pdf_file):
    data = []
    doc = fitz.open(pdf_file)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Extract text
        text = page.get_text()
        # Remove leading and trailing whitespace
        text = text.strip()
        # Replace multiple consecutive line breaks with a single line break
        text = text.replace('\n', ' ')
        print(f"Text from Page {page_num + 1}:\n{text}\n")
        data.append(text)

        # Render page as an image
        pix = page.get_pixmap()

        # Save the image
        image_path = f"{AUX_FOLDER}page{page_num + 1}.png"
        pix.save(image_path)

        print(f"Page {page_num + 1} saved as {image_path}")

    doc.close()
    print_text_data(data)
    return data


# Defining main function
def print_text_data(data):
    count = 0
    for line in data:
        count += 1
        print("{} - index - Line{}: {}".format((count - 1), count, line.strip()))


from PIL import Image, ImageFilter, ImageEnhance


def scale_image(image, target_width, target_height):
    """
    Scales the image while preserving aspect ratio to fit within target dimensions.
    If the image aspect ratio is smaller than 9:16, it scales by width; otherwise, by height.
    """
    width, height = image.size
    aspect_ratio = width / height

    if aspect_ratio < 9 / 16:  # Scale by width
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:  # Scale by height
        new_height = target_height
        new_width = int(target_height * aspect_ratio)

    return image.resize((new_width, new_height), Image.LANCZOS)


def crop_image(image, target_width, target_height):
    """
    Crops the image to a target rectangle from the center.
    """
    width, height = image.size
    left = (width - target_width) / 2
    top = (height - target_height) / 2
    right = (width + target_width) / 2
    bottom = (height + target_height) / 2

    return image.crop((left, top, right, bottom))


def apply_blur_and_darken(image, blur_radius, darken_factor):
    """
    Applies blur effect and darkens the image.
    """
    # Apply blur effect
    blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Darken the image
    enhancer = ImageEnhance.Brightness(blurred_image)
    darkened_image = enhancer.enhance(darken_factor)

    return darkened_image


def overlay_images(original_image, overlay_image):
    """
    Overlays the original image over the overlay image with scaling to fit.
    """
    overlay_width, overlay_height = overlay_image.size
    overlay_ratio = min(original_image.size[0] / overlay_width, original_image.size[1] / overlay_height)
    overlay_size = (int(overlay_width * overlay_ratio), int(overlay_height * overlay_ratio))
    scaled_overlay = overlay_image.resize(overlay_size, Image.LANCZOS)

    # Create a mask based on the alpha channel of the scaled overlay image
    if scaled_overlay.mode in ('RGBA', 'LA') or (scaled_overlay.mode == 'P' and 'transparency' in scaled_overlay.info):
        mask = scaled_overlay.split()[3]
        result = original_image.copy()
        result.paste(scaled_overlay, (
            (original_image.width - scaled_overlay.width) // 2, (original_image.height - scaled_overlay.height) // 2),
                     mask)
    else:
        result = original_image.copy()
        result.paste(scaled_overlay, (
            (original_image.width - scaled_overlay.width) // 2, (original_image.height - scaled_overlay.height) // 2))

    return result


def process_image(input_image_path, output_image_path, blur_radius=8, darken_factor=0.5):
    # def process_image(input_image_path, output_image_path, blur_radius=8, darken_factor=0.0):
    """
    Processes the input image and saves the resulting image.
    """
    # Open input image
    input_image = Image.open(input_image_path)

    # Scale the image to fit 1080p by 1920p
    scaled_image = scale_image(input_image, 1080, 1920)

    # Crop the resulting image to a 1080p by 1920p rectangle from the center
    cropped_image = crop_image(scaled_image, 1080, 1920)

    # Apply blur effect and darken the image
    processed_image = apply_blur_and_darken(cropped_image, blur_radius, darken_factor)

    # Overlay the original image over the processed image
    final_image = overlay_images(processed_image, input_image)

    # Save the resulting image
    final_image.save(output_image_path)


def trim_audio(in_audio_path, out_audio_path):
    trim_audio_clip = 'ffmpeg -y -i ' + in_audio_path + ' -af silenceremove=start_periods=1:start_silence=0.2:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_silence=0.2:start_threshold=-50dB,areverse ' + out_audio_path

    subprocess.check_output(trim_audio_clip, shell=True)


async def make_audio(text: str, audio_name: str, VOICE: str, speed: str) -> None:
    communicate = edge_tts.Communicate(text, VOICE, rate=speed)
    with open(audio_name, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
    print('New audio: [' + text + ']' + ' - file: ' + audio_name)


def make_audio_polly(text, filepath):
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Engine="neural", LanguageCode='en-GB', Text=text, OutputFormat="mp3",
                                           VoiceId="Emma")
    except (BotoCoreError, ClientError) as error:
        # The service returned an error
        print(error)
        sys.exit(-1)

    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            try:
                # Write the audio stream to the output file
                with open(filepath, "wb") as file:
                    file.write(stream.read())
            except IOError as error:
                # Could not write to file
                print(error)
                sys.exit(-1)
    else:
        # The response didn't contain audio data
        print("Could not stream audio")
        sys.exit(-1)


def merge_image_audio(image_in, audio_in, video_out, fade_duration):
    audio_in_2 = audio_in + 'hax.mp3'

    trim_audio(audio_in, audio_in_2)

    duration = get_length(audio_in_2)
    # duration = get_length(audio_in)

    duration += fade_duration

    make_audio_image_clip = 'ffmpeg -y -loop 1  -i ' + image_in + ' -i ' + audio_in + ' -t ' + str(
        duration) + ' -af apad -vcodec libx264 -r 30  -c:a aac -b:a 384k ' + video_out

    subprocess.check_output(make_audio_image_clip, shell=True)


def extract_audio(video_in, audio_out):
    extract_audio = 'ffmpeg -y -i ' + video_in + '  -async 1 ' + audio_out
    extract_audio = 'ffmpeg -y -i ' + video_in + '  -async 1  -vn -acodec mp3 -ab 384k -ar 44100 -ac 2  ' + audio_out
    subprocess.check_output(extract_audio, shell=True)


def merge_all_clips(list_in, video_out):
    make_audio_image_clip = 'ffmpeg -y -f concat -i ' + list_in + ' -c copy ' + video_out
    subprocess.check_output(make_audio_image_clip, shell=True)


def get_length(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
         filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)


def add_bg_audio(input_video, background_audio, output_video):
    ffmpeg_cmd = 'ffmpeg -y -i "' + input_video + '" '
    ffmpeg_cmd += '-i "' + background_audio + '" '
    ffmpeg_cmd += '-filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.15[a1];[a0][a1]amerge=inputs=2[a]" '
    ffmpeg_cmd += '-map 0:v '
    ffmpeg_cmd += '-map "[a]" '
    ffmpeg_cmd += '-c:v copy '
    ffmpeg_cmd += '-c:a aac '
    ffmpeg_cmd += '-strict experimental "' + output_video + '"'

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:
        print(line)


def add_bg_audio_2(input_video, background_audio, output_video):
    ffmpeg_cmd = 'ffmpeg -y '
    ffmpeg_cmd += '-i ' + input_video + ' '
    ffmpeg_cmd += '-i ' + background_audio + ' '
    ffmpeg_cmd += '-filter_complex '
    ffmpeg_cmd += '[0:a]volume=1.7[a0];'
    ffmpeg_cmd += '[1:a]volume=0.04[a1];'
    ffmpeg_cmd += '"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[a]" '
    ffmpeg_cmd += '-map 0:v '
    ffmpeg_cmd += '-map "[a]" '
    ffmpeg_cmd += '-c:v copy '
    ffmpeg_cmd += '-c:a aac '
    ffmpeg_cmd += '-strict experimental "' + output_video + '"'

    subprocess.run(ffmpeg_cmd, shell=True)


def ffmpeg_fade_merge(filepaths, fade_duration, video_out):
    cmd = 'ffmpeg -y -vsync 0'
    for i, filepath in enumerate(filepaths):
        cmd += ' -i ' + filepath

    cmd += ' -filter_complex "'

    for i, filepath in enumerate(filepaths):
        cmd += f'[{i}]settb=AVTB[{i}:v];'

    for i, filepath in enumerate(filepaths):
        # cmd += f'[{i}]atrim={get_length(filepath)}[{i}:a];'
        cmd += f'[{i}]atrim=0:{get_length(filepath)}[{i}:a];'
    current_total_time = 0
    for i, filepath in enumerate(filepaths):
        print(get_length(filepath))

        if not i == (len(filepaths) - 1):  # skip last
            # current_total_time += get_length(filepath)
            current_total_time += get_length(filepath) - fade_duration
            # fade_time = current_total_time - fade_duration
            fade_time = current_total_time
            if i == 0:  # first
                cmd += f'[0:v][{i + 1}:v]xfade=transition=fade:duration={fade_duration}:offset={fade_time}[v{i + 1}];'
            elif i == (len(filepaths) - 2):  # 2nd to last
                cmd += f'[v{i}][{i + 1}:v]xfade=transition=fade:duration={fade_duration}:offset={fade_time},format=yuv420p[video];'
            else:  # others
                cmd += f'[v{i}][{i + 1}:v]xfade=transition=fade:duration={fade_duration}:offset={fade_time}[v{i + 1}];'

    # for i, filepath in enumerate(filepaths):
    #     if not i == (len(filepaths) - 1):  # skip last
    #         print((len(filepaths) - 2))
    #         if i == 0:  # first
    #             cmd += f'[0:a][{i + 1}:a]acrossfade=d={fade_duration}:c1=tri:c2=tri[a{i + 1}];'
    #         elif i == (len(filepaths) - 2):  # 2nd to last
    #             print('dsadsadsa')
    #             cmd += f'[a{i}][{i + 1}:a]acrossfade=d={fade_duration}:c1=tri:c2=tri[audio]'
    #         else:  # others
    #             cmd += f'[a{i}][{i + 1}:a]acrossfade=d={fade_duration}:c1=tri:c2=tri[a{i + 1}];'

    for i, filepath in enumerate(filepaths):
        audio_trim_time = get_length(filepath) - fade_duration
        cmd += f'[{i}:a]atrim=0:{audio_trim_time}[{i}a];'
    for i, filepath in enumerate(filepaths):
        cmd += f'[{i}a]'
    cmd += f'concat=n={len(filepaths)}:v=0:a=1[audio]'

    cmd += '" -b:v 10M -map "[audio]" -map "[video]" "' + video_out + '"'

    print(cmd)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:
        print(line)  # return '\n'.join(script_lines)


def convert_to_mp4(video_in, video_out):
    convert_to_mp4 = 'ffmpeg -y -i "' + video_in + '" -c:v libx264 -c:a aac "' + video_out + '"'
    subprocess.check_output(convert_to_mp4, shell=True)


async def make_clips(data, fade_duration, final_video):
    clips_to_merge = []
    count = 0
    for i in range(len(data)):
        count += 1

        input_image_path = f"{AUX_FOLDER}page{count}.png"
        output_image_path = f"{AUX_FOLDER}page{count}_processed.png"
        audio_name = AUX_FOLDER + 'output_' + str(i) + '.wav'

        video_name = 'video_' + str(i) + '.mp4'
        video_out_mp4 = AUX_FOLDER + video_name

        process_image(input_image_path, output_image_path)
        # # # await make_audio(data[i], audio_name, VOICE, speed, PITCH)
        make_audio_polly(data[i], audio_name)
        merge_image_audio(output_image_path, audio_name, video_out_mp4, (fade_duration + 0.5))

        clips_to_merge.append(video_out_mp4)

    video_merged = AUX_FOLDER + 'video_ALL_MERGED.mp4'
    ffmpeg_fade_merge(clips_to_merge, fade_duration, video_merged)
    add_bg_audio_2(video_merged, 'bg_audio.mp3', final_video)
    convert_to_mp4(final_video, final_video + 'sdsds.mp4')


def find_pdfs(folder_path):
    pdf_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    return pdf_files


async def make_pdf_video(pdf_file):
    print(pdf_file)
    data = extract_text_and_images(pdf_file)
    # exit(0)
    final_video = VIDEOS_FOLDER + pdf_file.replace('./pdfs/', '').replace('.pdf', '') + '.mp4'
    fade_duration = 0.5
    await make_clips(data, fade_duration, final_video)


async def _main():
    if not os.path.exists(AUX_FOLDER):
        os.makedirs(AUX_FOLDER)

    if not os.path.exists(VIDEOS_FOLDER):
        os.makedirs(VIDEOS_FOLDER)

    # pdf_file = "./pdfs/The Adventure of Problem-Solving Pals.pdf"
    # # pdf_file = "./pdfs/pdf para video.pdf"
    # final_video = "./videos/The Adventure of Problem-Solving Pals.mp4"

    # pdf_files = find_pdfs('./pdfs/')
    #
    # if pdf_files:
    #     print("PDF files found:")
    #     for pdf_file in pdf_files:
    #         await make_pdf_video(pdf_file)
    # else:
    #     print("No PDF files found in the specified folder.")

    await make_pdf_video('./pdfs/error.pdf')


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(_main())
