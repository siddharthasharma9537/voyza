import React, { useState } from 'react';
import { View, Text, SafeAreaView, ScrollView, Alert, Image, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList, OwnerVehicle } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { StatusBadge } from '../components/StatusBadge';
import { fmtMoney } from './DashboardScreen';
import * as ImagePicker from 'expo-image-picker';

type Nav = StackNavigationProp<OwnerNavigationParamList, 'CarDetail'>;
type RouteType = RouteProp<OwnerNavigationParamList, 'CarDetail'>;

export const CarDetailScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const route = useRoute<RouteType>();
  const { car: initialCar } = route.params;
  const [car, setCar] = useState<OwnerVehicle>(initialCar);
  const [uploading, setUploading] = useState(false);

  const pickAndUpload = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') { Alert.alert('Permission needed'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });
    if (result.canceled) return;
    setUploading(true);
    try {
      const img = await api.owner.uploadImage(car.id, result.assets[0].uri, !car.images || car.images.length === 0);
      setCar((p) => ({ ...p, images: [...(p.images || []), img] }));
      Alert.alert('Uploaded', 'Image added successfully');
    } catch (e: any) { Alert.alert('Upload Failed', e.message); }
    finally { setUploading(false); }
  };

  const handleSubmit = async () => {
    try {
      await api.owner.submitCar(car.id);
      Alert.alert('Submitted', 'Your car is now under review.');
      setCar((p) => ({ ...p, status: 'pending' }));
    } catch (e: any) { Alert.alert('Error', e.message); }
  };

  const specs = [
    ['Registration', car.registration_number],
    ['Fuel', car.fuel_type],
    ['Transmission', car.transmission],
    ['Seating', `${car.seating} persons`],
    ['Year', String(car.year)],
    ['Color', car.color],
    ['City', car.city],
  ];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
            <View>
              <Text style={FONT.h2}>{car.make} {car.model}</Text>
              <Text style={FONT.body}>{car.variant} · {car.year}</Text>
            </View>
            <View style={{ alignItems: 'flex-end', gap: 4 }}>
              <StatusBadge status={car.status} />
              <StatusBadge status={car.kyc_status} />
            </View>
          </View>

          {/* Images */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 20 }}>
            {(car.images || []).map((img) => (
              <Image key={img.id} source={{ uri: img.url }} style={styles.image} />
            ))}
            <TouchableOpacity style={[styles.image, styles.addImage]} onPress={pickAndUpload}>
              <Text style={{ fontSize: 28 }}>📷</Text>
              <Text style={[FONT.body, { fontSize: 11 }]}>Add Image</Text>
            </TouchableOpacity>
          </ScrollView>

          {/* Pricing */}
          <Card style={{ marginBottom: 20, flexDirection: 'row', justifyContent: 'space-around' }}>
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 20, fontWeight: '700', color: C.charcoal }}>{fmtMoney(car.price_per_day)}</Text>
              <Text style={FONT.cap}>per day</Text>
            </View>
            <View style={{ width: 1, backgroundColor: C.border }} />
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 20, fontWeight: '700', color: C.charcoal }}>{fmtMoney(car.price_per_hour)}</Text>
              <Text style={FONT.cap}>per hour</Text>
            </View>
            <View style={{ width: 1, backgroundColor: C.border }} />
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 20, fontWeight: '700', color: C.charcoal }}>{fmtMoney(car.security_deposit)}</Text>
              <Text style={FONT.cap}>deposit</Text>
            </View>
          </Card>

          {/* Specs */}
          <Text style={[FONT.cap, { marginBottom: 10 }]}>Specifications</Text>
          <Card style={{ marginBottom: 20 }}>
            {specs.map(([label, value]) => (
              <View key={label} style={styles.row}>
                <Text style={[FONT.body, { color: C.mid }]}>{label}</Text>
                <Text style={[FONT.body, { fontWeight: '600', color: C.charcoal }]}>{value}</Text>
              </View>
            ))}
          </Card>

          {/* Actions */}
          {car.status === 'draft' && (
            <Button label="Submit for Review" onPress={handleSubmit} loading={uploading} style={{ marginBottom: 12 }} />
          )}
          <Button label="Manage Availability" variant="outline" onPress={() => navigation.navigate('Availability', { carId: car.id })} style={{ marginBottom: 32 }} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingVertical: 16 },
  image: { width: 140, height: 100, borderRadius: 10, marginRight: 10, backgroundColor: C.cream2 },
  addImage: { alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: C.border, borderStyle: 'dashed' },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.border },
});
