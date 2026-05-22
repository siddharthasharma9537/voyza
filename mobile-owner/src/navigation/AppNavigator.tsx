import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';

import { OwnerNavigationParamList } from '../types';

import { SplashScreen } from '../screens/SplashScreen';
import { LoginScreen } from '../screens/LoginScreen';
import { RegisterScreen } from '../screens/RegisterScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { CarsScreen } from '../screens/CarsScreen';
import { AddCarScreen } from '../screens/AddCarScreen';
import { CarDetailScreen } from '../screens/CarDetailScreen';
import { AvailabilityScreen } from '../screens/AvailabilityScreen';
import { BookingsScreen } from '../screens/BookingsScreen';
import { BookingDetailScreen } from '../screens/BookingDetailScreen';
import { EarningsScreen } from '../screens/EarningsScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { KycUploadScreen } from '../screens/KycUploadScreen';
import { KycStatusScreen } from '../screens/KycStatusScreen';

import { C } from '../constants/theme';

const Stack = createStackNavigator<OwnerNavigationParamList>();
const Tab = createBottomTabNavigator<OwnerNavigationParamList>();

function tabIcon(focused: boolean, icon: string) {
  return <Text style={{ fontSize: 20, color: focused ? C.orange : C.muted }}>{icon}</Text>;
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: C.orange,
        tabBarInactiveTintColor: C.muted,
        tabBarStyle: { backgroundColor: C.cream, borderTopColor: C.border, borderTopWidth: 1, paddingBottom: 8, paddingTop: 4, height: 64 },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
      }}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ tabBarIcon: ({ focused }) => tabIcon(focused, '📊') }} />
      <Tab.Screen name="Cars" component={CarsScreen} options={{ tabBarIcon: ({ focused }) => tabIcon(focused, '🚗') }} />
      <Tab.Screen name="Bookings" component={BookingsScreen} options={{ tabBarIcon: ({ focused }) => tabIcon(focused, '📋') }} />
      <Tab.Screen name="Earnings" component={EarningsScreen} options={{ tabBarIcon: ({ focused }) => tabIcon(focused, '💰') }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ tabBarIcon: ({ focused }) => tabIcon(focused, '👤') }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Splash" screenOptions={{ headerShown: false, cardStyle: { backgroundColor: C.cream } }}>
        <Stack.Screen name="Splash" component={SplashScreen} />
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="Main" component={MainTabs} />
        <Stack.Screen name="AddCar" component={AddCarScreen} />
        <Stack.Screen name="CarDetail" component={CarDetailScreen} />
        <Stack.Screen name="Availability" component={AvailabilityScreen} />
        <Stack.Screen name="BookingDetail" component={BookingDetailScreen} />
        <Stack.Screen name="KycUpload" component={KycUploadScreen} />
        <Stack.Screen name="KycStatus" component={KycStatusScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
