# 小斌斌，2020/11/11
import opencv as cv2
import numpy as np
import os
import subprocess
import glob
from matplotlib import pyplot as plt

# 因为是视频，所以定义输入路径以及处理好的输出视频路径
INPUT = "./input"
OUTPUT = "./output"
TEST_VIDEO = "test_video.mov"
DEBUG = False  # 显示效果防止出错，便于调试用


# 定义画图函数，因为后面多次调用，所以直接写成函数
def plot_image(image, title):
	plt.imshow(image, cmap=plt.cm.gray)
	plt.title(title)
	plt.show()


# 保存图片
def save_image(image, title):
	cv2.imwrite(title, image)


# 读取灰度图片
def grayscale(image):
	grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 读取图片取单通道
	if DEBUG:
		plot_image(grayscale_image, "grayscaleImage")
	return grayscale_image


# 使用高斯处理图片的噪声信息进行图片的平滑
def blur(image):
	blur_image = cv2.GaussianBlur(image, (3, 3), 0)
	if DEBUG:
		plot_image(blur_image, "blurImage")
	return blur_image


# 边缘检测算法
def canny(image):
	canny_image = cv2.Canny(image, 100, 150)
	if DEBUG:
		plot_image(canny_image, "canny")
	return canny_image


# 提取感兴趣区域，下面有解释
def roi(image):
	bottom_padding = 100
	height, width = image.shape
	# 获取图片四个角的坐标
	bottom_left = [0, height - bottom_padding]
	bottom_right = [width, height - bottom_padding]
	top_right = [width * 2 / 3, height / 3]
	top_left = [width / 3, height / 3]
	# 将坐标转换为矩阵格式
	vertices = [np.array([[bottom_left, bottom_right, top_right, top_left]], dtype=np.int32)]
	mask = np.zeros_like(image)  # 定义全黑的图片
	cv2.fillPoly(mask, vertices, 255)  # 填充方式画出来
	if DEBUG:
		plot_image(mask, "mask")
	masked_image = cv2.bitwise_and(image, mask)
	if DEBUG:
		plot_image(masked_image, "roi")
	return masked_image


# 实现霍夫曼可视化
def averaged_lines(image, lines):
	right_lines = []
	left_lines = []
	for x1, y1, x2, y2 in lines[:, 0]:
		parameters = np.polyfit((x1, x2), (y1, y2), 1)
		slope = parameters[0]
		intercept = parameters[1]
		if slope >= 0:
			right_lines.append([slope, intercept])
		else:
			left_lines.append([slope, intercept])

	def merge_lines(image, lines):
		if len(lines) > 0:
			slope, intercept = np.average(lines, axis=0)
			y1 = image.shape[0]
			y2 = int(y1 * (1 / 2))
			x1 = int((y1 - intercept) / slope)
			x2 = int((y2 - intercept) / slope)
			return np.array([x1, y1, x2, y2])

	left = merge_lines(image, left_lines)
	right = merge_lines(image, right_lines)
	return left, right


# 霍夫曼变化可视化
def hough_lines(image, rho, theta, threshold, min_line_len, max_line_gap):
	lines_image = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
	lines = cv2.HoughLinesP(image, rho, theta, threshold, np.array([]), minLineLength=min_line_len,
							maxLineGap=max_line_gap)
	if lines is not None:
		lines = averaged_lines(image, lines)
		for line in lines:
			if line is not None:
				x1, y1, x2, y2 = line
				cv2.line(lines_image, (x1, y1), (x2, y2), (0, 0, 255), 20)
			if DEBUG:
				plot_image(lines_image, "lines")
		return lines_image


# 图片视线合并
def combine_image(image, initial_image, a=0.9, b=1.0, c=0.0):
	combine_image = cv2.addWeighted(initial_image, a, image, b, c)
	if DEBUG:
		plot_image(combine_image, "combined")
	return combine_image


# 主函数
def find_street_lanes(image):
	grayscale_image = grayscale(image)  # 读取灰度图片
	blur_imamge = blur(grayscale_image)  # 平滑图片
	canny_image = canny(blur_imamge)  # 边缘算法
	roi_image = roi(canny_image)  # 提取感兴趣区域
	hough_lines_image = hough_lines(roi_image, 0.9, np.pi / 180, 100, 100, 50)
	final_image = combine_image(hough_lines_image, image)
	return final_image


# 读取视频的路径
caputure = cv2.VideoCapture('test_video.mov')
while True:
	_, frame = caputure.read()  # 读取视频中每帧得到图片
	if frame is not None:  # 判断每帧的图片是否为空
		stree_lanes = find_street_lanes(frame)
		cv2.imshow("video", stree_lanes)  # 实时展示每帧的图片
	else:
		break
	if cv2.waitKey(30) == ord('q'):
		break
caputure.release()  # 释放掉操作，以免占内存
cv2.destroyAllWindows()  # 摧毁所有窗口
exit()  # 退出驱动



