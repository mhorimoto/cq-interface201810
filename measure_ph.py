#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cv2
import io
import math
import numpy as np
import picamera
import readchar
import sys
import time

# ===========================================================================
# 色情報を用いた草高の計測
# ===========================================================================
def measure_height(image):
# 黒色領域を抽出する
  hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV_FULL)
  h = hsv[:, :, 0]
  s = hsv[:, :, 1]
  v = hsv[:, :, 2]
  mask = np.zeros(h.shape, dtype=np.uint8)
  mask[(h < 20) & (s > 235) & (v < 50)] = 255
  contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  rects = []
  for contour in contours:
    approx = cv2.convexHull(contour)
    rect = cv2.boundingRect(approx)
    rects.append(np.array(rect))

# 抽出された黒色領域の中で一番上のものを探し出す
  height = 0
  black_x = 0
  black_y = 10000
  black_h = 0
  black_v = 0
  if len(rects) > 0:
    black_y = 10000
    for rect in rects:
      if rect[2] * rect[3] > 400:
        if rect[1] < black_y:
          black_x = rect[0]
          black_y = rect[1]
          black_h = rect[2]
          black_v = rect[3]

# 黒色部分の面積と実際の面積からピクセルからmmへの変換割合を計算する
    if (float (black_h) * float(black_v)) != 0:
      scale = math.sqrt(1600 / (float(black_h) * float(black_v)))
    else:
      scale = 0

# 黒色領域の下端から下方に画素の色情報を調べ，緑が最初に現れた位置を抽出する．
    for j in range(black_y + black_v, image.shape[0]):
# 葉の上端面を抽出する
      if hsv[j, black_x + black_h / 2][1] > 120 and hsv[j, black_x + black_h / 2, 0] > 30 and hsv[j, black_x + black_h / 2, 0] < 60:
# 
        cv2.rectangle(image, (black_x - 10, j), (black_x + black_h + 10, j), (255, 255, 255), thickness = 2)
# 草高の計算
        height = 400 - (j - black_y) * scale
        break
# 
  cv2.rectangle(image, (black_x, black_y), (black_x + black_h, black_y + black_v), (0, 255, 255), thickness = 2)

  return height

# ===========================================================================
# メインプログラム
# ===========================================================================
if __name__ == "__main__":
# 現在時刻の取得
  now = time.strftime('%Y-%m-%d %H:%M:%S')

#画像処理のための取得画層条件
  camera = picamera.PiCamera()
  camera.resolution = (640, 480)
  camera.rotation = 180
  camera.exposure_mode = 'snow'
  camera.start_preview()

  stream = io.BytesIO()

# カメラの撮影状態を安定化させる
  time.sleep(5)

  num = 0
  avg_height = 0
  while cv2.waitKey(30) < 0:

    num = num +1

    camera.capture(stream, format = 'jpeg')
    img_data = np.fromstring(stream.getvalue(), dtype=np.uint8)
    frame = cv2.imdecode(img_data, 1)

    avg_height = avg_height + measure_height(frame)

    cv2.imshow('草高の計測', frame)
 
    if num > 4:
      break

    stream.seek(0)

  print "草高：", avg_height / 5 , " mm"
  cv2.destroyAllWindows()

