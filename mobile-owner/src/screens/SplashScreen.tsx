import React, { useEffect, useRef } from 'react';
import { View, Text, Animated, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList } from '../types';
import { C } from '../constants/theme';

type Nav = StackNavigationProp<OwnerNavigationParamList, 'Splash'>;

export const SplashScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const scale = useRef(new Animated.Value(0.8)).current;
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scale, { toValue: 1, useNativeDriver: true, friction: 8, tension: 80 }),
      Animated.timing(opacity, { toValue: 1, duration: 600, useNativeDriver: true }),
    ]).start();

    AsyncStorage.getItem('access_token').then((token) => {
      setTimeout(() => navigation.replace(token ? 'Main' : 'Login'), 1800);
    });
  }, []);

  return (
    <View style={styles.container}>
      <Animated.View style={{ transform: [{ scale }], opacity }}>
        <Text style={styles.title}>Voyza <Text style={{ color: C.orange }}>Host</Text></Text>
        <Text style={styles.subtitle}>Earn from your car</Text>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.charcoal, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 40, fontWeight: '800', color: C.white },
  subtitle: { color: C.muted, textAlign: 'center', marginTop: 8, fontSize: 14 },
});
