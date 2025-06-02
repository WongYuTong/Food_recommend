// 切換回覆表單的顯示和隱藏
function toggleReplyForm(formId) {
    const form = document.getElementById(formId);
    if (form.style.display === 'none') {
        form.style.display = 'block';
    } else {
        form.style.display = 'none';
    }
}

// 添加表情符號反應
function addReaction(reactionType, postId, csrfToken) {
    fetch(`/post/${postId}/reaction/add/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `reaction_type=${reactionType}`
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            updateReactionsUI(data.reactions_count, data.total_reactions, reactionType);
        }
    });
}

// 移除表情符號反應
function removeReaction(postId, csrfToken) {
    fetch(`/post/${postId}/reaction/remove/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            updateReactionsUI(data.reactions_count, data.total_reactions, null);
        }
    });
}

// 更新UI中的表情符號反應
function updateReactionsUI(reactionsCount, totalReactions, userReaction) {
    // 更新總反應數量
    const reactionsSummary = document.getElementById('reactions-summary');
    if (totalReactions > 0) {
        reactionsSummary.querySelector('.text-muted').textContent = `${totalReactions} 人反應`;
        reactionsSummary.style.display = 'block';
        
        // 更新各表情符號數量標籤
        for (const type in reactionsCount) {
            const badge = reactionsSummary.querySelector(`[title="${type}"]`);
            if (reactionsCount[type] > 0) {
                if (badge) {
                    badge.querySelector('.reaction-count').textContent = reactionsCount[type];
                } else {
                    // 如果不存在這個表情的標籤，可以考慮創建一個
                    // 但這比較複雜，這裡不實現
                }
            } else if (badge) {
                badge.remove();
            }
        }
    } else {
        reactionsSummary.style.display = 'none';
    }
    
    // 更新反應按鈕顯示
    const reactionButton = document.getElementById('reaction-button');
    
    // 更新下拉選單中的數量
    const dropdownItems = document.querySelectorAll('.reaction-btn');
    dropdownItems.forEach(item => {
        const type = item.getAttribute('data-reaction');
        const countBadge = item.querySelector('.badge');
        if (countBadge) {
            countBadge.textContent = reactionsCount[type] || '0';
        }
    });
    
    // 更新用戶的反應按鈕
    if (userReaction) {
        const reactionIcons = {
            'like': '👍 讚',
            'love': '❤️ 愛心',
            'haha': '😄 哈哈',
            'wow': '😲 哇',
            'sad': '😢 傷心',
            'angry': '😠 怒'
        };
        reactionButton.innerHTML = reactionIcons[userReaction];
        
        // 顯示移除反應選項
        document.querySelectorAll('#remove-reaction-option').forEach(el => {
            el.style.display = 'block';
        });
    } else {
        reactionButton.innerHTML = '<i class="far fa-smile me-1"></i> 表情';
        
        // 隱藏移除反應選項
        document.querySelectorAll('#remove-reaction-option').forEach(el => {
            el.style.display = 'none';
        });
    }
}

// 收藏/取消收藏貼文
function toggleFavorite(postId, csrfToken) {
    fetch(`/favorite/${postId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            const favoriteButton = document.getElementById('favorite-button');
            const favoriteText = document.getElementById('favorite-text');
            
            if(data.is_favorite) {
                favoriteButton.classList.replace('btn-outline-danger', 'btn-danger');
                favoriteText.textContent = '取消收藏';
            } else {
                favoriteButton.classList.replace('btn-danger', 'btn-outline-danger');
                favoriteText.textContent = '收藏';
            }
        }
    });
}

// 分享貼文
function sharePost(postTitle) {
    const shareUrl = window.location.href;
    
    if (navigator.share) {
        navigator.share({
            title: postTitle,
            url: shareUrl
        }).catch(error => {
            console.error('分享失敗:', error);
            fallbackShare(shareUrl);
        });
    } else {
        fallbackShare(shareUrl);
    }
}

// 後備分享方法
function fallbackShare(url) {
    // 創建一個臨時輸入框
    const input = document.createElement('input');
    input.value = url;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    document.body.removeChild(input);
    
    alert('連結已複製到剪貼簿！');
}

// 初始化地圖
function initMap(lat, lng, locationName) {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;
    
    const position = { lat, lng };
    const map = new google.maps.Map(mapElement, {
        zoom: 15,
        center: position,
    });
    
    const marker = new google.maps.Marker({
        position: position,
        map: map,
        title: locationName
    });
    
    const infowindow = new google.maps.InfoWindow({
        content: `<div><strong>${locationName}</strong></div>`
    });
    
    marker.addListener('click', function() {
        infowindow.open(map, marker);
    });
} 