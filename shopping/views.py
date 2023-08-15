from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib.auth.decorators import *
from django.http import HttpResponse
import json
from datetime import datetime, timedelta
from .models import Product
from users.models import Restaurant
from django.http import JsonResponse

# 배송날짜 계산 함수
def get_next_business_day(current_date):
    # 현재 날짜에서 2일을 더한 날짜를 계산
    target_date = current_date + timedelta(days=2)
    
    # 일요일을 제외한 다음 영업일을 찾음
    while target_date.weekday() in [6]: 
        target_date += timedelta(days=1)
    
    return target_date

# 메인페이지
def index(request):
    products=Product.objects.all()
    if request.method=="POST":
        search=request.POST['search']
        products=Product.objects.filter(title__contains=search)
    # 상품이 있는 경우 best 초기화 
    if products:
        best=products[0]
    else:
        best=None
    for p in products:
        if p.like_product.count() > best.like_product.count():
            best=p
    return render(request, 'shopping/index.html',{'products':products,'best':best})

    
# 상품 등록
def upload(request):
    if request.method=='GET':
        return render(request, 'shopping/upload.html')
    else:
        product=Product()
        title=request.POST['title']
        price=int(request.POST['price'])
        origin=request.POST['origin']
        feature=request.POST['feature']
        type=request.POST['type']
        total_quantity=int(request.POST['total_quantity'])
        discount_rate=int(request.POST['discount_rate'])
        product.title=title
        product.type=type
        product.total_quantity=total_quantity
        product.discount_rate=discount_rate
        product.price=price
        product.production_features=feature
        product.origin=origin
        product.discount_rate=discount_rate
        product.seller=request.user.merchant
        product.save()
        # 여러 이미지 저장 
        for img in request.FILES.getlist('imgs'):
            photo = Photo()
            photo.product = product
            photo.image = img
            photo.save()
        
        return redirect('index')
    
# 상품 상세페이지
def detail(request, id):
    product = get_object_or_404(Product, id=id)
    discount_rate = product.discount_rate or 0
    discount_price = product.price * (1 - discount_rate / 100)
    if request.method == 'POST':

        action = request.POST.get('action')

        # 절반만 구매하기 버튼을 누른 경우 > 결제 화면과 연결 
        if action == 'half_purchase':
            return redirect('kakao:kakaoPay')
        
        # 절반만 구매하기 +장바구니 버튼 선택 
        elif action== "half_goto_basket":
            total_quantity = int(request.POST.get('total_quantity'))
            user_id = request.user.id
            user = User.objects.get(pk=user_id)

            ShoppingBasket.objects.create(half_purchased=True, customer=user, product=product, quantity= total_quantity/2)
            
        # 장바구니에 디폴트 구매하기 옵션 선택 > 결제 화면과 연결 
        if action == 'purchase':
            return redirect('kakao:kakaoPay')
        
        # 한번에 결제 + 장바구니 버튼
        elif action == 'goto_basket':
            quantity = request.POST.get('quantity')
            user_id = request.user.id
            quantity = int(quantity)
            user = User.objects.get(pk=user_id)
            order, created = ShoppingBasket.objects.get_or_create(customer=user, product=product, defaults={'quantity': quantity})
        
            # 장바구니에 이미 기존의 상품이 있는 경우 수량 +n
            if not created:
                order.quantity += quantity
                order.save()

    return render(request, 'shopping/detail.html', {'product': product,'discount_price': discount_price})

# 좋아요
def add_remove_whishlist(request): 
    # ajax 요청만 처리 
    if request.method == "POST" and request.is_ajax():
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        user = request.user
        liked = False

        if product in user.like_product.all():
            # 이미 좋아요한 상품이라면 제거
            user.like_product.remove(product)
        else:
            # 아직 좋아요하지 않은 상품이라면 추가
            user.like_product.add(product)
            liked = True

        return JsonResponse({"liked": liked})
    return JsonResponse({}, status=400)

# 마이페이지
def mypage(request):
    products=request.user.like_product.all()
    return render(request,'shopping/mypage.html',{'products':products})

# 내 상품 조회
def my_product(request):
    products=Product.objects.filter(seller=request.user.merchant)
    return render(request,'shopping/my_product.html',{'products':products})

# 찜한 목록 조회
def wishlist(request):
    products=request.user.like_product.all()
    return render(request,'shopping/wishlist.html',{'products':products})

# 정보 수정
def update_user(request):
    if request.method=="GET":
        return render(request,'shopping/update_user.html')
    else:
        description=request.POST['description']
        farm_name=request.POST['farm_name']
        new_image=request.FILES.get('image')
        user=Merchant.objects.get(user=request.user)
        if new_image:
            if user.image != 'Koala.png':
                user.image.delete()
                user.image=new_image
        user.description=description
        user.farm_name=farm_name
        user.save()
        return redirect('mypage')
    
# 등록 상품 삭제
def delete_product(reuqest,id):
    product=get_object_or_404(Product, id=id)
    product.delete()
    return redirect('my_product')

# 상품 등록 수정
def update_upload(request, id):
    product=get_object_or_404(Product, id=id)
    if request.method=="GET":
        return render(request,'shopping/update_upload.html',{'product':product})
    else:
        title=request.POST['title']
        price=int(request.POST['price'])
        origin=request.POST['origin']
        feature=request.POST['feature']
        type=request.POST['type']
        total_quantity=int(request.POST['total_quantity'])
        discount_rate=int(request.POST['discount_rate'])
        print(total_quantity)
        product.title=title
        product.price=price
        product.origin=origin
        product.total_quantity=total_quantity
        product.discount_rate=discount_rate
        product.production_features=feature
        product.type=type
        product.save()
        if request.FILES.getlist('imgs'):
            for img in product.product_image.all():
                img.delete()
            for img in request.FILES.getlist('imgs'):
                photo = Photo()
                photo.product = product
                photo.image = img
            photo.save()
        return redirect('my_product')

# 장바구니
def basket(request):
    products = ShoppingBasket.objects.filter(customer=request.user)
    total_price=0
    for p in products:
        if p.half_purchased==True:
            total_price+=p.product.discounted_price * p.quantity*2
        else:
            total_price+=p.product.discounted_price
    current_date = datetime.now().date()
    # 배송 도착일 설정 
    arrive_day = get_next_business_day(current_date)

    # 결제하기 버튼 >> 결제 화면과 연결 
    return render(request, 'shopping/basket.html', {'products': products, 'total_p': total_price, 'arrive_day':arrive_day})

# 장바구니 삭제
def basket_delete(request, id):
    product = get_object_or_404(Product, id=id)
    order = ShoppingBasket.objects.get(product=product)
    order.delete()
    return redirect('basket')

# 절반만 구매했던 상품 필터링 > 구매한 후랑 연결 
def half_purchased_products(request):
    half_purchased_products = Storage.objects.filter(basket_product__customer=request.user)
    
    context = {
        'half_purchased_products': half_purchased_products,
    }
    return render(request, 'shopping/half_purchased)products.html', context)

# 장바구니에서 구매 >> post 참고..
def final(request):
    if request.method == "POST":
        selected_products = request.POST.getlist('selected_products')
        total_price = 0
        products = ShoppingBasket.objects.filter(customer=request.user, product__id__in=selected_products)
        request.session['selected_products'] = selected_products  # 선택한 제품의 ID 리스트 저장
        for p in products:
            total_price += p.product.price * p.quantity
        