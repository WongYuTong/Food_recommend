/**
 * 註冊頁面的JavaScript功能
 */
document.addEventListener('DOMContentLoaded', function() {
    // 為表單輸入添加Bootstrap樣式
    const usernameField = document.getElementById('id_username');
    const emailField = document.getElementById('id_email');
    const password1Field = document.getElementById('id_password1');
    const password2Field = document.getElementById('id_password2');
    
    if(usernameField) {
        usernameField.classList.add('form-control');
        usernameField.setAttribute('placeholder', '選擇一個用戶名');
    }
    
    if(emailField) {
        emailField.classList.add('form-control');
        emailField.setAttribute('placeholder', '輸入您的電子郵件');
    }
    
    if(password1Field) {
        password1Field.classList.add('form-control');
        password1Field.setAttribute('placeholder', '創建一個密碼');
    }
    
    if(password2Field) {
        password2Field.classList.add('form-control');
        password2Field.setAttribute('placeholder', '再次輸入您的密碼');
    }
    
    // 為單選按鈕添加樣式
    const radioButtons = document.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(function(radio) {
        radio.classList.add('form-check-input');
        const label = radio.nextSibling;
        if(label) {
            label.classList.add('form-check-label');
        }
    });

    // 商家註冊導向驗證頁面
    const form = document.querySelector('form');
    if(form) {
        form.addEventListener('submit', function(e) {
            // 檢查是否選擇了商家帳號類型
            const businessRadio = document.querySelector('input[name="user_type"][value="business"]');
            if(businessRadio && businessRadio.checked) {
                // 我們不阻止表單提交，而是在後端處理重定向
                // 這裡只做標記，提醒用戶註冊成功後需要進行驗證
                localStorage.setItem('redirect_to_verification', 'true');
            }
        });
    }
}); 