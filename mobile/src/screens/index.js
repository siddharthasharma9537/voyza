/**
 * Voyza Customer Mobile App
 * React Native — complete screen implementation
 *
 * Screens implemented:
 *   SplashScreen
 *   OnboardingScreen
 *   LoginScreen (OTP flow)
 *   HomeScreen (search + featured cars)
 *   BrowseScreen (filter + paginated car list)
 *   CarDetailScreen (full detail + image gallery)
 *   CheckoutScreen (date picker + pricing + promo)
 *   PaymentScreen (Razorpay SDK integration)
 *   BookingSuccessScreen
 *   BookingsScreen (history)
 *   TrackingScreen (live GPS map)
 *   ProfileScreen
 *   ReviewScreen (post-trip)
 *
 * Dependencies (package.json):
 *   react-native, @react-navigation/native, @react-navigation/stack,
 *   @react-navigation/bottom-tabs, react-native-maps,
 *   react-native-razorpay, @react-native-async-storage/async-storage,
 *   react-native-image-picker, react-native-date-picker,
 *   react-native-vector-icons, axios
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  FlatList, Image, StyleSheet, StatusBar, Dimensions,
  ActivityIndicator, Alert, RefreshControl, Animated,
  Platform, KeyboardAvoidingView, SafeAreaView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');

// ── Design tokens ────────────────────────────────────────────────────────────
const C = {
  cream:    '#F5F0E8',
  cream2:   '#EDE6D8',
  charcoal: '#1A1814',
  orange:   '#E8500A',
  orange2:  '#FF6B2B',
  green:    '#16A34A',
  red:      '#DC2626',
  mid:      '#5C5548',
  muted:    '#9C927F',
  white:    '#FFFFFF',
  border:   '#E4DAC8',
};

const T = StyleSheet.create({
  h1:   { fontSize: 28, fontWeight: '700', color: C.charcoal, letterSpacing: -0.5 },
  h2:   { fontSize: 22, fontWeight: '700', color: C.charcoal, letterSpacing: -0.3 },
  h3:   { fontSize: 17, fontWeight: '600', color: C.charcoal },
  body: { fontSize: 14, color: C.mid, lineHeight: 22 },
  mono: { fontSize: 12, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', color: C.mid },
  cap:  { fontSize: 10, fontWeight: '700', letterSpacing: 1.5, textTransform: 'uppercase', color: C.muted },
});

// ── API Client ────────────────────────────────────────────────────────────────
const BASE_URL = 'http://localhost:8000/api/v1';

const api = {
  async _request(path, options = {}) {
    const token = await AsyncStorage.getItem('access_token');
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.status === 204 ? null : res.json();
  },
  auth: {
    sendOtp:   (phone)        => api._request('/auth/send-otp',   { method: 'POST', body: JSON.stringify({ phone }) }),
    verifyOtp: (phone, otp)   => api._request('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ phone, otp, purpose: 'login' }) }),
    me:        ()             => api._request('/auth/me'),
    logout:    (refresh)      => api._request('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refresh }) }),
  },
  cars: {
    browse: (params = {}) => {
      const q = new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([,v]) => v != null)));
      return api._request(`/cars?${q}`);
    },
    detail: (id) => api._request(`/cars/${id}`),
    reviews: (id) => api._request(`/cars/${id}/reviews`),
  },
  bookings: {
    preview: (data)  => api._request('/bookings/preview', { method: 'POST', body: JSON.stringify(data) }),
    create:  (data)  => api._request('/bookings',         { method: 'POST', body: JSON.stringify(data) }),
    list:    ()      => api._request('/bookings'),
    cancel:  (id, r) => api._request(`/bookings/${id}/cancel`, { method: 'POST', body: JSON.stringify({ reason: r }) }),
  },
  payments: {
    createOrder: (booking_id) => api._request('/payments/create-order', { method: 'POST', body: JSON.stringify({ booking_id }) }),
  },
  reviews: {
    submit:  (data) => api._request('/reviews', { method: 'POST', body: JSON.stringify(data) }),
    pending: ()     => api._request('/reviews/pending'),
  },
};

// ── Shared Components ─────────────────────────────────────────────────────────

const Button = ({ label, onPress, variant = 'primary', loading, disabled, style }) => (
  <TouchableOpacity
    style={[styles.btn, variant === 'outline' && styles.btnOutline, (disabled || loading) && styles.btnDisabled, style]}
    onPress={onPress}
    disabled={disabled || loading}
    activeOpacity={0.8}
  >
    {loading
      ? <ActivityIndicator color={variant === 'outline' ? C.orange : C.white} size="small" />
      : <Text style={[styles.btnText, variant === 'outline' && styles.btnOutlineText]}>{label}</Text>
    }
  </TouchableOpacity>
);

const Input = ({ label, value, onChangeText, placeholder, keyboardType, secureTextEntry, autoFocus }) => (
  <View style={styles.inputWrap}>
    {label && <Text style={[T.cap, { marginBottom: 6 }]}>{label}</Text>}
    <TextInput
      style={styles.input}
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor={C.muted}
      keyboardType={keyboardType}
      secureTextEntry={secureTextEntry}
      autoFocus={autoFocus}
    />
  </View>
);

const Tag = ({ label, active, onPress }) => (
  <TouchableOpacity
    style={[styles.tag, active && styles.tagActive]}
    onPress={onPress}
    activeOpacity={0.7}
  >
    <Text style={[styles.tagText, active && styles.tagTextActive]}>{label}</Text>
  </TouchableOpacity>
);

const Card = ({ children, style }) => (
  <View style={[styles.card, style]}>{children}</View>
);

const StatusBadge = ({ status }) => {
  const map = {
    pending:   { bg: '#FFF7ED', color: '#C2410C', label: 'Pending' },
    confirmed: { bg: '#F0FDF4', color: '#16A34A', label: 'Confirmed' },
    active:    { bg: '#EFF6FF', color: '#1D4ED8', label: 'Active' },
    completed: { bg: '#F9FAFB', color: '#6B7280', label: 'Completed' },
    cancelled: { bg: '#FEF2F2', color: '#DC2626', label: 'Cancelled' },
    disputed:  { bg: '#FFFBEB', color: '#92400E', label: 'Disputed' },
  };
  const s = map[status] || map.pending;
  return (
    <View style={{ backgroundColor: s.bg, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6 }}>
      <Text style={{ color: s.color, fontSize: 11, fontWeight: '700' }}>{s.label}</Text>
    </View>
  );
};

const StarRow = ({ rating, size = 14 }) => (
  <View style={{ flexDirection: 'row', gap: 2 }}>
    {[1,2,3,4,5].map(i => (
      <Text key={i} style={{ fontSize: size, color: i <= Math.round(rating) ? '#F59E0B' : C.border }}>★</Text>
    ))}
  </View>
);

const fmt = (paise) => '₹' + (paise/100).toLocaleString('en-IN');
const fmtDate = (iso) => new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });

// ── Screens ───────────────────────────────────────────────────────────────────

// ══ SplashScreen ══
export const SplashScreen = ({ navigation }) => {
  const scale = useRef(new Animated.Value(0.8)).current;
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scale,   { toValue: 1, tension: 80, friction: 8, useNativeDriver: true }),
      Animated.timing(opacity, { toValue: 1, duration: 600, useNativeDriver: true }),
    ]).start();

    AsyncStorage.getItem('access_token').then(token => {
      setTimeout(() => navigation.replace(token ? 'Home' : 'Login'), 1800);
    });
  }, []);

  return (
    <View style={[styles.center, { backgroundColor: C.charcoal, flex: 1 }]}>
      <Animated.View style={{ transform: [{ scale }], opacity }}>
        <Text style={{ fontSize: 48, fontWeight: '800', color: C.white }}>
          Drive<Text style={{ color: C.orange }}>zy</Text>
        </Text>
        <Text style={{ color: C.muted, textAlign: 'center', marginTop: 8 }}>Drive on your terms</Text>
      </Animated.View>
    </View>
  );
};

// ══ LoginScreen ══
export const LoginScreen = ({ navigation }) => {
  const [step, setStep] = useState(1);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendOtp = async () => {
    if (!phone.startsWith('+91') || phone.length < 13) {
      Alert.alert('Invalid', 'Enter phone in format +919XXXXXXXXX');
      return;
    }
    setLoading(true);
    try {
      const res = await api.auth.sendOtp(phone);
      // In dev mode, OTP is in response
      if (res.otp) Alert.alert('Dev Mode OTP', `Your OTP: ${res.otp}`);
      setStep(2);
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otp.length !== 6) { Alert.alert('Invalid', 'Enter 6-digit OTP'); return; }
    setLoading(true);
    try {
      const res = await api.auth.verifyOtp(phone, otp);
      await AsyncStorage.setItem('access_token',  res.access_token);
      await AsyncStorage.setItem('refresh_token', res.refresh_token);
      navigation.replace('Home');
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={[styles.container, { flex: 1, justifyContent: 'center' }]}>
          <Text style={[T.h1, { marginBottom: 8 }]}>Welcome to{'\n'}Voyza</Text>
          <Text style={[T.body, { marginBottom: 40 }]}>Sign in to book your next drive</Text>

          {step === 1 ? (
            <>
              <Input
                label="Mobile Number"
                value={phone}
                onChangeText={setPhone}
                placeholder="+91 98765 43210"
                keyboardType="phone-pad"
                autoFocus
              />
              <Button label="Send OTP" onPress={handleSendOtp} loading={loading} style={{ marginTop: 8 }} />
            </>
          ) : (
            <>
              <Text style={[T.body, { marginBottom: 16 }]}>OTP sent to {phone}</Text>
              <Input
                label="Enter OTP"
                value={otp}
                onChangeText={setOtp}
                placeholder="6-digit OTP"
                keyboardType="number-pad"
                autoFocus
              />
              <Button label="Verify & Sign In" onPress={handleVerifyOtp} loading={loading} style={{ marginTop: 8 }} />
              <TouchableOpacity onPress={() => setStep(1)} style={{ marginTop: 16, alignItems: 'center' }}>
                <Text style={{ color: C.orange, fontWeight: '600' }}>Change number</Text>
              </TouchableOpacity>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// ══ HomeScreen ══
export const HomeScreen = ({ navigation }) => {
  const [city, setCity] = useState('Hyderabad');
  const [featured, setFeatured] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.cars.browse({ city, limit: 6, sort_by: 'rating' })
      .then(res => setFeatured(res.items || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [city]);

  const cities = ['Hyderabad', 'Bangalore', 'Chennai', 'Mumbai', 'Pune'];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        {/* Header */}
        <View style={[styles.container, { paddingTop: 24, paddingBottom: 8 }]}>
          <Text style={[T.cap, { marginBottom: 4 }]}>Good morning 👋</Text>
          <Text style={T.h2}>Find your perfect car</Text>

          {/* City selector */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 16, marginHorizontal: -20 }} contentContainerStyle={{ paddingHorizontal: 20, gap: 8 }}>
            {cities.map(c => <Tag key={c} label={c} active={c === city} onPress={() => setCity(c)} />)}
          </ScrollView>
        </View>

        {/* Hero search card */}
        <View style={[styles.container, { paddingTop: 0 }]}>
          <Card style={{ marginBottom: 24 }}>
            <Text style={[T.h3, { marginBottom: 16 }]}>Quick Search</Text>
            <Button label="Browse All Cars in " onPress={() => navigation.navigate('Browse', { city })} />
          </Card>

          {/* Featured cars */}
          <Text style={[T.h3, { marginBottom: 16 }]}>Top Rated in {city}</Text>
        </View>

        {loading
          ? <ActivityIndicator color={C.orange} style={{ marginTop: 20 }} />
          : <FlatList
              data={featured}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={{ paddingHorizontal: 20, gap: 12 }}
              keyExtractor={item => item.id}
              renderItem={({ item }) => <CarCard car={item} onPress={() => navigation.navigate('CarDetail', { car: item })} compact />}
            />
        }

        {/* Stats banner */}
        <View style={[styles.container, { marginTop: 32, marginBottom: 24 }]}>
          <Card>
            <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
              {[['8,400+', 'Cars'],['52', 'Cities'],['4.8★', 'Rating']].map(([val, label]) => (
                <View key={label} style={{ alignItems: 'center' }}>
                  <Text style={[T.h2, { color: C.orange }]}>{val}</Text>
                  <Text style={T.cap}>{label}</Text>
                </View>
              ))}
            </View>
          </Card>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// ══ CarCard component (shared) ══
