import React, { useState } from 'react';
import { View, Text, ScrollView, SafeAreaView, Alert, KeyboardAvoidingView, Platform, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Button } from '../components/Button';
import { Input } from '../components/Input';

type Nav = StackNavigationProp<OwnerNavigationParamList, 'AddCar'>;

export const AddCarScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    make: '', model: '', variant: '', year: '', color: '', city: '', state: '',
    registration_number: '', seating: '', fuel_type: '', transmission: '',
    price_per_hour: '', price_per_day: '', security_deposit: '',
  });

  const update = (key: string, value: string) => setForm((p) => ({ ...p, [key]: value }));

  const submit = async () => {
    if (!form.make || !form.model || !form.year || !form.registration_number || !form.price_per_day) {
      Alert.alert('Missing Fields', 'Please fill in all required fields');
      return;
    }
    setLoading(true);
    try {
      await api.owner.addCar({
        ...form,
        year: parseInt(form.year),
        seating: parseInt(form.seating) || 5,
        price_per_hour: parseInt(form.price_per_hour) || 0,
        price_per_day: parseInt(form.price_per_day),
        security_deposit: parseInt(form.security_deposit) || 0,
        features: { ac: true, gps: false, bluetooth: false, usb_charger: false, sunroof: false },
      });
      Alert.alert('Success', 'Car created in draft mode. Upload images and submit for review.', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (e: any) { Alert.alert('Error', e.message); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView>
          <View style={styles.container}>
            <Text style={[FONT.h2, { marginBottom: 20 }]}>Add New Car</Text>
            <Text style={[FONT.cap, { marginBottom: 12 }]}>Basic Info</Text>
            <Input label="Make *" value={form.make} onChangeText={(v) => update('make', v)} placeholder="e.g. Toyota" />
            <Input label="Model *" value={form.model} onChangeText={(v) => update('model', v)} placeholder="e.g. Innova" />
            <Input label="Variant" value={form.variant} onChangeText={(v) => update('variant', v)} placeholder="e.g. Crysta" />
            <Input label="Year *" value={form.year} onChangeText={(v) => update('year', v)} placeholder="2023" keyboardType="number-pad" />
            <Input label="Color *" value={form.color} onChangeText={(v) => update('color', v)} placeholder="e.g. White" />
            <Input label="Registration Number *" value={form.registration_number} onChangeText={(v) => update('registration_number', v)} placeholder="e.g. TS09AB1234" autoCapitalize="characters" />

            <Text style={[FONT.cap, { marginBottom: 12, marginTop: 8 }]}>Location</Text>
            <Input label="City *" value={form.city} onChangeText={(v) => update('city', v)} placeholder="e.g. Hyderabad" />
            <Input label="State" value={form.state} onChangeText={(v) => update('state', v)} placeholder="e.g. Telangana" />

            <Text style={[FONT.cap, { marginBottom: 12, marginTop: 8 }]}>Specs</Text>
            <Input label="Seating" value={form.seating} onChangeText={(v) => update('seating', v)} placeholder="5" keyboardType="number-pad" />
            <Input label="Fuel Type" value={form.fuel_type} onChangeText={(v) => update('fuel_type', v)} placeholder="petrol / diesel / electric / hybrid / cng" />
            <Input label="Transmission" value={form.transmission} onChangeText={(v) => update('transmission', v)} placeholder="manual / automatic" />

            <Text style={[FONT.cap, { marginBottom: 12, marginTop: 8 }]}>Pricing (in paise)</Text>
            <Input label="Price per Day *" value={form.price_per_day} onChangeText={(v) => update('price_per_day', v)} placeholder="e.g. 250000 for ₹2,500" keyboardType="number-pad" />
            <Input label="Price per Hour" value={form.price_per_hour} onChangeText={(v) => update('price_per_hour', v)} placeholder="e.g. 15000 for ₹150" keyboardType="number-pad" />
            <Input label="Security Deposit" value={form.security_deposit} onChangeText={(v) => update('security_deposit', v)} placeholder="e.g. 500000 for ₹5,000" keyboardType="number-pad" />

            <Button label="Create Car" onPress={submit} loading={loading} style={{ marginTop: 12, marginBottom: 32 }} />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({ container: { paddingHorizontal: 20, paddingVertical: 16 } });
