import { Tabs } from 'expo-router';
import React from 'react';
import { FontAwesome, Ionicons } from '@expo/vector-icons';

import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/colors';

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs initialRouteName="chat">
    <Tabs.Screen
      name="chat"
      options={{
        title: '推薦小幫手',
        tabBarIcon: ({ color, focused }) => (
          <FontAwesome name="comments" size={24} color={color} />
        ),
      }}
    />
    <Tabs.Screen
      name="saved"
      options={{
        title: '餐廳收藏',
        tabBarIcon: ({ color, focused }) => (
          <FontAwesome name={focused ? "heart" : "heart-o"} size={24} color={color} />
        ),
      }}
    />
    <Tabs.Screen
      name="preferences"
      options={{
        title: '口味偏好',
        tabBarIcon: ({ color, focused }) => (
          <FontAwesome name="sliders" size={24} color={color} />
        ),
      }}
    />
    <Tabs.Screen
      name="history"
      options={{
        title: '詢問記錄',
        tabBarIcon: ({ color, focused }) => (
          <FontAwesome name="history" size={24} color={color} />
        ),
      }}
    />
  </Tabs>
  );
}