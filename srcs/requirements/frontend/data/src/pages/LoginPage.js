import { useUser } from '../contexts/UserContext.js';

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/LoginForm.js';
//import useLogin from '../hooks/useLogin.js';

export default function LoginPage() {
//  const [loginStatus, setLoginStatus] = useState(null);
  const navigate = useNavigate();
//  const { login } = useLogin();
  const { login } = useUser();
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (userData) => {
    setError(false);
    setLoading(true);
    try {
      await login(userData);
      navigate('/leaderboard');
/*      if (success) {
        setLoginStatus('success');
        navigate('/leaderboard');
      } else {
        setLoginStatus('failure');
      }*/
    } catch (error) {
      setError(true);
//      setLoginStatus('failure');
    } finally {
      setLoading(false);
    }
  };
  return (
    <>
      {loading && <p>Logging in...</p>}
      {error && <p>Error while trying to log in</p>}
      <LoginForm onLogin={handleLogin} />
    </>
  );
}
