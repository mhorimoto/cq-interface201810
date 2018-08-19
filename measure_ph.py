#! /usr/bin/env python
#coding: utf-8
import cv2
import io
import math
import numpy as np
import picamera
import readchar
import sys
import time

#----------------------------------------------------------------------
# 色情報を用いた草高の計測
#----------------------------------------------------------------------
def measure_height(image):
# 黒色領域を抽出する
  hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV_FULL)
  h = hsv[:, :, 0] # Hue(色相)の取得
  s = hsv[:, :, 1] # Saturation(彩度)の取得
  v = hsv[:, :, 2] # Value(明度)の取得
# マスク情報作成
  mask = np.zeros(h.shape, dtype=np.uint8) 
  mask[(h < 20) & (s > 235) & (v < 50)] = 255 # 各色の値は環境に合わせて設定要
  contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # 画像の輪郭抽出
  rects = []
  for contour in contours:
    approx = cv2.convexHull(contour) # 抽出した輪郭を包含する凸領域を抽出
    rect = cv2.boundingRect(approx)  # 凸領域を包含する外接矩形を抽出
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
      if rect[2] * rect[3] > 400: # ある程度大きさを持った矩形をマーカとして処理。画像のサイズに応じて変更要
        if rect[1] < black_y: # 画像中の最も上方にある矩形を探索
          black_x = rect[0]   # 矩形の左上端x座標
          black_y = rect[1]   # 矩形の左上端y座標
          black_h = rect[2]   # 矩形の幅
          black_v = rect[3]   # 矩形の高さ

    cv2.rectangle(image, (black_x, black_y), (black_x + black_h, black_y + black_v), (0, 255, 255), thickness = 2) # 抽出した最上部マーカに黄色枠を描画

# 黒色部分の面積と実際の面積からピクセルからmmへの変換割合を計算する
    if (float (black_h) * float(black_v)) != 0:
      scale = math.sqrt(1600 / (float(black_h) * float(black_v)))
    else:
      scale = 0

# 黒色領域の下端から下方に画素の色情報を調べ，緑が最初に現れた位置を抽出する．
    for j in range(black_y + black_v, image.shape[0]):
# 葉の上端面を抽出する
      if hsv[j, black_x + black_h / 2][1] > 120 and hsv[j, black_x + black_h / 2, 0] > 30 and hsv[j, black_x + black_h / 2, 0] < 60: # 緑色の画素を判別。画像の状態により変更要
# 
        cv2.rectangle(image, (black_x - 10, j), (black_x + black_h + 10, j), (255, 255, 255), thickness = 2) # 植物の葉の位置に白線を描画
# 草高の計算
        height = 400 - (j - black_y) * scale # 高さの計算
        break

  return height

#----------------------------------------------------------------------
# メインプログラム
#----------------------------------------------------------------------
if __name__ == "__main__":
# 現在時刻の取得
  now = time.strftime('%Y-%m-%d %H:%M:%S')

#画像処理のための取得画層条件
  camera = picamera.PiCamera()
  camera.resolution = (640, 480) # 画像解像度
  camera.rotation = 180          # 画像の上下反転
  camera.exposure_mode = 'snow'  # ホワイトバランス設定
  camera.start_preview()
  stream = io.BytesIO()

# カメラの撮影状態を安定化させる
  time.sleep(5)

# 草高を計測（5回計測した平均値）
  num = 0
  sum_height = 0
  while cv2.waitKey(30) < 0:
    num = num +1
    camera.capture(stream, format = 'jpeg') # 画像を取得
    img_data = np.fromstring(stream.getvalue(), dtype=np.uint8)
    frame = cv2.imdecode(img_data, 1)
    sum_height = sum_height + measure_height(frame) # 植物の高さを計測
    cv2.imshow('草高の計測', frame)
    if num > 4:
      break
    stream.seek(0)
    avg_height = sum_height / 5

# 草高の表示
  print "平均草高（5回計測）：", avg_height , " mm"

# 草高をSDカードに出力
  f = open('plant_height.csv','a')
  f.write(now)
  f.write(', ')
  f.write(str(avg_height))
  f.write('\n')
  f.close()

  cv2.destroyAllWindows()
  sys.exit()
