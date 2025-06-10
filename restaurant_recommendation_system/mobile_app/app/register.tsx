import React, { useState } from 'react';
import { View, Text, TouchableOpacity, SafeAreaView, Alert } from 'react-native';
import { useRouter, Link } from 'expo-router';
import CustomInput from '../src/components/CustomInput';
import CustomButton from '../src/components/CustomButton';
import { register } from '../src/api/auth';
import { sharedStyles } from '../src/styles/sharedStyles';

const RegisterScreen = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleRegister = async () => {
    if (!username || !email || !password) {
      setError('所有欄位皆為必填');
      return;
    }
    try {
      const data = await register(username, email, password);
      if (data.access) {
        Alert.alert('註冊成功', '您現在可以登入您的帳號。', [
          { text: 'OK', onPress: () => router.replace('/login') }
        ]);
      } else {
        setError(data.detail || '註冊失敗，請稍後再試');
      }
    } catch (e) {
      setError('註冊時發生錯誤');
    }
  };

  return (
    <SafeAreaView style={sharedStyles.container}>
      <View>
        <Text style={sharedStyles.title}>建立新帳號</Text>
        {error ? <Text style={sharedStyles.errorText}>{error}</Text> : null}
        <CustomInput
          value={username}
          onChangeText={setUsername}
          placeholder="使用者名稱"
        />
        <CustomInput
          value={email}
          onChangeText={setEmail}
          placeholder="電子郵件"
          keyboardType="email-address"
        />
        <CustomInput
          value={password}
          onChangeText={setPassword}
          placeholder="密碼"
          secureTextEntry
        />
        <CustomButton title="註冊" onPress={handleRegister} />
        <Link href="/login" asChild>
            <TouchableOpacity>
                <Text style={sharedStyles.linkText}>已經有帳號了？點此登入</Text>
            </TouchableOpacity>
        </Link>
      </View>
    </SafeAreaView>
  );
};

export default RegisterScreen;
