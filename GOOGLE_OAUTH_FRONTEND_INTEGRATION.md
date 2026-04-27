# Google OAuth Frontend Integration Guide

Complete frontend implementation for Google Sign-In with phone verification.

## 📦 Prerequisites

```bash
npm install @react-oauth/google
# or
yarn add @react-oauth/google
```

## 🔧 Step 1: Setup Google OAuth Provider

**Create `src/providers/GoogleOAuthProvider.tsx`:**

```tsx
import { GoogleOAuthProvider } from '@react-oauth/google';
import { ReactNode } from 'react';

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

export function GoogleOAuthProvider_({ children }: { children: ReactNode }) {
  if (!GOOGLE_CLIENT_ID) {
    throw new Error('REACT_APP_GOOGLE_CLIENT_ID is not set');
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      {children}
    </GoogleOAuthProvider>
  );
}
```

**Add to `.env.local`:**
```
REACT_APP_GOOGLE_CLIENT_ID=<your_google_client_id>
REACT_APP_API_URL=https://api.voyzacar.online/api/v1
```

**Wrap your app:**
```tsx
import { GoogleOAuthProvider_ } from './providers/GoogleOAuthProvider';

function App() {
  return (
    <GoogleOAuthProvider_>
      {/* Your app routes */}
    </GoogleOAuthProvider_>
  );
}
```

---

## 🎯 Step 2: Google Sign-In Button Component

**Create `src/components/GoogleSignInButton.tsx`:**

```tsx
import { useGoogleLogin } from '@react-oauth/google';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface GoogleSignInProps {
  onSuccess?: (tokens: any) => void;
  onError?: (error: any) => void;
}

export function GoogleSignInButton({ onSuccess, onError }: GoogleSignInProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useGoogleLogin({
    onSuccess: async (codeResponse) => {
      try {
        setLoading(true);
        setError(null);

        // Exchange code for Voyza tokens
        const response = await fetch(
          `${process.env.REACT_APP_API_URL}/auth/oauth/google/callback?code=${codeResponse.code}`,
          {
            method: 'GET',
          }
        );

        if (!response.ok) {
          throw new Error('Failed to sign in with Google');
        }

        const data = await response.json();

        // Store temporary OAuth token
        localStorage.setItem('oauthAccessToken', data.access_token);
        localStorage.setItem('oauthTokenType', data.token_type);

        // Redirect to phone linking page
        navigate('/auth/oauth/link-phone');

        if (onSuccess) {
          onSuccess(data);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);
        if (onError) {
          onError(err);
        }
      } finally {
        setLoading(false);
      }
    },
    onError: () => {
      setError('Failed to sign in with Google');
    },
    flow: 'auth-code',
    redirect_uri: `${window.location.origin}/auth/oauth/google/callback`,
  });

  return (
    <div>
      <button
        onClick={() => login()}
        disabled={loading}
        style={{
          padding: '10px 20px',
          backgroundColor: '#4285F4',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontSize: '16px',
          fontWeight: '500',
        }}
      >
        {loading ? 'Signing in...' : 'Sign in with Google'}
      </button>
      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
    </div>
  );
}
```

---

## 📱 Step 3: Phone Linking Component (After OAuth)

**Create `src/components/OAuthPhoneLinking.tsx`:**

