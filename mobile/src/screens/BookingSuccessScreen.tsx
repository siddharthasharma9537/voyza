import React, { useEffect, useRef } from 'react';
import { View, Text, SafeAreaView, Animated, StyleSheet } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList } from '../types';
import { C, FONT } from '../constants/theme';
import { Card } from '../components/Card';
import { Button } from '../components/Button';

type SuccessNav = StackNavigationProp<NavigationParamList, 'BookingSuccess'>;
type SuccessRoute = RouteProp<NavigationParamList, 'BookingSuccess'>;

export const BookingSuccessScreen: React.FC = () => {
  const navigation = useNavigation<SuccessNav>();
  const route = useRoute<SuccessRoute>();
  const { booking, car } = route.params;
  const scale = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.spring(scale, { toValue: 1, useNativeDriver: true, friction: 6, tension: 80 }).start();
  }, []);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <View style={[styles.container, { flex: 1, justifyContent: 'center', alignItems: 'center' }]}>
        <Animated.View style={{ transform: [{ scale }], alignItems: 'center' }}>
          <Text style={{ fontSize: 80, marginBottom: 24 }}>🎉</Text>
          <Text style={[FONT.h1, { textAlign: 'center', marginBottom: 8 }]}>Booking Confirmed!</Text>
          <Text style={[FONT.body, { textAlign: 'center', marginBottom: 32 }]}>
            Your {car.make} {car.model} is ready. Show booking ID at pickup.
          </Text>
          <Card style={{ width: '100%', marginBottom: 32, backgroundColor: C.charcoal }}>
            <Text style={[FONT.cap, { color: C.muted, marginBottom: 6 }]}>Booking ID</Text>
            <Text style={{ fontSize: 24, fontWeight: '800', color: C.white, letterSpacing: 2 }}>
              #{booking.id.slice(0, 8).toUpperCase()}
            </Text>
          </Card>
          <Button label="View My Bookings" onPress={() => navigation.navigate('Bookings')} style={{ width: '100%', marginBottom: 12 }} />
          <Button label="Back to Home" onPress={() => navigation.navigate('Home')} variant="outline" style={{ width: '100%' }} />
        </Animated.View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
});
