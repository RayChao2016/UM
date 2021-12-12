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


def machine_check(msg):
    logger.info(msg)
    f_name_a = 'app/UM_List.xlsx'
    df=pd.read_excel(f_name_a, sheet_name=0)
    df_list = df.values.tolist()
    length = len(df)
    logger.info(str(length))
    for i in range(length):
        w_list = df.iloc[i,1]
        #logger.info(w_list)
        if msg.text == w_list:
            #active
            logger.info(df.iloc[i,24])
            if df.iloc[i,24] == 'N':
                text_reply = df.iloc[i,1] + '已賣出！ \uD83D\uDE06'

            else:

                year = str(df.iloc[i,2])[:4]        #year
                logger.info(year)
                model = df.iloc[i,12]                #model
                logger.info(model)
                name = df.iloc[i,4]                #name
                logger.info(name)
                cpu = df.iloc[i,7]                #CPU
                logger.info(cpu)
                dimm = df.iloc[i,8]                #DIMM
                logger.info(dimm)
                ssd = df.iloc[i,9]                #SSD
                logger.info(ssd)
                batt = str(df.iloc[i,15])               #battery
                logger.info(batt)
                cost = str(df.iloc[i,16])         #cost
                logger.info(cost)
                price = str(df.iloc[i,11])        #price
                logger.info(price)
                shop = df.iloc[i,19]                #Shoppee
                logger.info(shop)
                on_shelf = df.iloc[i,21]                #on_shelf
                logger.info(on_shelf)
                
                text_reply = year+' \n'+name +' \n'+model +' \n'+'CPU： '+cpu +' \n'+'DIMM/SSD： '+ dimm+'/'+ssd+'\n'+'成本： '+cost+' \n'+'賣價： '+price+' \n'+ '上架日： '+on_shelf+' \n'+'蝦皮： '+shop
                #text_reply = year+' \n'+name +' \n'+model +' \n'+cpu +' \n'+dimm+'/'+ssd+'\n'+'成本： '+cost

            return text_reply
            break
        else:
            
            pass
    text_reply = '沒有這台唷 \uD83D\uDE02'
    return text_reply

#儲存vendor user資料
def check_vendor_user(group_id, user_id, user_name):
    logger.info('start')
    the_time=datetime.now()
    try:
        if Group.objects.filter(group_id = group_id).exists():
            gro=Group.objects.get(group_id = group_id) 
            f_name_a = 'app/UMacc.xlsx'
            df=pd.read_excel(f_name_a, sheet_name=0)
            df_list = df.values.tolist()
            w_list = str(df_list[0][1:5])
            #logger.info(user_name)
            #logger.info(w_list)

            #if any(x in user_name for x in w_list):
            if user_name in w_list:
                gro.last_message=the_time
                if gro.last_message_byV:
                    gro.last_message_byV=False
                    gro.save(update_fields=['last_message', 'last_message_byV'])
                else:
                    gro.save(update_fields=['last_message'])
                logger.info('check')
            else:
                logger.info('check and go')
                if not gro.vender_name_exist and not gro.vender_name2_exist: #若不存在老闆1/老闆2
                    logger.info('1st situation')
                    gro.vendor_id=user_id
                    gro.vendor_name=user_name
                    gro.last_messagetime_byV=the_time
                    gro.last_message=the_time
                    gro.last_message_byV=True
                    gro.vender_name_exist = True
                    gro.save(update_fields=[ 'vendor_id', 'vendor_name', 'last_messagetime_byV', 'last_message', 'last_message_byV', 'vender_name_exist'])
                elif gro.vender_name_exist and not gro.vender_name2_exist: #若不存在老闆2
                    logger.info('2nd situation')
                    if gro.vendor_id==user_id: 
                        gro.last_messagetime_byV=the_time
                        gro.last_message=the_time
                        gro.last_message_byV=True
                        gro.save(update_fields=['last_messagetime_byV', 'last_message', 'last_message_byV'])

                    else: #存到老闆2
                        gro.vendor_id2=user_id
                        gro.vendor_name2=user_name
                        gro.last_messagetime_byV=the_time
                        gro.last_message=the_time
                        gro.last_message_byV=True
                        gro.vender_name2_exist = True
                        gro.save(update_fields=[ 'vendor_id2', 'vendor_name2', 'last_messagetime_byV', 'last_message', 'last_message_byV', 'vender_name2_exist'])     
                elif not gro.vender_name_exist and gro.vender_name2_exist: #若不存在老闆1
                    logger.info('3rd situation')
                    if gro.vendor_id2==user_id: 
                        gro.last_messagetime_byV=the_time
                        gro.last_message=the_time
                        gro.last_message_byV=True
                        gro.save(update_fields=['last_messagetime_byV', 'last_message', 'last_message_byV'])
                    else: #存到老闆1
                        gro.vendor_id=user_id
                        gro.vendor_name=user_name
                        gro.last_messagetime_byV=the_time
                        gro.last_message=the_time
                        gro.last_message_byV=True
                        gro.vender_name_exist = True
                        gro.save(update_fields=[ 'vendor_id', 'vendor_name', 'last_messagetime_byV', 'last_message', 'last_message_byV', 'vender_name_exist'])     

                else: #存在老闆1/老闆2
                    logger.info('4th situation')
                    if gro.vendor_id==user_id | gro.vendor_id2==user_id:
                        gro.last_messagetime_byV=the_time
                        gro.last_message_byV=True
                        gro.last_message=the_time
                        gro.save(update_fields=['last_messagetime_byV', 'last_message_byV', 'last_message'])
                    
                    else:
                        pass
                        logger.info('the 3rd vendor name')
        else:
            pass
    except Exception as e:
        logger.info(e)


