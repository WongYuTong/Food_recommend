import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: const LoginPage(),
    );
  }
}

class LoginPage extends StatelessWidget {
  const LoginPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFCEC4F4),
      body: Stack(
        children: [
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(flex: 2),
              Image.asset('assets/logo.png', width: 160, height: 160),
              const SizedBox(height: 40),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 30),
                child: Text(
                  '發掘最適合你的美食旅遊體驗！\n透過AI技術，根據你的口味與偏好推薦最佳餐廳',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, color: Colors.black87),
                ),
              ),
              const SizedBox(height: 40),
              ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const HomePage()),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  minimumSize: const Size(240, 50),
                  side: const BorderSide(color: Color(0xFFCBCDCF)),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Image.asset(
                      'assets/google_logo.png',
                      width: 24,
                      height: 24,
                    ),
                    const SizedBox(width: 10),
                    const Text(
                      '登入 Google 帳戶',
                      style: TextStyle(fontSize: 18, color: Color(0xFF353537)),
                    ),
                  ],
                ),
              ),
              const Spacer(flex: 3),
            ],
          ),
          Positioned(
            bottom: 20,
            right: 20,
            child: GestureDetector(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const HomePage()),
                );
              },
              child: const Text(
                '暫時略過>',
                style: TextStyle(
                  fontSize: 16,
                  color: Color.fromARGB(255, 75, 35, 122),
                  decoration: TextDecoration.underline,
                  decorationColor: Color.fromARGB(255, 75, 35, 122),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(60),
        child: AppBar(
          backgroundColor: const Color(0xFFA89DC3), // 紫色背景
          elevation: 0,
          centerTitle: true, // 🔹讓搜尋框置中
          title: Container(
            width:
                MediaQuery.of(context).size.width * 0.7, // 🔹 限制搜尋框寬度為螢幕的 70%
            height: 36,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: const Color.fromARGB(255, 255, 255, 255),
              borderRadius: BorderRadius.circular(18),
            ),
            child: Row(
              children: [
                Image.asset('assets/search_icon.png', width: 16, height: 16),
                const SizedBox(width: 8),
                const Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      hintText: '搜尋',
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.only(bottom: 12.5),
                    ),
                  ),
                ),
              ],
            ),
          ),
          leading: Padding(
            padding: const EdgeInsets.only(left: 16),
            child: Image.asset(
              'assets/menu_icon.png',
              width: 30,
              height: 30,
            ), // 左側選單
          ),
          leadingWidth: 60,
        ),
      ),
      body: ListView.builder(
        itemCount: 3,
        itemBuilder: (context, index) {
          return Container(
            margin: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 12,
            ), // 增加上下間距
            padding: const EdgeInsets.symmetric(
              horizontal: 20,
              vertical: 80,
            ), // 內部填充更大
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16), // 圓角更柔和
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4)],
            ),
            child: Center(
              child: Text(
                '內容 $index',
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          );
        },
      ),

      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: const Color.fromARGB(255, 255, 255, 255),
        type: BottomNavigationBarType.fixed, // 確保所有 icon 保持固定樣式
        selectedItemColor: const Color(0xFF5E2E84), // 選中的 icon 和文字顏色
        unselectedItemColor: Colors.grey, // 未選中的 icon 和文字顏色
        selectedLabelStyle: const TextStyle(fontSize: 12), // 確保字體大小一致
        unselectedLabelStyle: const TextStyle(fontSize: 12), // 確保未選中狀態的字體大小一致
        items: [
          BottomNavigationBarItem(
            icon: Image.asset('assets/home_icon.png', width: 24, height: 24),
            label: '主頁',
          ),
          BottomNavigationBarItem(
            icon: Image.asset(
              'assets/location_icon.png',
              width: 24,
              height: 24,
            ),
            label: '附近美食',
          ),
          BottomNavigationBarItem(
            icon: Image.asset('assets/chat_icon.png', width: 24, height: 24),
            label: '對話',
          ),
          BottomNavigationBarItem(
            icon: Image.asset('assets/account_icon.png', width: 24, height: 24),
            label: '帳戶管理',
          ),
        ],
      ),
    );
  }
}
