import requests
from urllib.parse import urlencode
from requests import codes
import os
import re
from hashlib import md5
from Crypto.Cipher import AES
import base64
import json
import time
import math
import random
import codecs
from xpinyin import Pinyin
import jieba
from jieba import analyse
from wordcloud import WordCloud,STOPWORDS
from scipy.misc import imread
import matplotlib.pyplot as plt
import sys


class WangYiYun():
    def __init__(self,d):
        self.d = str(d)
        self.g = '0CoJUm6Qyw8W8jud'
        self.e = '010001'
        self.f = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
    def get_random_str(self):
        res=''
        str='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        for x in range(16):
            index = math.floor(random.random()*len(str))
            res += str[index]
        return res
    def aes_encrypt(self,text,key):
        iv =b'0102030405060708'
        b_key=key.encode('utf-8')
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(b_key,AES.MODE_CBC,iv)
        msg = base64.b64encode(encryptor.encrypt(text.encode('utf-8')))
        return msg
    def rsa_encrypt(self,value,text,modulus):
        text = text[::-1]
        rs = int(codecs.encode(text.encode('utf-8'),'hex_codec'),16)**int(value,16)%int(modulus,16)
        return format(rs,'x').zfill(256)
    def get_data(self):
        random_text = self.get_random_str()
        params = self.aes_encrypt(self.d,self.g)
        params = self.aes_encrypt(params.decode('utf-8'),random_text).decode('utf-8')
        encseckey = self.rsa_encrypt(self.e,random_text,self.f)
        return {
            'params':str(params),
            'encSecKey':str(encseckey)
            }
    
def get_song_id(song_name):
    headers={
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.33 Safari/537.36',
        'Referer':'https://music.163.com/search/'
        }
    proxies= {
         'http:':'http://114.99.7.122:8752',
         'https:':'https://114.99.7.122.8752'
         }
    url='https://music.163.com/weapi/cloudsearch/get/web?csrf_token='
    d = '{"hlpretag":"<span class=\\"s-fc7\\">","hlposttag":"</span>","s":"'+str(song_name)+'","type":"1","offset":"0","total":"true","limit":"30","csrf_token":""}'
    wyy=WangYiYun(d)
    data=wyy.get_data()
    try:
        response = requests.post(url,headers=headers,data=data,proxies=proxies)
        if codes.ok == response.status_code:
            m=response.json().get('result')
            songs=m.get('songs')
            for item in songs:
                name=item.get('name')
                song_id=item.get('id')
                author=item.get('ar')
                for k in author:
                    author_name=k.get('name')
                yield {
                    'name':name,
                    'id':song_id,
                    'author':author_name
                    }
    except requests.ConnectionError:
        return None

def save_song(song_id,song_name,author):
    author=str(author)
    headers={
        'Referer':'https://music.163.com/search/',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.33 Safari/537.36',
        }
    proxies= {
         'http:':'http://114.99.7.122:8752',
         'https:':'https://114.99.7.122.8752'
         }
    url='https://music.163.com/weapi/song/enhance/player/url?csrf_token='
    d='{"ids":"['+ str(song_id) + ']","br":128000,"csrf_token":""}'
    wyy=WangYiYun(d)
    data=wyy.get_data()
    response = requests.post(url,data=data,headers=headers,proxies=proxies).json().get('data')
    for item in response:
        song=item.get('url')
        song_path = '网易云音乐'+ os.path.sep + str(song_name)
        if not os.path.exists(song_path):
            os.makedirs(song_path)
        try:
            resp = requests.get(str(song))
            if codes.ok == resp.status_code:
                file_path = song_path + os.path.sep + '{file_name}.{file_suffix}'.format(
                    file_name=song_name+'('+author+')',
                    file_suffix='mp3')
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f:
                        f.write(resp.content)
                    get_lrc(song_path,song_id,song_name,author)
                    print('Downloaded song path is %s' % file_path)
                    print('\n歌曲下载成功！\n')
                else:
                    print('检测到该歌曲已经下载过……', file_path)
        except requests.exceptions.MissingSchema:
            print('下载失败！该歌曲暂时不支持下载！')

