#! /usr/bin/env python
#coding: utf-8
import sht21  # SHT2xライブラリのimport
import subprocess
import sys
import time

# 現在時刻の取得
now = time.strftime('%Y-%m-%d %H:%M:%S')
#----------------------------------------------------------------------
#SHT-25による温湿度計測
#----------------------------------------------------------------------
with sht21.SHT21(1) as sht21:
  temp = float(sht21.read_temperature())
  humi = float(sht21.read_humidity())

#
#ec = 5   # Error Count : I2C通信などでエラーになった場合、リトライする回数を指定する。
#while True:
#  o = subprocess.Popen("/usr/local/lib/python2.7/site-packages/sht21.py",shell=True,stdout=subprocess.PIPE)
#  line = o.stdout.readline()
#  if (line==""):
#    ec = ec - 1
#    if (ec>0):
#      continue
#    else:
#      print >> sys.stderr, "{0} SHT2x READ Error.".format(now)
#  else:
#    ec = 5   # Error Count : I2C通信などでエラーになった場合、リトライする回数を指定する。
#    try:
#      temp = float( line.split()[1] )
#    except:
#      time.sleep(0.3)
#      continue
#    temp = int(temp * 100)
#    line = o.stdout.readline()
#    try:
#      humi = float( line.split()[1] )
#    except:
#      time.sleep(0.3)
#      continue
#    humi = int(humi * 100)
#  break

#----------------------------------------------------------------------
# AEH11による照度計測
#----------------------------------------------------------------------
# プログラム実行時のパラメータを有無を確認する
argvs = sys.argv
argc = len(argvs)
if (argc>1):
  reso = sys.argv[1]
else:
  reso = ""

#senseillu= 0x0102  # Sensor illuminate of AEH11
I2CGET = "/usr/sbin/i2cget -y 1 "      # 最後の1はBUS IDなので現物に合わせて変更要
I2CSET = "/usr/sbin/i2cset -f -y 1 "   # 最後の1はBUS IDなので現物に合わせて変更要

AEH11_ADDR = 0x23  # I2Cアドレス
AEH11_PON = 0x01   # PowerON
AEH11_BCLR = 0x07  # BufferClear
#AEH11_HIRS = 0x10  # 連続高解像度測定
AEH11_HIRS = 0x20  # 単発高解像度測定
AEH11_MTREG31_1 = 0x40  # Mtreg 31 1st parameter
AEH11_MTREG31_2 = 0x7F  # Mtreg 31 2nd parameter
AEH11_MTREG69_1 = 0x42  # Mtreg 69 1st parameter
AEH11_MTREG69_2 = 0x65  # Mtreg 69 2nd parameter
AEH11_DATA = 0x00

# センサデータの起動・初期化
ec = 5
while True:
  try:
    print >> sys.stderr, "{0} AEH11 PowerOn".format(now)
    cmnd = "{0} 0x{1:X} 0x{2:X} {3}".format(I2CSET,AEH11_ADDR,AEH11_PON,"c")
    o = subprocess.Popen(cmnd,shell=True,stdout=subprocess.PIPE)
    time.sleep(0.3)
    print >> sys.stderr, "{0} AEH11 BufferClear".format(now)
    cmnd = "{0} 0x{1:X} 0x{2:X} {3}".format(I2CSET,AEH11_ADDR,AEH11_BCLR,"c")
    o = subprocess.Popen(cmnd,shell=True,stdout=subprocess.PIPE)
    time.sleep(0.3)
    if reso=="L":
      print "Mtreg 31"
      cmnd = "{0} 0x{1:X} 0x{2:X} {3}".format(I2CSET,AEH11_ADDR,AEH11_MTREG31_1,"c")
      o = subprocess.Popen(cmnd,shell=True,stdout=subprocess.PIPE)
      time.sleep(0.3)
      cmnd = "{0} 0x{1:X} 0x{2:X} {3}".format(I2CSET,AEH11_ADDR,AEH11_MTREG31_2,"c")
      o = subprocess.Popen(cmnd,shell=True,stdout=subprocess.PIPE)
      time.sleep(0.3)
    else:
      print "Mtreg 69"
      cmnd = "{0} 0x{1:X} 0x{2:X} {3}".format(I2CSET,AEH11_ADDR,AEH11_MTREG69_1,"c")
      o = subprocess.Popen(cmnd,shell=True,stdout=subprocess.PIPE)
      time.sleep(0.3)
      cmnd = "{0} 0x{1:X} 0x{2:X} {3}".format(I2CSET,AEH11_ADDR,AEH11_MTREG69_2,"c")
      o = subprocess.Popen(cmnd,shell=True,stdout=subprocess.PIPE)
      time.sleep(0.3)

    if AEH11_HIRS==0x10:
      print >> sys.stderr, "{0} AEH11 ContinuousSampling".format(now)
    elif AEH11_HIRS==0x20:
      print >> sys.stderr, "{0} AEH11 OneShotSampling".format(now)
    cmnd = "{0} 0x{1:X} 0x{2:X} {3}".format(I2CSET,AEH11_ADDR,AEH11_HIRS,"c")
    o = subprocess.Popen(cmnd,shell=True,stdout=subprocess.PIPE)
    time.sleep(0.3)
    break
  except:
    ec = ec - 1
    if (ec>0):
      time.sleep(0.5)
      print >> sys.stderr, "{0} ERROR RETRY {1} TIMES".format(now),ec
      continue
    else:
      print "{0} AEH11 Power ON Fail.".format(now)
      break

# センサデータの読み取り
ec = 5
while True:
  print >> sys.stderr, "{0} AEH11 GetData".format(now)
  try:
    cmnd = "{0} 0x{1:X} 0x{2:X} {3}".format(I2CGET,AEH11_ADDR,AEH11_DATA,"w")
    p = subprocess.Popen(cmnd,shell=True,stdout=subprocess.PIPE)
  except:
    time.sleep(0.3)
    ec = ec - 1
    if (ec>0):
      time.sleep(0.5)
      continue
    else:
      print >> sys.stderr, "{0} AEH11 Read Fail.".format(now)
      break
  break

line = p.stdout.readline()
vstr = str(line)
print "{0} ill Data={1}".format(now,vstr)
if vstr=="":
  argvt = "DEVERR"
  illVal = -1

# 計測データの変換
illhex = "0x"+str(vstr[4])+str(vstr[5])+str(vstr[2])+str(vstr[3])
illVal = int(illhex,16)

# 計測データの補正（計測モードやセンサへのカバー等の取付など条件に合わせて補正を行う）
if reso=="L":
  illVal = int(illVal*1.79)  # 1.79はカバー無しの場合。現物に合わせて値の調整要
else:
  illVal = int(illVal*0.83)  # 0.83はカバー無しの場合。現物に合わせて値の調整要

# 計測データの表示
print now, temp, humi, illVal

# 計測データをSDカードに保存
f = open('data_env.csv','a')
f.write(now)
f.write(', ')
f.write(str(temp))
f.write(', ')
f.write(str(humi))
f.write(', ')
f.write(str(illVal))
f.write('\n')
f.close()

sys.exit()
