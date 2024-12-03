import tkinter as tk
from tkinter import scrolledtext, messagebox
from PIL import Image
import requests
from io import BytesIO
import os
import base64
import sys

# 上传图片到 ImgBB
def upload_image_to_imgbb(image_path, api_key, image_id):
    url = "https://api.imgbb.com/1/upload"
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            payload = {
                "key": api_key,
                "image": encoded_image,
            }
            response = requests.post(url, data=payload)

            if response.status_code == 200:
                image_url = response.json()['data']['url']
                print(f"Image {image_id}: 上传成功: {image_url}")
                return image_url
            elif response.status_code == 400 and "Rate limit reached" in response.text:
                error_message = "API失效：达到上传次数限制，请稍后再试。"
                print(f"Image {image_id}: 上传失败: {error_message}")
                messagebox.showerror("API失效", error_message)
                sys.exit()  # 停止程序
            else:
                error_message = f"上传失败 {image_path}: {response.status_code}, {response.text}"
                print(f"Image {image_id}: {error_message}")
                return None
    except Exception as e:
        error_message = f"上传异常 {image_path}: {str(e)}"
        print(f"Image {image_id}: {error_message}")
        return None

# 裁剪图片
def crop_image(url, output_dir, image_id):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        
        # 如果图像是 RGBA 模式，则转换为 RGB 模式
        if img.mode in ['RGBA', 'P']:
            img = img.convert('RGB')
        
        # 计算裁剪区域
        width, height = img.size
        aspect_ratio = width / height
        if aspect_ratio > 1:  # 宽图
            new_height = 1000
            new_width = int(new_height * aspect_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            left = (new_width - 1000) / 2
            top = 0
            right = (new_width + 1000) / 2
            bottom = new_height
        else:  # 垂直或正方形图
            new_width = 1000
            new_height = int(new_width / aspect_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            left = 0
            top = (new_height - 1000) / 2
            right = new_width
            bottom = (new_height + 1000) / 2

        img_cropped = img.crop((left, top, right, bottom))
        
        # 保存裁剪后的图片
        cropped_image_path = os.path.join(output_dir, f"{image_id}_{os.path.basename(url)}")
        img_cropped.save(cropped_image_path, "JPEG")  # 指定保存为JPEG格式
        print(f"Image {image_id}: 裁剪成功: {cropped_image_path}")

        return cropped_image_path
    except Exception as e:
        print(f"Image {image_id}: 裁剪失败: {str(e)}")
        messagebox.showerror("Error", f"Error processing {url}: {str(e)}")
        return None

# 处理所有链接
def process_images():
    api_key = "1501dacecf94d8d09d5fb965b4ba0667"  # 替换为你的 ImgBB API Key
    image_urls = text_area.get("1.0", tk.END).strip().splitlines()
    
    # 固定输出目录
    output_dir = r"E:\11\承人之美\图片"  # 设置固定输出目录
    if not os.path.exists(output_dir):  # 如果目录不存在，创建它
        os.makedirs(output_dir)

    uploaded_links = []
    for idx, url in enumerate(image_urls, start=1):
        if not url.strip():  # 如果链接为空
            print(f"Image {idx}: 跳过空链接")
            uploaded_links.append("")  # 记录一个空链接
            continue  # 跳过当前循环，处理下一个链接
        print(f"Image {idx}: 开始处理 {url}")
        cropped_image_path = crop_image(url, output_dir, idx)
        if cropped_image_path:
            print(f"Image {idx}: 裁剪后图片路径: {cropped_image_path}")
            # 上传裁剪后的图片
            image_link = upload_image_to_imgbb(cropped_image_path, api_key, idx)
            if image_link:
                uploaded_links.append(image_link)

    # 保存上传成功的链接
    if uploaded_links:
        save_links_to_txt(uploaded_links)

    messagebox.showinfo("完成", "所有图片已裁剪并上传。")

# 保存外链到 .txt 文件
def save_links_to_txt(links, file_path="E:/11/承人之美/图片外链.txt"):
    try:
        print(f"准备保存链接到: {file_path}")  # 打印路径
        with open(file_path, 'w', encoding='utf-8') as file:  # 使用 utf-8 编码
            for link in links:
                file.write(link + '\n')  # 每个链接换行
        print(f"外链已按行保存至 {file_path}")
    except Exception as e:
        print(f"保存 .txt 文件失败: {str(e)}")

# 创建主窗口
root = tk.Tk()
root.title("图片裁剪和上传工具")

# 创建文本区域，允许用户粘贴链接
text_area = scrolledtext.ScrolledText(root, width=50, height=15)
text_area.pack(padx=10, pady=10)

# 创建处理按钮
process_button = tk.Button(root, text="处理图片", command=process_images)
process_button.pack(pady=10)

# 运行主循环
root.mainloop()