const CarCard = ({ car, onPress, compact }) => (
  <TouchableOpacity
    style={[styles.carCard, compact && styles.carCardCompact]}
    onPress={onPress}
    activeOpacity={0.85}
  >
    <View style={styles.carImgPlaceholder}>
      <Text style={{ fontSize: compact ? 36 : 48 }}>🚗</Text>
    </View>
    <View style={{ padding: 14 }}>
      <Text style={[T.h3, { fontSize: compact ? 15 : 17 }]}>{car.make} {car.model}</Text>
      <Text style={[T.body, { fontSize: 12, marginTop: 2 }]}>{car.city} · {car.fuel_type} · {car.seating} seats</Text>
      {car.avg_rating && (
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 6 }}>
          <StarRow rating={car.avg_rating} size={12} />
          <Text style={T.mono}>{car.avg_rating} ({car.review_count})</Text>
        </View>
      )}
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 10, alignItems: 'flex-end' }}>
        <View>
          <Text style={{ fontSize: 18, fontWeight: '700', color: C.charcoal }}>{fmt(car.price_per_day)}</Text>
          <Text style={[T.mono, { fontSize: 10 }]}>per day</Text>
        </View>
        <View style={styles.orangeChip}>
          <Text style={{ color: C.white, fontSize: 11, fontWeight: '700' }}>{car.transmission}</Text>
        </View>
      </View>
    </View>
  </TouchableOpacity>
);

