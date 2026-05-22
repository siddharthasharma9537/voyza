import React from 'react';
import { TouchableOpacity, Text, ActivityIndicator, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { C } from '../constants/theme';

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: 'primary' | 'outline' | 'danger';
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
}

export const Button: React.FC<ButtonProps> = ({ label, onPress, variant = 'primary', loading, disabled, style }) => {
  const isOutline = variant === 'outline';
  const isDanger = variant === 'danger';

  const btnStyle: ViewStyle[] = [
    styles.btn,
    ...(isOutline ? [styles.btnOutline] : []),
    ...(isDanger ? [styles.btnDanger] : []),
    ...((disabled || loading) ? [styles.btnDisabled] : []),
    ...(style ? [style] : []),
  ];

  const textStyle: TextStyle[] = [
    styles.btnText,
    ...(isOutline ? [styles.btnOutlineText] : []),
    ...(isDanger ? [styles.btnDangerText] : []),
  ];

  return (
    <TouchableOpacity style={btnStyle} onPress={onPress} disabled={disabled || loading} activeOpacity={0.8}>
      {loading
        ? <ActivityIndicator color={isOutline ? C.orange : C.white} size="small" />
        : <Text style={textStyle}>{label}</Text>
      }
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  btn: { backgroundColor: C.orange, borderRadius: 12, padding: 16, alignItems: 'center' },
  btnOutline: { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: C.orange },
  btnDanger: { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: C.red },
  btnDisabled: { opacity: 0.5 },
  btnText: { color: C.white, fontWeight: '700', fontSize: 16 },
  btnOutlineText: { color: C.orange },
  btnDangerText: { color: C.red },
});
