## Group join
## Group check the latest message
## Send notice to UncleMAC members


from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext
import datetime, re, time
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.utils import timezone
from django.db.models import Q

#from django.views.generic import TemplateView, ListView
from django.shortcuts import redirect
from app.models import Group, Lineuser
from django.apps import apps

import sys
import pandas as pd
import json
from celery import Celery, shared_task
import pytz
import random


from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *

from django.conf import settings

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

import logging
logger = logging.getLogger(__name__)


#定時發圖
@shared_task
def weekly_push():
    tday=datetime.now().date()
    #weekday_num=datetime.datetime.now().date().weekday()
    weekday_num=datetime.today().weekday()
    #週一是0, 週日是6
    if weekday_num == 1:
        no=1
    else:
        no=2

    img_url = 'https://unclebot.site/media/um/'+'Buy_MacBook'+'.png' 
    img_url2 = 'https://unclebot.site/media/um/'+'Buy_iMac'+'.png' 
    #logger.info(img_url)
    length=len(Group.objects.all())
    logger.info(length)
    total_len=length+1
    for i in range(3, int(total_len)):
        logger.info(i)
        gp=Group.objects.get(id=i)
        if gp.active==False:
            pass
        else:
            f_name_a = 'app/UMacc.xlsx'
            df1=pd.read_excel(f_name_a, sheet_name=3)
            df2=pd.read_excel(f_name_a, sheet_name=4)
            df1_list = df1.values.tolist()
            df2_list = df2.values.tolist()
            length_1=len(df1)
            length_2=len(df2)
            #logger.info(length_2)
            wording=random.randint(0, length_1-1)
            emoji=random.randint(0, length_2-1)
            emoji2=random.randint(0, length_2-1)
            wording_len=len(df1_list[wording][1])

            emojis = [
                {
                    "index": int(wording_len),
                    "productId": df2_list[emoji][1],
                    "emojiId": str(df2_list[emoji][2]).zfill(3)
                },
                {
                    "index": int(wording_len)+1,
                    "productId": df2_list[emoji2][1],
                    "emojiId": str(df2_list[emoji2][2]).zfill(3)
                }

            ]
            text_message = TextSendMessage(text=df1_list[wording][1]+'$$', emojis=emojis)
            line_bot_api.push_message(gp.group_id, text_message)
            time.sleep(1)
            line_bot_api.push_message(gp.group_id, ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))
            time.sleep(1)
            line_bot_api.push_message(gp.group_id, ImageSendMessage(original_content_url=img_url2, preview_image_url=img_url2))
            logger.info('已送出收購文')
            time.sleep(1)

            #if no==2:
            #    if (i % 2) == 0:
            #        line_bot_api.push_message(gp.group_id, text_message)
            #        time.sleep(1)
            #        line_bot_api.push_message(gp.group_id, ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))
            #        time.sleep(1)
            #        line_bot_api.push_message(gp.group_id, ImageSendMessage(original_content_url=img_url2, preview_image_url=img_url2))
            #        logger.info('已送出收購文')
            #    else:
            #        pass
            #else:
            #    if (i % 2) == 0:
            #        pass
            #    else:
            #        line_bot_api.push_message(gp.group_id, text_message)
            #        time.sleep(1)
            #        line_bot_api.push_message(gp.group_id, ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))
            #        time.sleep(1)
            #        line_bot_api.push_message(gp.group_id, ImageSendMessage(original_content_url=img_url2, preview_image_url=img_url2))
            #        logger.info('已送出收購文')
    time.sleep(1)
    regular_reply = '定期訊息推播已送出'
    line_bot_api.push_message('Ceb756de0b3a4786ebcc2fc9c99d4badd', TextSendMessage(text=regular_reply))
  

#定時確認未讀訊息

@shared_task
def daily_check():
    utc=pytz.UTC
    tday= datetime.now().replace(tzinfo=utc)
    datetime2=(tday-timedelta(hours=10)).replace(tzinfo=utc)
    weekay_num=datetime.today().weekday()
    #週一是0, 週日是6

    length=len(Group.objects.all())
    total_len=length+1
    for i in range(3, int(total_len)):
        logger.info(i)
        gp=Group.objects.get(id=i)
        if gp.active==False:
            pass
        else:
            
            if gp.last_message_byV==True:
                #logger.info(gp.last_messagetime_byV)
                #logger.info(datetime2)
                if gp.last_messagetime_byV < datetime2:
                    logger.info(gp.last_messagetime_byV)
                    regular_reply = '群組 '+gp.vendor_company+' 有未回應之訊息唷'
                    line_bot_api.push_message('Ceb756de0b3a4786ebcc2fc9c99d4badd', TextSendMessage(text=regular_reply))
                    logger.info('有未讀訊息, 已寄通知')
                else:
                    pass
                    logger.info('沒未讀訊息')
            else:
                pass

@shared_task
def weekly_test():

    tday= datetime.now().date()
    logger.info('go')
    img_url = 'https://unclebot.site/media/um/'+'Buy_MacBook'+'.png' 
    #logger.info(img_url)
    length=len(Group.objects.all())

    #line_bot_api.push_message('C848a486eabe2eae82a9c6fce19deb16c', ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))



@shared_task
def test():
    tday= datetime.now()
    datetime2=tday-timedelta(hours=2)
    weekay_num=datetime.today().weekday()
    logger.info('1')
#    logger.info(tday)
#    logger.info(datetime2)
    #logger.info(weekay_num)

@shared_task
def test2():
    tday= datetime.now()
    datetime2=tday-timedelta(hours=2)
    weekay_num=datetime.today().weekday()
    logger.info('2')
#    logger.info(tday)
#    logger.info(datetime2)
    #logger.info(weekay_num)