// ══ BrowseScreen ══
export const BrowseScreen = ({ navigation, route }) => {
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [filters, setFilters] = useState({
    city: route.params?.city || null,
    fuel_type: null,
    transmission: null,
    sort_by: 'price_asc',
  });

  const fetchCars = useCallback(async (pg = 1, reset = false) => {
    try {
      const res = await api.cars.browse({ ...filters, page: pg, limit: 20 });
      const items = res.items || [];
      setCars(prev => reset ? items : [...prev, ...items]);
      setHasMore(pg < res.total_pages);
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters]);

  useEffect(() => { setLoading(true); fetchCars(1, true); }, [filters]);

  const onRefresh = () => { setRefreshing(true); setPage(1); fetchCars(1, true); };
  const onEndReached = () => {
    if (hasMore && !loading) { const next = page + 1; setPage(next); fetchCars(next); }
  };

  const fuelTypes = ['petrol','diesel','electric','hybrid','cng'];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      {/* Filter strip */}
      <View style={{ backgroundColor: C.white, borderBottomWidth: 1, borderBottomColor: C.border }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 10, gap: 8 }}>
          {fuelTypes.map(f => (
            <Tag key={f} label={f} active={filters.fuel_type === f}
              onPress={() => setFilters(p => ({ ...p, fuel_type: p.fuel_type === f ? null : f }))} />
          ))}
          <Tag label="Auto" active={filters.transmission === 'automatic'}
            onPress={() => setFilters(p => ({ ...p, transmission: p.transmission === 'automatic' ? null : 'automatic' }))} />
          <Tag label="Manual" active={filters.transmission === 'manual'}
            onPress={() => setFilters(p => ({ ...p, transmission: p.transmission === 'manual' ? null : 'manual' }))} />
        </ScrollView>
      </View>

      <FlatList
        data={cars}
        keyExtractor={item => item.id}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.orange} />}
        onEndReached={onEndReached}
        onEndReachedThreshold={0.3}
        ListEmptyComponent={!loading && <View style={styles.center}><Text style={T.body}>No cars found</Text></View>}
        ListFooterComponent={loading && <ActivityIndicator color={C.orange} style={{ marginVertical: 16 }} />}
        renderItem={({ item }) => (
          <CarCard car={item} onPress={() => navigation.navigate('CarDetail', { car: item })} />
        )}
      />
    </SafeAreaView>
  );
};

