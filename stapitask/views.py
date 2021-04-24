from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.shortcuts import render
import requests
from .forms import searchbar
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from ratelimit.decorators import ratelimit

CACHE_TTL = getattr(settings,'CACHE_TTL',DEFAULT_TIMEOUT)

def get_url_data(json_dict):
    data_list = []
    for item in json_dict['items']:        
        data_dict = {}
        data_dict["score"] = item["score"]
        data_dict["title"] = item["title"]
        data_dict["link"] = item["link"]
        data_dict["ByName"] = item["owner"]["display_name"]
        data_dict["Tags"] = item["tags"]
        data_dict["creation_date"] = item["creation_date"]
        data_dict["answer_count"] = item["answer_count"]
        data_list.append(data_dict)
    return data_list


def get_url(search='',sort='',tag=''):
    res = requests.get("https://api.stackexchange.com/" + f"/2.2/search?order=desc&sort={sort}&tagged={tag}&intitle={search}&site=stackoverflow")
    print(search)
    print('request dta')
    data = res.json()
    return get_url_data(data)


@ratelimit(key='ip', rate='5/m', block=True)
@ratelimit(key='ip', rate='100/d', block=True)
def stackresult(request):
    context = {'data':'','x': False}
    data = ''
    
    if not request.method == 'POST' and 'page' in request.GET:
        if 'post' in request.session:
            request.POST = request.session['post']
            request.method = 'POST'

    if request.method == 'POST' or (('tag' in request.POST) or ('relevance' in request.POST) or ('votes' in request.POST) or ('creation' in request.POST)):
        request.session['post'] = request.POST
        context['x']= True
        ques,vm = '',''
        ls = []
       
        if request.method == 'POST' and not (('tag' in request.POST) or ('relevance' in request.POST) or ('votes' in request.POST) or ('creation' in request.POST)):
            ques = request.POST.get('searchbar')
            request.session['ques'] = ques       
            ls.extend((ques,vm))

        elif 'tag' in request.POST:
            ques = request.POST.get('tag')
            request.session['ques'] = ques
            ls.extend((ques,vm))
        
        elif 'relevance' in request.POST:
            ques = request.session['ques']
            vm = 'relevance'
            ls.extend((ques,vm))
   
        elif 'votes' in request.POST:
            ques = request.session['ques']
            vm = 'votes'
            ls.extend((ques,vm))

        elif 'creation' in request.POST:
            ques = request.session['ques']
            vm = 'creation'
            ls.extend((ques,vm))
   
        else:
            ls.clear()
        

        if ques:
            if cache.get(ls):
                data = cache.get(ls)  
                print('cache data')                  
            else:
                if not ques=="":
                    data = get_url(*ls)
                    cache.set(ls,data)
                else:
                    data = get_url(*ls)
        
        context['dt_count']= len(data)
        context['sort']= vm
        context['searchresult'] = request.session['ques']         
    else:
        data = ''

   
        
    pagin = Paginator(data,5)
    page_number = request.GET.get('page')

    try:
        page_obj = pagin.get_page(page_number)
    except PageNotAnInteger:
        page_obj = pagin.get_page(1)
    except EmptyPage:
        page_obj = pagin.get_page(pagin.num_pages)    
    
    context['data'] = page_obj
    return render(request,'home.html',context)

    