```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function OAuthPhoneLinking() {
  const navigate = useNavigate();
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accessToken = localStorage.getItem('oauthAccessToken');

  if (!accessToken) {
    return <p>Error: No OAuth session found. Please sign in again.</p>;
  }

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      // Format phone number (remove +91 if present)
      const formattedPhone = phone.replace(/^\+91/, '');

      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/auth/send-otp`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            phone: formattedPhone,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to send OTP');
      }

      setStep('otp');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const formattedPhone = phone.replace(/^\+91/, '');

      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/auth/oauth/link-phone`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            phone: formattedPhone,
            otp: otp,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to verify OTP');
      }

      // Phone linked, move to password setting
      navigate('/auth/oauth/set-password');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to verify OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto' }}>
      <h2>Link Phone Number</h2>
      <p>Your Google account is verified. Now link your phone number to complete signup.</p>

      {step === 'phone' ? (
        <form onSubmit={handleSendOtp}>
          <input
            type="tel"
            placeholder="Enter 10-digit phone number (e.g., 9876543210)"
            value={phone}
            onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
            maxLength="10"
            required
            style={{
              width: '100%',
              padding: '10px',
              marginBottom: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '16px',
            }}
          />
          <button
            type="submit"
            disabled={loading || phone.length !== 10}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#4285F4',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading || phone.length !== 10 ? 'not-allowed' : 'pointer',
              fontSize: '16px',
              fontWeight: '500',
            }}
          >
            {loading ? 'Sending OTP...' : 'Send OTP'}
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOtp}>
          <p>Enter the OTP sent to {phone}</p>
          <input
            type="text"
            placeholder="6-digit OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
            maxLength="6"
            required
            style={{
              width: '100%',
              padding: '10px',
              marginBottom: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '16px',
            }}
          />
          <button
            type="submit"
            disabled={loading || otp.length !== 6}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#4285F4',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading || otp.length !== 6 ? 'not-allowed' : 'pointer',
              fontSize: '16px',
              fontWeight: '500',
            }}
          >
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
          <button
            type="button"
            onClick={() => setStep('phone')}
            style={{
              width: '100%',
              padding: '10px',
              marginTop: '10px',
              backgroundColor: '#f0f0f0',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px',
            }}
          >
            Back
          </button>
        </form>
      )}

      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
    </div>
  );
}
```

---

## 🔐 Step 4: Set Password Component

**Create `src/components/OAuthSetPassword.tsx`:**

```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function OAuthSetPassword() {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accessToken = localStorage.getItem('oauthAccessToken');

  if (!accessToken) {
    return <p>Error: No OAuth session found.</p>;
  }

  const handleSetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }

      if (password.length < 8) {
        setError('Password must be at least 8 characters');
        return;
      }

      setLoading(true);
      setError(null);

      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/auth/oauth/set-password`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            password: password,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to set password');
      }

      // Clear OAuth token and redirect to login
      localStorage.removeItem('oauthAccessToken');
      localStorage.removeItem('oauthTokenType');

      alert('Account created successfully! Please log in with your phone number.');
      navigate('/login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto' }}>
      <h2>Set Backup Password</h2>
      <p>Create a password as backup authentication in case you lose access to Google.</p>

      <form onSubmit={handleSetPassword}>
        <input
          type="password"
          placeholder="Password (min. 8 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{
            width: '100%',
            padding: '10px',
            marginBottom: '10px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '16px',
            boxSizing: 'border-box',
          }}
        />

        <input
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          style={{
            width: '100%',
            padding: '10px',
            marginBottom: '10px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '16px',
            boxSizing: 'border-box',
          }}
        />

        <button
          type="submit"
          disabled={loading || password.length < 8}
          style={{
            width: '100%',
            padding: '10px',
            backgroundColor: '#4285F4',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading || password.length < 8 ? 'not-allowed' : 'pointer',
            fontSize: '16px',
            fontWeight: '500',
          }}
        >
          {loading ? 'Creating Account...' : 'Complete Signup'}
        </button>
      </form>

      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
    </div>
  );
}
```

---

## 🔑 Step 5: Updated Login Component

**Update login to support email + password:**

```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleSignInButton } from './GoogleSignInButton';

