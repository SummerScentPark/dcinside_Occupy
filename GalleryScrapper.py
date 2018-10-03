import datetime
import requests
from bs4 import BeautifulSoup
from operator import itemgetter
import copy

    
def scrap_gallery(minor, gall_id, init_page, d_day):
    posts_d_day = []
    count = 0
    page_num = init_page
    ## Loop 탈출 조건
    ## - D-day 이전에 작성된 post가 20개 이상 확인 된 경우 (과거에 등록된 공지가 해제된 경우를 대비)
    ## - 탐색시작 페이지부터 50페이지 이상 탐색 한 경우
    while count < 20 and page_num - init_page < 50:
        sourcecode = get_sourcecode(minor, gall_id, page_num)
        posts = read_posts(sourcecode)
        for post in posts:
            info = extract_information(post)
            if info:
                date_difference = compare_date(info['date'], d_day)
                ## D-day에 작성된 post일 경우 list에 추가
                if date_difference == 0:
                    posts_d_day.append(info)
                elif date_difference < 0:
                    count = count + 1
        print(page_num,'page 탐색완료!')
        page_num = page_num + 1
    posts_d_day.sort(key=itemgetter('number'))        
    return posts_d_day


def get_sourcecode(minor, gall_id, page_num):
    headers = {
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'),
    }
    if minor : 
        url = 'http://gall.dcinside.com/mgallery/board/lists/'  
    else: 
        url = 'http://gall.dcinside.com/board/lists/'
    params = { 'id' : gall_id, 'page' : str(page_num) }     
    html = requests.get( url, headers = headers, params = params ).text
    return BeautifulSoup(html, 'html.parser')


def read_posts(sourcecode):
    return sourcecode.select('tbody .ub-content')  


def extract_information(post):
    info = {}  
    info['number'] = post.get('data-no')
    info['title'] = post.select('.gall_tit a')[0].text
    user = post.select('.gall_writer')[0]
    info['uid'] = user.get('data-uid')
    ## (반)고닉이 아니면 user-id 속성값이 없다.
    ## 유동닉은 ip를 id로 간주한다.
    if not info['uid']:
        info['uid'] = user.get('data-ip')
    info['nick'] = user.get('data-nick')
    time = post.select('.gall_date')[0].get('title')
    ## 운영자에 의한 공지 post에는 class='gall_date'가 없다.
    ## 운영자 공지는 어차피 수집할 필요가 없는 post이므로, 리턴하지 않는다.
    if time:
        info['date'] = datetime.date(int(time[0:4]), int(time[5:7]), int(time[8:10]))
        info['time'] = datetime.time(int(time[11:13]), int(time[14:16]), 0)
        return info


def compare_date(post_date, d_day):
    d_day = datetime.date(int(d_day[0:4]), int(d_day[5:7]), int(d_day[8:10]))
    return (post_date - d_day).days 


def filter_occupiers(post_list, period):
    ## post_list : D-day에 작성된 post 정보의 dict를 담은 list
    ## post_list는 글 number(작성시간)순으로 오름차순 정렬 되어 있다.
    occupiers = []
    i_beg = -1
    i_end = -1
    ## 첫 번째 post부터 다음 post와 비교 ("총 post개수 - 1" 만큼 반복)
    for i in range(len(post_list)-1):
        ## 인접한 두 post의 작성자가 같으면
        if post_list[i]['uid']== post_list[i+1]['uid']:
            ## 동일 작성자의 첫 번째 post일 경우, index_begin 저장
            ## 첫 번째 post가 아닐 경우, 아무것도 하지 않는다.
            if i_beg < 0:
                i_beg = i
        ## 인접한 두 post의 작성자가 다르면
        else:
            ## index_begin에 값이 있으면, 현재 post가 동일한 작성자의 마지막 post임을 의미한다.
            ## index_end 저장
            if i_beg >= 0:
                i_end = i
                temp = {}
                duration = post_list[i_end]['time'].hour*60 + post_list[i_end]['time'].minute - post_list[i_beg]['time'].hour*60 - post_list[i_beg]['time'].minute
                ## begin과 end 사이의 시간차이가 기준치(ex, 10분) 이상일 경우, 점령자로 발탁 
                if duration >= period and not ip_is_tongp(post_list[i]['uid']):
                    temp['uid'] = post_list[i]['uid']
                    temp['i_beg'] = i_beg
                    temp['i_end'] = i_end
                    temp['duration'] = duration
                    occupiers.append(temp)
            i_beg = -1
            i_end = -1
    return occupiers


def ip_is_tongp(ip):
    ## 나무위키 '통신사 IP' 기준
    SK_3G = ['203.226', '211.234']
    if SK_3G.count(ip) > 0:
        return 'SK_3G'
    KT_3G = ['39.7', '110.70', '175.223', '175.252', '211.246']
    if KT_3G.count(ip) > 0:
        return 'KT_3G'
    LG_3G = ['61.43', '211.234']
    if LG_3G.count(ip) > 0:
        return 'LG_3G'
    SK_LTE = ['115.161', '121.190', '122.202', '122.32', '175.202', '223.32', 
              '223.33', '223.62', '223.38', '223.39', '223.57']
    if SK_LTE.count(ip) > 0:
        return 'SK_LTE'
    KT_LTE = ['39.7', '110.70', '175.223', '175.252', '210.125', '211.246']
    if KT_LTE.count(ip) > 0:
        return 'KT_LTE'
    LG_LTE = ['114.200', '117.111', '211.36', '106.102', '125.188'] 
    if LG_LTE.count(ip) > 0:
        return 'LG_LTE'  


def summarize(occupiers):
    occupiers.sort(key=itemgetter('uid'))
    summary = []
    for occupier in occupiers:    
        if len(summary) == 0:
            temp = copy.deepcopy(occupier)
            summary.append(temp)
        else:
            if summary[-1]['uid'] == occupier['uid']:
                summary[-1]['duration'] += occupier['duration']
                summary[-1]['i_end'] = occupier['i_end']
            else:
                temp = copy.deepcopy(occupier)
                summary.append(temp)
    summary.sort(key=itemgetter('duration'), reverse=True)
    return summary


def make_log(occupiers, info, summary):
    log = d_day + '\n' + '"' + gall_id + '"' + ' 갤러리 점령!' + '\n\n'
    for idx,report in enumerate(summary):
        log += "%02d"%(idx+1) + '위: ' + '%03d'%(report['duration']) + '분  by ' + info[report['i_end']]['nick'] + ' ' + report['uid'] + '\n'

    time_gap = datetime.timedelta(hours=9)
    kor_time = datetime.datetime.utcnow() + time_gap
    log += '\n기준시간 : ' + str(kor_time) + '\n\n' 
    occupiers.sort(key=itemgetter('i_beg'))
    for occupier in occupiers:
        log += '-' + occupier['uid'] + ' {}분'.format(occupier['duration']) + '\n'
        for i in range(int(occupier['i_beg']), int(occupier['i_end'])+1):
            log += '{:02d}:{:02d}'.format(info[i]['time'].hour, info[i]['time'].minute) + ' #{}'.format(info[i]['number']) + '  ' + info[i]['title'] + '\n'
        log += '\n'
    log += '\n'
    return log


minor = True
gall_id = 'nuguri'
init_page = 1
d_day = '2018.10.03'
period = 10

G_info = scrap_gallery(minor, gall_id, init_page, d_day)
G_info.sort(key=itemgetter('number'))
G_occupiers = filter_occupiers(G_info, period)
G_Summary = summarize(G_occupiers)
log = make_log(G_occupiers, G_info, G_Summary)
print('\n')
print(log)   