import React, { useState } from 'react';
import {
  View, Text, TextInput, ScrollView, SafeAreaView, TouchableOpacity, Alert, StyleSheet,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Button } from '../components/Button';

import { fmtMoney } from '../components/CarCard';

type ReviewNav = StackNavigationProp<NavigationParamList, 'Review'>;
type ReviewRoute = RouteProp<NavigationParamList, 'Review'>;

export const ReviewScreen: React.FC = () => {
  const navigation = useNavigation<ReviewNav>();
  const route = useRoute<ReviewRoute>();
  const { booking } = route.params;
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      await api.reviews.submit({
        booking_id: booking.id,
        vehicle_id: booking.vehicle_id,
        rating,
        comment: comment || undefined,
      });
      Alert.alert('Thank you!', 'Your review has been submitted.', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <Text style={[FONT.h2, { marginBottom: 8 }]}>Rate your trip</Text>
          <Text style={[FONT.body, { marginBottom: 32 }]}>{booking.car_make} {booking.car_model}</Text>

          <Text style={[FONT.cap, { marginBottom: 12 }]}>Your Rating</Text>
          <View style={{ flexDirection: 'row', justifyContent: 'center', gap: 12, marginBottom: 32 }}>
            {[1, 2, 3, 4, 5].map((s) => (
              <TouchableOpacity key={s} onPress={() => setRating(s)}>
                <Text style={{ fontSize: 44, color: s <= rating ? '#F59E0B' : C.border }}>★</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={[FONT.cap, { marginBottom: 8 }]}>Comment (optional)</Text>
          <TextInput
            style={styles.textArea}
            value={comment}
            onChangeText={setComment}
            placeholder="How was your experience?"
            placeholderTextColor={C.muted}
            multiline
          />

          <Button label="Submit Review" onPress={submit} loading={loading} />
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
  textArea: {
    backgroundColor: C.cream2,
    borderRadius: 10,
    padding: 14,
    fontSize: 15,
    color: C.charcoal,
    borderWidth: 1,
    borderColor: C.border,
    height: 120,
    textAlignVertical: 'top',
    marginBottom: 24,
  },
});
