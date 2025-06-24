from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Post, BusinessVerification, Comment, Report, Announcement

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    user_type = forms.ChoiceField(choices=[('general', '一般使用者'), ('business', '商家')],
                                widget=forms.RadioSelect, initial='general')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']

class BusinessRegisterForm(UserCreationForm):
    email = forms.EmailField()
    user_type = forms.CharField(initial='business', widget=forms.HiddenInput())
    
    # 商家验证信息字段
    business_name = forms.CharField(max_length=100, label="商家名稱")
    business_registration_number = forms.CharField(max_length=50, label="營業登記號碼")
    business_address = forms.CharField(max_length=200, label="商家地址")
    business_phone = forms.CharField(max_length=20, label="聯絡電話")
    business_email = forms.EmailField(label="商業信箱")
    registration_document = forms.FileField(label="營業登記文件 (PDF檔、JPG或PNG格式)")
    additional_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), 
        required=False, 
        label="補充說明 (可選)"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['business_name'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入商家名稱'})
        self.fields['business_registration_number'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入營業登記號碼'})
        self.fields['business_address'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入商家地址'})
        self.fields['business_phone'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入聯絡電話'})
        self.fields['business_email'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入商業信箱'})
        self.fields['additional_notes'].widget.attrs.update({'class': 'form-control', 'placeholder': '如有其他需要說明的事項，請在此處補充'})
        
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email']
        
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic', 'bio', 'favorite_foods', 'food_restrictions']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': '請簡短介紹自己...'}),
            'favorite_foods': forms.TextInput(attrs={'placeholder': '例如：牛肉麵, 滷肉飯, 壽司'}),
            'food_restrictions': forms.TextInput(attrs={'placeholder': '例如：海鮮過敏, 不吃辣, 素食者'})
        }
        labels = {
            'profile_pic': '個人頭像',
            'bio': '自我介紹',
            'favorite_foods': '喜愛的食物',
            'food_restrictions': '飲食禁忌'
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_pic'].label = "個人頭像"
        self.fields['bio'].label = "自我介紹"
        self.fields['favorite_foods'].label = "喜愛的食物"
        self.fields['food_restrictions'].label = "飲食禁忌"

class BusinessProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic', 'bio', 'business_name', 'business_address', 'business_phone']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_pic'].label = "商家頭像"
        self.fields['bio'].label = "商家簡介"
        self.fields['business_name'].label = "商家名稱"
        self.fields['business_address'].label = "商家地址"
        self.fields['business_phone'].label = "聯絡電話"

class AnnouncementForm(forms.ModelForm):
    """系統公告表單"""
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'announcement_type', 'is_active', 'is_pinned', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入公告標題'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '請輸入公告內容...'
            }),
            'announcement_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
        labels = {
            'title': '公告標題',
            'content': '公告內容',
            'announcement_type': '公告類型',
            'is_active': '立即啟用',
            'is_pinned': '置頂公告',
            'start_date': '開始日期 (可選)',
            'end_date': '結束日期 (可選)'
        }
        help_texts = {
            'is_active': '勾選後公告將立即顯示給所有用戶',
            'is_pinned': '置頂公告將顯示在所有公告的最前面',
            'start_date': '設置公告生效的開始時間，不設置則立即生效',
            'end_date': '設置公告失效的結束時間，不設置則永久有效'
        }

class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'location_name', 'location_address', 'location_lat', 'location_lng', 'location_place_id']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '請輸入標題'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': '分享您的美食經驗...'}),
            'location_name': forms.TextInput(attrs={'placeholder': '餐廳名稱', 'id': 'location-name', 'readonly': 'readonly'}),
            'location_address': forms.TextInput(attrs={'placeholder': '餐廳地址', 'id': 'location-address', 'readonly': 'readonly'}),
            'location_lat': forms.HiddenInput(attrs={'id': 'location-lat'}),
            'location_lng': forms.HiddenInput(attrs={'id': 'location-lng'}),
            'location_place_id': forms.HiddenInput(attrs={'id': 'location-place-id'}),
        }
        labels = {
            'title': '標題',
            'content': '內容',
            'image': '圖片',
            'location_name': '餐廳名稱',
            'location_address': '餐廳地址',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = "標題"
        self.fields['content'].label = "內容"
        self.fields['image'].label = "圖片 (可選)"
        self.fields['location_name'].label = "餐廳名稱 (可選)"
        self.fields['location_address'].label = "餐廳地址 (可選)"
        # 隱藏座標欄位
        self.fields['location_lat'].widget = forms.HiddenInput()
        self.fields['location_lng'].widget = forms.HiddenInput()
        self.fields['location_place_id'].widget = forms.HiddenInput()

class BusinessVerificationForm(forms.ModelForm):
    class Meta:
        model = BusinessVerification
        fields = ['business_name', 'business_registration_number', 'business_address',
                 'business_phone', 'business_email', 'registration_document', 'additional_notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['business_name'].label = "商家名稱"
        self.fields['business_registration_number'].label = "營業登記號碼"
        self.fields['business_address'].label = "商家地址"
        self.fields['business_phone'].label = "聯絡電話"
        self.fields['business_email'].label = "商業信箱"
        self.fields['registration_document'].label = "營業登記文件 (PDF檔)"
        self.fields['additional_notes'].label = "補充說明 (可選)" 
        
        # 添加 Bootstrap 樣式
        self.fields['business_name'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入商家名稱'})
        self.fields['business_registration_number'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入營業登記號碼'})
        self.fields['business_address'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入商家地址'})
        self.fields['business_phone'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入聯絡電話'})
        self.fields['business_email'].widget.attrs.update({'class': 'form-control', 'placeholder': '請輸入商業信箱'})
        self.fields['registration_document'].widget.attrs.update({'class': 'form-control'})
        self.fields['additional_notes'].widget.attrs.update({'class': 'form-control', 'rows': 3, 'placeholder': '如有其他需要說明的事項，請在此處補充'})

class CommentForm(forms.ModelForm):
    """評論表單"""
    content = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'placeholder': '發表您的評論...',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Comment
        fields = ['content']

class ReportForm(forms.ModelForm):
    """回報表單"""
    reason = forms.CharField(
        label='回報原因',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': '請詳細說明回報原因...',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Report
        fields = ['reason'] 