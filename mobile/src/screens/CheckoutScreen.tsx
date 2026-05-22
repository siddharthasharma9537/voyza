import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, SafeAreaView, ActivityIndicator, Alert, StyleSheet,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList, PricingBreakdown } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { fmtMoney } from '../components/CarCard';

type CheckoutNav = StackNavigationProp<NavigationParamList, 'Checkout'>;
type CheckoutRoute = RouteProp<NavigationParamList, 'Checkout'>;

export const CheckoutScreen: React.FC = () => {
  const navigation = useNavigation<CheckoutNav>();
  const route = useRoute<CheckoutRoute>();
  const { car } = route.params;
  const [pickup, setPickup] = useState(new Date(Date.now() + 24 * 3600 * 1000));
  const [dropoff, setDropoff] = useState(new Date(Date.now() + 72 * 3600 * 1000));
  const [promo, setPromo] = useState('');
  const [pricing, setPricing] = useState<PricingBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);

  const previewPrice = async () => {
    setLoading(true);
    try {
      const res: any = await api.bookings.preview({
        car_id: car.id,
        pickup_time: pickup.toISOString(),
        dropoff_time: dropoff.toISOString(),
        promo_code: promo || undefined,
      });
      setPricing(res);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    previewPrice();
  }, [pickup, dropoff]);

  const confirmBooking = async () => {
    setBookingLoading(true);
    try {
      const b: any = await api.bookings.create({
        car_id: car.id,
        pickup_time: pickup.toISOString(),
        dropoff_time: dropoff.toISOString(),
        promo_code: promo || undefined,
      });
      navigation.navigate('Payment', { booking: b, car });
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <Text style={[FONT.h2, { marginBottom: 20 }]}>Checkout</Text>

          <Card style={{ marginBottom: 16 }}>
            <Text style={[FONT.h3, { marginBottom: 4 }]}>{car.make} {car.model}</Text>
            <Text style={FONT.body}>{car.city} · {car.fuel_type}</Text>
          </Card>

          <Text style={[FONT.cap, { marginBottom: 8 }]}>Pickup Time</Text>
          <Card style={{ marginBottom: 16 }}>
            <Text style={[FONT.body, { color: C.charcoal, fontWeight: '600' }]}>
              {pickup.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </Text>
          </Card>

          <Text style={[FONT.cap, { marginBottom: 8 }]}>Drop-off Time</Text>
          <Card style={{ marginBottom: 16 }}>
            <Text style={[FONT.body, { color: C.charcoal, fontWeight: '600' }]}>
              {dropoff.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </Text>
          </Card>

          <Input
            label="Promo Code"
            value={promo}
            onChangeText={setPromo}
            placeholder="e.g. WELCOME10"
          />
          <Button label="Apply Code" onPress={previewPrice} variant="outline" style={{ marginBottom: 20 }} />

          {pricing && (
            <Card style={{ marginBottom: 20 }}>
              <Text style={[FONT.cap, { marginBottom: 12 }]}>Price Breakdown</Text>
              {[
                ['Duration', `${pricing.duration_hours}h (${pricing.duration_days} day${pricing.duration_days > 1 ? 's' : ''})`],
                ['Base fare', fmtMoney(pricing.base_amount)],
                ...(pricing.discount_amount > 0 ? [['Promo discount', `-${fmtMoney(pricing.discount_amount)}`] as [string, string]] : []),
                ['GST (18%)', fmtMoney(pricing.tax_amount)],
                ['Security deposit', fmtMoney(pricing.security_deposit)],
              ].map(([label, value]) => (
                <View key={label} style={styles.specRow}>
                  <Text style={FONT.body}>{label}</Text>
                  <Text style={[FONT.body, { fontWeight: '600', color: label.includes('discount') ? C.green : C.charcoal }]}>{value}</Text>
                </View>
              ))}
              <View style={[styles.specRow, { borderTopWidth: 1, borderTopColor: C.border, marginTop: 8, paddingTop: 8 }]}>
                <Text style={FONT.h3}>Total</Text>
                <Text style={[FONT.h3, { color: C.orange }]}>{fmtMoney(pricing.total_amount)}</Text>
              </View>
            </Card>
          )}

          {loading && <ActivityIndicator color={C.orange} style={{ marginBottom: 16 }} />}

          <Button
            label={`Pay ${pricing ? fmtMoney(pricing.total_amount) : '...'}`}
            onPress={confirmBooking}
            loading={bookingLoading}
          />
          <Text style={[FONT.mono, { textAlign: 'center', marginTop: 12, color: C.muted }]}>
            Free cancellation up to 24h before pickup
          </Text>
        </View>
      </ScrollView>
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