def get_hotcomments(song_id,song_name,author):
    author=str(author)
    headers={
        'Referer':'https://music.163.com/search/',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.33 Safari/537.36',
        }
    proxies= {
         'http:':'http://114.99.7.122:8752',
         'https:':'https://114.99.7.122.8752'
         }
    url='https://music.163.com/weapi/v1/resource/comments/R_SO_4_'+str(song_id)+'?csrf_token='
    d='{"rid":"R_SO_4_'+str(song_id)+'","offset":"0","total":"true","limit":"20","csrf_token":""}'
    wyy=WangYiYun(d)
    data=wyy.get_data()
    response=requests.post(url,data=data,headers=headers,proxies=proxies).json()
    path = '网易云音乐'+ os.path.sep + str(song_name)
    save_path=path+ os.path.sep +'{file_name}.{file_suffix}'.format(file_name=song_name+'('+author+')',file_suffix='txt')
    if not os.path.exists(path):
            os.makedirs(path)         
    if response.get('hotComments'):
        hotcomments=response.get('hotComments')
    with open(path+'\\'+str(song_name)+'('+author+')'+'.txt','w+',encoding='utf-8') as f:
        f.write('热门评论：\n\n')
        f.close()
    non_bmp_map=dict.fromkeys(range(0x10000,sys.maxunicode+1),0xfffd)
    for item in hotcomments:
        content=str(json.dumps(item.get('content'),ensure_ascii=False)).replace('\\n','\n')+'\n'+'-'*40 +'\n'
        content=content.translate(non_bmp_map)
        print(content)
        with open(save_path,'a',encoding='utf-8') as f:
            f.write(content)
            f.close()
    return(int(response.get('total')))
                
def get_comments(total,song_id,song_name,author):
    author=str(author)
    headers={
        'Referer':'https://music.163.com/search/',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.33 Safari/537.36',
        }
    proxies= {
         'http:':'http://114.99.7.122:8752',
         'https:':'https://114.99.7.122.8752'
         }
    url='https://music.163.com/weapi/v1/resource/comments/R_SO_4_'+str(song_id)+'?csrf_token='
    offset=0
    path = '网易云音乐'+ os.path.sep + str(song_name)
    save_path=path+ os.path.sep +'{file_name}.{file_suffix}'.format(file_name=song_name+'('+author+')',file_suffix='txt')
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    with open(save_path,'a',encoding='utf-8') as f:
        f.write('普通评论：\n\n')
        f.close()
    while offset<total :
        d='{"rid":"R_SO_4_'+str(song_id)+'","offset":"'+str(offset)+'","total":"true","limit":"20","csrf_token":""}'
        wyy=WangYiYun(d)
        data=wyy.get_data()
        response=requests.post(url,data=data,headers=headers,proxies=proxies).json()
        comments=response.get('comments')
        non_bmp_map=dict.fromkeys(range(0x10000,sys.maxunicode+1),0xfffd)
        for item in comments:
            content=str(json.dumps(item.get('content'),ensure_ascii=False)).replace('\\n','\n')+'\n'+'-'*40 +'\n'
            content=content.translate(non_bmp_map)
            print(content)
            with open(save_path,'a',encoding='utf-8') as f:
                f.write(content)
                f.close()
        offset=offset+20
    m=input('评论获取成功！\n\n是否生成词云(需使用一张图片作为背景图案)：\n1、是\n2、否\n请输入选择序号：\n')
    if(m=='1'):
        get_wordcloud(save_path,path,song_name,author)
    elif(m=='2'):
        print('已退出此功能……')
    else:
        print('输入错误，已自动退出此功能！')

def get_wordcloud(save_path,path,song_name,author):
    author=str(author)
    print('\n请保证使用图片的保存位置与本程序的保存位置相同！！！\n否则程序将无法正常运行！！！\n')
    picture=input('请输入使用图片名称（例：picture.jpg）：\n')
    color_mask=imread(picture)
    with open(save_path,'r',encoding='utf-8') as f:
        string = f.read()
        words=' '.join(jieba.cut(string))
        top_words = analyse.textrank(words, topK=400, withWeight=True)
        ret_words = {}
        for word in top_words:
            ret_words[word[0]] = word[1]
        wordcloud = WordCloud(background_color='white',mask=color_mask,max_words=100,stopwords=STOPWORDS,font_path= 'C:\Windows\Fonts\simkai.ttf',max_font_size=100,random_state=30,margin=2)
        wc=wordcloud.generate_from_frequencies(frequencies=ret_words)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    save_path=path+ os.path.sep +'{file_name}.{file_suffix}'.format(file_name=song_name+'('+author+')',file_suffix='jpg')
    wc.to_file(save_path)
    plt.show()

