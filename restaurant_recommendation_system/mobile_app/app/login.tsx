import React, { useState } from 'react';
import { View, Text, TouchableOpacity, SafeAreaView } from 'react-native';
import { useRouter, Link } from 'expo-router';
import CustomInput from '../src/components/CustomInput';
import CustomButton from '../src/components/CustomButton';
import { login } from '../src/api/auth';
import { sharedStyles } from '../src/styles/sharedStyles';

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
    <SafeAreaView style={sharedStyles.container}>
      <View>
        <Text style={sharedStyles.title}>登入 QuickGnaw</Text>
        {error ? <Text style={sharedStyles.errorText}>{error}</Text> : null}
        <CustomInput
          value={username}
          onChangeText={setUsername}
          placeholder="帳號"
        />
        <CustomInput
          value={password}
          onChangeText={setPassword}
          placeholder="密碼"
          secureTextEntry
        />
        <CustomButton title="登入" onPress={handleLogin} />
        <Link href="/register" asChild>
            <TouchableOpacity>
                <Text style={sharedStyles.linkText}>還沒有帳號？點此註冊</Text>
            </TouchableOpacity>
        </Link>
      </View>
    </SafeAreaView>
  );
};

export default LoginScreen;
