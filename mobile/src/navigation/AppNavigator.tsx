import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';

import { NavigationParamList } from '../types';

import { SplashScreen } from '../screens/SplashScreen';
import { LoginScreen } from '../screens/LoginScreen';
import { RegisterScreen } from '../screens/RegisterScreen';
import { HomeScreen } from '../screens/HomeScreen';
import { BrowseScreen } from '../screens/BrowseScreen';
import { CarDetailScreen } from '../screens/CarDetailScreen';
import { CheckoutScreen } from '../screens/CheckoutScreen';
import { PaymentScreen } from '../screens/PaymentScreen';
import { BookingSuccessScreen } from '../screens/BookingSuccessScreen';
import { BookingsScreen } from '../screens/BookingsScreen';
import { ReviewScreen } from '../screens/ReviewScreen';
import { TrackingScreen } from '../screens/TrackingScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { KycUploadScreen } from '../screens/KycUploadScreen';
import { KycStatusScreen } from '../screens/KycStatusScreen';

import { C } from '../constants/theme';

const Stack = createStackNavigator<NavigationParamList>();
const Tab = createBottomTabNavigator<NavigationParamList>();

function tabBarIcon(focused: boolean, icon: string) {
  return (
    <Text style={{ fontSize: 20, color: focused ? C.orange : C.muted }}>
      {icon}
    </Text>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: C.orange,
        tabBarInactiveTintColor: C.muted,
        tabBarStyle: {
          backgroundColor: C.cream,
          borderTopColor: C.border,
          borderTopWidth: 1,
          paddingBottom: 8,
          paddingTop: 4,
          height: 64,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{ tabBarIcon: ({ focused }) => tabBarIcon(focused, '🏠') }}
      />
      <Tab.Screen
        name="Browse"
        component={BrowseScreen}
        options={{ tabBarIcon: ({ focused }) => tabBarIcon(focused, '🔍') }}
      />
      <Tab.Screen
        name="Bookings"
        component={BookingsScreen}
        options={{ tabBarIcon: ({ focused }) => tabBarIcon(focused, '📋') }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ tabBarIcon: ({ focused }) => tabBarIcon(focused, '👤') }}
      />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Splash"
        screenOptions={{
          headerShown: false,
          cardStyle: { backgroundColor: C.cream },
        }}
      >
        <Stack.Screen name="Splash" component={SplashScreen} />
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="Main" component={MainTabs} />
        <Stack.Screen name="CarDetail" component={CarDetailScreen} />
        <Stack.Screen name="Checkout" component={CheckoutScreen} />
        <Stack.Screen name="Payment" component={PaymentScreen} />
        <Stack.Screen name="BookingSuccess" component={BookingSuccessScreen} />
        <Stack.Screen name="Review" component={ReviewScreen} />
        <Stack.Screen name="Tracking" component={TrackingScreen} />
        <Stack.Screen name="KycUpload" component={KycUploadScreen} />
        <Stack.Screen name="KycStatus" component={KycStatusScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
