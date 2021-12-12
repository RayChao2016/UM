
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.template import RequestContext
import datetime, re
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.utils import timezone
from django.db.models import Q
from app.models import Group, Lineuser
from app.task1.Check import check_vendor_user, check_vendor_left, someone_join, wording_check
from app.task1.Test import test3, test4, test5
#from django.views.generic import TemplateView, ListView
from django.shortcuts import redirect

from django.apps import apps
import pandas as pd
import json

import sys

from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError

from linebot.models import *
from django.conf import settings

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

import logging
logger = logging.getLogger(__name__)

@csrf_exempt
def callback(request):
    logger.info("1")
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        return HttpResponse()
    else:
        logger.info("not POST")
        return HttpResponseBadRequest()



@handler.add(JoinEvent)
def process_join_event(event):
    logger.info(event)
    dateday = datetime.now().date().strftime("%Y/%b/%d")
    tday = datetime.now().date()
    receive_type=json.loads(str(event.source))['type']
    #logger.info(receive_type)
    if receive_type == 'room':
        room_id=json.loads(str(event.source))['roomId']
        #logger.info(room_id)

        regular_reply = 'Goodbye!\udbc0\udc0d'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=regular_reply))
        line_bot_api.leave_room(room_id)
        logger.info('left room')
    else:
        group_id=json.loads(str(event.source))['groupId']
        #logger.info(group_id)
        #Check if UncleMac in group
        summary = line_bot_api.get_group_summary(group_id)
        #logger.info(summary)
        
        if "UncleMAC" not in summary.group_name:
            line_bot_api.leave_group(event.source.group_id)
            logger.info('left')
        
        else:
            if Group.objects.filter(group_id = group_id).exists():
                gro=Group.objects.get(group_id = group_id)       
                gro.group_name=summary.group_name
                gro.vendor_company=summary.group_name[9:]
                gro.updated_at=datetime.now()
                gro.last_message=datetime.now()
                gro.last_messagetime_byV=datetime.now()
                gro.last_message_byV=False
                gro.active=True
                gro.save(update_fields=[ 'group_name', 'vendor_company', 'updated_at', 'last_message', 'last_messagetime_byV', 'last_message_byV','active'])
            else:
                gp = Group(
                    group_id=group_id, 
                    group_name=summary.group_name, 
                    vendor_company=summary.group_name[9:], 
                    updated_at=datetime.now(), 
                    last_message=datetime.now(),
                    last_messagetime_byV=datetime.now()          
                )
                gp.save()

            welcome_message = TextSendMessage(text='您好～我是UncleBOT, 請多多指教!')
            line_bot_api.reply_message(event.reply_token, welcome_message) 
    
            logger.info('Done')



@handler.add(FollowEvent)
def handle_follow(event):
    # 取得使用者資料
    logger.info('1, start')
    profile = line_bot_api.get_profile(event.source.user_id)

    name = profile.display_name
    uid = profile.user_id
    pic = profile.picture_url
    stat = profile.status_message

    if Lineuser.objects.filter(userid = uid).exists():
        lui=Lineuser.objects.get(userid = uid)       
        if name and pic and stat:
            lui.displayname=name
            lui.pic_url=pic
            lui.stat_message=stat
            lui.updated_at=datetime.now()
            lui.save(update_fields=[ 'displayname', 'pic_url', 'stat_message', 'updated_at'])
        elif name and pic and not stat:
            lui.displayname=name
            lui.pic_url=pic
            lui.updated_at=datetime.now()
            lui.save(update_fields=['displayname', 'pic_url', 'updated_at'])
        elif name and stat and not pic:
            lui.displayname=name
            lui.stat_message=stat
            lui.updated_at=datetime.now()
            lui.save(update_fields=['displayname', 'stat_message', 'updated_at'])
        elif stat and pic and not name:
            lui.pic_url=pic
            lui.stat_message=stat
            lui.updated_at=datetime.now()
            lui.save(update_fields=['pic_url', 'stat_message', 'updated_at'])
        elif name and not pic and not stat:
            lui.displayname=name
            lui.updated_at=datetime.now()
            lui.save(update_fields=['displayname', 'updated_at'])
        elif pic and not name and not stat:
            lui.pic_url=pic
            lui.updated_at=datetime.now()
            lui.save(update_fields=['pic_url', 'updated_at'])
        elif stat and not pic and not name:
            lui.stat_message=stat
            lui.updated_at=datetime.now()
            lui.save(update_fields=['stat_message', 'updated_at'])
        else:
            pass
    else:
        if name and pic and stat:
            ui = Lineuser(userid=uid, displayname=name, pic_url=pic, stat_message=stat, created_at=datetime.now(), last_req=datetime.now() )
        elif name and pic and not stat:
            ui = Lineuser(userid=uid, displayname=name, pic_url=pic, created_at=datetime.now(), last_req=datetime.now() )
        elif name and stat and not pic:
            ui = Lineuser(userid=uid, displayname=name, stat_message=stat, created_at=datetime.now(), last_req=datetime.now() )
        elif stat and pic and not name:
            ui = Lineuser(userid=uid, pic_url=pic, stat_message=stat, created_at=datetime.now(), last_req=datetime.now() )
        elif name and not pic and not stat:
            ui = Lineuser(userid=uid, displayname=name, created_at=datetime.now(), last_req=datetime.now() )
        elif pic and not name and not stat:
            ui = Lineuser(userid=uid, pic_url=pic, created_at=datetime.now(), last_req=datetime.now() )
        elif stat and not pic and not name:
            ui = Lineuser(userid=uid, stat_message=stat, created_at=datetime.now(), last_req=datetime.now() )
        else:
            pass

        ui.save()
        logger.info('1, done')