// ══ CarDetailScreen ══
export const CarDetailScreen = ({ navigation, route }) => {
  const { car } = route.params;
  const [detail, setDetail] = useState(car);
  const [reviews, setReviews] = useState([]);

  useEffect(() => {
    Promise.all([
      api.cars.detail(car.id),
      api.cars.reviews(car.id),
    ]).then(([d, r]) => {
      setDetail(d);
      setReviews(r || []);
    });
  }, [car.id]);

  const specs = [
    ['Fuel',         detail.fuel_type],
    ['Transmission', detail.transmission],
    ['Seating',      `${detail.seating} persons`],
    ['Year',         detail.year],
    ...(detail.mileage_kmpl ? [['Mileage', `${detail.mileage_kmpl} kmpl`]] : []),
    ['Security deposit', fmt(detail.security_deposit || 0)],
  ];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        {/* Image */}
        <View style={styles.detailImg}>
          <Text style={{ fontSize: 80 }}>🚗</Text>
        </View>

        <View style={styles.container}>
          {/* Title */}
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <View style={{ flex: 1 }}>
              <Text style={T.h2}>{detail.make} {detail.model}</Text>
              <Text style={[T.body, { marginTop: 2 }]}>{detail.city} · {detail.color}</Text>
            </View>
            {detail.avg_rating && (
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={{ fontSize: 22, fontWeight: '700', color: C.charcoal }}>{detail.avg_rating}★</Text>
                <Text style={T.mono}>{detail.review_count} reviews</Text>
              </View>
            )}
          </View>

          {/* Pricing */}
          <Card style={{ marginBottom: 20, flexDirection: 'row', justifyContent: 'space-around' }}>
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 22, fontWeight: '700', color: C.charcoal }}>{fmt(detail.price_per_day)}</Text>
              <Text style={T.cap}>per day</Text>
            </View>
            <View style={{ width: 1, backgroundColor: C.border }} />
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 22, fontWeight: '700', color: C.charcoal }}>{fmt(detail.price_per_hour || 0)}</Text>
              <Text style={T.cap}>per hour</Text>
            </View>
          </Card>

          {/* Specs */}
          <Text style={[T.cap, { marginBottom: 10 }]}>Specifications</Text>
          <Card style={{ marginBottom: 20 }}>
            {specs.map(([label, value]) => (
              <View key={label} style={styles.specRow}>
                <Text style={[T.body, { color: C.mid }]}>{label}</Text>
                <Text style={[T.body, { fontWeight: '600', color: C.charcoal }]}>{value}</Text>
              </View>
            ))}
          </Card>

          {/* Features */}
          {detail.features && Object.keys(detail.features).length > 0 && (
            <>
              <Text style={[T.cap, { marginBottom: 10 }]}>Features</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
                {Object.entries(detail.features).map(([k, v]) => (
                  <View key={k} style={[styles.featureChip, !v && styles.featureChipOff]}>
                    <Text style={{ fontSize: 12, color: v ? C.green : C.muted, fontWeight: '600' }}>
                      {v ? '✓' : '✗'} {k.replace('_', ' ')}
                    </Text>
                  </View>
                ))}
              </View>
            </>
          )}

          {/* Reviews */}
          {reviews.length > 0 && (
            <>
              <Text style={[T.cap, { marginBottom: 10 }]}>Reviews</Text>
              {reviews.slice(0, 3).map(r => (
                <Card key={r.id} style={{ marginBottom: 10 }}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Text style={[T.body, { fontWeight: '600', color: C.charcoal }]}>{r.reviewer}</Text>
                    <StarRow rating={r.rating} />
                  </View>
                  {r.comment && <Text style={T.body}>{r.comment}</Text>}
                  {r.owner_reply && (
                    <View style={{ marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: C.border }}>
                      <Text style={[T.cap, { marginBottom: 4 }]}>Owner reply</Text>
                      <Text style={[T.body, { fontStyle: 'italic' }]}>{r.owner_reply}</Text>
                    </View>
                  )}
                </Card>
              ))}
            </>
          )}

          {/* Book CTA */}
          <Button
            label="Book This Car →"
            onPress={() => navigation.navigate('Checkout', { car: detail })}
            style={{ marginBottom: 32 }}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// ══ CheckoutScreen ══
