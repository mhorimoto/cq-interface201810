#! /usr/bin/env python
#coding: utf-8
#
#######################################################
# CQ出版
#   インターフェース2018年10月号
#   Ver. 1.00  18th Aug. 2018
#          T.Okayasu, M.Horimoto
#######################################################
#
#
import subprocess
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages')
import time
import sht21  # SHT2xのライブラリをimportする

BUSID = 1     # I2CのバスID、RPiの場合には1
ERCNT = 5     # Error Count エラーリトライの回数を指定する
LOGNAME = "/var/log/measure.log"  # 観測結果を収めるファイル。
#                                   パーミッションに注意。

# 現在時刻の取得
now = time.strftime('%Y-%m-%d %H:%M:%S')
#----------------------
#SHT-25による温湿度計測
#----------------------
with sht21.SHT21(BUSID) as sht21:
  temp = float(sht21.read_temperature())
  humi = float(sht21.read_humidity())


#----------------------
# AEH11による照度計測
#----------------------
# プログラム実行時のパラメータを有無を確認する
# コマンド引数に"L"を付けると低感度、すなわち超明るい環境で使う
# 場合に指定する。農業用ならば、ほとんど"L"が必要。

argvs = sys.argv
argc = len(argvs)
if (argc>1):
  reso = sys.argv[1]
else:
  reso = ""

I2CGET = "/usr/sbin/i2cget -y "+str(BUSID)
I2CSET = "/usr/sbin/i2cset -f -y "+str(BUSID)

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

ec = ERCNT
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

ec = ERCNT
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

illhex = "0x"+str(vstr[4])+str(vstr[5])+str(vstr[2])+str(vstr[3])
illVal = int(illhex,16)

if reso=="L":
  illVal = int(illVal*1.79)  # 1.79はカバー無しの場合。現物合わせの調整が必要
else:
  illVal = int(illVal*0.83)  # 0.83はカバー無しの場合。現物合わせの調整が必要

tx = "{0},{1:6.3f},{2:6.3f},{3}\n".format(now,temp,humi,illVal)
logfp = open(LOGNAME,'a')
logfp.write(tx)
logfp.close()
sys.exit()
