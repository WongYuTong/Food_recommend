document.addEventListener("DOMContentLoaded", function() {
    var map = L.map('taiwanMap').setView([23.7, 121], 7.2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    var cityStats = JSON.parse(document.getElementById('city-stats-data').textContent);
    var cityPosts = JSON.parse(document.getElementById('city-posts-data').textContent);
    // 新增：取得用餐記錄資料
    var cityRecords = {};
    var cityRecordsScript = document.getElementById('city-records-data');
    if (cityRecordsScript) {
        cityRecords = JSON.parse(cityRecordsScript.textContent);
    }
    var geojsonUrl = document.getElementById('taiwanMap').dataset.geojsonUrl;

    function getColor(d) {
        return d > 20 ? '#00441b' :
               d > 10 ? '#238b45' :
               d > 5  ? '#41ae76' :
               d > 0  ? '#66c2a4' :
                        '#ccece6';
    }

    function showCityPosts(city) {
        console.log('showCityPosts:', city, cityPosts[city]);
        var posts = cityPosts[city] || [];
        var container = document.getElementById('cityPosts');
        var postsHtml = '';
        if (posts.length === 0) {
            postsHtml = `<div class="text-muted">尚無貼文</div>`;
        } else {
            postsHtml = `<h6 class="mb-2">${city} 貼文：</h6><ul class="list-group mb-2">` +
                posts.map(p => `<li class="list-group-item">${p}</li>`).join('') +
                `</ul>`;
        }
        container.innerHTML = postsHtml;
    }

    fetch(geojsonUrl)
    .then(response => response.json())
    .then(geojsonData => {
        L.geoJson(geojsonData, {
            style: function(feature) {
                var name = feature.properties.COUNTYNAME;
                var count = cityStats[name] || 0;
                return {
                    fillColor: getColor(count),
                    weight: 1,
                    opacity: 1,
                    color: '#fff',
                    fillOpacity: 0.7
                };
            },
            onEachFeature: function(feature, layer) {
                var name = feature.properties.COUNTYNAME;
                var count = cityStats[name] || 0;
                layer.bindPopup(name + "：" + count + " 筆");
                layer.on('click', function() {
                    console.log('點擊地圖縣市:', name);
                    showCityPosts(name);
                    layer.openPopup();
                });
            }
        }).addTo(map);
    });

    // 點選清單也能顯示貼文與用餐記錄
    document.querySelectorAll('.city-list-item').forEach(function(item) {
        item.addEventListener('click', function() {
            var city = this.dataset.city;
            showCityPosts(city);
        });
    });
});