#收到
@handler.add(MessageEvent, message=(StickerMessage,TextMessage, ImageMessage, VideoMessage, AudioMessage))
def handle_message(event):
    #regular_reply = '感謝您的訊息，但很抱歉，本帳號無法個別回覆用戶的訊息\udbc0\udc0d，敬請期待我們下次發送的訊息內容。  \udbc0\udc30   有任何問題歡迎來信 service@style-info.com   \udbc0\udc0b'
    #line_bot_api.reply_message(event.reply_token, TextSendMessage(text=regular_reply))
    
    #logger.info("received sticker")
    receive_type=json.loads(str(event.source))['type']
    logger.info(receive_type)
    if receive_type=='group':
        user_id=json.loads(str(event.source))['userId']
        group_id=json.loads(str(event.source))['groupId']
    #logger.info(user_id)
        try:
            profile=line_bot_api.get_group_member_profile(group_id, user_id)
            #logger.info(profile)
            #logger.info(group_id)
            check_vendor_user(group_id, user_id, profile.display_name)
        except LineBotApiError as e:
            logger.info(e)

        try:

            wording_check(group_id, event.message, event.reply_token)

        except Exception as e:
            logger.info(e)
    else:
        regular_reply = '感謝您的訊息，但很抱歉，本帳號無法個別回覆用戶的訊息\udbc0\udc0d，敬請期待我們下次發送的訊息內容。\udbc0\udc0b'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=regular_reply))



@handler.add(LeaveEvent)
def leave_event(event):
    try:
        #logger.info(event)
        event_type=json.loads(str(event.source))['type']
        if event_type=='group':
            group_id = json.loads(str(event.source))['groupId']
        #logger.info(group_id)
            gro=Group.objects.get(group_id = group_id)       
            gro.active=False
            gro.save(update_fields=[ 'active'])
        else:
            pass
    except Exception as e:
        logger.info(e)


#成員離開
@handler.add(MemberLeftEvent)
def member_leave_event(event):
    try:
        #logger.info(event)
        event_type=json.loads(str(event.source))['type']
        if event_type=='group':
            group_id = json.loads(str(event.source))['groupId']
            user_id=json.loads(str(event.left))['members'][0]['userId']
        #logger.info(group_id)
            check_vendor_left(group_id, user_id)

        else:
            pass
    except Exception as e:
        logger.info(e)

#成員加入
@handler.add(MemberJoinedEvent)
def member_join_event(event):
    try:
        #logger.info(event)
        event_type=json.loads(str(event.source))['type']
        if event_type=='group':
            group_id = json.loads(str(event.source))['groupId']
            #user_id=json.loads(str(event.left))['members'][0]['userId']
        #logger.info(group_id)
            someone_join(group_id)

        else:
            pass
    except Exception as e:
        logger.info(e)



#def push_test(request):
    #weekly_test()
    #test5()