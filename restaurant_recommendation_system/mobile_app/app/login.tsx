import React, { useState } from 'react';
import { View, Text, TouchableOpacity, SafeAreaView } from 'react-native';
import { useRouter, Link } from 'expo-router';
import CustomInput from '../components/CustomInput';
import CustomButton from '../components/CustomButton';
import { login } from '../api/auth';
import { globalStyles } from "@/constants/styles";

const LoginScreen = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    if (!username || !password) {
      setError('請輸入帳號和密碼');
      return;
    }
    try {
      const data = await login(username, password);
      if (data.access) {
        router.replace('/chat');
      } else {
        setError(data.error || '登入失敗，請檢查您的帳號密碼');
      }
    } catch (e) {
      setError('登入時發生錯誤，請稍後再試');
    }
  };

  return (
    <SafeAreaView style={globalStyles.container}>
      <View>
        <Text style={globalStyles.title}>登入 QuickGnaw</Text>
        {error ? <Text style={globalStyles.errorText}>{error}</Text> : null}
        <CustomInput
          value={username}
          onChangeText={setUsername}
          placeholder="帳號"
          style={globalStyles.input}
        />
        <CustomInput
          value={password}
          onChangeText={setPassword}
          placeholder="密碼"
          secureTextEntry
          style={globalStyles.input}
        />
        <CustomButton title="登入" onPress={handleLogin} style={globalStyles.button} textStyle={globalStyles.buttonText} />
        <Link href="/register" asChild>
            <TouchableOpacity>
                <Text style={globalStyles.linkText}>還沒有帳號？點此註冊</Text>
            </TouchableOpacity>
        </Link>
      </View>
    </SafeAreaView>
  );
};

export default LoginScreen;
