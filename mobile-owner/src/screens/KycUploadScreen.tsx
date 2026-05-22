import React, { useState } from 'react';
import { View, Text, SafeAreaView, ScrollView, Alert, Image, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import * as ImagePicker from 'expo-image-picker';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Button } from '../components/Button';

const OWNER_DOCS = ['vehicle_rc', 'vehicle_insurance'];

const DOC_LABELS: Record<string, string> = {
  vehicle_rc: 'Vehicle RC',
  vehicle_insurance: 'Vehicle Insurance',
  driving_license: 'Driving License',
  aadhar: 'Aadhar ID',
  selfie: 'Selfie Verification',
};

export const KycUploadScreen: React.FC = () => {
  const navigation = useNavigation();
  const [selectedType, setSelectedType] = useState<string>(OWNER_DOCS[0]);
  const [image, setImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') { Alert.alert('Permission needed'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });
    if (!result.canceled) setImage(result.assets[0].uri);
  };

  const upload = async () => {
    if (!image) { Alert.alert('Select a photo'); return; }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('document_type', selectedType);
      formData.append('file', { uri: image, name: 'document.jpg', type: 'image/jpeg' } as any);
      await api.kyc.upload(formData);
      Alert.alert('Uploaded!', 'Document submitted for review.', [{ text: 'OK', onPress: () => navigation.goBack() }]);
    } catch (e: any) { Alert.alert('Upload Failed', e.message); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <Text style={[FONT.h2, { marginBottom: 8 }]}>Upload Document</Text>
          <Text style={[FONT.body, { marginBottom: 24 }]}>Submit vehicle documents for verification</Text>

          <Text style={[FONT.cap, { marginBottom: 12 }]}>Document Type</Text>
          {OWNER_DOCS.map((type) => (
            <TouchableOpacity
              key={type}
              style={[styles.docOption, selectedType === type && styles.docOptionActive]}
              onPress={() => { setSelectedType(type); setImage(null); }}
            >
              <Text style={[styles.docLabel, selectedType === type && styles.docLabelActive]}>{DOC_LABELS[type]}</Text>
              {selectedType === type && <Text style={{ color: C.orange }}>✓</Text>}
            </TouchableOpacity>
          ))}

          <Text style={[FONT.cap, { marginBottom: 12, marginTop: 24 }]}>Photo</Text>
          <TouchableOpacity style={styles.imageBox} onPress={pickImage}>
            {image ? (
              <Image source={{ uri: image }} style={styles.image} />
            ) : (
              <>
                <Text style={{ fontSize: 32, marginBottom: 8 }}>📷</Text>
                <Text style={FONT.body}>Tap to choose from gallery</Text>
              </>
            )}
          </TouchableOpacity>

          <Button label="Upload Document" onPress={upload} loading={loading} style={{ marginTop: 24 }} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingVertical: 16 },
  docOption: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 14, backgroundColor: C.white, borderRadius: 10, borderWidth: 1.5, borderColor: C.border, marginBottom: 8 },
  docOptionActive: { borderColor: C.charcoal },
  docLabel: { fontSize: 15, fontWeight: '600', color: C.charcoal },
  docLabelActive: { color: C.charcoal },
  imageBox: { height: 220, backgroundColor: C.cream2, borderRadius: 12, borderWidth: 1, borderColor: C.border, borderStyle: 'dashed', alignItems: 'center', justifyContent: 'center' },
  image: { width: '100%', height: '100%', borderRadius: 12 },
});