#老闆離開
def check_vendor_left(group_id, user_id):
    #logger.info('start')
    try:
        if Group.objects.filter(group_id = group_id).exists():
            gro=Group.objects.get(group_id = group_id) 
            if gro.active:
                if gro.vender_name_exist and gro.vender_name2_exist:
                    if gro.vender_id==user_id:
                        gro.vender_name_exist= False

                        gro.save(update_fields=['vender_name_exist'])
                    else:
                        gro.vender_name2_exist= False
                        gro.save(update_fields=['vender_name2_exist'])

                elif gro.vender_name_exist and not gro.vender_name2_exist:
                    if gro.vender_id==user_id:
                        gro.vender_name_exist= False
                        gro.active=False
                        gro.save(update_fields=['active', 'vender_name_exist'])
                        regular_reply = '群組 '+gro.vendor_company+' 老闆已離開群組了'
                        ine_bot_api.push_message('Ceb756de0b3a4786ebcc2fc9c99d4badd', TextSendMessage(text=regular_reply))
                    else:
                        pass
                elif not gro.vender_name_exist and gro.vender_name2_exist:  
                    if gro.vender_id2==user_id:
                        gro.vender_name2_exist= False
                        gro.active=False
                        gro.save(update_fields=['active', 'vender_name2_exist'])
                        regular_reply = '群組 '+gro.vendor_company+' 老闆已離開群組了'
                        ine_bot_api.push_message('Ceb756de0b3a4786ebcc2fc9c99d4badd', TextSendMessage(text=regular_reply))
                    else:
                        pass
                else:
                    pass
                    logger.info('no vendor in this group')

            else:
                pass
                logger.info('no vendor in this group')

        else:
            pass
                
    except Exception as e:
        logger.info(e)

#有人加入
def someone_join(group_id):
    try:
        if Group.objects.filter(group_id = group_id).exists():
            gro=Group.objects.get(group_id = group_id) 
            regular_reply = '群組 '+gro.vendor_company+' 有新成員加入唷！'
            ine_bot_api.push_message('Ceb756de0b3a4786ebcc2fc9c99d4badd', TextSendMessage(text=regular_reply))
        else:
            pass
    except Exception as e:
        logger.info(e)



def test3():
    tday= datetime.now()
    datetime2=tday-timedelta(hours=2)
    weekay_num=datetime.today().weekday()
    length=len(Group.objects.all())
    total_len=length+1
    for i in range(3, int(total_len)):
        logger.info(i)
        gp=Group.objects.get(id=i)
        logger.info(gp.vendor_company)


#關鍵字確認
def wording_check(group_id,msg, reply_token):
    
    f_name_a = 'app/UMacc.xlsx'
    df=pd.read_excel(f_name_a, sheet_name=1)
    df_list = df.values.tolist()
    #w_list = str(df_list[0][1])
    #logger.info(w_list)
    #logger.info(user_name)
    length = len(df)

    for i in range(length):
        #logger.info(df_list[i][1])
        if group_id == df_list[i][1]:

            f_name_a = 'app/UMacc.xlsx'
            df2=pd.read_excel(f_name_a, sheet_name=2)
            df2_list = df2.values.tolist()
            length2 = len(df2)
            for j in range(length2):
                w2_list=df2_list[j][1:4]
                #logger.info(w2_list)
                if any(x in msg.text.lower() for x in w2_list):
                    if j == 2:
                        logger.info('machine_check')
                        machine_reply = machine_check(msg)
                        r_text = '機台紀錄如下'+'\u2B07\uFE0F'
                        line_bot_api.reply_message(reply_token, [TextSendMessage(text=r_text),TextSendMessage(text=machine_reply)])

                    else:
                        reply_img=df2_list[j][4]
                        logger.info(reply_img)
                        r_text = df2_list[j][5]+ '\u2B07\uFE0F'
                        #logger.info(reply_text)
                        time.sleep(1)
                        if df2_list[j][6] == 'P':
                            line_bot_api.reply_message(reply_token, [TextSendMessage(text=r_text),ImageSendMessage(original_content_url=reply_img, preview_image_url=reply_img)])
                            
                        else:
                            line_bot_api.reply_message(reply_token, [TextSendMessage(text=r_text),TextSendMessage(text=reply_img)])

                    break
                else:
                    #logger.info('Not match')
                    pass
        else:
            pass



