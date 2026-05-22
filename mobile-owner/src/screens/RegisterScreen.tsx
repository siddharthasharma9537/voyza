import React, { useState } from 'react';
import { View, Text, ScrollView, Alert, KeyboardAvoidingView, Platform, SafeAreaView, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { storage } from '../utils/storage';
import { Button } from '../components/Button';
import { Input } from '../components/Input';

type Nav = StackNavigationProp<OwnerNavigationParamList, 'Register'>;

export const RegisterScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const [step, setStep] = useState<1 | 2>(1);
  const [phone, setPhone] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendOtp = async () => {
    if (!fullName.trim()) { Alert.alert('Invalid', 'Please enter your full name'); return; }
    if (!phone.startsWith('+91') || phone.length < 13) { Alert.alert('Invalid', 'Enter phone in format +919XXXXXXXXX'); return; }
    setLoading(true);
    try {
      const res: any = await api.auth.registerSendOtp(phone, fullName);
      if (res.otp) Alert.alert('Dev Mode OTP', `Your OTP: ${res.otp}`);
      setStep(2);
    } catch (e: any) { Alert.alert('Error', e.message); } finally { setLoading(false); }
  };

  const handleVerify = async () => {
    if (otp.length !== 6) { Alert.alert('Invalid', 'Enter 6-digit OTP'); return; }
    setLoading(true);
    try {
      const res: any = await api.auth.registerVerifyOtp(phone, otp, fullName, email || undefined);
      await storage.setTokens(res.access_token, res.refresh_token);
      Alert.alert('Welcome!', 'Your owner account has been created.', [{ text: 'OK', onPress: () => navigation.replace('Main') }]);
    } catch (e: any) { Alert.alert('Error', e.message); } finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={[styles.container, { flex: 1, justifyContent: 'center' }]}>
          <Text style={[FONT.h1, { marginBottom: 8 }]}>Become a Host</Text>
          <Text style={[FONT.body, { marginBottom: 40 }]}>List your car and start earning</Text>
          {step === 1 ? (
            <>
              <Input label="Full Name" value={fullName} onChangeText={setFullName} placeholder="John Doe" autoFocus />
              <Input label="Mobile Number" value={phone} onChangeText={setPhone} placeholder="+91 98765 43210" keyboardType="phone-pad" />
              <Input label="Email (optional)" value={email} onChangeText={setEmail} placeholder="john@example.com" keyboardType="email-address" />
              <Button label="Send OTP" onPress={handleSendOtp} loading={loading} style={{ marginTop: 8 }} />
              <Button label="Already have an account?" variant="outline" onPress={() => navigation.navigate('Login')} style={{ marginTop: 12 }} />
            </>
          ) : (
            <>
              <Text style={[FONT.body, { marginBottom: 16 }]}>OTP sent to {phone}</Text>
              <Input label="Enter OTP" value={otp} onChangeText={setOtp} placeholder="6-digit OTP" keyboardType="number-pad" autoFocus />
              <Button label="Create Account" onPress={handleVerify} loading={loading} style={{ marginTop: 8 }} />
              <Text style={{ marginTop: 16, alignSelf: 'center', color: C.orange, fontWeight: '600' }} onPress={() => setStep(1)}>Change number</Text>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({ container: { paddingHorizontal: 20, paddingVertical: 16 } });
