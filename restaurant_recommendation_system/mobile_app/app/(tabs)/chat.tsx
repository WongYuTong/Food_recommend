import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, FlatList, StyleSheet, SafeAreaView, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { Colors } from '@/constants/colors';
import { FontAwesome } from '@expo/vector-icons';

type Message = {
  _id: string | number;
  text: string;
  createdAt: Date;
  user: { _id: number; name?: string };
};

const ChatScreen = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const flatListRef = useRef<FlatList<Message>>(null);

  useEffect(() => {
    setMessages([
      { _id: 1, text: '您好！今天想吃點什麼？', createdAt: new Date(), user: { _id: 2, name: 'Bot' } }
    ]);
  }, []);

  const handleSend = async () => {
    if (input.trim().length === 0) return;

    const userMessage: Message = {
      _id: Math.random().toString(),
      text: input,
      createdAt: new Date(),
      user: { _id: 1 },
    };

    setMessages(previousMessages => [userMessage, ...previousMessages]);
    setInput('');

    // TODO: 請確認 processMessage 是否正確
    try {
      // const botResponse = await processMessage(input);
      // const botMessage: Message = {
      //   _id: Math.random().toString(),
      //   text: botResponse.content,
      //   createdAt: new Date(),
      //   user: { _id: 2, name: 'Bot' },
      // };
      // setMessages(previousMessages => [botMessage, ...previousMessages]);
      // Demo 回覆
      const botMessage: Message = {
        _id: Math.random().toString(),
        text: `您輸入了：${input}`,
        createdAt: new Date(),
        user: { _id: 2, name: 'Bot' },
      };
      setMessages(previousMessages => [botMessage, ...previousMessages]);
    } catch (error) {
      console.error("Failed to get bot response:", error);
      const errorMessage: Message = {
        _id: Math.random().toString(),
        text: "抱歉，我現在無法回應。請稍後再試。",
        createdAt: new Date(),
        user: { _id: 2, name: 'Bot' },
      };
      setMessages(previousMessages => [errorMessage, ...previousMessages]);
    }
  };

  const renderItem = ({ item }: { item: Message }) => {
    const isUserMessage = item.user._id === 1;
    return (
      <View style={[styles.messageRow, isUserMessage ? styles.userMessageRow : styles.botMessageRow]}>
        <View style={[styles.messageBubble, isUserMessage ? styles.userMessageBubble : styles.botMessageBubble]}>
          <Text style={isUserMessage ? styles.userMessageText : styles.botMessageText}>{item.text}</Text>
        </View>
      </View>
    );
  };

  // 取得主題色
  const theme = 'light'; // TODO: 可根據 useColorScheme() 動態切換
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={90}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderItem}
          keyExtractor={(item) => item._id.toString()}
          inverted
          contentContainerStyle={{ paddingHorizontal: 10 }}
        />
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="輸入訊息..."
            placeholderTextColor={Colors[theme].icon}
          />
          <TouchableOpacity style={styles.sendButton} onPress={handleSend}>
            <FontAwesome name="paper-plane" size={20} color={Colors[theme].background} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const theme = 'light'; // TODO: 可根據 useColorScheme() 動態切換
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors[theme].background,
  },
  messageRow: {
    flexDirection: 'row',
    marginVertical: 5,
  },
  userMessageRow: {
    justifyContent: 'flex-end',
  },
  botMessageRow: {
    justifyContent: 'flex-start',
  },
  messageBubble: {
    borderRadius: 20,
    padding: 10,
    maxWidth: '80%',
  },
  userMessageBubble: {
    backgroundColor: Colors[theme].tint,
    borderBottomRightRadius: 5,
  },
  botMessageBubble: {
    backgroundColor: Colors[theme].background,
    borderWidth: 1,
    borderColor: Colors[theme].icon,
    borderBottomLeftRadius: 5,
  },
  userMessageText: {
    color: Colors[theme].background,
  },
  botMessageText: {
    color: Colors[theme].text,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    borderTopWidth: 1,
    borderTopColor: Colors[theme].icon,
    backgroundColor: Colors[theme].background,
  },
  input: {
    flex: 1,
    height: 40,
    borderColor: Colors[theme].icon,
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 15,
    backgroundColor: '#f0f0f0',
  },
  sendButton: {
    backgroundColor: Colors[theme].tint,
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },
});

export default ChatScreen;
