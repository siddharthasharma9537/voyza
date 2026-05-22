import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
};

export const storage = {
  getAccessToken: (): Promise<string | null> =>
    AsyncStorage.getItem(KEYS.ACCESS_TOKEN),

  getRefreshToken: (): Promise<string | null> =>
    AsyncStorage.getItem(KEYS.REFRESH_TOKEN),

  setTokens: async (access: string, refresh: string): Promise<void> => {
    await AsyncStorage.multiSet([
      [KEYS.ACCESS_TOKEN, access],
      [KEYS.REFRESH_TOKEN, refresh],
    ]);
  },

  clearTokens: async (): Promise<void> => {
    await AsyncStorage.multiRemove([KEYS.ACCESS_TOKEN, KEYS.REFRESH_TOKEN]);
  },
};
