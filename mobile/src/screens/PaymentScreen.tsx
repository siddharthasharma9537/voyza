import React, { useState } from 'react';
import {
  View, Text, SafeAreaView, Alert, StyleSheet,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { fmtMoney } from '../components/CarCard';

type PayNav = StackNavigationProp<NavigationParamList, 'Payment'>;
type PayRoute = RouteProp<NavigationParamList, 'Payment'>;

export const PaymentScreen: React.FC = () => {
  const navigation = useNavigation<PayNav>();
  const route = useRoute<PayRoute>();
  const { booking, car } = route.params;
  const [loading, setLoading] = useState(false);

  const initiatePayment = async () => {
    setLoading(true);
    try {
      // Create Razorpay order from backend
      await api.payments.createOrder(booking.id);

      // In production, this would open Razorpay SDK.
      // For now, simulate success.
      navigation.replace('BookingSuccess', { booking, car });
    } catch (e: any) {
      Alert.alert('Payment Failed', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <View style={[styles.container, { flex: 1, justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={{ fontSize: 56, marginBottom: 24 }}>💳</Text>
        <Text style={[FONT.h2, { textAlign: 'center', marginBottom: 8 }]}>Complete Payment</Text>
        <Text style={[FONT.body, { textAlign: 'center', marginBottom: 40 }]}>
          Secure payment powered by Razorpay
        </Text>
        <Card style={{ width: '100%', marginBottom: 32 }}>
          <View style={styles.specRow}>
            <Text style={FONT.body}>Booking</Text>
            <Text style={[FONT.mono, { fontSize: 11 }]}>
              #{(booking.id || '').slice(0, 8).toUpperCase()}
            </Text>
          </View>
          <View style={styles.specRow}>
            <Text style={FONT.body}>Car</Text>
            <Text style={[FONT.body, { fontWeight: '600' }]}>{car.make} {car.model}</Text>
          </View>
          <View style={[styles.specRow, { borderTopWidth: 1, borderTopColor: C.border, marginTop: 8, paddingTop: 8 }]}>
            <Text style={FONT.h3}>Amount</Text>
            <Text style={[FONT.h3, { color: C.orange }]}>{fmtMoney(booking.total_amount)}</Text>
          </View>
        </Card>
        <Button label="Pay with Razorpay" onPress={initiatePayment} loading={loading} style={{ width: '100%' }} />
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  specRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
});