export function LoginPage() {
  const navigate = useNavigate();
  const [loginMethod, setLoginMethod] = useState<'phone-otp' | 'email-password'>('phone-otp');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'request' | 'verify'>('request');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.REACT_APP_API_URL;

  // Phone + OTP Login
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const formattedPhone = phone.replace(/\D/g, '');

      const response = await fetch(`${API_URL}/auth/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: formattedPhone }),
      });

      if (!response.ok) throw new Error('Failed to send OTP');

      setStep('verify');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const formattedPhone = phone.replace(/\D/g, '');

      const response = await fetch(`${API_URL}/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: formattedPhone,
          otp: otp,
          purpose: 'login',
        }),
      });

      if (!response.ok) throw new Error('Invalid OTP');

      const data = await response.json();

      // Store tokens
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('refreshToken', data.refresh_token);

      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  // Email + Password Login
  const handleEmailPasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      if (!response.ok) throw new Error('Invalid email or password');

      const data = await response.json();

      // Store tokens
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('refreshToken', data.refresh_token);

      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto' }}>
      <h1>Voyza Login</h1>

      {/* Google Sign-In */}
      <div style={{ marginBottom: '30px' }}>
        <GoogleSignInButton />
      </div>

      <hr />

      {/* Login Method Selector */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ marginRight: '20px' }}>
          <input
            type="radio"
            value="phone-otp"
            checked={loginMethod === 'phone-otp'}
            onChange={(e) => setLoginMethod(e.target.value as any)}
          />
          Phone + OTP
        </label>
        <label>
          <input
            type="radio"
            value="email-password"
            checked={loginMethod === 'email-password'}
            onChange={(e) => setLoginMethod(e.target.value as any)}
          />
          Email + Password
        </label>
      </div>

      {/* Phone + OTP Form */}
      {loginMethod === 'phone-otp' && (
        <form onSubmit={step === 'request' ? handleSendOtp : handleVerifyOtp}>
          {step === 'request' ? (
            <>
              <input
                type="tel"
                placeholder="Phone (10 digits)"
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                maxLength="10"
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  marginBottom: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '16px',
                  boxSizing: 'border-box',
                }}
              />
              <button type="submit" disabled={loading || phone.length !== 10}>
                {loading ? 'Sending...' : 'Send OTP'}
              </button>
            </>
          ) : (
            <>
              <input
                type="text"
                placeholder="6-digit OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                maxLength="6"
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  marginBottom: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '16px',
                  boxSizing: 'border-box',
                }}
              />
              <button type="submit" disabled={loading || otp.length !== 6}>
                {loading ? 'Verifying...' : 'Verify OTP'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setStep('request');
                  setOtp('');
                }}
                style={{ marginTop: '10px' }}
              >
                Back
              </button>
            </>
          )}
        </form>
      )}

      {/* Email + Password Form */}
      {loginMethod === 'email-password' && (
        <form onSubmit={handleEmailPasswordLogin}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '10px',
              marginBottom: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '16px',
              boxSizing: 'border-box',
            }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '10px',
              marginBottom: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '16px',
              boxSizing: 'border-box',
            }}
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      )}

      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
    </div>
  );
}
```

---

## 🛣️ Step 6: Add Routes

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { OAuthPhoneLinking } from './components/OAuthPhoneLinking';
import { OAuthSetPassword } from './components/OAuthSetPassword';

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/oauth/link-phone" element={<OAuthPhoneLinking />} />
      <Route path="/auth/oauth/set-password" element={<OAuthSetPassword />} />
      {/* Other routes */}
    </Routes>
  );
}
```

---

## ✅ Complete Signup/Login Flow

### Google OAuth Signup:
```
1. User clicks "Sign in with Google"
2. Google login modal opens
3. User authorizes Voyza
4. Backend exchanges code for tokens
5. Redirect to /auth/oauth/link-phone
6. User enters phone + OTP
7. Redirect to /auth/oauth/set-password
8. User sets backup password
9. Account created ✅
```

### Phone + OTP Login:
```
1. User selects "Phone + OTP"
2. Enters phone number
3. Receives OTP
4. Enters OTP
5. Logged in with access_token + refresh_token ✅
```

### Email + Password Login:
```
1. User selects "Email + Password"
2. Enters email + password
3. Logged in with access_token + refresh_token ✅
```

---

## 🧪 Testing Checklist

- [ ] Google Sign-In button works
- [ ] OAuth callback receives code
- [ ] Phone linking form appears
- [ ] Phone OTP can be sent/verified
- [ ] Password setting works
- [ ] Phone + OTP login works
- [ ] Email + Password login works
- [ ] Tokens stored in localStorage
- [ ] Refresh token works
- [ ] Logout clears tokens

Done! Your frontend is ready. 🎉