def get_lrc(path,song_id,song_name,author):
    author=str(author)
    headers={
        'Referer':'https://music.163.com/search/',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.33 Safari/537.36',
        }
    proxies= {
         'http:':'http://114.99.7.122:8752',
         'https:':'https://114.99.7.122.8752'
         }
    url='https://music.163.com/weapi/song/lyric?csrf_token='
    d='{"id":"'+str(song_id)+'","lv":-1,"tv":-1,"csrf_token":""}'
    wyy=WangYiYun(d)
    data=wyy.get_data()
    response=requests.post(url,data=data,headers=headers,proxies=proxies).json()
    lyric=response.get('lrc').get('lyric')
    lrc=str(lyric).split('\n')
    LRC=lrc[0]
    if LRC[1:3]=='by':
        del lrc[0]
    if (response.get('tlyric').get('lyric') != None):
        tlyric=str(response.get('tlyric').get('lyric')).split('\n')
        if tlyric[0][1:3]=='by':
            del tlyric[0]
        with open(path+'\\'+str(song_name)+'('+author+')'+'.lrc','a',encoding='utf-8') as f:
            i=0
            k=0
            while(i<len(tlyric)):
                f.write(lrc[k]+'\n'+tlyric[i]+'\n')
                if(i+1<len(tlyric)):
                    a=tlyric[i+1]
                    b=lrc[k+1]
                    if(a[0:9]!=b[0:9]):
                        f.write(lrc[k+1]+'\n')
                        k=k+1
                k=k+1
                i=i+1
            f.close()
    else:
        with open(path+'\\'+str(song_name)+'('+author+')'+'.lrc','a',encoding='utf-8') as f:
            for i in range(0,len(lrc)):
                f.write(lrc[i]+'\n')
            f.close()
            
def main():
    song_name=input('请输入要下载的音乐名称：\n')
    pin=Pinyin()
    song_name_pinyin=pin.get_pinyin(song_name,'')
    id_list=[]
    author_list=[]
    information=get_song_id(str(song_name_pinyin))
    i=1
    for item in information:
        L=str(i)+'、'+'  歌曲名称：'+str(item['name'])+'   演唱者：'+str(item['author'])
        print(L)
        i=i+1
        id_list.append(item['id'])
        author_list.append(item['author'])
    k=int(input('请选择要下载的歌曲（输入序号即可）：\n'))
    song_id=(id_list[k-1])
    author=(author_list[k-1])
    save_song(str(song_id),str(song_name),str(author))
    print('是否获取相关评论：\n1、是\n2、否\n')
    m=input('请输入选择序号：\n')
    if(m=='1'):
        total=get_hotcomments(str(song_id),str(song_name),str(author))
        get_comments(total,str(song_id),str(song_name),str(author))
    elif(m=='2'):
        print('已退出本功能！\n')
    else:
        print('输入错误，已自动退出此功能……')

def exit_process():
    key=input('\n是否继续：\n1、是\n2、否\n请输入选择序号：\n')
    return (key)
    
if __name__=='__main__':
    print("\n****************************************************\n")
    print("*******===========欢迎使用本程序!============*******\n")
    print("*******  说明：                              *******\n")
    print("*******     本程序只用于下载网易云上部分     *******\n")
    print("*******     音乐以及相关评论，请按提示输入。 *******\n")
    print("*******     请勿用于非法途径！！！           *******\n")
    print("*******  PS：                                *******\n")
    print("*******     请在下载后对歌曲进行重命         *******\n")
    print("*******     名，以便后续使用！！！           *******\n")
    print("*******                                      *******\n")
    print("*******          版权所有 侵权必究           *******\n")
    print("*******============Copyright By==============*******\n")
    print("*******==============LiuSheng================*******\n")
    print("****************************************************\n")
    while True:
        main()
        key=exit_process()
        if(key=='1'):
            continue
        elif(key=='2'):
            print('退出成功！')
            break
        else:
            print('输入错误！\n已自动继续执行本程序……\n\n')
            
            
        
