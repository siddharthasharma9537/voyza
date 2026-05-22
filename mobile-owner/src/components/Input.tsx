import React from 'react';
import { View, Text, TextInput, StyleSheet, TextInputProps } from 'react-native';
import { C, FONT } from '../constants/theme';

interface InputProps extends TextInputProps {
  label?: string;
  multiline?: boolean;
}

export const Input: React.FC<InputProps> = ({ label, multiline, style, ...props }) => (
  <View style={styles.inputWrap}>
    {label && <Text style={[FONT.cap, { marginBottom: 6 }]}>{label}</Text>}
    <TextInput
      style={[styles.input, multiline && styles.inputMultiline, style]}
      placeholderTextColor={C.muted}
      multiline={multiline}
      {...props}
    />
  </View>
);

const styles = StyleSheet.create({
  inputWrap: { marginBottom: 14 },
  input: { backgroundColor: C.cream2, borderRadius: 10, padding: 14, fontSize: 15, color: C.charcoal, borderWidth: 1, borderColor: C.border },
  inputMultiline: { height: 120, textAlignVertical: 'top' },
});