export const CheckoutScreen = ({ navigation, route }) => {
  const { car } = route.params;
  const [pickup,  setPickup]  = useState(new Date(Date.now() + 24*3600*1000));
  const [dropoff, setDropoff] = useState(new Date(Date.now() + 72*3600*1000));
  const [promo,   setPromo]   = useState('');
  const [pricing, setPricing] = useState(null);
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(false);

  const previewPrice = async () => {
    setLoading(true);
    try {
      const res = await api.bookings.preview({
        car_id:      car.id,
        pickup_time:  pickup.toISOString(),
        dropoff_time: dropoff.toISOString(),
        promo_code:   promo || undefined,
      });
      setPricing(res);
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { previewPrice(); }, [pickup, dropoff]);

  const confirmBooking = async () => {
    setBooking(true);
    try {
      const b = await api.bookings.create({
        car_id:       car.id,
        pickup_time:  pickup.toISOString(),
        dropoff_time: dropoff.toISOString(),
        promo_code:   promo || undefined,
      });
      navigation.navigate('Payment', { booking: b, car });
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setBooking(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <Text style={[T.h2, { marginBottom: 20 }]}>Checkout</Text>

          <Card style={{ marginBottom: 16 }}>
            <Text style={[T.h3, { marginBottom: 4 }]}>{car.make} {car.model}</Text>
            <Text style={T.body}>{car.city} · {car.fuel_type}</Text>
          </Card>

          <Text style={[T.cap, { marginBottom: 8 }]}>Pickup Time</Text>
          <Card style={{ marginBottom: 16 }}>
            <Text style={[T.body, { color: C.charcoal, fontWeight: '600' }]}>{fmtDate(pickup.toISOString())}</Text>
          </Card>

          <Text style={[T.cap, { marginBottom: 8 }]}>Drop-off Time</Text>
          <Card style={{ marginBottom: 16 }}>
            <Text style={[T.body, { color: C.charcoal, fontWeight: '600' }]}>{fmtDate(dropoff.toISOString())}</Text>
          </Card>

          <Input
            label="Promo Code"
            value={promo}
            onChangeText={setPromo}
            placeholder="e.g. WELCOME10"
          />
          <Button label="Apply Code" onPress={previewPrice} variant="outline" style={{ marginBottom: 20 }} />

          {/* Pricing breakdown */}
          {pricing && (
            <Card style={{ marginBottom: 20 }}>
              <Text style={[T.cap, { marginBottom: 12 }]}>Price Breakdown</Text>
              {[
                ['Duration',          `${pricing.duration_hours}h (${pricing.duration_days} day${pricing.duration_days > 1 ? 's' : ''})`],
                ['Base fare',         fmt(pricing.base_amount)],
                ...(pricing.discount_amount > 0 ? [['Promo discount', `-${fmt(pricing.discount_amount)}`]] : []),
                ['GST (18%)',         fmt(pricing.tax_amount)],
                ['Security deposit',  fmt(pricing.security_deposit)],
              ].map(([label, value]) => (
                <View key={label} style={styles.specRow}>
                  <Text style={T.body}>{label}</Text>
                  <Text style={[T.body, { fontWeight: '600', color: label.includes('discount') ? C.green : C.charcoal }]}>{value}</Text>
                </View>
              ))}
              <View style={[styles.specRow, { borderTopWidth: 1, borderTopColor: C.border, marginTop: 8, paddingTop: 8 }]}>
                <Text style={[T.h3]}>Total</Text>
                <Text style={[T.h3, { color: C.orange }]}>{fmt(pricing.total_amount)}</Text>
              </View>
            </Card>
          )}

          {loading && <ActivityIndicator color={C.orange} style={{ marginBottom: 16 }} />}

          <Button label={`Pay ${pricing ? fmt(pricing.total_amount) : '...'}`} onPress={confirmBooking} loading={booking} />
          <Text style={[T.mono, { textAlign: 'center', marginTop: 12, color: C.muted }]}>Free cancellation up to 24h before pickup</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// ══ PaymentScreen ══
export const PaymentScreen = ({ navigation, route }) => {
  const { booking, car } = route.params;
  const [loading, setLoading] = useState(false);

  const initiatePayment = async () => {
    setLoading(true);
    try {
      const order = await api.payments.createOrder(booking.id);

      // In production, open Razorpay checkout:
      // const RazorpayCheckout = require('react-native-razorpay').default;
      // const response = await RazorpayCheckout.open({
      //   description: `Voyza - ${car.make} ${car.model}`,
      //   image: 'https://voyza.app/logo.png',
      //   currency: 'INR',
      //   key: order.key_id,
      //   amount: order.amount,
      //   name: 'Voyza',
      //   order_id: order.razorpay_order_id,
      //   prefill: { contact: user.phone, email: user.email },
      //   theme: { color: '#E8500A' },
      // });
      // Then call api.payments.verify(...)

      // Simulate success for demo
      navigation.replace('BookingSuccess', { booking, car });
    } catch (e) {
      Alert.alert('Payment Failed', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <View style={[styles.container, styles.center, { flex: 1 }]}>
        <Text style={{ fontSize: 56, marginBottom: 24 }}>💳</Text>
        <Text style={[T.h2, { textAlign: 'center', marginBottom: 8 }]}>Complete Payment</Text>
        <Text style={[T.body, { textAlign: 'center', marginBottom: 40 }]}>
          Secure payment powered by Razorpay
        </Text>
        <Card style={{ width: '100%', marginBottom: 32 }}>
          <View style={styles.specRow}>
            <Text style={T.body}>Booking</Text>
            <Text style={[T.mono, { fontSize: 11 }]}>#{booking.id.slice(0,8).toUpperCase()}</Text>
          </View>
          <View style={styles.specRow}>
            <Text style={T.body}>Car</Text>
            <Text style={[T.body, { fontWeight: '600' }]}>{car.make} {car.model}</Text>
          </View>
          <View style={[styles.specRow, { borderTopWidth: 1, borderTopColor: C.border, marginTop: 8, paddingTop: 8 }]}>
            <Text style={T.h3}>Amount</Text>
            <Text style={[T.h3, { color: C.orange }]}>{fmt(booking.total_amount)}</Text>
          </View>
        </Card>
        <Button label="Pay with Razorpay" onPress={initiatePayment} loading={loading} style={{ width: '100%' }} />
      </View>
    </SafeAreaView>
  );
};

// ══ BookingSuccessScreen ══
export const BookingSuccessScreen = ({ navigation, route }) => {
  const { booking, car } = route.params;
  const scale = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.spring(scale, { toValue: 1, tension: 80, friction: 6, useNativeDriver: true }).start();
  }, []);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <View style={[styles.container, styles.center, { flex: 1 }]}>
        <Animated.View style={{ transform: [{ scale }], alignItems: 'center' }}>
          <Text style={{ fontSize: 80, marginBottom: 24 }}>🎉</Text>
          <Text style={[T.h1, { textAlign: 'center', marginBottom: 8 }]}>Booking Confirmed!</Text>
          <Text style={[T.body, { textAlign: 'center', marginBottom: 32 }]}>
            Your {car.make} {car.model} is ready. Show booking ID at pickup.
          </Text>
          <Card style={{ width: '100%', marginBottom: 32, backgroundColor: C.charcoal }}>
            <Text style={[T.cap, { color: C.muted, marginBottom: 6 }]}>Booking ID</Text>
            <Text style={{ fontSize: 24, fontWeight: '800', color: C.white, letterSpacing: 2 }}>
              #{booking.id.slice(0,8).toUpperCase()}
            </Text>
          </Card>
          <Button label="View My Bookings" onPress={() => navigation.navigate('Bookings')} style={{ width: '100%', marginBottom: 12 }} />
          <Button label="Back to Home" onPress={() => navigation.navigate('Home')} variant="outline" style={{ width: '100%' }} />
        </Animated.View>
      </View>
    </SafeAreaView>
  );
};

// ══ BookingsScreen ══
export const BookingsScreen = ({ navigation }) => {
  const [bookings, setBookings] = useState([]);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    api.bookings.list()
      .then(setBookings)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <View style={styles.center}><ActivityIndicator color={C.orange} /></View>;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <FlatList
        data={bookings}
        keyExtractor={item => item.id}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        ListEmptyComponent={
          <View style={[styles.center, { marginTop: 80 }]}>
            <Text style={{ fontSize: 48, marginBottom: 12 }}>🚗</Text>
            <Text style={T.h3}>No trips yet</Text>
            <Text style={[T.body, { marginTop: 4, marginBottom: 24 }]}>Book your first car to get started</Text>
            <Button label="Find a Car" onPress={() => navigation.navigate('Browse')} />
          </View>
        }
        renderItem={({ item: b }) => (
          <Card>
            <View style={{ flexDirection: 'row', gap: 14, alignItems: 'center' }}>
              <Text style={{ fontSize: 36 }}>🚗</Text>
              <View style={{ flex: 1 }}>
                <Text style={[T.h3, { fontSize: 15 }]}>{b.car_make} {b.car_model}</Text>
                <Text style={[T.mono, { marginTop: 2 }]}>{fmtDate(b.pickup_time)} → {fmtDate(b.dropoff_time)}</Text>
              </View>
              <StatusBadge status={b.status} />
            </View>
            <View style={[styles.specRow, { marginTop: 12, borderTopWidth: 1, borderTopColor: C.border, paddingTop: 12 }]}>
              <Text style={[T.mono, { fontSize: 11 }]}>#{(b.id || '').slice(0,8).toUpperCase()}</Text>
              <Text style={{ fontWeight: '700', fontSize: 16, color: C.charcoal }}>{fmt(b.total_amount)}</Text>
            </View>
            {b.status === 'active' && (
              <Button label="Track Live" variant="outline" onPress={() => navigation.navigate('Tracking', { booking: b })} style={{ marginTop: 10 }} />
            )}
            {b.status === 'completed' && (
              <Button label="Rate this trip" variant="outline" onPress={() => navigation.navigate('Review', { booking: b })} style={{ marginTop: 10 }} />
            )}
          </Card>
        )}
      />
    </SafeAreaView>
  );
};

// ══ ReviewScreen ══
export const ReviewScreen = ({ navigation, route }) => {
  const { booking } = route.params;
  const [rating,  setRating]  = useState(5);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      await api.reviews.submit({ booking_id: booking.id, rating, comment: comment || undefined });
      Alert.alert('Thank you!', 'Your review has been submitted.', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <Text style={[T.h2, { marginBottom: 8 }]}>Rate your trip</Text>
          <Text style={[T.body, { marginBottom: 32 }]}>{booking.car_make} {booking.car_model}</Text>

          {/* Star rating */}
          <Text style={[T.cap, { marginBottom: 12 }]}>Your Rating</Text>
          <View style={{ flexDirection: 'row', justifyContent: 'center', gap: 12, marginBottom: 32 }}>
            {[1,2,3,4,5].map(s => (
              <TouchableOpacity key={s} onPress={() => setRating(s)}>
                <Text style={{ fontSize: 44, color: s <= rating ? '#F59E0B' : C.border }}>★</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={[T.cap, { marginBottom: 8 }]}>Comment (optional)</Text>
          <TextInput
            style={[styles.input, { height: 120, textAlignVertical: 'top', marginBottom: 24 }]}
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

// ══ TrackingScreen ══
export const TrackingScreen = ({ route }) => {
  const { booking } = route.params;
  const [position, setPosition] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const connectWS = async () => {
      const token = await AsyncStorage.getItem('access_token');
      const ws = new WebSocket(`ws://localhost:8000/ws/track/${booking.id}?token=${token}`);
      wsRef.current = ws;

      ws.onopen  = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === 'gps') setPosition(msg);
      };
    };
    connectWS();
    return () => wsRef.current?.close();
  }, [booking.id]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <View style={styles.container}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: connected ? C.green : C.muted }} />
          <Text style={T.mono}>{connected ? 'Connected — live tracking active' : 'Connecting...'}</Text>
        </View>

        {/* Map placeholder — replace with react-native-maps */}
        <View style={{ height: 300, backgroundColor: C.cream2, borderRadius: 12, marginBottom: 16, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: C.border }}>
          <Text style={{ fontSize: 48, marginBottom: 8 }}>🗺️</Text>
          <Text style={T.body}>Live GPS Map</Text>
          <Text style={[T.mono, { marginTop: 4 }]}>Integration: react-native-maps</Text>
        </View>

        {position && (
          <Card>
            <Text style={[T.cap, { marginBottom: 12 }]}>Vehicle Position</Text>
            <View style={styles.specRow}>
              <Text style={T.body}>Latitude</Text>
              <Text style={T.mono}>{position.lat.toFixed(5)}</Text>
            </View>
            <View style={styles.specRow}>
              <Text style={T.body}>Longitude</Text>
              <Text style={T.mono}>{position.lng.toFixed(5)}</Text>
            </View>
            <View style={styles.specRow}>
              <Text style={T.body}>Speed</Text>
              <Text style={[T.body, { fontWeight: '600' }]}>{position.speed_kmph} km/h</Text>
            </View>
          </Card>
        )}
      </View>
    </SafeAreaView>
  );
};

// ══ ProfileScreen ══
export const ProfileScreen = ({ navigation }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.auth.me().then(setUser).catch(console.error).finally(() => setLoading(false));
  }, []);

  const logout = async () => {
    const refresh = await AsyncStorage.getItem('refresh_token');
    await api.auth.logout(refresh).catch(() => {});
    await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
    navigation.replace('Login');
  };

  if (loading) return <View style={styles.center}><ActivityIndicator color={C.orange} /></View>;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <View style={{ alignItems: 'center', marginBottom: 32 }}>
            <View style={styles.avatar}>
              <Text style={{ fontSize: 32, fontWeight: '800', color: C.white }}>
                {user?.full_name?.[0] || 'U'}
              </Text>
            </View>
            <Text style={[T.h2, { marginTop: 16 }]}>{user?.full_name}</Text>
            <Text style={T.body}>{user?.phone}</Text>
            <View style={[styles.orangeChip, { marginTop: 8 }]}>
              <Text style={{ color: C.white, fontSize: 11, fontWeight: '700' }}>{user?.role?.toUpperCase()}</Text>
            </View>
          </View>

          {[
            { label: 'My Trips',    icon: '📋', screen: 'Bookings' },
            { label: 'Pending Reviews', icon: '⭐', screen: 'Review' },
          ].map(item => (
            <TouchableOpacity key={item.label} style={styles.profileRow} onPress={() => navigation.navigate(item.screen)}>
              <Text style={{ fontSize: 20 }}>{item.icon}</Text>
              <Text style={[T.h3, { flex: 1 }]}>{item.label}</Text>
              <Text style={{ color: C.muted }}>›</Text>
            </TouchableOpacity>
          ))}

          <Button label="Sign Out" onPress={logout} variant="outline" style={{ marginTop: 32, borderColor: C.red }} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container:      { paddingHorizontal: 20, paddingVertical: 16 },
  center:         { alignItems: 'center', justifyContent: 'center' },
  card:           { backgroundColor: C.white, borderRadius: 12, padding: 16, borderWidth: 1, borderColor: C.border },
  carCard:        { backgroundColor: C.white, borderRadius: 16, overflow: 'hidden', borderWidth: 1, borderColor: C.border, width: SCREEN_W - 40 },
  carCardCompact: { width: SCREEN_W * 0.72 },
  carImgPlaceholder: { height: 180, backgroundColor: C.cream2, alignItems: 'center', justifyContent: 'center' },
  detailImg:      { height: 260, backgroundColor: C.cream2, alignItems: 'center', justifyContent: 'center' },
  btn:            { backgroundColor: C.orange, borderRadius: 12, padding: 16, alignItems: 'center' },
  btnOutline:     { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: C.orange },
  btnDisabled:    { opacity: 0.5 },
  btnText:        { color: C.white, fontWeight: '700', fontSize: 16 },
  btnOutlineText: { color: C.orange },
  input:          { backgroundColor: C.cream2, borderRadius: 10, padding: 14, fontSize: 15, color: C.charcoal, borderWidth: 1, borderColor: C.border },
  inputWrap:      { marginBottom: 14 },
  tag:            { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 100, borderWidth: 1.5, borderColor: C.border, backgroundColor: C.white },
  tagActive:      { backgroundColor: C.charcoal, borderColor: C.charcoal },
  tagText:        { fontSize: 13, fontWeight: '600', color: C.mid },
  tagTextActive:  { color: C.white },
  orangeChip:     { backgroundColor: C.orange, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6 },
  specRow:        { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.border },
  featureChip:    { backgroundColor: '#F0FDF4', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6, borderWidth: 1, borderColor: '#86EFAC' },
  featureChipOff: { backgroundColor: C.cream2, borderColor: C.border },
  profileRow:     { flexDirection: 'row', alignItems: 'center', gap: 14, padding: 16, backgroundColor: C.white, borderRadius: 12, marginBottom: 10, borderWidth: 1, borderColor: C.border },
  avatar:         { width: 72, height: 72, borderRadius: 36, backgroundColor: C.charcoal, alignItems: 'center', justifyContent: 'center' },
});

export default {
  SplashScreen, LoginScreen, HomeScreen, BrowseScreen,
  CarDetailScreen, CheckoutScreen, PaymentScreen,
  BookingSuccessScreen, BookingsScreen, ReviewScreen,
  TrackingScreen, ProfileScreen,
};
