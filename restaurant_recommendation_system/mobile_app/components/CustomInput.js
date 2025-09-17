import React from 'react';
import { TextInput, StyleSheet } from 'react-native';
import { COLORS } from '../constants/colors';

const CustomInput = ({ value, onChangeText, placeholder, secureTextEntry = false, style }) => {
  return (
    <TextInput
      style={[styles.input, style]}
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      secureTextEntry={secureTextEntry}
      placeholderTextColor={COLORS.textLight}
    />
  );
};

const styles = StyleSheet.create({
  input: {
    height: 50,
    borderColor: COLORS.border,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 15,
    marginBottom: 15,
    backgroundColor: COLORS.white,
    fontSize: 16,
    color: COLORS.textDark,
  },
});

export default CustomInput;
